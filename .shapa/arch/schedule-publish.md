---
id: schedule-publish
type: reference
created: "2026-10-06T23:59:00Z"
consequence: 7
locus: output
summary: Box schedule-publish - Buffer posts the operator picks at a terminal (upload, createPost, sync); the older direct route of slots, fill and post run.
scope: repo
status: active
---

# Box: schedule-publish

Part of [[index]]. Two routes. Buffer is the one in use (rule R14): the operator picks the post, the channels and the time, code sends it, and Buffer publishes. The direct route is older and has no live accounts: people or agents set calendar slots, code fills them, and the timer posts through the platform adapters (rule R3).

| Field | Value |
|---|---|
| Purpose | Turn approved posts (video plus its signed text) into posts on Instagram, Facebook and X, once, and record what happened |
| Owned paths | `src/social_studio/posting.py` (Buffer route), `platforms/buffer.py` (GraphQL client), `platforms/media.py` (S3-compatible public hosting, SigV4); `schedule.py`, `publish.py`, `platforms/` (`__init__.py` HTTP, OAuth, captions; `meta.py`, `youtube.py`, `x.py`, `bluesky.py`); `<project>/drafts/` |
| In | `post` / `post schedule ID --at ... -c ...` at a terminal; `post sync`; `post run` from the systemd user timer; `schedule add ...` (direct route); `channel connect buffer|media`; approved videos from [[library]]; `publish.*` config and preset keys |
| Out | `posts` and `post_targets` rows (`via` buffer or direct, Buffer channel id, the text sent, post URL); the video in the public bucket at `<public_url>/<prefix><sha256>.mp4` |

## Buffer route

1. `post` (human-only) lists approved videos not on a live post, then Buffer's connected Instagram, Facebook and X channels, then asks for a time (`YYYY-MM-DD HH:MM` local, at least 2 minutes out, or `now`) and a yes.
2. The plan re-checks everything before anything leaves: the status is approved (or failed, to try again); the approval signature verifies; the file re-hashes; the post-text hash matches the signed one; each text fits the network limit (Instagram 2,196, Facebook 5,000, X 280, X links count 23; `publish.buffer.limits.x` for Premium).
3. `media.ensure_hosted` HEADs the public URL and, if it is missing, PUTs the file with SigV4, signing the video's own sha256 as the payload hash, then HEADs again. Buffer has no upload endpoint and fetches the URL when the post goes out, so the URL must stay public and stable.
4. Under `post.lock`: one `posts` row and one `post_targets` row per channel (`via buffer`), video `scheduled`; then `createPost` per channel (Instagram `reel`, shared to feed, cover frame from `poster_at`; Facebook `reel` when vertical and 90 s or less, else `post`; X plain). An id is stored per target; a refusal fails that target. When no channel accepted it, the post is cancelled and the video goes back to approved.
5. `post sync` (also the tail of every `post run`) asks Buffer only about targets that are due: `sent` records the URL, `error` records Buffer's message, a missing post means it was deleted in Buffer; then the post settles to posted, partial or failed.
6. `post cancel ID` deletes the Buffer posts still queued and returns the video to approved; `post list` shows posts, titles and URLs (human-only).

## Direct route (no live accounts)

| Platform | Adapter | Upload |
|---|---|---|
| instagram, facebook | `meta.py` | Meta resumable upload (rupload) |
| youtube | `youtube.py` | resumable; private until the API audit passes |
| x | `x.py` | v2 chunked media upload, 4 MB chunks |
| bluesky | `bluesky.py` | blob |
| linkedin, tiktok | `Draft` | a folder under `drafts/` to post by hand |

`schedule add` parses local time, rejects past and clashing slots, claims under `BEGIN IMMEDIATE`, then fills with the oldest approved video whose signature verifies and file re-hashes. `post run` holds `post.lock`, fills, sweeps past-due open slots to `missed`, then per due `via direct` target: skip if `platform_post_id` is set, re-verify, call the adapter, record, else back off 5 min, 30 min, 2 h, then fail.

## Invariants

- Nothing an agent can run schedules, cancels or lists Buffer posts; `publish.buffer.*` and `publish.media.*` are human-only config. `post sync` and `post run` only read back.
- Mutations are never retried: createPost has no idempotency key. A network error during createPost fails that target with "check Buffer's queue"; a target left without an id is failed by the next sync with the same note.
- Buffer HTTP reads happen outside database write transactions; one posting process at a time through `post.lock`.
- `posts.video_id UNIQUE`: one live post per video; a failed post releases its video when the operator tries again.
- Agent views never show which video sits in a post.
- Not run against live Buffer yet (job J22, operator task T4); the client follows developers.buffer.com as of 2026-10-06, and SigV4 matches the AWS get-vanilla test vector.

## Rules and open work

- Rules: R14 (operator picks Buffer posts), R4 (signed approval, post text included), R3 (direct route only).
- Ledger: F6 (Buffer: J18-J21 done; live test J22 with operator task T4), F7 (terminal UI), F4 (direct-route live tests J10-J12; duplicate window J13), T1 (approval key), J15 (launchd and schtasks timers).
- Research: [[buffer-api-coverage]], [[social-platform-apis]].
