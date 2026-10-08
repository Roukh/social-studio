"""Human approval as a signature the agent cannot forge.

`approve` signs "video id + exact file sha256 + post text hash" with an ed25519 key protected by a
passphrase only the human knows (OpenSSH `ssh-keygen -Y sign`, which reads the passphrase from the
terminal). `post` verifies that signature with the public key before it uploads or schedules a video, so editing the database by hand, swapping the file, or rewriting the caption after approval gets
nothing posted.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .core import ConfigError, Ctx, Denied, Unavailable, iso, require_human

NAMESPACE = "social-studio-approval"
IDENTITY = "social-studio"


def _keygen() -> str:
    exe = shutil.which("ssh-keygen")
    if not exe:
        raise Unavailable("ssh-keygen not found", "install OpenSSH (it signs approvals)")
    return exe


def _tmp_root(ctx: Ctx) -> Path:
    """Scratch space for payload and signature files, inside the project like everything else."""
    ctx.studio_dir.mkdir(parents=True, exist_ok=True)
    return ctx.studio_dir


def key_paths(ctx: Ctx) -> tuple[Path, Path, Path]:
    d = ctx.approval_dir
    return d / "key", d / "key.pub", d / "allowed_signers"


def is_ready(ctx: Ctx) -> bool:
    _, pub, allowed = key_paths(ctx)
    return pub.is_file() and allowed.is_file()


def init_key(ctx: Ctx) -> Path:
    """Create the approval key. ssh-keygen asks the human for a passphrase on the terminal."""
    require_human("creating the approval key")
    key, pub, allowed = key_paths(ctx)
    if key.exists():
        return pub
    key.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([_keygen(), "-q", "-t", "ed25519", "-C", IDENTITY, "-f", str(key)], check=True)
    probe = subprocess.run([_keygen(), "-y", "-P", "", "-f", str(key)], capture_output=True)
    if probe.returncode == 0:
        key.unlink()
        pub.unlink(missing_ok=True)
        raise ConfigError("the approval key needs a passphrase",
                          "run init again and enter a passphrase; without one an agent could sign")
    allowed.write_text(f'{IDENTITY} namespaces="{NAMESPACE}" {pub.read_text().strip()}\n')
    return pub


# What a post says, besides the video: the human approves this text together with the file.
POST_FIELDS = ("captions", "hashtags", "poster_at")


def post_hash(video: dict) -> str:
    """sha256 over the post text: title, description, and the captions, hashtags and cover frame from video.json."""
    meta = json.loads(video["meta"] or "{}").get("video", {})
    post = {"title": video["title"], "description": video["description"], **{k: meta.get(k) for k in POST_FIELDS}}
    return hashlib.sha256(json.dumps(post, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def payload(video: dict, approved_at: str) -> str:
    return (f"social-studio approval v2\nvideo:{video['id']}\nsha256:{video['sha256']}\n"
            f"post:{post_hash(video)}\napproved_at:{approved_at}\n")


def sign(ctx: Ctx, videos: list[dict]) -> list[tuple[dict, str, str]]:
    """One passphrase prompt signs every given video. Returns (video, payload, signature)."""
    require_human("approving videos")
    key, _, _ = key_paths(ctx)
    if not key.is_file():
        raise ConfigError("no approval key", "run `sclstdio init` yourself, in a terminal")
    stamp = iso()
    with tempfile.TemporaryDirectory(dir=_tmp_root(ctx)) as tmp:
        files = []
        for v in videos:
            f = Path(tmp) / f"v{v['id']}"
            f.write_text(payload(v, stamp))
            files.append(f)
        res = subprocess.run([_keygen(), "-Y", "sign", "-q", "-f", str(key), "-n", NAMESPACE, *map(str, files)])
        if res.returncode != 0:
            raise Denied("signing failed (wrong passphrase or no terminal)")
        return [(v, f.read_text(), Path(f"{f}.sig").read_text()) for v, f in zip(videos, files)]


def verify(ctx: Ctx, approval_payload: str, signature: str, video: dict) -> bool:
    """True only if the signature is valid AND it covers this video id and this exact sha256."""
    _, _, allowed = key_paths(ctx)
    if not allowed.is_file():
        return False
    expected = f"video:{video['id']}\nsha256:{video['sha256']}\n"
    if expected not in approval_payload:
        return False
    with tempfile.TemporaryDirectory(dir=_tmp_root(ctx)) as tmp:
        sig = Path(tmp) / "sig"
        sig.write_text(signature)
        res = subprocess.run([_keygen(), "-Y", "verify", "-f", str(allowed), "-I", IDENTITY, "-n", NAMESPACE,
                              "-s", str(sig)], input=approval_payload.encode(), capture_output=True)
        return res.returncode == 0


def check_video(ctx: Ctx, con, video: dict, rehash: bool = True, post: bool = False) -> str | None:
    """Return None when the video is cleared to schedule/post, else the reason it is not.
    `post=True` also requires the signed post text to match what the library holds now."""
    from .core import sha256_file
    row = con.execute("SELECT payload, signature, sha256 FROM approvals WHERE video_id = ?", (video["id"],)).fetchone()
    if row is None:
        return "no approval record"
    if row["sha256"] != video["sha256"]:
        return "approval is for a different file"
    if not verify(ctx, row["payload"], row["signature"], video):
        return "approval signature does not verify"
    if post and f"\npost:{post_hash(video)}\n" not in row["payload"]:
        return ("post text changed after approval" if "\npost:" in row["payload"]
                else "approved before post text was signed; approve it again")
    if rehash:
        path = ctx.abs(video["file"]) if video["file"] else None
        if path is None or not path.is_file():
            return "video file is missing"
        if sha256_file(path) != video["sha256"]:
            return "video file changed after approval"
    return None
