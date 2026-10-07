"""The accounts social-studio talks to, plus the small HTTP and caption helpers they share (stdlib only).

Buffer (buffer.py) is the only posting route, for Instagram, Facebook and X; media.py hosts the video
Buffer fetches. Their keys live in the project .env, written by `channel connect buffer|media`.
"""
from __future__ import annotations

import getpass
import json
import urllib.error
import urllib.parse
import urllib.request

from ..core import ConfigError, Ctx, Unavailable, require_human, save_env


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


def ask(prompt: str, secret: bool = False) -> str:
    require_human("connecting an account")
    val = getpass.getpass(f"{prompt}: ") if secret else input(f"{prompt}: ")
    if not val.strip():
        raise ConfigError(f"{prompt} is required")
    return val.strip()


def need(ctx: Ctx, *keys: str) -> list[str]:
    missing = [k for k in keys if not ctx.env(k)]
    if missing:
        raise ConfigError(f"missing in .env: {', '.join(missing)}", "run `social-studio channel connect <name>`")
    return [ctx.env(k) for k in keys]


# --- captions -----------------------------------------------------------------------------------------

LINK_PLATFORMS = ("x", "facebook")  # Instagram captions do not make links clickable


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


# --- accounts -----------------------------------------------------------------------------------------

class Adapter:
    """An account `channel connect|test|disconnect` manages: its .env keys, a connect flow, a live check."""
    name = ""
    keys: tuple[str, ...] = ()

    def connect(self, ctx: Ctx) -> dict[str, str]:
        raise NotImplementedError

    def whoami(self, ctx: Ctx) -> str:
        raise NotImplementedError

    def connected(self, ctx: Ctx) -> bool:
        return all(ctx.env(k) for k in self.keys)

    def save(self, ctx: Ctx, values: dict[str, str]) -> None:
        save_env(ctx.env_path, values)


def registry() -> dict[str, Adapter]:
    from .buffer import BufferAdapter
    from .media import MediaAdapter
    return {a.name: a for a in (BufferAdapter(), MediaAdapter())}


def get(name: str) -> Adapter:
    reg = registry()
    if name not in reg:
        raise ConfigError(f"unknown account {name!r}", f"use one of: {', '.join(reg)}")
    return reg[name]
