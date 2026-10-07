"""Report-only quality gates (motion-quality-plan G1), run after the final render. Nothing here rejects or
retries a video: `check()` only measures the finished video and its composition and reports what it found.
`copy`, `contrast`, `safe_zone`, `min_px`, `overlap`, `frame0`, `poster` and `fonts` read the composition
through `qa-probe.mjs`, a headless-Chrome probe run in the same jail the render uses (no network). `check`
shells out to `hyperframes check --json` inside the jail. `audio` reads the already-encoded video only."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from . import engine, sampler
from .core import PKG_DIR, Ctx, DataError, Preset, Unavailable

SCHEMA_VERSION = 1

# Apple HIG: 11 pt is the minimum legible text size, defined against a 393-pt-wide phone (e.g. iPhone 14).
# Scaling that to this frame's pixels is the same `width / 393` ratio review.py's reviewer prompt already
# uses for its own min-text-px number, kept here so the two numbers never drift apart.
HIG_MIN_PT = 11
HIG_REFERENCE_WIDTH = 393

# WCAG 2.x: "large text" needs only a 3:1 contrast ratio instead of 4.5:1 once it is >= 18pt regular or
# >= 14pt (18.66px) bold. 1pt == 1px at the HIG reference width above, so the same width ratio scales these.
LARGE_TEXT_REGULAR_PT = 24
LARGE_TEXT_BOLD_PT = 18.66
BOLD_WEIGHT = 600
NORMAL_RATIO = 4.5
LARGE_RATIO = 3.0

OVERLAP_MIN_AREA_PX = 4  # a shared pixel or two at a rounded edge is not an overlap finding
FRAME0_UNIFORM_SPREAD = 12  # ffmpeg signalstats YMAX-YMIN below this (0-255) reads as a near-blank frame
PROBE_TIMEOUT_S = 180
CHECK_TIMEOUT_S = 180


# --- small math: WCAG contrast, HIG scaling --------------------------------------------------------------

def _srgb_channel(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[float, float, float]) -> float:
    r, g, b = (_srgb_channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(rgb1: tuple[float, float, float], rgb2: tuple[float, float, float]) -> float:
    """WCAG 2.x contrast ratio: (L1 + 0.05) / (L2 + 0.05), lighter over darker."""
    l1, l2 = relative_luminance(rgb1), relative_luminance(rgb2)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def _blend(fg: tuple[float, float, float], alpha: float, bg: tuple[float, float, float]) -> tuple[float, float, float]:
    """Alpha-composite a (possibly translucent, possibly dimmed-by-opacity) foreground onto an opaque bg."""
    alpha = max(0.0, min(1.0, alpha))
    return tuple(f * alpha + b * (1 - alpha) for f, b in zip(fg, bg))


def min_text_px(width: int) -> int:
    """Apple HIG's 11pt minimum, scaled from its 393pt-wide reference phone to this frame's pixels."""
    return round(HIG_MIN_PT * width / HIG_REFERENCE_WIDTH)


def large_text_px(width: int, bold: bool) -> float:
    base = LARGE_TEXT_BOLD_PT if bold else LARGE_TEXT_REGULAR_PT
    return base * width / HIG_REFERENCE_WIDTH


# --- composition inspection: declared fonts, banned copy -------------------------------------------------

FONT_FACE_RE = re.compile(r"@font-face\s*{[^}]*font-family\s*:\s*([^;]+);", re.I | re.S)


def declared_font_families(html: str) -> set[str]:
    out = set()
    for block in FONT_FACE_RE.findall(html):
        out.add(block.strip().strip("'\"").lower())
    return out


def _word_pattern(phrase: str) -> re.Pattern:
    return re.compile(r"\b" + re.escape(phrase.strip()) + r"\b", re.I)


def _normalize_words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _similar_but_not_equal(candidate: str, expected: str) -> bool:
    """True when `candidate` shares most of `expected`'s words but is not character-for-character the
    same line: evidence that an exact line (the offer, the brand, the CTA) drifted instead of being typed
    verbatim. A candidate sharing nothing with `expected` is unrelated text, not a mismatch."""
    if candidate.strip() == expected.strip():
        return False
    cw, ew = _normalize_words(candidate), _normalize_words(expected)
    if not ew:
        return False
    overlap = len(cw & ew) / len(ew)
    return overlap >= 0.6


# --- gate: copy -------------------------------------------------------------------------------------------

def check_copy(p: Preset, texts: list[str]) -> list[dict]:
    findings = []
    pool = " \n".join(texts)
    for banned in p.get("content.banned", []):
        if _word_pattern(str(banned)).search(pool):
            findings.append({"gate": "copy", "t": None, "detail": f"banned word/phrase found: {banned!r}"})
    for key, expected in p.get("content.exact_lines", {}).items():
        if str(expected).strip() in texts:
            continue
        for line in texts:
            if _similar_but_not_equal(line, str(expected)):
                findings.append({"gate": "copy", "t": None,
                                 "detail": f"content.exact_lines[{key!r}] expected exactly {expected!r}, found {line!r}"})
                break
    cta = p.get("content.cta")
    if cta and str(cta).strip() not in texts:
        for line in texts:
            if _similar_but_not_equal(line, str(cta)):
                findings.append({"gate": "copy", "t": None,
                                 "detail": f"content.cta expected exactly {cta!r}, found {line!r}"})
                break
    return findings


# --- gate: hyperframes check (informational: finding 6, it misfires on some brands) ----------------------

def run_hf_check(ctx: Ctx, comp: Path, work: Path, version: str, sandbox: bool) -> dict | None:
    """`hyperframes check <comp> --json` inside the jail. Returns the parsed JSON, or None if the tool itself
    could not run (never raises: a broken `check` must not take the report-only gate down with it)."""
    try:
        hf = engine.hf_bin(ctx, version)
        eng_root = engine.engine_root(ctx, version)
        chrome = engine.chrome_path(ctx, version)
        node_ro, node_path = engine.node_dirs(ctx)
        home = work / "check-home"
        home.mkdir(parents=True, exist_ok=True)
        env = engine.base_env(home, [eng_root / "node_modules" / ".bin", *node_path])
        env["HYPERFRAMES_BROWSER_PATH"] = str(chrome)
        argv = [str(hf), "check", str(comp), "--json"]
        if sandbox:
            prefix = engine.bwrap_argv(work, home, rw=[work],  # the agent's page runs here: no network, as the probe
                                       ro=[eng_root, engine.chrome_root(chrome), *node_ro, comp], env=env,
                                       network=False)
            cmd, run_env = prefix + argv, None
        else:
            cmd, run_env = argv, env
        res = subprocess.run(cmd, capture_output=True, text=True, env=run_env, timeout=CHECK_TIMEOUT_S)
        return json.loads(res.stdout)
    except Exception:
        return None


def check_hf(ctx: Ctx, comp: Path, work: Path, version: str, sandbox: bool) -> tuple[str, list[dict]]:
    data = run_hf_check(ctx, comp, work, version, sandbox)
    if data is None:
        return "skipped", []
    findings = []
    for section in ("lint", "runtime", "layout", "motion", "contrast"):
        for f in data.get(section, {}).get("findings", []) or []:
            detail = f.get("message") if isinstance(f, dict) else str(f)
            t = f.get("time") if isinstance(f, dict) else None
            findings.append({"gate": "check", "t": t, "detail": f"{section}: {detail}"})
    return ("ok" if data.get("ok") else "fail"), findings


# --- the composition probe (qa-probe.mjs) -----------------------------------------------------------------

def run_probe(ctx: Ctx, comp: Path, work: Path, version: str, sandbox: bool, width: int, height: int,
              times: list[float]) -> dict[float, list[dict]]:
    """Run qa-probe.mjs inside the jail (no network) and return {time: [visible text nodes]}."""
    node_bin = shutil.which("node")
    if not node_bin:
        raise Unavailable("node not found", "install Node.js 22 or later")
    eng_root = engine.engine_root(ctx, version)
    chrome = engine.chrome_path(ctx, version)
    node_ro, node_path = engine.node_dirs(ctx)
    script = PKG_DIR / "data" / "qa-probe.mjs"
    home = work / "probe-home"
    home.mkdir(parents=True, exist_ok=True)
    config_path = work / "qa-probe-config.json"
    config_path.write_text(json.dumps({"html": str(comp / "index.html"), "chrome": str(chrome),
                                       "engineRoot": str(eng_root), "width": width, "height": height,
                                       "times": times, "userDataDir": str(work / "chrome-profile")}))
    env = engine.base_env(home, [eng_root / "node_modules" / ".bin", *node_path])
    argv = [node_bin, str(script), str(config_path)]
    if sandbox:
        prefix = engine.bwrap_argv(work, home, rw=[work],
                                   ro=[eng_root, engine.chrome_root(chrome), *node_ro, comp, script.parent],
                                   env=env, network=False)
        cmd, run_env = prefix + argv, None
    else:
        cmd, run_env = argv, env
    res = subprocess.run(cmd, capture_output=True, text=True, env=run_env, timeout=PROBE_TIMEOUT_S)
    if res.returncode != 0 or not res.stdout.strip():
        raise DataError(f"qa probe failed: {(res.stdout + res.stderr).strip()[-1500:]}")
    data = json.loads(res.stdout)
    return {entry["t"]: entry["nodes"] for entry in data["times"]}


# --- gates computed from the probe's nodes ------------------------------------------------------------------

def _box_corners(box: dict) -> tuple[float, float, float, float]:
    return box["x"], box["y"], box["x"] + box["w"], box["y"] + box["h"]


def _overlap_area(a: dict, b: dict) -> float:
    ax0, ay0, ax1, ay1 = _box_corners(a)
    bx0, by0, bx1, by1 = _box_corners(b)
    w = min(ax1, bx1) - max(ax0, bx0)
    h = min(ay1, by1) - max(ay0, by0)
    return max(0.0, w) * max(0.0, h)


def check_contrast(nodes: list[dict], t: float, width: int) -> list[dict]:
    findings = []
    for n in nodes:
        if n.get("bg") is None:
            continue  # an unknown background (image/gradient) is skipped, never a finding
        bold = n["font_weight"] >= BOLD_WEIGHT
        large = n["font_size"] >= large_text_px(width, bold)
        threshold = LARGE_RATIO if large else NORMAL_RATIO
        alpha = n["color"][3] * n["opacity"]
        fg = _blend(tuple(n["color"][:3]), alpha, tuple(n["bg"][:3]))
        ratio = contrast_ratio(fg, tuple(n["bg"][:3]))
        if ratio < threshold:
            findings.append({"gate": "contrast", "t": t,
                             "detail": f"{ratio:.2f}:1 (needs {threshold}:1) on {n['text']!r}"})
    return findings


def check_safe_zone(nodes: list[dict], t: float, width: int, height: int, safe: dict) -> list[dict]:
    x0, y0 = width * safe.get("left", 0.06), height * safe.get("top", 0.12)
    x1, y1 = width * (1 - safe.get("right", 0.10)), height * (1 - safe.get("bottom", 0.25))
    findings = []
    for n in nodes:
        bx0, by0, bx1, by1 = _box_corners(n["box"])
        if bx0 < x0 or by0 < y0 or bx1 > x1 or by1 > y1:
            findings.append({"gate": "safe_zone", "t": t, "detail": f"{n['text']!r} outside the safe zone"})
    return findings


def check_min_px(nodes: list[dict], t: float, width: int) -> list[dict]:
    floor = min_text_px(width)
    return [{"gate": "min_px", "t": t, "detail": f"{n['font_size']:.0f}px (needs >= {floor}px) on {n['text']!r}"}
            for n in nodes if n["font_size"] < floor]


def check_overlap(nodes: list[dict], t: float) -> list[dict]:
    findings = []
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            if nodes[i]["text"] == nodes[j]["text"]:
                continue
            # A line and a word inside it ("Say <span>one</span> thing."): one block of text, not two colliding
            if nodes[i].get("id") in nodes[j].get("parents", []) or nodes[j].get("id") in nodes[i].get("parents", []):
                continue
            if _overlap_area(nodes[i]["box"], nodes[j]["box"]) > OVERLAP_MIN_AREA_PX:
                findings.append({"gate": "overlap", "t": t,
                                 "detail": f"{nodes[i]['text']!r} overlaps {nodes[j]['text']!r}"})
    return findings


def check_fonts(nodes_by_time: dict[float, list[dict]], declared: set[str]) -> list[dict]:
    seen, findings = set(), []
    for nodes in nodes_by_time.values():
        for n in nodes:
            family = str(n.get("font_family", "")).strip()
            if not family or n.get("font_generic") or family.lower() in declared or family.lower() in seen:
                continue
            seen.add(family.lower())
            findings.append({"gate": "fonts", "t": None,
                             "detail": f"{family!r} is not declared by an @font-face in the composition"})
    return findings


# --- gates computed from the rendered video itself ------------------------------------------------------

def _frame0_spread(video: Path) -> float:
    """YMAX - YMIN (0-255) of frame 0: small means a near-uniform, possibly blank, first frame."""
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-loglevel", "error", "-i", str(video),
                          "-frames:v", "1", "-vf", "signalstats,metadata=print:file=-", "-f", "null", "-"],
                         capture_output=True, text=True, check=True).stdout
    vals = dict(re.findall(r"lavfi\.signalstats\.(YMAX|YMIN)=([\d.]+)", out))
    if "YMAX" not in vals or "YMIN" not in vals:
        return 0.0
    return float(vals["YMAX"]) - float(vals["YMIN"])


def check_frame0(video: Path, nodes_at_0: list[dict]) -> list[dict]:
    if nodes_at_0:
        return []  # visible text at frame 0: not a ghost, whatever the pixel spread
    if _frame0_spread(video) <= FRAME0_UNIFORM_SPREAD:
        return [{"gate": "frame0", "t": 0.0, "detail": "frame 0 has no visible text and is near-uniform"}]
    return []


def check_poster(poster_at: float | None, holds_s: list[tuple[float, float]]) -> list[dict]:
    if poster_at is None:
        return []
    if any(a <= poster_at <= b for a, b in holds_s):
        return []
    return [{"gate": "poster", "t": poster_at, "detail": "the poster frame falls inside a move, not a settled hold"}]


def check_audio(brief: dict | None, has_audio: bool) -> list[dict]:
    if not brief or has_audio:
        return []
    cues = [*(brief.get("cues") or []), *(shot.get("cue") for shot in brief.get("shots", []) or [])]
    if any(str(c.get("kind", "") if isinstance(c, dict) else c or "").strip() for c in cues):
        return [{"gate": "audio", "t": None, "detail": "the brief has sound cues but the video has no audio stream"}]
    return []


LOUDNESS_TARGET, LOUDNESS_TOLERANCE = -14.0, 1.0  # LUFS integrated; the encode normalizes to the preset's target


def integrated_lufs(video: Path) -> float | None:
    """EBU R128 integrated loudness of the file's audio, or None when it has none or ffmpeg cannot say."""
    res = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True)
    found = re.findall(r"^\s+I:\s+(-?[\d.]+) LUFS", res.stderr, re.M)
    return float(found[-1]) if found else None


def check_loudness(lufs: float | None, target: float = LOUDNESS_TARGET) -> list[dict]:
    if lufs is None or abs(lufs - target) <= LOUDNESS_TOLERANCE:
        return []
    return [{"gate": "loudness", "t": None, "detail": f"{lufs:.1f} LUFS integrated (target {target:.0f} ± "
                                                       f"{LOUDNESS_TOLERANCE:.0f})"}]


# --- entry point --------------------------------------------------------------------------------------------

def check(ctx: Ctx, p: Preset, comp: Path, video: Path, work: Path, version: str, sandbox: bool,
          brief: dict | None, poster_at: float | None) -> dict:
    """Measure the finished video and its composition; report findings. Never rejects or retries anything."""
    work.mkdir(parents=True, exist_ok=True)
    gates: dict[str, str] = {}
    findings: list[dict] = []
    info = engine.probe(video)
    width, height = info["width"], info["height"]
    short = min(width, height)  # text floors scale from the short side, so 16:9 is not held to a 1920 px phone
    fps = int(p.get("video.fps", 30))

    # Only genuine holds (sampler.py: kind "settled"), never its "calmest" fallback frames: those stand in
    # for a reviewer wanting at least a few frames to look at, but they are still mid-motion and would hand
    # pixel-exact gates like contrast a frame that is mid-fade by design (motion-quality-plan finding 6).
    plan = sampler.pick_samples(sampler.motion_curve(video), fps)
    holds = [x for x in plan["settled"] if x["kind"] == "settled"]
    holds_s = [(x["from"] / fps, x["to"] / fps) for x in holds]
    settled_times = sorted({round((x["from"] + x["to"]) / 2 / fps, 3) for x in holds})
    probe_times = sorted({0.0, *settled_times, *([round(poster_at, 3)] if poster_at is not None else [])})

    try:
        nodes_by_time = run_probe(ctx, comp, work, version, sandbox, width, height, probe_times)
    except Exception as e:
        skip = {"gate": None, "t": None, "detail": f"qa probe did not run: {e}"}
        for gate in ("contrast", "safe_zone", "min_px", "overlap", "fonts", "frame0", "copy", "poster"):
            gates[gate] = "skipped"
        findings.append({**skip, "gate": "probe"})
        nodes_by_time = None

    if nodes_by_time is not None:
        settled_nodes = {t: nodes_by_time.get(t, []) for t in settled_times}
        for t, nodes in settled_nodes.items():
            findings += check_contrast(nodes, t, short)
            findings += check_safe_zone(nodes, t, width, height, p.get("video.safe_zone", {}))
            findings += check_min_px(nodes, t, short)
            findings += check_overlap(nodes, t)
        html = (comp / "index.html").read_text() if (comp / "index.html").is_file() else ""
        findings += check_fonts(nodes_by_time, declared_font_families(html))
        findings += check_frame0(video, nodes_by_time.get(0.0, []))
        poster_findings = check_poster(poster_at, holds_s)
        findings += poster_findings
        texts = sorted({n["text"] for nodes in nodes_by_time.values() for n in nodes} |
                       set((brief or {}).get("on_screen_text", []) or []))
        findings += check_copy(p, list(texts))
        for gate in ("contrast", "safe_zone", "min_px", "overlap"):
            gates[gate] = ("skipped" if not settled_times else
                           "fail" if any(f["gate"] == gate for f in findings) else "ok")
        for gate in ("fonts", "frame0", "copy"):
            gates[gate] = "fail" if any(f["gate"] == gate for f in findings) else "ok"
        gates["poster"] = "skipped" if poster_at is None else ("fail" if poster_findings else "ok")

    audio_findings = check_audio(brief, info["audio"])
    findings += audio_findings
    gates["audio"] = "skipped" if not brief else ("fail" if audio_findings else "ok")
    lufs = integrated_lufs(video) if info["audio"] else None
    loud_findings = check_loudness(lufs, float(p.get("encode.loudness", LOUDNESS_TARGET)))
    findings += loud_findings
    gates["loudness"] = "skipped" if lufs is None else ("fail" if loud_findings else "ok")

    check_status, check_findings = check_hf(ctx, comp, work, version, sandbox)
    gates["check"] = check_status
    findings += check_findings

    return {"version": SCHEMA_VERSION, "gates": gates, "findings": findings, "settled": settled_times, "lufs": lufs}
