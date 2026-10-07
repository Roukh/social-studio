"""The independent reviewer (motion-quality-plan A2). Code picks what the reviewer sees from the video's own motion
(sampler.py: settled holds, strips over the biggest moves, frame 0), a fresh session scores it against anchors tied to
observable failures, and Python checks the verdict before anything trusts it."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from . import engine
from .core import PKG_DIR, Ctx, DataError, Preset, StudioError, load_preset, new_id
from .runner import (DEFAULT_CRITERIA, Session, _claude_cost, _common_values, _fill, _history, _read_json,
                     _session_end, _session_row, backend_command, remove_within, resolve_backend, run_jailed,
                     trim_session)
from .sampler import HOLD_S, MIN_SAMPLES, PAGE_PX, STRIP_FRAMES, STRIPS, motion_curve, pick_samples, write_samples

__all__ = ["HOLD_S", "MIN_SAMPLES", "PAGE_PX", "STRIPS", "STRIP_FRAMES", "motion_curve", "pick_samples",
           "write_samples", "composition_css", "task_text", "check_verdict", "review_session", "rescore"]


def composition_css(comp: Path) -> str:
    """The styles the video was built with, so the reviewer reads declared fonts, sizes and shadows, not guesses."""
    html = (comp / "index.html").read_text() if (comp / "index.html").is_file() else ""
    parts = [x.strip() for x in re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I)]
    parts += [f"/* {f.relative_to(comp)} */\n{f.read_text().strip()}" for f in sorted(comp.rglob("*.css"))
              if "vendor" not in f.relative_to(comp).parts]
    inline = []
    for tag, attrs, style in re.findall(r'<(\w+)([^>]*?)\sstyle="([^"]*)"', html):
        name = re.search(r'\s(?:id|class)="([^"]*)"', attrs)
        inline.append(f"{tag} {name.group(1) if name else ''} {{ {style} }}")
    if inline:
        parts.append("/* inline style attributes (tag, then id or class) */\n" + "\n".join(inline))
    return "\n\n".join(parts) + "\n" if parts else "/* the composition declared no styles */\n"


def task_text(p: Preset, size: list[int]) -> str:
    """The reviewer's TASK.md: the prompt with its anchors, and the frame's numbers in pixels."""
    (w, h), safe = size, p.get("video.safe_zone", {})
    vals = {**_common_values(p), "hold_s": HOLD_S, "strips": STRIPS, "strip_frames": STRIP_FRAMES, "width": w,
            "height": h, "min_text_px": round(11 * min(w, h) / 393),  # HIG 11 pt on a 393 pt-wide phone, short side
            "safe_x0": round(w * safe.get("left", 0.06)), "safe_x1": round(w * (1 - safe.get("right", 0.10))),
            "safe_y0": round(h * safe.get("top", 0.12)), "safe_y1": round(h * (1 - safe.get("bottom", 0.25)))}
    vals["safe_check"] = _fill("Text the viewer must read inside the platform safe zone on the settled frames: x from "
                               "{{safe_x0}} to {{safe_x1}} px and y from {{safe_y0}} to {{safe_y1}} px. HUD labels, "
                               "counters and texture type are exempt." if h > w else
                               "Nothing the viewer must read is cut off by the frame edge on the settled frames.", vals)
    anchors = json.loads((PKG_DIR / "data" / "anchors.json").read_text())
    lines = []
    for c in p.get("review.criteria", DEFAULT_CRITERIA):
        a = anchors.get(c, anchors["*"])
        lines.append(f"- **{c}** (judge on {a['on']}): " + "; ".join(f"{k} = {a[k]}" for k in ("10", "7", "4", "1"))
                     + (f". {a['note']}" if a.get("note") else "."))
    vals["anchors"] = _fill("\n".join(lines), vals)
    return _fill((PKG_DIR / "data" / "review_prompt.md").read_text(), vals)


def check_verdict(raw: dict, criteria: list[str], min_score: int) -> dict:
    """verdict.json checked in Python: its shape, every criterion scored 1 to 10, and a pass that agrees with the
    scores and the repeat check. A verdict that fails the check is an error, never a pass."""
    problems = []
    scores = raw.get("scores") if isinstance(raw.get("scores"), dict) else {}
    for c in criteria:
        v = scores.get(c)
        if isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= 10:
            problems.append(f"{c!r} is scored {v!r}, not a whole number from 1 to 10")
    problems += [f"{k!r} is not a criterion" for k in scores if k not in criteria]
    repeat = raw.get("repeat")
    for ok, what in ((isinstance(raw.get("pass"), bool), "pass is not true or false"),
                     (isinstance(repeat, dict) and isinstance(repeat.get("found"), bool), "repeat.found is not true or false"),
                     (isinstance(raw.get("issues"), list) and all(isinstance(i, str) for i in raw.get("issues", [])),
                      "issues is not a list of strings"),
                     (isinstance(raw.get("summary"), str), "summary is not a string")):
        if not ok:
            problems.append(what)
    if problems:
        return {"pass": None, "error": "verdict.json failed its check: " + "; ".join(problems), "raw": raw}
    below = [c for c in criteria if scores[c] < min_score]
    verdict = {**raw, "scores": {c: scores[c] for c in criteria}, "pass": raw["pass"] and not below and not repeat["found"]}
    if verdict["pass"] != raw["pass"]:
        verdict["checked"] = {"reviewer_said": raw["pass"], "below_min": below, "repeat": repeat["found"]}
    return verdict


INPUTS = ("preset.json", "history.json", "video.json", "brief.json")


def review_session(ctx: Ctx, p: Preset, maker: Session, video_file: Path, version: str, sandbox: bool | None,
                   sid: str | None = None, inputs: dict[str, Path] | None = None, comp: Path | None = None,
                   contact: Path | None = None) -> dict:
    """A fresh reviewer, ideally on another model, that never saw the maker's context. The inputs default to the
    maker session's own files; a re-score passes them from the library instead."""
    b = resolve_backend(ctx, p, p.get("review.backend"), p.get("review.model"), sandbox, role="review")
    sid = sid or maker.id + "-review"
    s = Session(sid, ctx.sessions_dir / sid)
    for d in (s.home, s.work, s.render, s.logs):
        d.mkdir(parents=True, exist_ok=True)
    for name, src in (inputs or {n: maker.work / n for n in INPUTS}).items():
        if src.is_file():
            shutil.copy2(src, s.work / name)
    (s.work / "composition.css").write_text(composition_css(comp or maker.comp))
    info = engine.probe(video_file)
    fps = int(p.get("video.fps", 30))
    samples = write_samples(video_file, pick_samples(motion_curve(video_file), fps), s.work, info)
    shutil.copy2(contact or maker.dir / "contact.jpg", s.work / "contact.jpg")
    (s.work / "TASK.md").write_text(task_text(p, samples["size"]))
    criteria = p.get("review.criteria", DEFAULT_CRITERIA)
    _session_row(ctx, s, "review", p, b)
    prompt = "Read TASK.md in the current folder and complete it. Nobody will answer questions."
    argv, env, ro, rw = backend_command(ctx, p, b, s, prompt, [], review=True)
    code = run_jailed(ctx, s, argv, env, ro, rw, b.sandbox, version, "review", int(p.get("review.timeout_min", 15)) * 60)
    try:
        verdict = check_verdict(_read_json(s.work / "verdict.json", "verdict.json"), criteria,
                                int(p.get("review.min_score", 8)))
    except StudioError as e:
        verdict = {"pass": None, "error": f"exit {code}: {e}"}
    verdict["model"] = f"{b.name}:{b.model or 'default'}"
    verdict["effort"] = p.get("review.effort") or "default"
    verdict["cost_usd"] = _claude_cost(s, "review")
    _session_end(ctx, s, "failed" if verdict["pass"] is None else "ok", verdict.get("error"), verdict["cost_usd"])
    return verdict


def rescore(ctx: Ctx, v: dict, times: int = 2, sets: dict | None = None) -> dict:
    """Review a filed video `times` times on the same inputs, to measure how much the reviewer's scores move on
    their own (motion-quality-plan A2, the noise floor). The video and its stored verdict are left as they are;
    each verdict stays in its own trimmed review session."""
    video = ctx.abs(v["file"]) if v["file"] else None
    folder = ctx.abs(v["dir"])
    if not video or not video.is_file() or not (folder / "contact.jpg").is_file():
        raise DataError(f"video {v['id']} has no files left to review", "superseded versions are purged")
    p = load_preset(ctx, v["preset"], sets)
    version = engine.require_version(p.get("render.version"))
    maker = Session(v["session_id"] or "none", ctx.sessions_dir / (v["session_id"] or "none"))
    staged = ctx.sessions_dir / f"rescore-{v['id']}"  # what the maker saw, or the closest thing still on disk
    staged.mkdir(parents=True, exist_ok=True)
    inputs = {}
    for name in INPUTS:
        src = maker.work / name if (maker.work / name).is_file() else folder / name
        if not src.is_file() and name in ("preset.json", "history.json"):
            src = staged / name
            past = [h for h in _history(ctx) if (h["topic"], h["angle"]) != (v["topic"], v["angle"])]
            src.write_text(json.dumps(p.data if name == "preset.json" else past, indent=2))
        inputs[name] = src
    runs = []
    try:
        for _ in range(max(1, times)):
            sid = f"{new_id()}-review"
            verdict = review_session(ctx, p, maker, video, version, None, sid, inputs, folder / "composition",
                                     folder / "contact.jpg")
            trim_session(Session(sid, ctx.sessions_dir / sid))
            runs.append({"session": sid, **{k: verdict.get(k) for k in ("pass", "scores", "error", "model", "cost_usd")}})
    finally:
        remove_within(staged, ctx.sessions_dir)
    scored = [r["scores"] for r in runs if r["pass"] is not None]
    crit = list(scored[0]) if scored else []
    return {"video": v["id"], "title": v["title"], "runs": runs,
            "spread": {c: max(s[c] for s in scored) - min(s[c] for s in scored) for c in crit},
            "mean": {c: round(sum(s[c] for s in scored) / len(scored), 2) for c in crit}}
