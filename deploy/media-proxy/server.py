"""social-studio media proxy: serves approved videos from a private Railway bucket at a public URL.

Railway buckets are private (public buckets are not supported) and Buffer needs a direct, stable,
public URL it can fetch when the post goes out, so this service streams GET and HEAD for the video keys
only: `<PREFIX><sha256>.mp4`, plus the `<PREFIX>probe.txt` that `channel test media` writes. Nothing
else is served: no listing, no writes, no other keys. Every bucket request is signed with AWS
Signature V4. Standard library only.

Variables (Railway references to the bucket): ENDPOINT, BUCKET, ACCESS_KEY_ID, SECRET_ACCESS_KEY, REGION.
Optional: PREFIX (default social-studio/), ADDRESSING (virtual, the Railway default, or path), PORT.
Without the bucket variables it still starts: /healthz answers "unconfigured" and videos answer 503.
"""
from __future__ import annotations

import hashlib
import hmac
import http.client
import os
import re
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote, unquote, urlsplit

EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
PASS_HEADERS = ("content-type", "content-length", "content-range", "accept-ranges", "etag", "last-modified")


def key_pattern(prefix: str) -> re.Pattern:
    return re.compile(rf"^{re.escape(prefix)}(?:[0-9a-f]{{64}}\.mp4|probe\.txt)$")


def _hmac(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def sign(method: str, url: str, headers: dict, payload_hash: str, *, access: str, secret: str, region: str,
         service: str = "s3", amz_date: str | None = None) -> dict:
    """AWS Signature V4, header form (the same algorithm as social_studio.platforms.media.sign)."""
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


def object_url(env: dict, key: str) -> str:
    endpoint = urlsplit(env["ENDPOINT"])
    if env.get("ADDRESSING", "virtual") == "path":
        return f"{endpoint.scheme}://{endpoint.netloc}/{quote(env['BUCKET'])}/{quote(key)}"
    return f"{endpoint.scheme}://{env['BUCKET']}.{endpoint.netloc}/{quote(key)}"


def fetch(env: dict, method: str, key: str, byte_range: str | None):
    """Open a signed request to the bucket; returns (connection, response)."""
    url = object_url(env, key)
    headers = {"x-amz-content-sha256": EMPTY_SHA256, **({"range": byte_range} if byte_range else {})}
    signed = sign(method, url, headers, EMPTY_SHA256, access=env["ACCESS_KEY_ID"], secret=env["SECRET_ACCESS_KEY"],
                  region=env.get("REGION") or "auto")
    parts = urlsplit(url)
    conn = http.client.HTTPSConnection(parts.netloc, timeout=60)
    conn.request(method, parts.path, headers=signed)
    return conn, conn.getresponse()


REQUIRED = ("ENDPOINT", "BUCKET", "ACCESS_KEY_ID", "SECRET_ACCESS_KEY")


class Handler(BaseHTTPRequestHandler):
    env: dict = {}
    keys: re.Pattern = key_pattern("social-studio/")
    upstream = staticmethod(fetch)
    ready = True  # False until the bucket variables are set: health says so, videos answer 503

    def do_GET(self):  # noqa: N802
        self._serve(body=True)

    def do_HEAD(self):  # noqa: N802
        self._serve(body=False)

    def _plain(self, status: int, text: str, body: bool) -> None:
        data = text.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if body:
            self.wfile.write(data)

    def _serve(self, body: bool) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/healthz":
            return self._plain(200, "ok\n" if self.ready else "unconfigured\n", body)
        key = unquote(path.lstrip("/"))
        if not self.keys.match(key):
            return self._plain(404, "not found\n", body)
        if not self.ready:
            return self._plain(503, "bucket variables are not set\n", body)
        conn, resp = self.upstream(self.env, "GET" if body else "HEAD", key, self.headers.get("Range"))
        try:
            if resp.status not in (200, 206):
                return self._plain(404 if resp.status in (403, 404) else 502,
                                   "not found\n" if resp.status in (403, 404) else "bucket error\n", body)
            self.send_response(resp.status)
            for name in PASS_HEADERS:
                value = resp.getheader(name)
                if value:
                    self.send_header(name, value)
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
            self.end_headers()
            while body and (chunk := resp.read(1 << 16)):
                self.wfile.write(chunk)
        finally:
            conn.close()

    def log_message(self, fmt, *args):  # one short line per request, never headers
        print(f"{self.command} {self.path.split('?', 1)[0]} {args[1] if len(args) > 1 else ''}", flush=True)


def main() -> None:
    missing = [k for k in REQUIRED if not os.environ.get(k)]
    Handler.env = dict(os.environ)
    Handler.keys = key_pattern(os.environ.get("PREFIX", "social-studio/"))
    Handler.ready = not missing
    server = ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), Handler)
    state = f"bucket {os.environ['BUCKET']}" if not missing else f"unconfigured, missing {', '.join(missing)}"
    print(f"media proxy on :{server.server_port}, {state}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
