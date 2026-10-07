"""Platform adapters, plus the small HTTP and OAuth helpers they share (stdlib only).

Buffer (buffer.py) is the posting route for Instagram, Facebook and X; media.py hosts the video it fetches.
The direct adapters below remain for a developer app of your own: every platform's client id/secret and
tokens live in the .env.
LinkedIn's API terms forbid automated posting and TikTok rejects in-house upload tools in audit,
so those two export ready-to-post drafts instead of calling an API.
"""
from __future__ import annotations

import base64
import getpass
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import secrets
import shutil
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
from pathlib import Path

from ..core import ConfigError, Ctx, DataError, Unavailable, log, require_human, save_env


# --- HTTP ---------------------------------------------------------------------------------------------

class HttpError(Unavailable):
    def __init__(self, status: int, url: str, body: str):
        super().__init__(f"HTTP {status} from {urllib.parse.urlsplit(url).netloc}: {body[:600]}")
        self.status = status


def http(method: str, url: str, *, params: dict | None = None, headers: dict | None = None,
         json_body=None, form: dict | None = None, data: bytes | None = None, timeout: int = 120):
    """Returns (status, headers, parsed JSON or text). Raises HttpError on 4xx/5xx."""
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    hdrs = dict(headers or {})
    if json_body is not None:
        data = json.dumps(json_body).encode()
        hdrs.setdefault("Content-Type", "application/json")
    elif form is not None:
        data = urllib.parse.urlencode(form).encode()
        hdrs.setdefault("Content-Type", "application/x-www-form-urlencoded")
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            status, rh = resp.status, dict(resp.headers)
    except urllib.error.HTTPError as e:
        raise HttpError(e.code, url, e.read().decode("utf-8", "replace")) from e
    text = raw.decode("utf-8", "replace")
    try:
        return status, rh, json.loads(text) if text else {}
    except json.JSONDecodeError:
        return status, rh, text


def multipart(fields: dict[str, str], files: dict[str, tuple[str, bytes, str]]) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    out = bytearray()
    for k, v in fields.items():
        out += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    for k, (fname, blob, ctype) in files.items():
        out += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{fname}\"\r\n"
                f"Content-Type: {ctype}\r\n\r\n").encode() + blob + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={boundary}"


# --- OAuth (authorization code + PKCE, loopback redirect or paste-back) ---------------------------------

def pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)[:96]
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


def authorize(auth_url: str, redirect_uri: str, state: str, paste: bool) -> dict[str, str]:
    """Open the consent page, then catch the redirect on 127.0.0.1 (or read the pasted URL)."""
    require_human("connecting an account")
    log(f"\nOpen this URL and approve access:\n\n  {auth_url}\n")
    parsed = urllib.parse.urlsplit(redirect_uri)
    loopback = parsed.hostname in ("127.0.0.1", "localhost") and parsed.scheme == "http" and not paste
    if not loopback:
        url = input("After approving, paste the full URL your browser landed on:\n> ").strip()
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
    else:
        result: dict[str, str] = {}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.path).query))
                if "code" in q or "error" in q:
                    result.update(q)
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"social-studio: done, you can close this tab.")

            def log_message(self, *a):
                pass

        server = HTTPServer((parsed.hostname, parsed.port or 80), Handler)
        threading.Thread(target=lambda: webbrowser.open(auth_url), daemon=True).start()
        log(f"waiting for the redirect on {redirect_uri} ...")
        while "code" not in result and "error" not in result:
            server.handle_request()
        server.server_close()
        q = result
    if q.get("error"):
        raise DataError(f"authorization refused: {q.get('error_description') or q['error']}")
    if q.get("state") != state:
        raise DataError("OAuth state mismatch; start again")
    return q


def ask(prompt: str, secret: bool = False) -> str:
    require_human("connecting an account")
    val = getpass.getpass(f"{prompt}: ") if secret else input(f"{prompt}: ")
    if not val.strip():
        raise ConfigError(f"{prompt} is required")
    return val.strip()


def need(ctx: Ctx, *keys: str) -> list[str]:
    missing = [k for k in keys if not ctx.env(k)]
    if missing:
        raise ConfigError(f"missing in .env: {', '.join(missing)}", "run `social-studio channel connect <platform>`")
    return [ctx.env(k) for k in keys]


# --- captions -----------------------------------------------------------------------------------------

LINK_PLATFORMS = ("x", "linkedin", "facebook", "bluesky", "youtube")


def caption_for(platform: str, video: dict, preset_publish: dict) -> str:
    meta = json.loads(video["meta"]).get("video", {})
    caps = meta.get("captions") or {}
    text = caps.get(platform) or caps.get("default") or video["description"] or video["title"]
    tags = " ".join(h if h.startswith("#") else f"#{h}" for h in meta.get("hashtags", []))
    link = preset_publish.get("link")
    if link and platform in preset_publish.get("link_platforms", LINK_PLATFORMS):
        sep = "&" if "?" in link else "?"
        text += "\n\n" + link + sep + urllib.parse.urlencode({
            "utm_source": platform, "utm_medium": "organic", "utm_campaign": video["pillar"] or "social",
            "utm_content": video["slug"]})
    elif link and preset_publish.get("bio_note"):
        text += "\n\n" + preset_publish["bio_note"]
    return (text + ("\n\n" + tags if tags else "")).strip()


# --- adapters -----------------------------------------------------------------------------------------

class Adapter:
    name = ""
    kind = "api"
    keys: tuple[str, ...] = ()

    def connect(self, ctx: Ctx, paste: bool = False) -> dict[str, str]:
        raise NotImplementedError

    def whoami(self, ctx: Ctx) -> str:
        raise NotImplementedError

    def publish(self, ctx: Ctx, video: dict, caption: str, post_id: int) -> tuple[str, str]:
        """Upload and publish. Returns (platform_post_id, url)."""
        raise NotImplementedError

    def connected(self, ctx: Ctx) -> bool:
        return all(ctx.env(k) for k in self.keys)

    def save(self, ctx: Ctx, values: dict[str, str]) -> None:
        save_env(ctx.env_path, values)


class Draft(Adapter):
    """Export a ready-to-post folder (video, poster, caption) for posting by hand."""
    kind = "draft"

    def __init__(self, name: str, why: str):
        self.name, self.why = name, why

    def connect(self, ctx, paste=False):
        log(f"{self.name}: no API connection ({self.why}). Posts are exported to {ctx.drafts_dir / self.name}.")
        return {}

    def connected(self, ctx):
        return True

    def whoami(self, ctx):
        return f"drafts folder {ctx.drafts_dir / self.name}"

    def publish(self, ctx, video, caption, post_id):
        dest = ctx.drafts_dir / self.name / f"post-{post_id}-{video['slug']}"
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ctx.abs(video["file"]), dest / "video.mp4")
        poster = ctx.abs(video["dir"]) / "poster.jpg"
        if poster.exists():
            shutil.copy2(poster, dest / "poster.jpg")
        (dest / "caption.txt").write_text(caption + "\n")
        return f"draft:{post_id}", str(dest)


def registry() -> dict[str, Adapter]:
    from .bluesky import Bluesky
    from .buffer import BufferAdapter
    from .media import MediaAdapter
    from .meta import Facebook, Instagram
    from .x import X
    from .youtube import YouTube
    return {a.name: a for a in (
        BufferAdapter(), MediaAdapter(),
        Instagram(), Facebook(), YouTube(), X(), Bluesky(),
        Draft("linkedin", "LinkedIn API Terms 3.1 forbid automated posting"),
        Draft("tiktok", "TikTok's audit rejects in-house upload tools; unaudited apps post private only"),
    )}


def get(name: str) -> Adapter:
    reg = registry()
    if name not in reg:
        raise ConfigError(f"unknown platform {name!r}", f"use one of: {', '.join(reg)}")
    return reg[name]


def interactive() -> bool:
    return sys.stdin.isatty()
