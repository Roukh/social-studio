"""Render engine (HyperFrames, pinned per preset), the bubblewrap sandbox, and the ffmpeg encode.

Everything that executes LLM-written code (the agent itself, `hyperframes` checks, the final
render) runs inside the sandbox: an empty throwaway HOME, the session folder as the only
writable place, read-only system dirs, and no path to the library, the database or the .env.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from .core import SEMVER, ConfigError, Ctx, DataError, Unavailable, log, sha256_file

QUIET_ENV = {
    "DO_NOT_TRACK": "1",
    "HYPERFRAMES_NO_UPDATE_CHECK": "1",
    "HYPERFRAMES_NO_AUTO_INSTALL": "1",
    "HYPERFRAMES_SKIP_SKILLS": "1",
}


# --- engine install -------------------------------------------------------------------------------

# Every composition gets GSAP and three.js (with the motion kit, runner.KIT_JS), so any technique in the library
# is open to any preset (operator, 2026-10-07). A preset that pins its own version of a package keeps it.
KIT_LIBRARIES = {"gsap": "gsap@3.14.2", "three": "three@0.181.2"}
KIT_VENDOR = {"gsap.min.js": "gsap/dist/gsap.min.js"}
KIT_ESM = {"three": ["three/build/three.module.min.js", "three/build/three.core.min.js"]}


def _package(spec: str) -> str:
    """npm package name of `name@1.2.3` or `@scope/name@1.2.3`, or of a path inside node_modules."""
    if "/" in spec and not spec.startswith("@"):
        return spec.split("/")[0]
    at = spec.rfind("@")
    name = spec[:at] if at > 0 else spec
    return "/".join(name.split("/")[:2]) if name.startswith("@") else name.split("/")[0]


def libraries(p) -> list[str]:
    """The preset's render.libraries plus the kit's packages it does not pin itself."""
    own = list(p.get("render.libraries", []))
    pinned = {_package(s) for s in own}
    return own + [spec for name, spec in KIT_LIBRARIES.items() if name not in pinned]


def vendor(p) -> dict[str, str]:
    """render.vendor plus the kit's classic scripts for packages the preset does not vendor itself."""
    own = dict(p.get("render.vendor", {}))
    mine = {_package(rel) for rel in own.values()}
    return {**own, **{n: rel for n, rel in KIT_VENDOR.items() if _package(rel) not in mine and n not in own}}


def esm(p) -> dict[str, list[str]]:
    """render.esm plus the kit's modules; a preset's own entry for a module name wins."""
    return {**KIT_ESM, **p.get("render.esm", {})}


def engine_root(ctx: Ctx, version: str) -> Path:
    return ctx.engine_dir / f"hyperframes-{version}"


def hf_bin(ctx: Ctx, version: str) -> Path:
    return engine_root(ctx, version) / "node_modules" / ".bin" / "hyperframes"


def ensure_engine(ctx: Ctx, version: str, libraries: list[str] | None = None) -> Path:
    """Install hyperframes@version (+ preset libraries such as gsap@3.14.2) once, then reuse it."""
    root = engine_root(ctx, version)
    libs = sorted(set(libraries or []))
    stamp = root / ".installed.json"
    if stamp.is_file() and json.loads(stamp.read_text()).get("libraries") == libs and hf_bin(ctx, version).exists():
        return root
    npm = shutil.which("npm")
    if not npm:
        raise Unavailable("npm not found", "install Node.js 22 or later")
    root.mkdir(parents=True, exist_ok=True)
    if not (root / "package.json").exists():
        (root / "package.json").write_text('{"name": "social-studio-engine", "private": true}\n')
    log(f"installing hyperframes@{version} {' '.join(libs)} into {root}")
    subprocess.run([npm, "install", "--no-audit", "--no-fund", "--prefix", str(root),
                    "--cache", str(ctx.cache_dir / "npm"), f"hyperframes@{version}", *libs],
                   check=True, stdout=subprocess.DEVNULL, env=engine_env(ctx))
    subprocess.run([str(hf_bin(ctx, version)), "browser", "ensure"], check=True, env=engine_env(ctx),
                   stdout=subprocess.DEVNULL)
    stamp.write_text(json.dumps({"version": version, "libraries": libs}))
    return root


def skills_root(ctx: Ctx, version: str) -> Path:
    return engine_root(ctx, version) / "skills"


def ensure_skills(ctx: Ctx, version: str) -> Path:
    """The engine's agent skills at the exact same git tag as the npm package, fetched once."""
    import tarfile
    import urllib.request
    root = skills_root(ctx, version)
    if (root / "hyperframes-core" / "SKILL.md").is_file():
        return root
    url = f"https://codeload.github.com/heygen-com/hyperframes/tar.gz/refs/tags/v{version}"
    log(f"fetching hyperframes v{version} skills")
    tmp = root.with_name("skills.partial")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    with urllib.request.urlopen(url, timeout=300) as resp, tarfile.open(fileobj=resp, mode="r|gz") as tar:
        for member in tar:
            parts = member.name.split("/", 2)
            if len(parts) == 3 and parts[1] == "skills" and (member.isfile() or member.isdir()):
                member.name = parts[2]
                tar.extract(member, tmp, filter="data")
    if not (tmp / "hyperframes-core" / "SKILL.md").is_file():
        raise Unavailable(f"skills for hyperframes v{version} not found in {url}")
    shutil.rmtree(root, ignore_errors=True)
    tmp.rename(root)
    return root


def engine_env(ctx: Ctx) -> dict[str, str]:
    """HyperFrames keeps Chrome and fonts under $HOME/.cache: point that inside the project."""
    home = ctx.cache_dir / "home"
    home.mkdir(parents=True, exist_ok=True)
    # Node 24 ignores HTTPS_PROXY unless told to; behind a proxy the Chrome download would hang with no output.
    return {**os.environ, **QUIET_ENV, "NODE_USE_ENV_PROXY": "1", "HOME": str(home), "XDG_CACHE_HOME": str(home / ".cache")}


def chrome_path(ctx: Ctx, version: str) -> Path:
    out = subprocess.run([str(hf_bin(ctx, version)), "browser", "path"], capture_output=True, text=True,
                         env=engine_env(ctx))
    p = Path(out.stdout.strip().splitlines()[-1]) if out.stdout.strip() else None
    if not p or not p.exists():
        raise Unavailable("pinned Chrome not found", "run `social-studio engine install`")
    return p


def chrome_root(path: Path) -> Path:
    """The versioned folder holding chrome-headless-shell, bound read-only into the sandbox."""
    for parent in path.parents:
        if parent.name.startswith("linux-") or parent.name.startswith("mac"):
            return parent
    return path.parent


# --- sandbox --------------------------------------------------------------------------------------

def sandbox_available() -> bool:
    return shutil.which("bwrap") is not None


def bwrap_argv(workdir: Path, home: Path, rw: list[Path], ro: list[Path], env: dict[str, str],
               network: bool = True) -> list[str]:
    """bubblewrap argv prefix. HOME is the session's throwaway home; nothing else from $HOME exists."""
    exe = shutil.which("bwrap")
    if not exe:
        raise Unavailable("bubblewrap (bwrap) not found", "install bubblewrap, or run with --no-sandbox")
    argv = [exe, "--die-with-parent", "--unshare-all", "--new-session"]
    if network:
        argv.append("--share-net")
    argv += ["--ro-bind", "/usr", "/usr", "--ro-bind", "/etc", "/etc",
             "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/dev/shm", "--tmpfs", "/tmp"]
    for top in ("/bin", "/sbin", "/lib", "/lib64", "/lib32", "/opt"):
        p = Path(top)
        if p.is_symlink():
            argv += ["--symlink", os.readlink(p), top]
        elif p.is_dir():
            argv += ["--ro-bind", top, top]
    if Path("/var/cache/fontconfig").is_dir():
        argv += ["--ro-bind", "/var/cache/fontconfig", "/var/cache/fontconfig"]
    real_home = Path.home()
    argv += ["--tmpfs", str(real_home), "--bind", str(home), str(home)]
    for p in ro:
        if p.exists():
            argv += ["--ro-bind", str(p), str(p)]
    for p in rw:
        if p.exists():
            argv += ["--bind", str(p), str(p)]
    argv += ["--clearenv"]
    for k, v in env.items():
        argv += ["--setenv", k, v]
    argv += ["--chdir", str(workdir), "--"]
    return argv


def protected(ctx: Ctx) -> list[Path]:
    """Folders the sandbox must never see, not even through a parent bind: home and the project."""
    return [Path.home(), ctx.need()]


def safe_root(candidate: Path, fallback: Path, ctx: Ctx) -> Path:
    """`candidate` unless it is (or contains) a protected folder; then `fallback`, then nothing wider."""
    for path in (candidate, fallback):
        path = path.resolve()
        if not any(path == p.resolve() or path in p.resolve().parents for p in protected(ctx)):
            return path
    raise ConfigError(f"refusing to expose {fallback} to the sandbox: it contains your home or the project",
                      "install the harness or node somewhere other than directly in your home folder")


def node_dirs(ctx: Ctx) -> tuple[list[Path], list[Path]]:
    """(read-only binds, PATH entries) so the sandbox runs the same node as the host (nvm, asdf...)."""
    exe = shutil.which("node")
    if not exe:
        return [], []
    real = Path(exe).resolve()
    if str(real).startswith(("/usr/", "/bin/", "/opt/")):
        return [], []
    return [safe_root(real.parent.parent, real.parent, ctx)], [real.parent]


def base_env(home: Path, extra_path: list[Path] | None = None) -> dict[str, str]:
    path = ":".join([*(str(p) for p in extra_path or []), "/usr/local/bin", "/usr/bin", "/bin"])
    env = {"HOME": str(home), "PATH": path, "LANG": os.environ.get("LANG", "C.UTF-8"),
           "TERM": "dumb", "SOCIAL_STUDIO_ROLE": "agent", **QUIET_ENV}
    if os.environ.get("TZ"):
        env["TZ"] = os.environ["TZ"]
    return env


# --- render + encode --------------------------------------------------------------------------------

def render_master(prefix: list[str], hf: Path, comp: Path, out: Path, fps: int, crf: int = 10,
                  timeout: int = 1800, env: dict[str, str] | None = None) -> None:
    """Final render to a near-lossless, opaque H.264 master (CRF 10). Not MOV: HyperFrames renders MOV
    with alpha and drops the page background, which a yuv420p encode then turns black."""
    cmd = [*prefix, str(hf), "render", str(comp), "--format", "mp4", "--crf", str(crf), "-o", str(out),
           "--fps", str(fps), "--no-browser-gpu", "--strict"]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    if res.returncode != 0 or not out.exists():  # not --quiet: it also hides the lint findings that abort a render
        raise DataError(f"render failed: {(res.stdout + res.stderr).strip()[-1500:]}",
                        "inspect the session folder; the composition did not render")


def probe(path: Path) -> dict:
    exe = shutil.which("ffprobe")
    if not exe:
        raise Unavailable("ffprobe not found", "install ffmpeg")
    out = subprocess.run([exe, "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)],
                         capture_output=True, text=True, check=True)
    info = json.loads(out.stdout)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    if v is None:
        raise DataError(f"{path} has no video stream")
    return {"width": int(v["width"]), "height": int(v["height"]),
            "duration": float(info["format"].get("duration") or v.get("duration") or 0),
            "audio": any(s["codec_type"] == "audio" for s in info["streams"])}


def _loudnorm_args(src: Path, target: float) -> list[str]:
    """Two-pass loudnorm: measure, then apply linear normalization to the measured values."""
    res = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-af",
                          f"loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True)
    text = res.stderr
    try:
        m = json.loads(text[text.rindex("{"):text.rindex("}") + 1])
        return ["-af", (f"loudnorm=I={target}:TP=-1.5:LRA=11:measured_I={m['input_i']}:"
                        f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
                        f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")]
    except (ValueError, KeyError):
        return ["-af", f"loudnorm=I={target}:TP=-1.5:LRA=11"]


def encode(src: Path, dst: Path, enc: dict, fps: int) -> dict:
    """The delivery encode: H.264 for every platform, sized for upload limits, faststart."""
    if not shutil.which("ffmpeg"):
        raise Unavailable("ffmpeg not found", "install ffmpeg")
    info = probe(src)
    gop = str(int(fps) * 2)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", str(enc.get("preset", "slow")),
           "-crf", str(enc.get("crf", 20)), "-tune", str(enc.get("tune", "animation")),
           "-g", gop, "-keyint_min", gop, "-sc_threshold", "0",
           "-maxrate", str(enc.get("maxrate", "8M")), "-bufsize", str(enc.get("bufsize", "16M")),
           "-r", str(fps)]
    if info["audio"]:
        cmd += ["-c:a", "aac", "-b:a", str(enc.get("audio_bitrate", "192k")), "-ar", "48000"]
        cmd += _loudnorm_args(src, float(enc.get("loudness", -14)))
    else:
        cmd += ["-an"]
    cmd += ["-movflags", "+faststart", str(dst)]
    subprocess.run(cmd, check=True)
    out = probe(dst)
    out.update(bytes=dst.stat().st_size, sha256=sha256_file(dst))
    return out


def poster_and_sheet(video: Path, poster: Path, sheet: Path, duration: float, poster_at: float | None) -> None:
    t = poster_at if poster_at is not None else max(0.0, duration * 0.5)
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(video),
                    "-frames:v", "1", "-q:v", "3", str(poster)], check=True)
    n = 12
    rate = max(n / max(duration, 0.1), 0.01)
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video), "-vf",
                    f"fps={rate:.4f},scale=270:-2,tile=6x2:padding=6:margin=6:color=white",
                    "-frames:v", "1", "-q:v", "3", str(sheet)], check=True)


def check_ffmpeg() -> list[str]:
    return [b for b in ("ffmpeg", "ffprobe", "node", "npm") if not shutil.which(b)]


def require_version(preset_version: str | None) -> str:
    """An exact version only: it names a folder under .studio/engine and an npm spec run on the host."""
    if not preset_version:
        raise ConfigError("preset has no render.version", "pin an exact hyperframes version, e.g. 0.8.106")
    if not SEMVER.fullmatch(str(preset_version)):
        raise ConfigError(f"render.version {preset_version!r} is not an exact version", "pin one, e.g. 0.8.106")
    return preset_version
