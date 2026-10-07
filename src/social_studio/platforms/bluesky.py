"""Bluesky via an app password: createSession, uploadBlob (mp4 up to 300 MB), createRecord."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from . import Adapter, ask, http, need


class Bluesky(Adapter):
    name = "bluesky"
    keys = ("BLUESKY_HANDLE", "BLUESKY_APP_PASSWORD")

    def _pds(self, ctx) -> str:
        return (ctx.env("BLUESKY_PDS") or "https://bsky.social").rstrip("/")

    def _session(self, ctx) -> dict:
        handle, password = need(ctx, *self.keys)
        _, _, s = http("POST", f"{self._pds(ctx)}/xrpc/com.atproto.server.createSession",
                       json_body={"identifier": handle, "password": password})
        return s

    def connect(self, ctx, paste=False):
        handle = ask("Bluesky handle (e.g. name.bsky.social)")
        password = ask("App password (Settings > Privacy and security > App passwords)", secret=True)
        values = {"BLUESKY_HANDLE": handle, "BLUESKY_APP_PASSWORD": password}
        self.save(ctx, values)
        self.whoami(ctx)
        return values

    def whoami(self, ctx):
        s = self._session(ctx)
        return f"{s['handle']} ({s['did']})"

    def publish(self, ctx, video, caption, post_id):
        s = self._session(ctx)
        auth = {"Authorization": f"Bearer {s['accessJwt']}"}
        blob = ctx.abs(video["file"]).read_bytes()
        _, _, up = http("POST", f"{self._pds(ctx)}/xrpc/com.atproto.repo.uploadBlob",
                        headers={**auth, "Content-Type": "video/mp4"}, data=blob, timeout=600)
        alt = json.loads(video["meta"]).get("video", {}).get("alt_text", video["title"])
        record = {
            "$type": "app.bsky.feed.post",
            "text": caption[:300],
            "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "embed": {"$type": "app.bsky.embed.video", "video": up["blob"], "alt": alt[:1000],
                      "aspectRatio": {"width": video["width"], "height": video["height"]}},
        }
        _, _, res = http("POST", f"{self._pds(ctx)}/xrpc/com.atproto.repo.createRecord", headers=auth,
                         json_body={"repo": s["did"], "collection": "app.bsky.feed.post", "record": record})
        rkey = res["uri"].rsplit("/", 1)[-1]
        return res["uri"], f"https://bsky.app/profile/{s['handle']}/post/{rkey}"
