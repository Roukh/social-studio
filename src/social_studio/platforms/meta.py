"""Instagram (API with Facebook Login) and Facebook Page Reels, both via local resumable upload.

One connect covers both: Facebook Login gives a long-lived user token, which yields a Page token
(no expiry when derived this way) and the Page's linked Instagram professional account.
"""
from __future__ import annotations

import json
import secrets
import time
import urllib.parse
from pathlib import Path

from . import Adapter, authorize, http, need
from ..core import ConfigError, DataError, log

SCOPES = ("pages_show_list,pages_read_engagement,pages_manage_posts,business_management,"
          "instagram_basic,instagram_content_publish")


def graph(ctx) -> str:
    return f"https://graph.facebook.com/{ctx.env('META_GRAPH_VERSION') or 'v24.0'}"


def connect_meta(ctx, paste: bool) -> dict[str, str]:
    app_id, app_secret = need(ctx, "META_APP_ID", "META_APP_SECRET")
    redirect = ctx.cfg("publish.meta.redirect_uri", "http://localhost:8724/callback")
    state = secrets.token_urlsafe(16)
    version = ctx.env("META_GRAPH_VERSION") or "v24.0"
    url = f"https://www.facebook.com/{version}/dialog/oauth?" + urllib.parse.urlencode(
        {"client_id": app_id, "redirect_uri": redirect, "state": state, "scope": SCOPES, "response_type": "code"})
    q = authorize(url, redirect, state, paste)
    _, _, short = http("GET", f"{graph(ctx)}/oauth/access_token",
                       params={"client_id": app_id, "client_secret": app_secret, "redirect_uri": redirect, "code": q["code"]})
    _, _, long = http("GET", f"{graph(ctx)}/oauth/access_token",
                      params={"grant_type": "fb_exchange_token", "client_id": app_id, "client_secret": app_secret,
                              "fb_exchange_token": short["access_token"]})
    _, _, pages = http("GET", f"{graph(ctx)}/me/accounts",
                       params={"fields": "id,name,access_token,instagram_business_account",
                               "access_token": long["access_token"]})
    data = pages.get("data", [])
    if not data:
        raise ConfigError("this login manages no Facebook Page", "Instagram publishing needs a Page linked to it")
    for i, page in enumerate(data):
        log(f"  [{i}] {page['name']} (page {page['id']}, instagram {page.get('instagram_business_account', {}).get('id', '-')})")
    choice = int(input("Page number: ").strip() or "0") if len(data) > 1 else 0
    page = data[choice]
    values = {"META_PAGE_ID": page["id"], "META_PAGE_TOKEN": page["access_token"],
              "META_IG_USER_ID": page.get("instagram_business_account", {}).get("id", "")}
    return values


def rupload(ctx, upload_url: str, token: str, path: Path) -> None:
    data = path.read_bytes()
    http("POST", upload_url, headers={"Authorization": f"OAuth {token}", "offset": "0", "file_size": str(len(data))},
         data=data, timeout=1800)


class Instagram(Adapter):
    name = "instagram"
    keys = ("META_PAGE_TOKEN", "META_IG_USER_ID")

    def connect(self, ctx, paste=False):
        values = connect_meta(ctx, paste)
        if not values["META_IG_USER_ID"]:
            raise ConfigError("that Page has no linked Instagram professional account")
        self.save(ctx, values)
        return values

    def whoami(self, ctx):
        token, ig = need(ctx, *self.keys)
        _, _, me = http("GET", f"{graph(ctx)}/{ig}", params={"fields": "username", "access_token": token})
        return "@" + me.get("username", ig)

    def publish(self, ctx, video, caption, post_id):
        token, ig = need(ctx, *self.keys)
        _, _, c = http("POST", f"{graph(ctx)}/{ig}/media", params={
            "media_type": "REELS", "upload_type": "resumable", "caption": caption[:2200],
            "share_to_feed": "true", "access_token": token})
        rupload(ctx, c["uri"], token, ctx.abs(video["file"]))
        for _ in range(120):
            _, _, st = http("GET", f"{graph(ctx)}/{c['id']}", params={"fields": "status_code,status", "access_token": token})
            if st.get("status_code") == "FINISHED":
                break
            if st.get("status_code") in ("ERROR", "EXPIRED"):
                raise DataError(f"Instagram rejected the upload: {st.get('status')}")
            time.sleep(5)
        else:
            raise DataError("Instagram processing timed out")
        _, _, pub = http("POST", f"{graph(ctx)}/{ig}/media_publish", params={"creation_id": c["id"], "access_token": token})
        _, _, link = http("GET", f"{graph(ctx)}/{pub['id']}", params={"fields": "permalink", "access_token": token})
        return pub["id"], link.get("permalink", "")


class Facebook(Adapter):
    name = "facebook"
    keys = ("META_PAGE_TOKEN", "META_PAGE_ID")

    def connect(self, ctx, paste=False):
        values = connect_meta(ctx, paste)
        self.save(ctx, values)
        return values

    def whoami(self, ctx):
        token, page = need(ctx, *self.keys)
        _, _, me = http("GET", f"{graph(ctx)}/{page}", params={"fields": "name", "access_token": token})
        return me.get("name", page)

    def publish(self, ctx, video, caption, post_id):
        token, page = need(ctx, *self.keys)
        _, _, start = http("POST", f"{graph(ctx)}/{page}/video_reels",
                           params={"upload_phase": "start", "access_token": token})
        rupload(ctx, start["upload_url"], token, ctx.abs(video["file"]))
        meta = json.loads(video["meta"]).get("video", {})
        http("POST", f"{graph(ctx)}/{page}/video_reels", params={
            "upload_phase": "finish", "video_id": start["video_id"], "video_state": "PUBLISHED",
            "description": caption, "title": meta.get("title", video["title"]), "access_token": token})
        return start["video_id"], f"https://www.facebook.com/reel/{start['video_id']}"
