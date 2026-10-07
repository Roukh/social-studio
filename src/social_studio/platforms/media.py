"""Public hosting for approved videos. Buffer has no upload endpoint: it fetches the video from a URL when
the post goes out, so the file must sit at a stable public HTTPS address until then (no signed links).

Any S3-compatible bucket with public read works: Cloudflare R2 (r2.dev or a custom domain), AWS S3,
Backblaze B2, MinIO. The object key is the file's sha256, so an upload is idempotent and a changed file
never hides behind an old URL. Requests are signed with AWS Signature V4, and the video's own sha256 is
the signed payload hash, so the storage refuses any body that is not the approved file.
"""
from __future__ import annotations

import hashlib
import hmac
import time
from datetime import datetime, timezone
from urllib.parse import quote, urlsplit

from ..core import ConfigError, Ctx, Unavailable, dset
from . import Adapter, HttpError, ask, http, need

KEYS = ("MEDIA_ACCESS_KEY_ID", "MEDIA_SECRET_ACCESS_KEY")
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
    s = {k: (ctx.cfg(f"publish.media.{k}") or "").strip() for k in ("endpoint", "bucket", "region", "public_url", "prefix")}
    missing = [k for k in ("endpoint", "bucket", "public_url") if not s[k]]
    if missing:
        raise ConfigError(f"media hosting is not set up (publish.media.{', '.join(missing)})",
                          "run `social-studio channel connect media` yourself")
    for k in ("endpoint", "public_url"):
        if not s[k].startswith("https://"):
            raise ConfigError(f"publish.media.{k} must be an https:// URL")
    s["region"] = s["region"] or "auto"
    return s


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
    url = f"{s['endpoint'].rstrip('/')}/{quote(s['bucket'])}/{quote(key)}"
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
    """`channel connect media`: the bucket Buffer fetches videos from."""
    name = "media"
    kind = "storage"
    keys = KEYS

    def connect(self, ctx, paste=False):
        print("An S3-compatible bucket with public read (Cloudflare R2, AWS S3, Backblaze B2, MinIO).")
        values = {
            "endpoint": ask("S3 API endpoint (R2: https://<account id>.r2.cloudflarestorage.com)"),
            "bucket": ask("bucket name"),
            "region": input("region [auto]: ").strip() or "auto",
            "public_url": ask("public base URL the bucket serves at (R2: https://pub-....r2.dev or your domain)"),
            "prefix": input("key prefix [social-studio/]: ").strip() or "social-studio/",
        }
        for k, v in values.items():
            dset(ctx.config, f"publish.media.{k}", v)
        ctx.save_config()
        self.save(ctx, {KEYS[0]: ask("access key id"), KEYS[1]: ask("secret access key", secret=True)})
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

    def publish(self, ctx, video, caption, post_id):
        raise ConfigError("media hosting is used by `social-studio post`, not by the timer")
