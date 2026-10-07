"""`make`: one isolated agent session per try, then render, encode and file into the library.

Session layout (<project>/.studio/sessions/<id>/):
  home/        throwaway HOME: the harness's config, skills, login copy and caches live and die here
  work/        the agent's working folder (the only place it can write)
    TASK.md, preset.json, history.json, skills/, composition/, brief.json, video.json
  render/      final near-lossless master, written by the runner (not the agent)
  logs/        harness output
A finished session is trimmed to its notes (task, brief, metadata, contact sheet, gzipped logs).
"""
from __future__ import annotations

import gzip
import json
import os
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from . import db, engine
from .core import (FORMATS, MCP_FILE, PKG_DIR, SLUG, ConfigError, Ctx, DataError, Preset, StudioError, Unavailable, iso,
                   load_preset, log, mcp_registry, new_id, require_human, slugify, validate_preset)

DEFAULT_SKILLS = ["hyperframes-core", "hyperframes-cli", "hyperframes-animation", "hyperframes-audio", "media-use"]
# Shipped with the tool and mounted in every maker session: the motion doctrine distilled from the engine's
# product-launch-video and hyperframes-keyframes skills (Apache-2.0, see its NOTICE.md), and motion-canon, the
# working method of non-AI motion design (rulings 16 and 19).
PACKAGE_SKILLS = ["motion-doctrine", "motion-canon"]
# Third-party skills vendored at pinned commits (data/skills/vendor/skills.lock.json); a preset mounts them by name
# through agent.package_skills.
VENDOR_DIR = PKG_DIR / "data" / "skills" / "vendor"
LICENSE_FILES = ("LICENSE", "LICENSE.txt", "LICENSE.md", "NOTICE", "NOTICE.md", "NOTICE.txt")


def vendored_skills() -> dict[str, Path]:
    """Every vendored skill by its own name (the SKILL.md `name:`), mapped to its folder."""
    out: dict[str, Path] = {}
    for f in sorted(VENDOR_DIR.rglob("SKILL.md")):
        if any(part.startswith(".") for part in f.relative_to(VENDOR_DIR).parts):
            continue
        m = re.search(r"^name:\s*['\"]?([a-z0-9][a-z0-9-]*)", f.read_text(errors="replace"), re.M)
        out.setdefault(m.group(1) if m else f.parent.name, f.parent)
    return out


def _mount_vendored(src: Path, dst: Path) -> None:
    """Copy one vendored skill, plus its pack's licence and notice when the skill sits inside a pack folder."""
    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".*", "node_modules"))
    pack = VENDOR_DIR / src.relative_to(VENDOR_DIR).parts[0]
    for name in LICENSE_FILES:
        if (pack / name).is_file() and not (dst / name).exists():
            shutil.copy2(pack / name, dst / name)
NO_SECRETS = shutil.ignore_patterns(".env", ".env.*")  # a copied folder never carries a .env into a session
DEFAULT_CRITERIA = ["hook in the first 2 seconds", "readability on a phone", "composition", "variety",
                    "brand accuracy", "motion quality"]
PROVIDER_KEYS = {
    "anthropic": ["ANTHROPIC_API_KEY"], "openai": ["OPENAI_API_KEY"], "xai": ["XAI_API_KEY"],
    "deepseek": ["DEEPSEEK_API_KEY"], "google": ["GOOGLE_GENERATIVE_AI_API_KEY", "GEMINI_API_KEY"],
    "openrouter": ["OPENROUTER_API_KEY"], "groq": ["GROQ_API_KEY"], "mistral": ["MISTRAL_API_KEY"],
}
BACKENDS = ("claude", "opencode", "codex")
HOUSE_FILE = "house.md"     # the house rules, given to the maker through its harness's system channel, never work/
BASH_TIMEOUT_MS = 600_000   # the maker's draft renders run through its shell tool


@dataclass
class MakeOpts:
    preset: str
    count: int = 1
    parallel: int = 1
    backend: str | None = None
    model: str | None = None
    sets: dict = field(default_factory=dict)
    sandbox: bool | None = None
    revise: int | None = None
    review: bool | None = None


@dataclass
class Session:
    id: str
    dir: Path

    @property
    def home(self) -> Path:
        return self.dir / "home"

    @property
    def work(self) -> Path:
        return self.dir / "work"

    @property
    def comp(self) -> Path:
        return self.work / "composition"

    @property
    def render(self) -> Path:
        return self.dir / "render"

    @property
    def logs(self) -> Path:
        return self.dir / "logs"


@dataclass
class Backend:
    name: str
    model: str | None
    bin: Path
    sandbox: bool


# --- preparation ---------------------------------------------------------------------------------------

def _fill(template: str, values: dict) -> str:
    return re.sub(r"\{\{(\w+)\}\}", lambda m: str(values.get(m.group(1), m.group(0))), template)


def _common_values(p: Preset) -> dict:
    criteria = p.get("review.criteria", DEFAULT_CRITERIA)
    safe = p.get("video.safe_zone", {})
    platforms = p.get("publish.platforms", []) or ["default"]
    return {
        "criteria": ", ".join(criteria),
        "min_score": p.get("review.min_score", 8),
        "no_repeat_days": p.get("content.no_repeat_days", 30),
        "safe_top": safe.get("top", 0.12), "safe_bottom": safe.get("bottom", 0.25),
        "safe_left": safe.get("left", 0.06), "safe_right": safe.get("right", 0.10),
        "captions_example": json.dumps({pl: "" for pl in platforms}),
        "scores_example": json.dumps({c: 0 for c in criteria}),
    }


def _rules_block(p: Preset) -> str:
    lines = [f"- {r}" for r in [*p.get("content.rules", []), *p.get("brand.rules", [])]]
    banned = p.get("content.banned", [])
    if banned:
        lines.append("- Never use these words or phrases: " + "; ".join(f"\"{b}\"" for b in banned) + ".")
    exact = p.get("content.exact_lines", {})
    if exact:
        lines.append("- Lines that state the offer or the brand must be copied exactly from this list:")
        lines += [f"  - {k}: \"{v}\"" for k, v in exact.items()]
    cta = p.get("content.cta")
    if cta:
        lines.append(f"- The call to action is exactly: \"{cta}\".")
    return "\n".join(lines)


def _brief_block(p: Preset, pillar: str | None, revise: dict | None = None) -> str:
    parts = []
    if revise:
        parts.append(f"- This is a revision of video {revise['id']}, \"{revise['title']}\". Keep its idea: pillar "
                     f"\"{revise['pillar']}\", topic \"{revise['topic']}\", angle \"{revise['angle']}\". Do not start a "
                     "new idea; change only what the notes and the reviewer's issues ask for.")
    for key, label in (("content.title", "Title"), ("content.subject", "Subject"), ("content.topic", "Topic"),
                       ("content.notes", "Notes")):
        if p.get(key):
            parts.append(f"- {label} (set by the operator, keep it): {p.get(key)}")
    if pillar and not revise:
        idea = next((x.get("idea") for x in p.get("content.pillars", []) if isinstance(x, dict) and x.get("name") == pillar),
                    None)
        parts.append(f"- Pillar for this video: {pillar}" + (f". The idea: {idea}" if idea else ""))
    if not parts:
        parts.append("- Choose the pillar, topic and angle yourself from `preset.json` and `history.json`.")
    return "\n".join(parts)


def _weight(value) -> int | str:
    """A fixed weight (700), or a variable font's range written as CSS writes it ("100 900")."""
    if isinstance(value, str) and re.fullmatch(r"\d{1,3} \d{1,4}", value.strip()):
        return value.strip()
    return int(value)


def font_files(font: dict) -> list[tuple[str, int | str, str]]:
    """A font's files as (path, weight, style). Each entry is a path, or {file, weight, style}."""
    out = []
    for entry in font.get("files", []):
        if isinstance(entry, dict):
            out.append((entry["file"], _weight(entry.get("weight", font.get("weight", 400))),
                        entry.get("style", font.get("style", "normal"))))
        else:
            out.append((entry, _weight(font.get("weight", 400)), font.get("style", "normal")))
    return out


def _font_faces(p: Preset) -> str:
    css = []
    for font in p.get("brand.fonts", {}).values():
        if not isinstance(font, dict):
            continue
        for rel, weight, style in font_files(font):
            fmt = {"woff2": "woff2", "woff": "woff", "ttf": "truetype", "otf": "opentype"}.get(Path(rel).suffix[1:], "woff2")
            css.append(f'@font-face {{ font-family: "{font["family"]}"; src: url("assets/{Path(rel).name}") '
                       f'format("{fmt}"); font-weight: {weight}; font-style: {style}; font-display: block; }}')
    return "\n      ".join(css)


def _scaffold(p: Preset, s: Session, eng_root: Path) -> None:
    """A brand-correct starting composition: fonts, colour tokens, easing curves, local libraries."""
    comp = s.comp
    (comp / "assets").mkdir(parents=True, exist_ok=True)
    (comp / "vendor").mkdir(exist_ok=True)
    for rel in [*p.get("assets.files", []),
                *[f for font in p.get("brand.fonts", {}).values() if isinstance(font, dict) for f, _, _ in font_files(font)]]:
        src = p.path(rel)
        dst = comp / "assets" / src.name
        shutil.copytree(src, dst, dirs_exist_ok=True, ignore=NO_SECRETS) if src.is_dir() else shutil.copy2(src, dst)
    scripts = []
    for name, rel in p.get("render.vendor", {}).items():
        src = eng_root / "node_modules" / rel
        if not src.is_file():
            raise ConfigError(f"render.vendor.{name}: {src} not found", "add the package to render.libraries")
        shutil.copy2(src, comp / "vendor" / name)
        if name.endswith(".js"):
            scripts.append(f'<script src="vendor/{name}"></script>')
    imports = {}
    for spec, files in p.get("render.esm", {}).items():  # ES modules, importable by bare name: `import * from "three"`
        for rel in files:
            src = eng_root / "node_modules" / rel
            if not src.is_file():
                raise ConfigError(f"render.esm.{spec}: {src} not found", "add the package to render.libraries")
            shutil.copy2(src, comp / "vendor" / src.name)  # side by side, so the entry's relative imports resolve
        imports[spec] = f"./vendor/{Path(files[0]).name}"
    if imports:
        scripts.append(f'<script type="importmap">{json.dumps({"imports": imports})}</script>')
    for rel in p.get("render.scripts", []):  # preset helpers, after the libraries they use
        if not (comp / "assets" / Path(rel).name).is_file():
            raise ConfigError(f"render.scripts: {rel} must also be listed in assets.files")
        scripts.append(f'<script src="assets/{Path(rel).name}"></script>')
    w, h, fps = p.get("video.width"), p.get("video.height"), p.get("video.fps")
    dur = p.get("video.duration")[1]
    colors = "\n        ".join(f"--{k}: {v};" for k, v in p.get("brand.colors", {}).items())
    sans = next((f for f in p.get("brand.fonts", {}).values() if isinstance(f, dict) and f.get("role") == "sans"), {})
    family = sans.get("stack") or (f'"{sans["family"]}", sans-serif' if sans.get("family") else "sans-serif")
    bg = p.get("video.background", "#ffffff")
    html = f"""<!doctype html>
<html lang="{p.get('content.language', 'en')}">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={w}, height={h}" />
    {chr(10).join('    ' + x for x in scripts).strip()}
    <style>
      {_font_faces(p)}
      :root {{
        {colors}
      }}
      {p.get('brand.css', '').strip()}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {w}px; height: {h}px; overflow: hidden; background: {bg}; }}
      #root {{ position: relative; width: 100%; height: 100%; font-family: {family}; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{dur}"
         data-width="{w}" data-height="{h}" data-fps="{fps}">
      <!-- Each visible element: class="clip" data-start data-duration data-track-index. -->
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      // Build every animation on `tl`. Nothing may animate outside this timeline.
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""
    (comp / "index.html").write_text(html)
    (comp / "hyperframes.json").write_text(json.dumps({"paths": {"assets": "assets"}, "media": {"autoProxy": False}}, indent=2))
    (comp / "meta.json").write_text(json.dumps({"id": s.id, "name": s.id}))


def _skills(ctx: Ctx, p: Preset, s: Session, version: str) -> list[str]:
    """Copy the pinned engine skills plus preset skills into work/skills (readable by any harness)."""
    out = s.work / "skills"
    out.mkdir(parents=True, exist_ok=True)
    src_root = engine.skills_root(ctx, version)
    names = []
    for name in [*p.get("agent.engine_skills", DEFAULT_SKILLS), *p.get("agent.skills", {})]:
        if not SLUG.fullmatch(str(name)):  # a name is a folder under work/skills, never a path elsewhere
            raise ConfigError(f"skill name {name!r} is not a slug", "use a-z, 0-9 and hyphens")
        if name in PACKAGE_SKILLS:
            raise ConfigError(f"skill name {name!r} is taken by a skill social-studio ships", "rename the preset's skill")
    for name in PACKAGE_SKILLS:  # a shipped skill has no hidden files; anything hidden there is not ours
        shutil.copytree(PKG_DIR / "data" / "skills" / name, out / name, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(".*"))
        names.append(name)
    vendored = vendored_skills()
    for name in p.get("agent.package_skills", []):
        if name not in vendored:
            raise ConfigError(f"agent.package_skills: no vendored skill named {name!r}",
                              f"pick from: {', '.join(sorted(vendored))}")
        if name not in names:
            _mount_vendored(vendored[name], out / name)
            names.append(name)
    for name in p.get("agent.engine_skills", DEFAULT_SKILLS):
        src = src_root / name
        if not src.is_dir():
            raise ConfigError(f"engine skill not found: {name}", "run `social-studio engine install`")
        shutil.copytree(src, out / name, dirs_exist_ok=True)
        names.append(name)
    for name, spec in p.get("agent.skills", {}).items():
        dst = out / name
        if isinstance(spec, dict) and spec.get("path"):
            shutil.copytree(p.path(spec["path"]), dst, dirs_exist_ok=True, ignore=NO_SECRETS)
        else:
            text = spec if isinstance(spec, str) else spec.get("text", "")
            dst.mkdir(parents=True, exist_ok=True)
            first = text.strip().splitlines()[0][:150] if text.strip() else name
            (dst / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {json.dumps(first)}\n---\n\n{text.strip()}\n")
        names.append(name)
    return names


def _history(ctx: Ctx, days: int = 120) -> list[dict]:
    con = db.connect(ctx, actor="make")
    try:
        return db.rows(con.execute(
            "SELECT day, pillar, topic, angle FROM agent_topics WHERE day >= date('now', ?) ORDER BY day DESC",
            (f"-{days} days",)))
    finally:
        con.close()


def _pillar_plan(p: Preset, history: list[dict], count: int) -> list[str | None]:
    """Spread a batch across pillars, least recently used first, so parallel tries differ."""
    pillars = p.get("content.pillars", [])
    names = [x["name"] if isinstance(x, dict) else str(x) for x in pillars]
    if not names or p.get("content.pillar"):
        return [p.get("content.pillar")] * count
    last_used = {n: "" for n in names}
    for row in history:
        if row["pillar"] in last_used and not last_used[row["pillar"]]:
            last_used[row["pillar"]] = row["day"]
    order = sorted(names, key=lambda n: last_used[n])
    return [order[i % len(order)] for i in range(count)]


def prepare(ctx: Ctx, p: Preset, s: Session, version: str, eng_root: Path, pillar: str | None,
            history: list[dict], revise: dict | None) -> list[str]:
    for d in (s.home, s.work, s.render, s.logs):
        d.mkdir(parents=True, exist_ok=True)
    (s.work / "preset.json").write_text(json.dumps(p.data, indent=2))
    (s.work / "history.json").write_text(json.dumps(history, indent=2))
    _scaffold(p, s, eng_root)
    revision_block = ""
    if revise:
        old_comp = ctx.abs(revise["dir"]) / "composition"
        # Outside composition/: a second root HTML there fails the strict render (multiple_root_compositions).
        (s.comp / "index.html").rename(s.work / "scaffold.reference.html")
        if old_comp.is_dir():
            shutil.copytree(old_comp, s.comp, dirs_exist_ok=True)
        meta = json.loads(revise["meta"])
        # Never scores or rounds: a maker handed its predecessor's scores reported exactly those (finding 2).
        previous = {k: v for k, v in meta.get("video", {}).items() if k not in ("scores", "rounds")}
        reviewer = {k: (meta.get("verdict") or {}).get(k) for k in ("issues", "summary") if (meta.get("verdict") or {}).get(k)}
        (s.work / "revision.json").write_text(json.dumps(
            {"previous": previous, "reviewer": reviewer, "notes": revise["notes"]}, indent=2))
        revision_block = ("- `revision.json`: this is a revision. `composition/index.html` is the previous version. "
                          "Apply the operator's notes and fix the reviewer's issues listed there; keep everything "
                          "they did not ask to change. `scaffold.reference.html` is the current brand setup from "
                          "the preset (leave it where it is): bring the previous version's fonts, colour tokens, brand CSS and scripts in "
                          "line with it.\n")
    skills = _skills(ctx, p, s, version)
    (s.work / "tools").mkdir(exist_ok=True)
    (s.work / "drafts").mkdir(exist_ok=True)
    shutil.copy2(PKG_DIR / "sampler.py", s.work / "tools" / "sampler.py")
    for tool in sorted((PKG_DIR / "data" / "tools").glob("*")):  # session tools the maker runs: sound.mjs ...
        if tool.is_file() and not tool.name.startswith("."):
            shutil.copy2(tool, s.work / "tools" / tool.name)
    vals = {**_maker_values(p), "skill_list": ", ".join(skills), "revision_block": revision_block,
            "brief_block": _brief_block(p, pillar, revise)}
    (s.home / HOUSE_FILE).write_text(_fill((PKG_DIR / "data" / "house.md").read_text(), vals))
    (s.work / "TASK.md").write_text(_fill((PKG_DIR / "data" / "session_prompt.md").read_text(), vals))
    return skills


def _maker_values(p: Preset) -> dict:
    """What the house rules and the brief are filled from. The maker never sees min_score: it works a fixed number of
    rounds and is not told the bar it is scored against (C1)."""
    safe, (w, h) = p.get("video.safe_zone", {}), (p.get("video.width"), p.get("video.height"))
    pacing, motion, sound = p.get("video.pacing"), p.get("video.motion"), p.get("video.sound")
    common = {k: v for k, v in _common_values(p).items() if k != "min_score"}
    motion_rule = ("Motion follows the motion signature in TASK.md first, then `skills/motion-doctrine` wherever the "
                   "signature is silent" if motion else "An arrival is spatial by default (it moves, scales, wipes or "
                   "draws in), never a fade: fades everywhere are the first tell of template motion "
                   "(`skills/motion-doctrine`)")
    portrait = h > w
    format_note = (f"\n- This frame is for Reels, TikTok and Shorts, whose buttons and captions cover about the bottom "
                   f"{round(100 * safe.get('bottom', 0.25))}% and right {round(100 * safe.get('right', 0.10))}%: keep "
                   f"anything the viewer must read out of there." if portrait else "")
    return {**common, "width": w, "height": h, "fps": p.get("video.fps"), "draft_fps": min(int(p.get("video.fps")), 30),
            "aspect": _aspect(w, h),
            "min_s": p.get("video.duration")[0], "max_s": p.get("video.duration")[1], "rules": _rules_block(p),
            "rounds": int(p.get("agent.rounds", p.get("review.max_rounds", 2))),
            "min_text_px": round(11 * min(w, h) / 393),  # 11 pt on a 393 pt-wide phone, scaled from the short side
            "end_card_pct": round(100 * float(p.get("video.end_card_max", 0.2))), "format_note": format_note,
            "pacing_line": f"\nPacing: {pacing}." if pacing else "", "motion_rule": motion_rule,
            "motion_line": (f"\nMotion signature, set by the operator (it wins where `skills/motion-doctrine` "
                            f"differs): {motion}.") if motion else "",
            "sound_line": f"\nSound: {SOUND_LINES[sound]}" if sound else "",
            "sound_step": SOUND_STEP if sound and sound != "none" else ": none for this video, skip this step",
            "safe_arg": ",".join(str(safe.get(k, d)) for k, d in
                                 (("top", 0.12), ("bottom", 0.25), ("left", 0.06), ("right", 0.10)))}


def _aspect(w: int, h: int) -> str:
    return next((name for name, size in FORMATS.items() if size == (w, h)), f"{w}:{h}")


SOUND_LINES = {
    "none": "none. The video is silent.",
    "sfx": "effects on the cuts and the key moves. No music, no voice.",
    "bed+sfx": "a music bed composed for this film on its beat grid, with effects on the cuts and the key moves. "
               "No voice.",
    "sfx+voice": "a short voice-over plus effects on the cuts and the key moves. No music.",
    "bed+sfx+voice": "a voice-over over a music bed on the film's beat grid, with effects on the cuts and the key moves.",
}
SOUND_STEP = (". Build the soundtrack from the beat grid and the cues in `brief.json`: `node tools/sound.mjs --help` "
              "synthesizes a bed and effects in code; `skills/media-use/audio/assets/sfx/` holds recorded effects "
              "(Pixabay licence) and `hyperframes tts` speaks a voice-over offline. Copy every file into "
              "`composition/assets/` and place each as `<audio id=\"...\" src=\"assets/...\" data-start "
              "data-duration data-track-index>` on the timeline. An `<audio>` without an `id` renders silent")


# --- backends -----------------------------------------------------------------------------------------

def resolve_backend(ctx: Ctx, p: Preset, name: str | None, model: str | None, sandbox: bool | None,
                    role: str = "agent") -> Backend:
    key = "agent" if role == "agent" else "review"
    name = name or p.get(f"{key}.backend") or p.get("agent.backend") or ctx.cfg("backend.default", "claude")
    if name not in BACKENDS:
        raise ConfigError(f"unknown backend {name!r}", f"use one of: {', '.join(BACKENDS)}")
    if model is None:
        if p.get(f"{key}.backend", p.get("agent.backend")) == name:
            model = p.get(f"{key}.model") or (p.get("agent.model") if key == "agent" else None)
        model = model or ctx.cfg(f"backend.{name}.model")
    exe = ctx.cfg(f"backend.{name}.bin") or shutil.which(name)
    if not exe:
        raise Unavailable(f"{name} not found on PATH", f"install {name}, or set backend.{name}.bin in config.toml")
    if sandbox is None:
        sandbox = bool(ctx.cfg("sandbox.enabled", True))
    if not sandbox:  # flag or config: either way an unjailed harness could write outside the repo
        require_human("running sessions without the sandbox")
    if sandbox and not engine.sandbox_available():
        raise Unavailable("sandbox requested but bubblewrap is missing", "install bubblewrap or pass --no-sandbox")
    return Backend(name, model, Path(exe).resolve(), sandbox)


def _install_root(binary: Path, ctx: Ctx) -> Path:
    """The harness's install folder, read-only in the sandbox; never a folder holding home or our data."""
    parent = binary.parent
    return engine.safe_root(parent.parent if parent.name == "bin" else parent, parent, ctx)


def _secret(ctx: Ctx, server: str, declared: set[str], value) -> str:
    """Fill ${VAR} from the environment or .env, but only names the server's registry entry declares (R0)."""
    def fill(m: re.Match) -> str:
        if m.group(1) not in declared:
            raise ConfigError(f"mcp server {server} uses ${{{m.group(1)}}}, which its {MCP_FILE} entry does not declare",
                              f"a human lists it under secrets in [servers.{server}], or removes it")
        if not ctx.env(m.group(1)):
            raise ConfigError(f"mcp server {server} needs {m.group(1)}", "add it to the .env")
        return ctx.env(m.group(1))
    return re.sub(r"\$\{(\w+)\}", fill, str(value))


def _mcp(ctx: Ctx, p: Preset) -> dict:
    """The preset's MCP servers, by name from the vetted registry; a preset never defines one itself."""
    registry, out = mcp_registry(ctx), {}
    for name in p.get("agent.mcp", []) or []:
        entry = registry.get(name)
        if not entry or not (entry.get("url") or entry.get("command")):
            raise ConfigError(f"mcp server {name!r} is not in {MCP_FILE}", "a human adds vetted servers there")
        declared = set(entry.get("secrets", []))
        out[name] = {"args": [_secret(ctx, name, declared, a) for a in entry.get("args", [])],
                     "env": {k: _secret(ctx, name, declared, v) for k, v in entry.get("env", {}).items()},
                     "headers": {k: _secret(ctx, name, declared, v) for k, v in entry.get("headers", {}).items()}}
        if entry.get("url"):
            out[name]["url"] = _secret(ctx, name, declared, entry["url"])
        else:
            out[name]["command"] = entry["command"]
    return out


def _private_copy(dest: Path, data: dict) -> None:
    """Logins enter the jail as a 0600 copy inside the session (the trim deletes it), never as a mount."""
    fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)


def backend_command(ctx: Ctx, p: Preset, b: Backend, s: Session, prompt: str, skills: list[str],
                    review: bool = False) -> tuple[list[str], dict[str, str], list[Path], list[Path]]:
    """argv, extra env, extra read-only binds, extra read-write binds for one harness run. Every limit is read for
    the run's own role (agent.* for the maker, review.* for the reviewer): neither inherits the other's."""
    role = "review" if review else "agent"
    env: dict[str, str] = {}
    ro: list[Path] = [_install_root(b.bin, ctx)]
    rw: list[Path] = []
    mcp = _mcp(ctx, p) if not review else {}
    max_turns = str(p.get(f"{role}.max_turns", 40 if review else 80))  # 20 ran a 60 fps reel's review out of turns
    allow_web = bool(p.get(f"{role}.allow_web", False))
    effort = p.get(f"{role}.effort")
    house = s.home / HOUSE_FILE if not review and (s.home / HOUSE_FILE).is_file() else None

    if b.name == "claude":
        cfg = s.home / ".claude-config"
        (cfg / "skills").mkdir(parents=True, exist_ok=True)
        for name in skills:
            shutil.copytree(s.work / "skills" / name, cfg / "skills" / name, dirs_exist_ok=True)
        (cfg / "settings.json").write_text(json.dumps({"sandbox": {"enabled": False}}))
        env.update(CLAUDE_CONFIG_DIR=str(cfg), DISABLE_AUTOUPDATER="1", DISABLE_TELEMETRY="1",
                   DISABLE_ERROR_REPORTING="1", BASH_DEFAULT_TIMEOUT_MS=str(BASH_TIMEOUT_MS),
                   BASH_MAX_TIMEOUT_MS=str(BASH_TIMEOUT_MS))  # a draft render outlasts the 2-minute default
        auth = ctx.cfg("backend.claude.auth", "user")
        if auth == "token":
            tok = ctx.env("CLAUDE_CODE_OAUTH_TOKEN")
            if not tok:
                raise ConfigError("CLAUDE_CODE_OAUTH_TOKEN missing", "run `claude setup-token` and add it to the .env")
            env["CLAUDE_CODE_OAUTH_TOKEN"] = tok
        elif auth == "api-key":
            key = ctx.env("ANTHROPIC_API_KEY")
            if not key:
                raise ConfigError("ANTHROPIC_API_KEY missing", "add it to the .env")
            env["ANTHROPIC_API_KEY"] = key
        else:
            real = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / ".credentials.json"
            if not b.sandbox:
                raise ConfigError("backend.claude.auth = \"user\" needs the sandbox",
                                  "use auth = \"token\" (claude setup-token) when running with --no-sandbox")
            if not real.is_file():
                raise ConfigError(f"no Claude login at {real}", "log in with `claude`, or set backend.claude.auth")
            login = json.loads(real.read_text()).get("claudeAiOauth")
            if not login:
                raise ConfigError(f"no Claude subscription login in {real}", "log in with `claude`, or set backend.claude.auth")
            minutes = int(p.get("review.timeout_min", 15) if review else p.get("agent.timeout_min", 45))
            left = (login.get("expiresAt", 0) / 1000 - time.time()) / 60
            if left < minutes + 5:  # a refresh inside the jail could rotate the host's login away
                raise Unavailable(f"the Claude login expires in {max(left, 0):.0f} min, before this session could end",
                                  "use Claude Code once so it refreshes the login, or set backend.claude.auth = \"token\"")
            # Only the Claude login: the same file also holds MCP servers' and other OAuth tokens.
            _private_copy(cfg / ".credentials.json", {"claudeAiOauth": login})
        argv = [str(b.bin), "-p", prompt, "--output-format", "stream-json", "--verbose",
                "--max-turns", max_turns, "--permission-prompts", "none",
                "--permission-mode", "bypassPermissions" if b.sandbox else "acceptEdits"]
        if b.model:
            argv += ["--model", b.model]
        if effort:
            argv += ["--effort", effort]
        if house:
            argv += ["--append-system-prompt-file", str(house)]
        if not b.sandbox:
            argv += ["--allowedTools", "Bash(hyperframes *)", "Bash(ffprobe *)", "Bash(python3 tools/sampler.py *)",
                     "Read", "Write", "Edit", "Glob", "Grep"]
        if not allow_web:
            argv += ["--disallowedTools", "WebFetch", "WebSearch"]
        budget = p.get(f"{role}.max_budget_usd")
        if budget:
            argv += ["--max-budget-usd", str(budget)]
        if mcp:
            servers = {n: ({"type": "http", "url": m["url"], "headers": m["headers"]} if m.get("url") else
                           {"type": "stdio", "command": m["command"], "args": m.get("args", []), "env": m["env"]})
                       for n, m in mcp.items()}
            mfile = s.home / "mcp.json"
            mfile.write_text(json.dumps({"mcpServers": servers}))
            argv += ["--strict-mcp-config", "--mcp-config", str(mfile)]
        else:
            argv += ["--strict-mcp-config"]
        for plugin in p.get("agent.plugins", []) if not review else ():
            argv += ["--plugin-dir", str(p.path(plugin))]
            ro.append(p.path(plugin))

    elif b.name == "opencode":
        provider = (b.model or "").split("/", 1)[0]
        for k in ctx.cfg("backend.opencode.env", PROVIDER_KEYS.get(provider, [])):
            if ctx.env(k):
                env[k] = ctx.env(k)
        conf: dict = {"$schema": "https://opencode.ai/config.json", "autoupdate": False, "share": "disabled",
                      "permission": {"edit": "allow", "bash": "allow",
                                     "webfetch": "allow" if allow_web else "deny"}}
        if mcp:
            conf["mcp"] = {n: ({"type": "remote", "url": m["url"], "headers": m["headers"]} if m.get("url") else
                               {"type": "local", "command": [m["command"], *m.get("args", [])], "environment": m["env"]})
                           for n, m in mcp.items()}
        if house:
            conf["instructions"] = [str(house)]
        env["OPENCODE_CONFIG_CONTENT"] = json.dumps(conf)
        env["OPENCODE_DISABLE_AUTOUPDATE"] = "1"
        argv = [str(b.bin), "run", "--standalone", "--format", "json", "--auto"]
        if b.model:  # opencode takes the effort as the model's variant: provider/model#high
            argv += ["-m", f"{b.model}#{effort}" if effort and "#" not in b.model else b.model]
        argv.append(prompt)

    else:  # codex
        home = s.home / ".codex"
        home.mkdir(parents=True, exist_ok=True)
        env["CODEX_HOME"] = str(home)
        real = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "auth.json"
        auth = ctx.cfg("backend.codex.auth") or ("user" if b.sandbox and real.is_file() else "api-key")
        if auth == "user":
            if not (b.sandbox and real.is_file()):
                raise ConfigError("backend.codex.auth = \"user\" needs the sandbox and a codex login")
            _private_copy(home / "auth.json", json.loads(real.read_text()))
        else:
            key = ctx.env("OPENAI_API_KEY") or ctx.env("CODEX_API_KEY")
            if not key:
                raise ConfigError("OPENAI_API_KEY missing", "add it to the .env, or set backend.codex.auth = \"user\"")
            env["OPENAI_API_KEY"] = key
        if house:  # codex reads its global instructions from $CODEX_HOME/AGENTS.md
            shutil.copy2(house, home / "AGENTS.md")
        argv = [str(b.bin), "exec", "--ephemeral", "--skip-git-repo-check", "--json", "-C", str(s.work),
                "--sandbox", "danger-full-access" if b.sandbox else "workspace-write"]
        if b.model:
            argv += ["-m", b.model]
        if effort:  # codex has no "max"; xhigh is its highest
            argv += ["-c", f"model_reasoning_effort={json.dumps('xhigh' if effort == 'max' else effort)}"]
        for n, m in mcp.items():
            pre = f"mcp_servers.{n}"
            if m.get("url"):
                argv += ["-c", f"{pre}.url={json.dumps(m['url'])}"]
            else:
                argv += ["-c", f"{pre}.command={json.dumps(m['command'])}",
                         "-c", f"{pre}.args={json.dumps(m.get('args', []))}"]
                for k, v in m["env"].items():
                    argv += ["-c", f"{pre}.env.{k}={json.dumps(v)}"]
        argv.append(prompt)
    return argv, env, ro, rw


def run_jailed(ctx: Ctx, s: Session, argv: list[str], env: dict[str, str], ro: list[Path], rw: list[Path],
               sandbox: bool, version: str, log_name: str, timeout: int, workdir: Path | None = None) -> int:
    """Run argv with an empty HOME and only the session folder writable."""
    eng = engine.engine_root(ctx, version)
    chrome = engine.chrome_path(ctx, version)
    node_ro, node_path = engine.node_dirs(ctx)
    full_env = engine.base_env(s.home, [eng / "node_modules" / ".bin", *node_path])
    full_env["HYPERFRAMES_BROWSER_PATH"] = str(chrome)
    full_env.update(env)
    workdir = workdir or s.work
    if sandbox:  # render/ is the runner's: the final master is written there after the session, by code
        prefix = engine.bwrap_argv(workdir, s.home, rw=[s.work, *rw],
                                   ro=[eng, engine.chrome_root(chrome), *node_ro, *ro], env=full_env)
        cmd, sub_env = prefix + argv, None
    else:
        cmd, sub_env = argv, full_env
    with open(s.logs / f"{log_name}.out", "w") as out, open(s.logs / f"{log_name}.err", "w") as err:
        try:
            return subprocess.run(cmd, stdout=out, stderr=err, env=sub_env, cwd=workdir,
                                  timeout=timeout, stdin=subprocess.DEVNULL).returncode
        except subprocess.TimeoutExpired:
            err.write(f"\nsocial-studio: timed out after {timeout}s\n")
            return 124


def _claude_cost(s: Session, log_name: str) -> float | None:
    f = s.logs / f"{log_name}.out"
    if not f.exists():
        return None
    for line in reversed(f.read_text().splitlines()):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "result":
            return ev.get("total_cost_usd")
    return None


# --- one try, end to end ---------------------------------------------------------------------------------

def _read_json(path: Path, what: str) -> dict:
    if not path.is_file():
        raise DataError(f"the agent did not write {path.name}", f"see the session logs: {path.parent.parent / 'logs'}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise DataError(f"{what} is not valid JSON: {e}") from e
    if not isinstance(data, dict):
        raise DataError(f"{what} must be a JSON object")
    return data


def _session_row(ctx: Ctx, s: Session, kind: str, p: Preset, b: Backend) -> None:
    con = db.connect(ctx, actor="make")
    try:
        con.execute("INSERT INTO sessions (id, kind, preset, preset_hash, backend, model, sandbox, dir, status, started_at)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'running', ?)",
                    (s.id, kind, p.name, p.hash, b.name, b.model, int(b.sandbox), ctx.rel(s.dir), iso()))
    finally:
        con.close()


def _session_end(ctx: Ctx, s: Session, status: str, error: str | None = None, cost: float | None = None,
                 video_id: int | None = None) -> None:
    con = db.connect(ctx, actor="make")
    try:
        con.execute("UPDATE sessions SET status = ?, error = ?, cost_usd = ?, video_id = ?, ended_at = ? WHERE id = ?",
                    (status, error, cost, video_id, iso(), s.id))
    finally:
        con.close()


def remove_within(path: Path, root: Path) -> None:
    """rmtree, but only strictly inside `root`. A blank or stray path can never take out the project."""
    path, root = path.resolve(), root.resolve()
    if root not in path.parents:
        raise DataError(f"refusing to delete {path}: not inside {root}")
    shutil.rmtree(path, ignore_errors=True)


def _drop(path: Path, root: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        path.unlink(missing_ok=True)
    else:
        remove_within(path, root)


def trim_session(s: Session, keep_composition: bool = False) -> None:
    """A finished session keeps what explains it (task, brief and metadata files, contact sheet, gzipped
    logs) and drops everything else it made. A failed one also keeps its composition, the evidence."""
    if not s.dir.is_dir():
        return
    for p in s.dir.iterdir():
        if p.name not in ("work", "logs", "contact.jpg"):
            _drop(p, s.dir)
    for p in s.work.iterdir() if s.work.is_dir() else ():
        if p.is_dir() and not p.is_symlink():
            if not (keep_composition and p == s.comp):
                _drop(p, s.dir)
        elif p.suffix not in (".md", ".json"):
            _drop(p, s.dir)
    for f in s.logs.iterdir() if s.logs.is_dir() else ():
        if f.is_file() and f.suffix != ".gz":
            with open(f, "rb") as src, gzip.open(f"{f}.gz", "wb") as dst:
                shutil.copyfileobj(src, dst)
            f.unlink()


def purge_version(ctx: Ctx, old: dict) -> None:
    """A revision replaces its predecessor: delete its files and sessions, keep its row as history."""
    if old.get("dir"):
        remove_within(ctx.abs(old["dir"]), ctx.library_dir)
    sids = [x for x in (old.get("session_id"), f"{old.get('session_id')}-review") if x and not x.startswith("None")]
    for sid in sids:
        if (ctx.sessions_dir / sid).exists():
            remove_within(ctx.sessions_dir / sid, ctx.sessions_dir)
    con = db.connect(ctx, actor="make")
    try:
        with db.tx(con):
            con.execute("UPDATE videos SET dir = '', file = '' WHERE id = ?", (old["id"],))
            for sid in sids:
                con.execute("UPDATE sessions SET dir = '' WHERE id = ?", (sid,))
    finally:
        con.close()


def _qa(ctx: Ctx, p: Preset, s: Session, video: Path, version: str, sandbox: bool, meta: dict) -> dict:
    """The report-only gates (qa.py) on the filed video. A finding, or the gates failing to run, never stops it."""
    from . import qa
    try:
        brief = json.loads((s.work / "brief.json").read_text()) if (s.work / "brief.json").is_file() else None
        poster = meta.get("poster_at")
        return qa.check(ctx, p, s.comp, video, s.work / "qa", version, sandbox, brief if isinstance(brief, dict) else None,
                        float(poster) if isinstance(poster, (int, float)) and not isinstance(poster, bool) else None)
    except Exception as e:  # noqa: BLE001
        log(f"[{s.id}] warning: quality gates did not run: {e}")
        return {"version": 1, "gates": {}, "findings": [], "error": f"{type(e).__name__}: {e}"[:1000]}


def run_one(ctx: Ctx, p: Preset, opts: MakeOpts, b: Backend, version: str, pillar: str | None,
            history: list[dict], revise: dict | None) -> dict:
    sid = new_id()
    s = Session(sid, ctx.sessions_dir / sid)
    _session_row(ctx, s, "make", p, b)
    try:
        eng_root = engine.engine_root(ctx, version)
        skills = prepare(ctx, p, s, version, eng_root, pillar, history, revise)
        prompt = ("Read TASK.md in the current folder and complete it. Work autonomously; nobody will answer "
                  "questions. Finish by writing video.json.")
        argv, env, ro, rw = backend_command(ctx, p, b, s, prompt, skills)
        log(f"[{s.id}] {b.name}{':' + b.model if b.model else ''} working{' (sandboxed)' if b.sandbox else ''}")
        code = run_jailed(ctx, s, argv, env, ro, rw, b.sandbox, version, "agent",
                          int(p.get("agent.timeout_min", 45)) * 60)
        meta = _read_json(s.work / "video.json", "video.json")
        if not str(meta.get("title", "")).strip():
            raise DataError(f"video.json has no title (agent exit {code})")
        log(f"[{s.id}] rendering")
        fps = int(p.get("video.fps"))
        hf = engine.hf_bin(ctx, version)
        mov = s.render / "master.mp4"
        chrome = engine.chrome_path(ctx, version)
        node_ro, node_path = engine.node_dirs(ctx)
        env2 = engine.base_env(s.home, [eng_root / "node_modules" / ".bin", *node_path])
        env2["HYPERFRAMES_BROWSER_PATH"] = str(chrome)
        prefix = engine.bwrap_argv(s.work, s.home, rw=[s.work, s.render],
                                   ro=[eng_root, engine.chrome_root(chrome), *node_ro], env=env2) if b.sandbox else []
        engine.render_master(prefix, hf, s.comp, mov, fps, int(p.get("render.master_crf", 10)),
                             env=None if b.sandbox else env2)
        title = str(meta["title"]).strip()
        dest = ctx.library_dir / f"{s.id[:8]}-{slugify(title)}-{s.id[-4:]}"
        dest.mkdir(parents=True, exist_ok=True)
        log(f"[{s.id}] encoding")
        info = engine.encode(mov, dest / "video.mp4", p.get("encode", {}), fps)
        engine.poster_and_sheet(dest / "video.mp4", dest / "poster.jpg", s.dir / "contact.jpg", info["duration"],
                                meta.get("poster_at"))
        shutil.copy2(s.dir / "contact.jpg", dest / "contact.jpg")
        for name in ("video.json", "brief.json"):
            if (s.work / name).exists():
                shutil.copy2(s.work / name, dest / name)
        shutil.copytree(s.comp, dest / "composition", ignore=shutil.ignore_patterns("snapshots", "renders", ".hf*", "scaffold.html"),
                        dirs_exist_ok=True)
        qa_report = _qa(ctx, p, s, dest / "video.mp4", version, b.sandbox, meta)
        (dest / "qa.json").write_text(json.dumps(qa_report, indent=2))
        verdict = None
        if opts.review if opts.review is not None else p.get("review.independent", False):
            from .review import review_session
            log(f"[{s.id}] independent review")
            verdict = review_session(ctx, p, s, dest / "video.mp4", version, b.sandbox)
            (dest / "verdict.json").write_text(json.dumps(verdict, indent=2))
        mov.unlink(missing_ok=True)
        meta_all = {"video": meta, "verdict": verdict, "session": s.id, "backend": f"{b.name}:{b.model or 'default'}",
                    "effort": p.get("agent.effort") or "default", "qa": qa_report.get("gates"), "preset_hash": p.hash}
        if revise:  # the version this replaces leaves Buffer before it is superseded
            from . import posting
            try:
                posting.withdraw(ctx, revise["id"], "superseded by a revision")
            except (StudioError, OSError) as e:
                log(f"[{s.id}] warning: drafts of video {revise['id']} are still in Buffer; delete them there: {e}")
        con = db.connect(ctx, actor="make")
        try:
            with db.tx(con):
                cur = con.execute(
                    "INSERT INTO videos (session_id, parent_id, slug, title, description, topic, angle, pillar, meta,"
                    " preset, dir, file, sha256, bytes, duration, width, height, created_at, updated_at)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (s.id, revise["id"] if revise else None, slugify(title), title, str(meta.get("description", "")),
                     str(meta.get("topic", "")), str(meta.get("angle", "")), str(meta.get("pillar", pillar or "")),
                     json.dumps(meta_all), p.name, ctx.rel(dest), ctx.rel(dest / "video.mp4"), info["sha256"], info["bytes"],
                     info["duration"], info["width"], info["height"], iso(), iso()))
                vid = cur.lastrowid
                if revise:
                    db.set_status(con, revise["id"], "superseded", f"superseded by {vid}")
        finally:
            con.close()
        cost = _claude_cost(s, "agent")
        _session_end(ctx, s, "ok", cost=cost, video_id=vid)
        try:  # the video exists from here on; cleanup trouble is a warning, never a failed run
            trim_session(s)
            trim_session(Session(s.id + "-review", s.dir.parent / (s.id + "-review")))
            if revise:
                purge_version(ctx, revise)
        except Exception as e:
            log(f"[{s.id}] warning: cleanup incomplete: {e}")
        log(f"[{s.id}] video {vid}: {title} ({info['bytes'] / 1e6:.1f} MB, {info['duration']:.1f}s)")
        return {"ok": True, "session": s.id, "video_id": vid, "title": title, "file": str(dest / "video.mp4"),
                "bytes": info["bytes"], "duration": info["duration"], "cost_usd": cost,
                "verdict": (verdict or {}).get("pass")}
    except Exception as e:  # one failed try must not sink the batch; the session folder keeps the evidence
        _session_end(ctx, s, "failed", f"{type(e).__name__}: {e}"[:2000])
        log(f"[{s.id}] failed: {e}")
        try:
            trim_session(s, keep_composition=True)
            trim_session(Session(s.id + "-review", s.dir.parent / (s.id + "-review")), keep_composition=True)
        except Exception:
            pass
        return {"ok": False, "session": s.id, "error": str(e)[:2000], "dir": str(s.dir)}


def make(ctx: Ctx, opts: MakeOpts) -> list[dict]:
    p = load_preset(ctx, opts.preset, opts.sets)
    problems = validate_preset(p, ctx)
    if problems:
        raise ConfigError(f"preset {p.name} is not usable: " + "; ".join(problems), "fix the preset, then retry")
    version = engine.require_version(p.get("render.version"))
    engine.ensure_engine(ctx, version, p.get("render.libraries", []))
    engine.ensure_skills(ctx, version)
    b = resolve_backend(ctx, p, opts.backend, opts.model, opts.sandbox)
    revise = None
    if opts.revise is not None:
        con = db.connect(ctx)
        try:
            revise = db.get_video(con, opts.revise)
        finally:
            con.close()
        if revise["status"] not in ("revision", "review", "rejected"):
            raise DataError(f"video {opts.revise} is {revise['status']}; only review, revision or rejected videos can be revised")
        opts.count = 1
    history = _history(ctx)
    if revise:  # the version being revised is not a repeat of itself
        history = [h for h in history if not (h["topic"] == revise["topic"] and h["angle"] == revise["angle"])]
    plan = [revise["pillar"] or None] if revise else _pillar_plan(p, history, max(1, opts.count))
    workers = max(1, min(opts.parallel, opts.count))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_one, ctx, p, opts, b, version, plan[i], history, revise) for i in range(opts.count)]
        return [f.result() for f in futures]
