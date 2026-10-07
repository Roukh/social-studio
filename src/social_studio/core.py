"""Shared plumbing: errors, the project folder, social-studio.toml, .env, presets, small helpers.

Precedence everywhere: command-line flags > environment > social-studio.toml > defaults.
Everything lives in one project folder and nothing is written outside its git repo.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

APP = "social-studio"
# HyperFrames 0.8.x rewrites these family names to Google Fonts substitutes (Helvetica and Arial become
# Inter) and ignores an authored @font-face under them (dist/chunk-HBBJFK6I.js, FONT_ALIAS_MAP).
ALIASED_FONTS = {"helvetica neue", "helvetica", "arial", "helvetica bold", "sf pro", "sf pro display",
                 "sf pro text", "avenir", "avenir next", "segoe ui", "verdana", "tahoma", "futura",
                 "garamond", "courier new"}
PKG_DIR = Path(__file__).resolve().parent
SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
SEMVER = re.compile(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?")
NPM_PIN = re.compile(r"(?:@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*@" + SEMVER.pattern)
# Keys that decide what enters a session or runs on the host. An agent cannot set them, by --set or by a preset
# file from outside the presets folders: only a human at a terminal can (R0).
GUARDED_PRESET = ("agent.mcp", "agent.plugins", "agent.skills", "agent.engine_skills", "assets", "brand.fonts", "render")
# Config keys that pick the harness binary and the credentials it gets, the sandbox, or where presets come from.
GUARDED_CONFIG = ("preset_paths", "sandbox", "publish.buffer", "publish.media",  # where posts and videos go
                  *(f"backend.{b}.{k}" for b in ("claude", "opencode", "codex") for k in ("bin", "auth", "env")))
MCP_FILE = "mcp.toml"
# `make --aspect`: frame size on a 1080 px short side. Only 9:16 keeps the preset's safe zone, which is sized for the
# Reels, TikTok and Shorts overlays; the others get broadcast title-safe, 5 % on every edge.
FORMATS = {"9:16": (1080, 1920), "4:5": (1080, 1350), "1:1": (1080, 1080), "16:9": (1920, 1080)}
TITLE_SAFE = {"top": 0.05, "bottom": 0.05, "left": 0.05, "right": 0.05}
SOUNDS = ("none", "sfx", "bed+sfx", "sfx+voice", "bed+sfx+voice")
EFFORTS = ("low", "medium", "high", "xhigh", "max")  # claude --effort; codex and opencode get the nearest equivalent


# --- errors: each maps to a sysexits.h code and carries a remediation hint ---------------------

class StudioError(Exception):
    exit_code = 1
    code = "error"

    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.hint = hint


class UsageError(StudioError):
    exit_code, code = 64, "usage"


class DataError(StudioError):
    exit_code, code = 65, "data"


class Unavailable(StudioError):
    exit_code, code = 69, "unavailable"


class ConfigError(StudioError):
    exit_code, code = 78, "config"


class Denied(StudioError):
    exit_code, code = 77, "denied"


# --- small helpers -----------------------------------------------------------------------------

def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt: datetime | None = None) -> str:
    return (dt or now_utc()).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def new_id() -> str:
    """Time-sortable session id: 20261001-213000-a1b2."""
    return datetime.now().strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(2)


def slugify(text: str, limit: int = 48) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (s[:limit].rstrip("-")) or "video"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_tty() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def require_human(action: str) -> None:
    """Human-only actions need an interactive terminal. Agents in a harness run without one."""
    if not is_tty() or os.environ.get("SOCIAL_STUDIO_ROLE") == "agent":
        raise Denied(f"{action} is human-only and needs an interactive terminal",
                     "run it yourself in a terminal; an agent cannot do this")


# --- dotted keys and TOML --------------------------------------------------------------------------

def dget(d: dict, key: str, default=None):
    cur = d
    for part in key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def dset(d: dict, key: str, value) -> None:
    parts = key.split(".")
    cur = d
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = cur[part] = {}
        cur = nxt
    cur[parts[-1]] = value


def parse_value(raw: str):
    """`--set k=v` values are TOML when they parse (15, true, ["a"], "x"), plain strings otherwise."""
    try:
        return tomllib.loads(f"v = {raw}")["v"]
    except tomllib.TOMLDecodeError:
        return raw


def parse_sets(pairs: list[str]) -> dict:
    out = {}
    for item in pairs:
        if "=" not in item:
            raise UsageError(f"--set {item!r}: use key=value")
        k, v = item.split("=", 1)
        out[k.strip()] = parse_value(v.strip())
    return out


def format_sets(aspect: str | None = None, fps: int | None = None, duration: str | None = None,
                sound: str | None = None, rounds: int | None = None) -> dict:
    """The preset keys behind `make --aspect --fps --duration --sound --rounds` (ruling 15: format per run)."""
    out: dict = {}
    if aspect:
        if aspect not in FORMATS:
            raise UsageError(f"--aspect {aspect!r}: use one of {', '.join(FORMATS)}")
        out["video.width"], out["video.height"] = FORMATS[aspect]
        if aspect != "9:16":
            out["video.safe_zone"] = dict(TITLE_SAFE)
    if fps:
        out["video.fps"] = int(fps)
    if duration:
        m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*(?:-\s*(\d+(?:\.\d+)?))?\s*", str(duration))
        if not m or (m.group(2) and float(m.group(2)) < float(m.group(1))):
            raise UsageError(f"--duration {duration!r}: use seconds, e.g. 15 or 10-18")
        lo = float(m.group(1))
        hi = float(m.group(2)) if m.group(2) else lo
        out["video.duration"] = [int(lo) if lo.is_integer() else lo, int(hi) if hi.is_integer() else hi]
    if sound:
        if sound not in SOUNDS:
            raise UsageError(f"--sound {sound!r}: use one of {', '.join(SOUNDS)}")
        out["video.sound"] = sound
    if rounds:
        out["agent.rounds"] = int(rounds)
    return out


def guarded(key: str, prefixes: tuple[str, ...]) -> bool:
    """`key` sets a guarded key, or a whole table holding one (`agent` would replace agent.mcp too)."""
    return any(key == g or key.startswith(g + ".") or g.startswith(key + ".") for g in prefixes)


def deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def _toml_key(k: str) -> str:
    return k if re.fullmatch(r"[A-Za-z0-9_-]+", k) else json.dumps(k)


def _toml_scalar(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, list):
        return "[" + ", ".join(_toml_scalar(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{_toml_key(k)} = {_toml_scalar(x)}" for k, x in v.items()) + " }"
    return json.dumps(str(v), ensure_ascii=False)


def dump_toml(data: dict) -> str:
    """Minimal writer for config.toml (comments are not preserved)."""
    lines: list[str] = []

    def walk(prefix: str, table: dict) -> None:
        simple = {k: v for k, v in table.items() if not isinstance(v, dict)}
        nested = {k: v for k, v in table.items() if isinstance(v, dict)}
        if prefix and (simple or not nested):
            lines.append(f"\n[{prefix}]")
        for k, v in simple.items():
            lines.append(f"{_toml_key(k)} = {_toml_scalar(v)}")
        for k, v in nested.items():
            walk(f"{prefix}.{_toml_key(k)}" if prefix else _toml_key(k), v)

    walk("", data)
    return "\n".join(lines).lstrip("\n") + "\n"


def load_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{path}: {e}", "fix the TOML syntax") from e


# --- .env --------------------------------------------------------------------------------------------

def load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.removeprefix("export ").strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "'\"":
            val = val[1:-1]
        out[key] = val
    return out


def save_env(path: Path, updates: dict[str, str | None]) -> None:
    """Rewrite only the given keys (None deletes), keep everything else, mode 0600."""
    lines = path.read_text().splitlines() if path.exists() else []
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        key = line.split("=", 1)[0].removeprefix("export ").strip() if "=" in line and not line.lstrip().startswith("#") else None
        if key in updates:
            seen.add(key)
            if updates[key] is not None:
                out.append(f"{key}={updates[key]}")
            continue
        out.append(line)
    out += [f"{k}={v}" for k, v in updates.items() if k not in seen and v is not None]
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write("\n".join(out) + "\n")
    os.replace(tmp, path)
    os.chmod(path, 0o600)


# --- paths + config ------------------------------------------------------------------------------------

# --- the project: one folder holds everything, and nothing is written outside its repo ------------------

PROJECT_FILE = "social-studio.toml"


def find_project(start: Path) -> Path | None:
    """Walk up from `start` to a folder holding social-studio.toml, or one whose social/ child does."""
    for d in (start, *start.parents):
        if (d / PROJECT_FILE).is_file():
            return d
        if (d / "social" / PROJECT_FILE).is_file():
            return d / "social"
    return None


def repo_root(path: Path) -> Path:
    """The git work tree holding `path` (or `path` itself outside git): the write boundary."""
    for d in (path, *path.parents):
        if (d / ".git").exists():
            return d
    return path


@dataclass
class Ctx:
    """Everything a command needs: the project folder, its config and its .env."""
    project: Path | None
    config: dict
    json: bool = False

    def need(self) -> Path:
        if self.project is None:
            raise ConfigError("no social-studio project found",
                              "run `social-studio init <dir>`, pass --project <dir>, or run inside the project")
        return self.project

    @property
    def boundary(self) -> Path:
        return repo_root(self.need())

    @property
    def studio_dir(self) -> Path:
        return self.need() / ".studio"

    @property
    def db_path(self) -> Path:
        return self.studio_dir / "library.db"

    @property
    def sessions_dir(self) -> Path:
        return self.studio_dir / "sessions"

    @property
    def engine_dir(self) -> Path:
        return self.studio_dir / "engine"

    @property
    def cache_dir(self) -> Path:
        return self.studio_dir / "cache"

    @property
    def approval_dir(self) -> Path:
        return self.studio_dir / "approval"

    @property
    def drafts_dir(self) -> Path:
        return self.need() / "drafts"

    @property
    def env_path(self) -> Path:
        return self.need() / ".env"

    @property
    def config_path(self) -> Path:
        return self.need() / PROJECT_FILE

    @property
    def library_dir(self) -> Path:
        return self.inside(self.abs(self.cfg("paths.library") or "library"), "the library")

    def abs(self, path: str | Path) -> Path:
        q = Path(path).expanduser()
        return q if q.is_absolute() else self.need() / q

    def rel(self, path: str | Path) -> str:
        """Paths stored in the database are relative to the project, so the project can move."""
        q = Path(path).resolve()
        try:
            return str(q.relative_to(self.need().resolve()))
        except ValueError:
            return str(q)

    def inside(self, path: str | Path, what: str) -> Path:
        q, b = Path(path).resolve(), self.boundary.resolve()
        if q != b and b not in q.parents:
            raise Denied(f"{what} must stay inside {b}", "social-studio never writes outside the project's repo")
        return q

    def env(self, name: str, default: str | None = None) -> str | None:
        file_env = load_env(self.env_path) if self.project else {}
        return os.environ.get(name) or file_env.get(name) or default

    def cfg(self, key: str, default=None):
        return dget(self.config, key, default)

    def save_config(self) -> None:
        self.config_path.write_text(dump_toml(self.config))


def make_ctx(project: str | None = None, as_json: bool = False) -> Ctx:
    given = project or os.environ.get("SOCIAL_STUDIO_PROJECT")
    root = Path(given).expanduser().resolve() if given else find_project(Path.cwd().resolve())
    config = load_toml(root / PROJECT_FILE) if root else {}
    return Ctx(root, config, as_json)


def path_problem(ctx: Ctx, path: Path) -> str | None:
    """Why `path` may not go into a session: outside the repo, or the project's own secrets and state (R0).
    Files shipped inside a built-in preset (fonts, helpers, skills) are part of the tool and always allowed."""
    q, root, project = path.resolve(), ctx.boundary.resolve(), ctx.need().resolve()
    if (PKG_DIR / "presets").resolve() in q.parents and not q.name.startswith(".env"):
        return None
    if q != root and root not in q.parents:
        return "is outside the repo"
    if q == project or q in project.parents:
        return "holds the whole project, its .env and database included"
    for private in (ctx.env_path, ctx.studio_dir, ctx.library_dir, ctx.drafts_dir):
        if q == private.resolve() or private.resolve() in q.parents:
            return "is the project's private state"
    if q.name.startswith(".env"):
        return "is a secrets file"
    return None


def mcp_registry(ctx: Ctx) -> dict[str, dict]:
    """The vetted MCP servers a preset may name: [servers.NAME] in the project's mcp.toml, which only a human edits.
    Each entry's `secrets` lists the only ${VAR} names it may fill (R0)."""
    servers = load_toml(ctx.need() / MCP_FILE).get("servers", {})
    return {k: v for k, v in servers.items() if SLUG.fullmatch(k) and isinstance(v, dict)}


# --- presets ----------------------------------------------------------------------------------------------

@dataclass
class Preset:
    name: str
    dir: Path
    data: dict

    def get(self, key: str, default=None):
        return dget(self.data, key, default)

    def path(self, rel: str) -> Path:
        p = Path(rel).expanduser()
        return p if p.is_absolute() else self.dir / p

    @property
    def hash(self) -> str:
        return hashlib.sha256(json.dumps(self.data, sort_keys=True).encode()).hexdigest()[:16]


def preset_dirs(ctx: Ctx) -> list[Path]:
    dirs = []
    if ctx.project:
        dirs.append(ctx.project / "presets")
        dirs += [ctx.abs(p) for p in ctx.cfg("preset_paths", [])]
    return [*dirs, PKG_DIR / "presets"]


def _preset_file(ctx: Ctx, name: str) -> tuple[Path, bool]:
    """The preset's file, and whether it sits in a presets folder (trusted) rather than being a path from the
    command line. Preset files other than the built-ins must sit inside the repo."""
    dirs = [d.resolve() for d in preset_dirs(ctx)]
    p, found = Path(name).expanduser(), None
    if p.suffix == ".toml" and p.is_file():
        found = p.resolve()
    elif p.is_dir() and (p / "preset.toml").is_file():
        found = (p / "preset.toml").resolve()
    else:
        found = next((c.resolve() for d in dirs for c in (d / name / "preset.toml", d / f"{name}.toml") if c.is_file()),
                     None)
    if found is None:
        raise ConfigError(f"preset not found: {name}",
                          "run `social-studio preset list`; presets live in the project's presets/ folder")
    if (PKG_DIR / "presets").resolve() not in found.parents:
        ctx.inside(found, "a preset file")
    return found, any(d in found.parents for d in dirs)


def load_preset(ctx: Ctx, name: str, overrides: dict | None = None, _depth: int = 0) -> Preset:
    if _depth > 5:
        raise ConfigError("preset `extends` chain is too deep")
    f, trusted = _preset_file(ctx, name)
    data = load_toml(f)
    for key in () if trusted else GUARDED_PRESET:
        if dget(data, key) is not None:
            require_human(f"taking {key} from {f}, a preset outside the presets folders")
    base = data.pop("extends", None)
    if base:
        data = deep_merge(load_preset(ctx, base, None, _depth + 1).data, data)
    for key, val in (overrides or {}).items():
        if guarded(key, GUARDED_PRESET):
            require_human(f"overriding {key}")
        dset(data, key, val)
    pname = dget(data, "preset.name") or (f.parent.name if f.name == "preset.toml" else f.stem)
    return Preset(pname, f.parent, data)


def list_presets(ctx: Ctx) -> list[dict]:
    found: dict[str, dict] = {}
    for d in preset_dirs(ctx):
        if not d.is_dir():
            continue
        for item in sorted(d.iterdir()):
            f = item / "preset.toml" if item.is_dir() else item
            if f.is_file() and f.suffix == ".toml" and (item.is_dir() or item.suffix == ".toml"):
                name = item.name if item.is_dir() else item.stem
                if name not in found:
                    desc = dget(load_toml(f), "preset.description", "")
                    found[name] = {"name": name, "path": str(f), "description": desc}
    return list(found.values())


def validate_preset(p: Preset, ctx: Ctx) -> list[str]:
    """Problems that would break a run or cross the boundary. Empty list means usable."""
    errs: list[str] = _r0_problems(p, ctx)
    for key, typ in (("video.width", int), ("video.height", int), ("video.fps", int),
                     ("render.engine", str), ("render.version", str)):
        if not isinstance(p.get(key), typ):
            errs.append(f"{key} must be a {typ.__name__}")
    if p.get("render.engine") not in (None, "hyperframes"):
        errs.append("render.engine: only `hyperframes` is supported")
    dur = p.get("video.duration")
    if not (isinstance(dur, list) and len(dur) == 2 and all(isinstance(x, (int, float)) for x in dur)):
        errs.append("video.duration must be [min_seconds, max_seconds]")
    errs += [f"{role}.effort must be one of {', '.join(EFFORTS)}" for role in ("agent", "review")
             if p.get(f"{role}.effort") is not None and p.get(f"{role}.effort") not in EFFORTS]
    rounds = p.get("agent.rounds", 2)
    if isinstance(rounds, bool) or not isinstance(rounds, int) or not 1 <= rounds <= 5:
        errs.append("agent.rounds must be a whole number from 1 to 5")
    errs += [f"{key} must be text" for key in ("video.pacing", "video.motion")
             if p.get(key) is not None and not isinstance(p.get(key), str)]
    if p.get("video.sound") is not None and p.get("video.sound") not in SOUNDS:
        errs.append(f"video.sound must be one of {', '.join(SOUNDS)}")
    if p.get("agent.package_skills"):
        from .runner import vendored_skills  # runner imports core; this import runs only when the key is set
        known = vendored_skills()
        errs += [f"agent.package_skills: no vendored skill named {n!r}" for n in p.get("agent.package_skills")
                 if n not in known]
    end = p.get("video.end_card_max", 0.2)
    if isinstance(end, bool) or not isinstance(end, (int, float)) or not 0 < end < 1:
        errs.append("video.end_card_max must be a share of the runtime between 0 and 1")
    for font in p.get("brand.fonts", {}).values():
        if not isinstance(font, dict):
            continue
        for entry in font.get("files", []):
            rel = entry.get("file", "") if isinstance(entry, dict) else entry
            if not p.path(rel).is_file():
                errs.append(f"font file missing: {rel}")
        family = str(font.get("family", ""))
        if family.lower() in ALIASED_FONTS:
            errs.append(f"font family {family!r} is swapped for a Google font (Inter for Helvetica/Arial) by the "
                        "renderer; ship the font file under a family name of your own")
    for rel in p.get("assets.files", []):
        if not p.path(rel).exists():
            errs.append(f"asset missing: {rel}")
    for name, spec in p.get("agent.skills", {}).items():
        if isinstance(spec, str) and not spec.strip():
            errs.append(f"agent.skills.{name} is empty")
        elif isinstance(spec, dict) and spec.get("path") and not p.path(spec["path"]).is_dir():
            errs.append(f"agent.skills.{name}.path is not a directory")
    return errs


def _r0_problems(p: Preset, ctx: Ctx) -> list[str]:
    """R0: MCP servers come from the registry by name, skill names are slugs, every path stays inside the repo
    and away from the project's secrets, and the engine is an exact pin."""
    errs: list[str] = []

    def where(key: str, rel) -> None:
        why = path_problem(ctx, p.path(str(rel)))
        if why:
            errs.append(f"{key}: {rel} {why}")

    for rel in p.get("assets.files", []):
        where("assets.files", rel)
    for fname, font in p.get("brand.fonts", {}).items():
        for entry in font.get("files", []) if isinstance(font, dict) else []:
            where(f"brand.fonts.{fname}", entry.get("file", "") if isinstance(entry, dict) else entry)
    for rel in p.get("agent.plugins", []):
        where("agent.plugins", rel)
        if p.path(str(rel)).is_dir() and next(p.path(str(rel)).rglob(".env*"), None):
            errs.append(f"agent.plugins: {rel} holds a .env file")
    for name in p.get("agent.engine_skills", []):
        if not SLUG.fullmatch(str(name)):
            errs.append(f"agent.engine_skills: {name!r} is not a skill name (a-z, 0-9, hyphens)")
    for name, spec in p.get("agent.skills", {}).items():
        if not SLUG.fullmatch(name):
            errs.append(f"agent.skills: {name!r} is not a skill name (a-z, 0-9, hyphens)")
        if isinstance(spec, dict) and spec.get("path"):
            where(f"agent.skills.{name}.path", spec["path"])
    mcp = p.get("agent.mcp", [])
    if isinstance(mcp, dict):
        if mcp:
            errs.append(f"agent.mcp: name servers from {MCP_FILE}; a preset cannot define them")
    elif isinstance(mcp, list):
        registry = mcp_registry(ctx)
        errs += [f"agent.mcp: {n!r} is not in {MCP_FILE}" for n in mcp if not isinstance(n, str) or n not in registry]
    else:
        errs.append(f"agent.mcp must be a list of server names from {MCP_FILE}")
    if isinstance(p.get("render.version"), str) and not SEMVER.fullmatch(p.get("render.version")):
        errs.append(f"render.version: {p.get('render.version')!r} is not an exact version")
    errs += [f"render.libraries: {lib!r} must be a registry package at an exact version (name@1.2.3)"
             for lib in p.get("render.libraries", []) if not NPM_PIN.fullmatch(str(lib))]
    for name, rel in p.get("render.vendor", {}).items():
        if Path(name).name != name or name.startswith(".") or Path(str(rel)).is_absolute() or ".." in Path(str(rel)).parts:
            errs.append(f"render.vendor: {name} = {rel!r} must be a file name and a path inside node_modules")
    for spec, files in p.get("render.esm", {}).items():
        if not (isinstance(files, list) and files and all(isinstance(f, str) for f in files)):
            errs.append(f"render.esm.{spec} must be a list of paths inside node_modules, the entry first")
            continue
        if not re.fullmatch(r"[a-z0-9@][a-z0-9._/-]*", spec):
            errs.append(f"render.esm: {spec!r} is not a module name")
        errs += [f"render.esm.{spec}: {rel!r} must be a path inside node_modules" for rel in files
                 if Path(rel).is_absolute() or ".." in Path(rel).parts or Path(rel).name.startswith(".")]
    return errs


# --- output ------------------------------------------------------------------------------------------------

def emit(ctx: Ctx | None, data, human: str | None = None) -> None:
    """stdout carries the result only: JSON with --json, a human rendering otherwise."""
    if ctx is not None and ctx.json:
        print(json.dumps(data, indent=2, default=str))
    elif human is not None:
        print(human)
    else:
        print(json.dumps(data, indent=2, default=str))


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)
