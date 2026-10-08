"""Public hosting for approved videos. Buffer has no upload endpoint: it fetches the video from a URL when
the post goes out, so the file must sit at a stable public HTTPS address until then (no signed links).

The file goes into an S3-compatible bucket; `publish.media.public_url` is where it can be read without
credentials. In use: a private Railway bucket read through the media proxy in deploy/media-proxy (Railway
buckets cannot be public). A bucket with public read of its own (Cloudflare R2, AWS S3) works the same.
The object key is the file's sha256, so an upload is idempotent and a changed file never hides behind
an old URL. Requests are signed with AWS Signature V4, and the video's own sha256 is the signed payload
hash, so the storage refuses any body that is not the approved file.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from datetime import datetime, timezone
from urllib.parse import quote, urlsplit

from ..core import ConfigError, Ctx, Unavailable, dset, require_human
from . import Adapter, HttpError, ask, http, need

KEYS = ("MEDIA_ACCESS_KEY_ID", "MEDIA_SECRET_ACCESS_KEY")
ENV_SETTINGS = {"endpoint": "MEDIA_ENDPOINT", "bucket": "MEDIA_BUCKET", "region": "MEDIA_REGION",
                "addressing": "MEDIA_ADDRESSING", "public_url": "MEDIA_PUBLIC_URL", "prefix": "MEDIA_PREFIX"}
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


def _hmac(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def sign(method: str, url: str, headers: dict, payload_hash: str, *, access: str, secret: str, region: str,
         service: str = "s3", amz_date: str | None = None) -> dict:
    """AWS Signature V4 (header form). Returns the headers to send, Authorization included."""
    amz_date = amz_date or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    parts = urlsplit(url)
    hdrs = {k.lower(): " ".join(str(v).split()) for k, v in headers.items()}
    hdrs.update({"host": parts.netloc, "x-amz-date": amz_date})
    names = sorted(hdrs)
    query = "&".join(sorted(p for p in parts.query.split("&") if p))
    canonical = "\n".join([method, parts.path or "/", query, "".join(f"{n}:{hdrs[n]}\n" for n in names),
                           ";".join(names), payload_hash])
    scope = f"{amz_date[:8]}/{region}/{service}/aws4_request"
    to_sign = "\n".join(["AWS4-HMAC-SHA256", amz_date, scope, hashlib.sha256(canonical.encode()).hexdigest()])
    key = _hmac(_hmac(_hmac(_hmac(f"AWS4{secret}".encode(), amz_date[:8]), region), service), "aws4_request")
    signature = hmac.new(key, to_sign.encode(), hashlib.sha256).hexdigest()
    out = {k: v for k, v in hdrs.items() if k != "host"}
    out["authorization"] = (f"AWS4-HMAC-SHA256 Credential={access}/{scope}, SignedHeaders={';'.join(names)}, "
                            f"Signature={signature}")
    return out


def settings(ctx: Ctx) -> dict:
    s = {k: (ctx.cfg(f"publish.media.{k}") or "").strip()
         for k in ("endpoint", "bucket", "region", "public_url", "prefix", "addressing")}
    missing = [k for k in ("endpoint", "bucket", "public_url") if not s[k]]
    if missing:
        raise ConfigError(f"media hosting is not set up (publish.media.{', '.join(missing)})",
                          "run `sclstdio channel connect media` yourself")
    for k in ("endpoint", "public_url"):
        if not s[k].startswith("https://"):
            raise ConfigError(f"publish.media.{k} must be an https:// URL")
    s["region"] = s["region"] or "auto"
    s["addressing"] = url_style(s["addressing"])
    return s


def url_style(text: str) -> str:
    """virtual or path; providers spell them differently (Railway says virtual-host, others path-style)."""
    style = (text or "virtual").strip().lower()
    for name in ("virtual", "path"):
        if style.startswith(name):
            return name
    raise ConfigError(f"publish.media.addressing {text!r} must be virtual or path")


def object_url(s: dict, key: str) -> str:
    """Where the S3 API holds `key`: virtual-hosted (bucket.host, the S3 default and Railway's) or path style."""
    endpoint = urlsplit(s["endpoint"].rstrip("/"))
    if s["addressing"] == "path":
        return f"{endpoint.scheme}://{endpoint.netloc}/{quote(s['bucket'])}/{quote(key)}"
    return f"{endpoint.scheme}://{s['bucket']}.{endpoint.netloc}/{quote(key)}"


def object_key(ctx: Ctx, name: str) -> str:
    prefix = ctx.cfg("publish.media.prefix")
    return f"{'social-studio/' if prefix is None else prefix}{name}"


def public_url(ctx: Ctx, video: dict) -> str:
    return f"{settings(ctx)['public_url'].rstrip('/')}/{quote(object_key(ctx, video['sha256'] + '.mp4'))}"


def is_live(url: str, size: int | None = None) -> bool:
    """The URL answers without credentials, with the expected size when the server reports one."""
    try:
        status, headers, _ = http("HEAD", url, timeout=30)
    except (HttpError, OSError):
        return False
    length = {k.lower(): v for k, v in headers.items()}.get("content-length")
    return status == 200 and (size is None or length is None or int(length) == size)


def put(ctx: Ctx, key: str, data: bytes, sha256: str, content_type: str) -> None:
    s = settings(ctx)
    access, secret = need(ctx, *KEYS)
    url = object_url(s, key)
    headers = sign("PUT", url, {"content-type": content_type, "x-amz-content-sha256": sha256,
                                "cache-control": "public, max-age=31536000, immutable"},
                   sha256, access=access, secret=secret, region=s["region"])
    http("PUT", url, headers=headers, data=data, timeout=600)


def ensure_hosted(ctx: Ctx, video: dict) -> str:
    """Upload the approved file once and return its public URL, checked reachable."""
    url = public_url(ctx, video)
    if is_live(url, video["bytes"]):
        return url
    put(ctx, object_key(ctx, video["sha256"] + ".mp4"), ctx.abs(video["file"]).read_bytes(), video["sha256"],
        "video/mp4")
    for _ in range(5):
        if is_live(url, video["bytes"]):
            return url
        time.sleep(1)
    raise Unavailable(f"uploaded, but {url} is not publicly readable",
                      "turn on public access for the bucket (R2: r2.dev or a custom domain) and check publish.media.public_url")


class MediaAdapter(Adapter):
    """`channel connect media`: the bucket the videos go into, and the public URL Buffer reads them from."""
    name = "media"
    keys = KEYS

    def connect(self, ctx, paste=False):
        """Prompts, or takes MEDIA_* from the environment (deploy/media-proxy/setup.sh sets them, so the
        keys never pass through argv or the screen). Either way a human at a terminal runs it."""
        require_human("connecting media hosting")
        given = {k: os.environ.get(v, "").strip() for k, v in ENV_SETTINGS.items()}
        if given["endpoint"] and given["bucket"] and given["public_url"] and all(os.environ.get(k) for k in KEYS):
            print("using the media settings and keys from the environment")
            values = {**given, "region": given["region"] or "auto", "addressing": url_style(given["addressing"]),
                      "prefix": given["prefix"] or "social-studio/"}
            keys = {k: os.environ[k] for k in KEYS}
        else:
            print("An S3-compatible bucket. Railway: `railway bucket credentials` has the endpoint, bucket and\n"
                  "keys; the public URL is the media proxy's domain.")
            values = {
                "endpoint": ask("S3 API endpoint (Railway: https://t3.storageapi.dev)"),
                "bucket": ask("bucket name for the S3 API (Railway: the name with its hash)"),
                "region": input("region [auto]: ").strip() or "auto",
                "addressing": url_style(input("URL style, virtual (Railway, AWS) or path (MinIO) [virtual]: ")),
                "public_url": ask("public base URL the videos are read from (the media proxy's https:// domain)"),
                "prefix": input("key prefix [social-studio/]: ").strip() or "social-studio/",
            }
            keys = {KEYS[0]: ask("access key id"), KEYS[1]: ask("secret access key", secret=True)}
        for k, v in values.items():
            dset(ctx.config, f"publish.media.{k}", v)
        settings(ctx)  # refuse bad values before anything is saved
        ctx.save_config()
        self.save(ctx, keys)
        return {"bucket": values["bucket"]}

    def whoami(self, ctx):
        """Write a small probe object and read it back through the public URL."""
        body = b"social-studio media probe\n"
        key = object_key(ctx, "probe.txt")
        put(ctx, key, body, hashlib.sha256(body).hexdigest(), "text/plain")
        url = f"{settings(ctx)['public_url'].rstrip('/')}/{quote(key)}"
        if not is_live(url, len(body)):
            raise Unavailable(f"upload works but {url} is not publicly readable",
                              "turn on public access for the bucket, or fix publish.media.public_url")
        return f"bucket {settings(ctx)['bucket']}, public at {url.rsplit('/', 1)[0]}/"
