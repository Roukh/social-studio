---
id: schedule-publish
type: reference
created: "2026-10-06T23:59:00Z"
consequence: 7
locus: output
summary: Box schedule-publish - Buffer, the only posting route: the operator picks at a terminal, code uploads and calls createPost, the timer's sync records results.
scope: repo
status: active
---

# Box: schedule-publish

Part of [[index]]. One route, Buffer (rule R14): the operator picks the post, the channels and the time; code sends it; Buffer publishes; the timer records what happened. The older direct route (platform adapters, agent-set calendar slots, `post run`, draft folders) was removed on 2026-10-06.

| Field | Value |
|---|---|
| Purpose | Turn approved posts (video plus its signed text) into posts on Instagram, Facebook and X, once, and record what happened |
| Owned paths | `src/social_studio/posting.py` (pick, plan, execute, sync, cancel, list; time helpers, `post.lock`, settling), `platforms/__init__.py` (HTTP, captions, the account registry), `platforms/buffer.py` (GraphQL client), `platforms/media.py` (bucket upload, public check), `deploy/media-proxy/` (`server.py` proxy, `Dockerfile`, `setup.sh`) |
| In | `post` / `post schedule ID --at ... -c ...` at a terminal; `post sync` from the systemd user timer (`timer install`); `channel connect buffer|media`; approved videos from [[library]]; `publish.*` config and preset keys |
| Out | `posts` and `post_targets` rows (`via buffer`, Buffer channel id, the text sent, post URL); the video at `<public_url>/<prefix><sha256>.mp4` |

## Flow

1. `post` (human-only) lists approved videos not on a live post, then Buffer's connected Instagram, Facebook and X channels, then asks for a time (`YYYY-MM-DD HH:MM` local, at least 2 minutes out, or `now`) and a yes.
2. The plan re-checks everything before anything leaves: the status is approved (or failed, to try again); the approval signature verifies; the file re-hashes; the post-text hash matches the signed one; each text fits the network limit (Instagram 2,196, Facebook 5,000, X 280, X links count 23; `publish.buffer.limits.x` for Premium). After the yes it checks again that nothing changed while the operator was confirming.
3. `media.ensure_hosted` checks the public URL and, if the file is missing, uploads it, then checks again. Buffer has no upload endpoint and fetches the URL when the post goes out, so the URL must stay public and stable.
4. Under `post.lock`: one `posts` row and one `post_targets` row per channel, video `scheduled`; then `createPost` per channel (Instagram `reel`, shared to feed, cover frame from `poster_at`; Facebook `reel` when vertical and 90 s or less, else `post`; X plain). An id is stored per target; a refusal fails that target. When no channel accepted it, the post is cancelled and the video goes back to approved.
5. `post sync` (the timer runs it) asks Buffer only about targets that are due: `sent` records the URL, `error` records Buffer's message, a missing post means it was deleted in Buffer; then the post settles to posted, partial or failed.
6. `post cancel ID` deletes the Buffer posts still queued and returns the video to approved; `post list` shows posts, titles and URLs (human-only).

## Hosting (Railway)

| Part | Where | What |
|---|---|---|
| Bucket | Railway project ghobz-projects, bucket `social-studio-videos` (iad) | private S3-compatible storage (Tigris); virtual-hosted URLs at `https://<bucket>.t3.storageapi.dev`; keys `<prefix><sha256>.mp4` |
| Proxy | same project, service `social-studio-media`, `https://social-studio-media-production.up.railway.app` | `deploy/media-proxy/server.py`: GET and HEAD (ranges passed through) for video keys and the probe only; 404 for anything else; reads the bucket through Railway variable references; `/healthz` says ok or unconfigured |
| Setup | `deploy/media-proxy/setup.sh <project>` (operator) | creates the bucket, wires the proxy, waits, runs `channel connect media` with the keys in environment variables only |

Railway buckets cannot be public (docs.railway.com/storage-buckets) and Buffer wants a direct URL, not a redirect to a presigned link, so the proxy streams. Bucket egress is free; the proxy's egress is billed as service egress.

## Invariants

- Nothing an agent can run schedules, cancels, lists or sends a post; `agent calendar` shows when and where only. `publish.buffer.*` and `publish.media.*` are human-only config. `post sync` only reads Buffer.
- Mutations are never retried: createPost has no idempotency key. A network error during createPost fails that target with "check Buffer's queue"; a target left without an id is failed by the next sync with the same note.
- Buffer HTTP reads happen outside database write transactions; one posting process at a time through `post.lock`.
- `posts.video_id UNIQUE`: one live post per video; a failed post releases its video when the operator tries again.
- Agent views never show which video sits in a post.
- Not run against live Buffer or the bucket yet (job J22, operator task T4); the client follows developers.buffer.com as of 2026-10-06, and SigV4 matches the AWS get-vanilla test vector. The proxy is deployed and answers health; it serves videos once setup.sh attaches the bucket.

## Rules and open work

- Rules: R14 (operator picks Buffer posts), R4 (signed approval, post text included).
- Ledger: F6 (Buffer: live test J22 with operator task T4), F7 (terminal UI), T1 (approval key), J15 (launchd and schtasks timers).
- Research: [[buffer-api-coverage]]; [[social-platform-apis]] (the removed direct route, kept as reference).
