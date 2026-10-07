"""Buffer's GraphQL API (api.buffer.com): the route approved posts leave by.

A personal API key (BUFFER_API_KEY in the .env) acts for the operator's whole Buffer account. Buffer
publishes at the scheduled time; social-studio only creates, reads and deletes the queued posts.
Mutations are never retried here: createPost has no idempotency key, so a blind retry could double-post.
"""
from __future__ import annotations

import json
import re
import time

from ..core import ConfigError, Ctx, DataError, Unavailable, dset
from . import Adapter, HttpError, ask, http

API = "https://api.buffer.com"
KEY = "BUFFER_API_KEY"
# Buffer service -> the caption key the maker writes in video.json (and the platform name in post_targets).
SERVICES = {"instagram": "instagram", "facebook": "facebook", "twitter": "x"}
# Post text limits Buffer enforces, in UTF-16 units (developers.buffer.com/guides/character-limits).
# X on a free account is 280; set publish.buffer.limits.x for Premium.
LIMITS = {"instagram": 2196, "facebook": 5000, "x": 280}
X_URL_WEIGHT = 23

Q_ORGS = "query { account { organizations { id name } } }"
Q_CHANNELS = """query Channels($input: ChannelsInput!) {
  channels(input: $input) { id name displayName service isDisconnected isLocked isQueuePaused timezone } }"""
Q_POST = """query Post($input: PostInput!) {
  post(input: $input) { id status dueAt sentAt externalLink error { message } } }"""
M_CREATE = """mutation Create($input: CreatePostInput!) {
  createPost(input: $input) {
    __typename
    ... on PostActionSuccess { post { id status dueAt } }
    ... on MutationError { message } } }"""
M_DELETE = """mutation Delete($input: DeletePostInput!) {
  deletePost(input: $input) { __typename ... on DeletePostSuccess { id } ... on MutationError { message } } }"""


class BufferError(Unavailable):
    def __init__(self, message: str, code: str = ""):
        super().__init__(f"Buffer: {message}" + (f" ({code})" if code else ""),
                         "run `social-studio channel test buffer`" if code in ("UNAUTHORIZED", "FORBIDDEN") else "")
        self.buffer_code = code


def gql(ctx: Ctx, query: str, variables: dict | None = None, *, mutation: bool = False) -> dict:
    """One GraphQL call. Errors come back with HTTP 200 in `errors`; a read is retried once on UNEXPECTED."""
    key = ctx.env(KEY)
    if not key:
        raise ConfigError(f"missing {KEY} in .env", "run `social-studio channel connect buffer` yourself")
    for attempt in (0, 1):
        try:
            _, _, body = http("POST", API, headers={"Authorization": f"Bearer {key}"},
                              json_body={"query": query, "variables": variables or {}}, timeout=60)
        except HttpError as e:
            if e.status >= 500 and not mutation and attempt == 0:
                time.sleep(2)
                continue
            raise BufferError(str(e), "UNAUTHORIZED" if e.status == 401 else "") from e
        except OSError as e:  # DNS, refused, timeout: a write may still have landed, so it is never repeated
            if not mutation and attempt == 0:
                time.sleep(2)
                continue
            raise BufferError(f"network error: {e}" + ("; the request may have reached Buffer, so check its "
                                                       "queue before trying again" if mutation else "")) from e
        if not isinstance(body, dict):
            raise BufferError(f"unexpected response: {str(body)[:200]}")
        if body.get("errors"):
            err = body["errors"][0]
            code = (err.get("extensions") or {}).get("code", "")
            if code == "UNEXPECTED" and not mutation and attempt == 0:
                time.sleep(2)
                continue
            raise BufferError(err.get("message", "error"), code)
        return body.get("data") or {}
    raise BufferError("no answer after a retry", "UNEXPECTED")


def _mutation_result(payload: dict, field: str) -> dict:
    """A mutation returns its success type or a MutationError carrying `message`."""
    if payload.get("message") is not None or field not in payload:
        raise DataError(f"Buffer refused: {payload.get('message') or payload.get('__typename')}")
    return payload[field]


def organizations(ctx: Ctx) -> list[dict]:
    return gql(ctx, Q_ORGS)["account"]["organizations"]


def organization(ctx: Ctx) -> str:
    """The configured organization, or the account's only one."""
    org = ctx.cfg("publish.buffer.organization")
    if org:
        return org
    orgs = organizations(ctx)
    if len(orgs) == 1:
        return orgs[0]["id"]
    raise ConfigError(f"the Buffer account has {len(orgs)} organizations",
                      "run `social-studio channel connect buffer` to pick one")


def channels(ctx: Ctx, supported_only: bool = True) -> list[dict]:
    """Connected, unlocked channels, sorted by service then name; `platform` is the caption key."""
    out = []
    for c in gql(ctx, Q_CHANNELS, {"input": {"organizationId": organization(ctx)}})["channels"]:
        if supported_only and (c["service"] not in SERVICES or c["isDisconnected"] or c["isLocked"]):
            continue
        out.append({**c, "platform": SERVICES.get(c["service"], c["service"]),
                    "label": f"{SERVICES.get(c['service'], c['service'])} {c.get('displayName') or c['name']}"})
    return sorted(out, key=lambda c: (c["platform"], c["label"]))


def text_length(platform: str, text: str) -> int:
    """Length the way Buffer counts it: UTF-16 units; on X a link counts as 23."""
    if platform == "x":
        text = re.sub(r"https?://\S+", "x" * X_URL_WEIGHT, text)
    return len(text.encode("utf-16-le")) // 2


def limit(ctx: Ctx, platform: str) -> int:
    return int(ctx.cfg(f"publish.buffer.limits.{platform}") or LIMITS[platform])


def post_input(channel: dict, text: str, video_url: str, video: dict, due_at: str | None,
               ai_label: bool = False) -> dict:
    """CreatePostInput for one channel: a video post, Reel-shaped where the network has one."""
    service = channel["service"]
    asset: dict = {"url": video_url}
    meta: dict = {}
    if service == "instagram":
        poster = _poster_ms(video)
        if poster is not None:
            asset["metadata"] = {"thumbnailOffset": poster}
        meta["instagram"] = {"type": "reel", "shouldShareToFeed": True, "isAiGenerated": ai_label}
    elif service == "facebook":
        vertical = video["height"] > video["width"] and video["duration"] <= 90
        meta["facebook"] = {"type": "reel" if vertical else "post"}
    elif service == "twitter" and ai_label:
        meta["twitter"] = {"isAiGenerated": True}
    out = {"channelId": channel["id"], "text": text, "schedulingType": "automatic",
           "assets": [{"video": asset}], "metadata": meta or None}
    if due_at:
        out.update(mode="customScheduled", dueAt=due_at)
    else:
        out["mode"] = "shareNow"
    return {k: v for k, v in out.items() if v is not None}


def _poster_ms(video: dict) -> int | None:
    at = json.loads(video["meta"]).get("video", {}).get("poster_at")
    if isinstance(at, (int, float)) and 0 <= at < video["duration"]:
        return int(at * 1000)
    return None


def create_post(ctx: Ctx, data: dict) -> dict:
    """Returns {id, status, dueAt}. Raises DataError when Buffer refuses the input."""
    res = gql(ctx, M_CREATE, {"input": data}, mutation=True)["createPost"]
    return _mutation_result(res, "post")


def get_post(ctx: Ctx, post_id: str) -> dict | None:
    """The post's state at Buffer, or None when it no longer exists there."""
    try:
        return gql(ctx, Q_POST, {"input": {"id": post_id}})["post"]
    except BufferError as e:
        if e.buffer_code == "NOT_FOUND":
            return None
        raise


def delete_post(ctx: Ctx, post_id: str) -> None:
    res = gql(ctx, M_DELETE, {"input": {"id": post_id}}, mutation=True)["deletePost"]
    _mutation_result(res, "id")


class BufferAdapter(Adapter):
    """`channel connect buffer`: store the personal API key and pick the organization."""
    name = "buffer"
    kind = "scheduler"
    keys = (KEY,)

    def connect(self, ctx, paste=False):
        key = ask("Buffer API key (publish.buffer.com/settings/api)", secret=True)
        self.save(ctx, {KEY: key})
        orgs = organizations(ctx)
        if not orgs:
            raise DataError("this Buffer account has no organization")
        org = orgs[0]
        if len(orgs) > 1:
            for i, o in enumerate(orgs):
                print(f"  [{i}] {o['name']}")
            org = orgs[int(input("organization number: ").strip() or "0")]
        dset(ctx.config, "publish.buffer.organization", org["id"])
        ctx.save_config()
        return {KEY: "(saved)"}

    def whoami(self, ctx):
        found = channels(ctx)
        names = ", ".join(c["label"] for c in found) or "no Instagram, Facebook or X channel connected in Buffer"
        return f"Buffer organization {organization(ctx)}: {names}"

    def publish(self, ctx, video, caption, post_id):
        raise ConfigError("Buffer posts are scheduled with `social-studio post`, not by the timer")
