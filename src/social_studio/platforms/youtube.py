"""YouTube Shorts: OAuth installed-app flow with a 127.0.0.1 redirect, resumable upload.

Projects created after 2020-07-28 upload as private until YouTube's compliance audit passes,
whatever privacyStatus says. Use your own "Desktop app" OAuth client from Google Cloud.
"""
from __future__ import annotations

import json
import secrets
import urllib.parse
from pathlib import Path

from . import Adapter, authorize, http, need, pkce
from ..core import DataError

AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly"


class YouTube(Adapter):
    name = "youtube"
    keys = ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")

    def connect(self, ctx, paste=False):
        cid, secret = need(ctx, "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET")
        port = int(ctx.cfg("publish.youtube.port", 8723))
        redirect = f"http://127.0.0.1:{port}/callback"
        verifier, challenge = pkce()
        state = secrets.token_urlsafe(16)
        url = AUTH + "?" + urllib.parse.urlencode({
            "client_id": cid, "redirect_uri": redirect, "response_type": "code", "scope": SCOPE,
            "access_type": "offline", "prompt": "consent", "state": state,
            "code_challenge": challenge, "code_challenge_method": "S256"})
        q = authorize(url, redirect, state, paste)
        _, _, tok = http("POST", TOKEN, form={"code": q["code"], "client_id": cid, "client_secret": secret,
                                              "redirect_uri": redirect, "grant_type": "authorization_code",
                                              "code_verifier": verifier})
        if not tok.get("refresh_token"):
            raise DataError("Google returned no refresh token",
                            "remove the app's access in your Google account, then connect again")
        values = {"YOUTUBE_REFRESH_TOKEN": tok["refresh_token"]}
        self.save(ctx, values)
        return values

    def _access(self, ctx) -> str:
        cid, secret, refresh = need(ctx, *self.keys)
        _, _, tok = http("POST", TOKEN, form={"client_id": cid, "client_secret": secret,
                                              "refresh_token": refresh, "grant_type": "refresh_token"})
        return tok["access_token"]

    def whoami(self, ctx):
        _, _, res = http("GET", "https://www.googleapis.com/youtube/v3/channels",
                         params={"part": "snippet", "mine": "true"},
                         headers={"Authorization": f"Bearer {self._access(ctx)}"})
        items = res.get("items", [])
        return items[0]["snippet"]["title"] if items else "no channel on this account"

    def publish(self, ctx, video, caption, post_id):
        token = self._access(ctx)
        meta = json.loads(video["meta"]).get("video", {})
        status = {"privacyStatus": ctx.cfg("publish.youtube.privacy", "private"),
                  "selfDeclaredMadeForKids": False}
        if ctx.cfg("publish.youtube.synthetic_media") is not None:
            status["containsSyntheticMedia"] = bool(ctx.cfg("publish.youtube.synthetic_media"))
        body = {"snippet": {"title": video["title"][:100], "description": caption[:5000],
                            "tags": [h.lstrip("#") for h in meta.get("hashtags", [])][:15],
                            "categoryId": str(ctx.cfg("publish.youtube.category", "22"))},
                "status": status}
        data = ctx.abs(video["file"]).read_bytes()
        _, headers, _ = http("POST", "https://www.googleapis.com/upload/youtube/v3/videos",
                             params={"uploadType": "resumable", "part": "snippet,status"},
                             headers={"Authorization": f"Bearer {token}", "X-Upload-Content-Type": "video/mp4",
                                      "X-Upload-Content-Length": str(len(data))}, json_body=body)
        location = headers.get("Location") or headers.get("location")
        _, _, res = http("PUT", location, headers={"Authorization": f"Bearer {token}", "Content-Type": "video/mp4"},
                         data=data, timeout=1800)
        return res["id"], f"https://www.youtube.com/shorts/{res['id']}"
