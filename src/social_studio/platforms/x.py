"""X: OAuth 2.0 with PKCE (rotating refresh tokens), chunked v2 media upload, then a post.

Every post is billed (pay per use): about $0.015, or $0.20 when the text holds a link.
"""
from __future__ import annotations

import base64
import secrets
import time
import urllib.parse
from pathlib import Path

from . import Adapter, authorize, http, multipart, need, pkce
from ..core import DataError

API = "https://api.x.com/2"
SCOPES = "tweet.read tweet.write users.read media.write offline.access"
CHUNK = 4 * 1024 * 1024


class X(Adapter):
    name = "x"
    keys = ("X_CLIENT_ID", "X_REFRESH_TOKEN")

    def _redirect(self, ctx) -> str:
        return ctx.env("X_REDIRECT_URI") or "http://127.0.0.1:8725/callback"

    def _token_headers(self, ctx) -> dict:
        secret = ctx.env("X_CLIENT_SECRET")
        if not secret:
            return {}
        basic = base64.b64encode(f"{ctx.env('X_CLIENT_ID')}:{secret}".encode()).decode()
        return {"Authorization": f"Basic {basic}"}

    def connect(self, ctx, paste=False):
        (cid,) = need(ctx, "X_CLIENT_ID")
        verifier, challenge = pkce()
        state = secrets.token_urlsafe(16)
        redirect = self._redirect(ctx)
        url = "https://x.com/i/oauth2/authorize?" + urllib.parse.urlencode({
            "response_type": "code", "client_id": cid, "redirect_uri": redirect, "scope": SCOPES,
            "state": state, "code_challenge": challenge, "code_challenge_method": "S256"})
        q = authorize(url, redirect, state, paste)
        _, _, tok = http("POST", f"{API}/oauth2/token", headers=self._token_headers(ctx), form={
            "grant_type": "authorization_code", "code": q["code"], "redirect_uri": redirect,
            "code_verifier": verifier, "client_id": cid})
        values = {"X_REFRESH_TOKEN": tok["refresh_token"]}
        self.save(ctx, values)
        return values

    def _access(self, ctx) -> str:
        cid, refresh = need(ctx, *self.keys)
        _, _, tok = http("POST", f"{API}/oauth2/token", headers=self._token_headers(ctx), form={
            "grant_type": "refresh_token", "refresh_token": refresh, "client_id": cid})
        if tok.get("refresh_token"):  # X rotates refresh tokens on every use
            self.save(ctx, {"X_REFRESH_TOKEN": tok["refresh_token"]})
        return tok["access_token"]

    def whoami(self, ctx):
        _, _, me = http("GET", f"{API}/users/me", headers={"Authorization": f"Bearer {self._access(ctx)}"})
        return "@" + me["data"]["username"]

    def publish(self, ctx, video, caption, post_id):
        auth = {"Authorization": f"Bearer {self._access(ctx)}"}
        data = ctx.abs(video["file"]).read_bytes()
        _, _, init = http("POST", f"{API}/media/upload/initialize", headers=auth, json_body={
            "media_type": "video/mp4", "total_bytes": len(data), "media_category": "tweet_video"})
        mid = init["data"]["id"]
        for i in range(0, len(data), CHUNK):
            body, ctype = multipart({"segment_index": str(i // CHUNK)}, {"media": ("chunk", data[i:i + CHUNK], "video/mp4")})
            http("POST", f"{API}/media/upload/{mid}/append", headers={**auth, "Content-Type": ctype}, data=body, timeout=600)
        _, _, fin = http("POST", f"{API}/media/upload/{mid}/finalize", headers=auth)
        info = fin.get("data", {}).get("processing_info")
        while info and info.get("state") in ("pending", "in_progress"):
            time.sleep(max(1, int(info.get("check_after_secs", 5))))
            _, _, st = http("GET", f"{API}/media/upload", headers=auth, params={"command": "STATUS", "media_id": mid})
            info = st.get("data", {}).get("processing_info")
        if info and info.get("state") == "failed":
            raise DataError(f"X rejected the video: {info.get('error')}")
        _, _, res = http("POST", f"{API}/tweets", headers=auth,
                         json_body={"text": caption[:280], "media": {"media_ids": [mid]}})
        tid = res["data"]["id"]
        return tid, f"https://x.com/i/web/status/{tid}"
