---
id: schedule-publish
type: reference
created: "2026-10-06T23:59:00Z"
consequence: 7
locus: output
summary: Box schedule-publish - Buffer, the only route: new videos become Buffer drafts approved there, or signed posts picked at a terminal; sync records results.
scope: repo
status: active
---

# Box: schedule-publish

Part of [[index]]. One route, Buffer, with two places to approve (rule R14). In Buffer (the default since 2026-10-07): code puts each finished video into Buffer as drafts, and the operator approves, edits or deletes them there. At the terminal: the operator picks a signed-approved post, the channels and the time. Either way Buffer publishes and the timer records what happened. The older direct route (platform adapters, agent-set calendar slots, `post run`, draft folders) was removed on 2026-10-06.

| Field | Value |
|---|---|
| Purpose | Turn finished videos and their post text into posts on Instagram, Facebook and X, once, only after a human approved them, and record what happened |
| Owned paths | `src/social_studio/posting.py` (drafts, withdraw, pick, plan, execute, sync, cancel, list; time helpers, `post.lock`, settling), `platforms/__init__.py` (HTTP, captions, the account registry), `platforms/buffer.py` (GraphQL client), `platforms/media.py` (bucket upload, public check), `deploy/media-proxy/` (`server.py` proxy, `Dockerfile`, `setup.sh`) |
| In | the end of `make` and `post draft ID`; `post` / `post schedule ID --at ... -c ...` at a terminal; `post sync` from the systemd user timer (`timer install`); `channel connect buffer|media`; videos from [[library]]; `publish.*` config and preset keys |
| Out | `posts` and `post_targets` rows (`via buffer`, Buffer channel id, the text sent, post URL); the video at `<public_url>/<prefix><sha256>.mp4` |

## Flow: approval in Buffer (drafts)

1. On when Buffer is connected, unless `publish.buffer.drafts = false`. After `make` returns, the CLI (not the agent, whose session has ended and never held the Buffer key) calls `draft` for each new video; `post draft ID` does the same by hand. Only a video in `review` that is on no post goes.
2. Channels are every connected, unlocked Buffer channel on any network Buffer serves, with every account on it (operator 2026-10-07: a channel connected later gets the next video). `publish.buffer.channels` narrows the list. Buffer's services on 2026-10-07 were bluesky, facebook, googlebusiness, instagram, linkedin, mastodon, pinterest, startPage, substack, threads, tiktok, twitter, whatsapp and youtube.
   - Text: the maker's caption for that network, else the default caption or the description.
   - Text limits: Instagram 2,196 (a line break counts 2), Facebook 5,000, X 280 (a link counts 23), LinkedIn 3,000 (a link counts 24), Pinterest 500, TikTok 2,200, Threads 500, Bluesky 300, YouTube 5,000, Google Business 4,000 and Mastodon 500. A text over its limit is skipped. Start Page, Substack and WhatsApp have no published limit.
   - Metadata: YouTube, TikTok and Pinterest get the title (100 at most), and Google Business gets type `whats_new` (its one required field).
3. `media.ensure_hosted` uploads the file, then one `posts` row (`created_by drafts`, status `open`) and one `draft` target per channel are written. Then `createPost` runs with `saveToDraft: true` and `mode: addToQueue`, with the same per-network shape as below. The video stays `review`. When no channel accepted a draft, the post is cancelled and the video is free to try again.
4. In Buffer the operator schedules or queues a draft (approves it), edits it, or deletes it. Buffer reports `draft` or `needs_approval` while it waits.
5. `post sync` reads every draft target on each run. `scheduled` or `sending` turns the target `pending` at Buffer's time and the post `scheduled`. `sent` records the URL. `error` records Buffer's message. A deleted draft turns that channel down (`cancelled`). Once nothing is a draft or pending, the post settles. With any channel posted, the video goes `review → posted`. With all failed, it becomes `failed`. With every draft deleted, the post is cancelled and the video `rejected`.
6. Rejecting or revising the video at the terminal, a revision superseding it, or `post cancel ID` first withdraws it: each draft or approved-but-unsent post is read, a sent one is recorded, and the rest are deleted from Buffer. Local approval of a video with live drafts is refused.

## Flow: approval at the terminal

1. `post` (human-only) lists approved videos not on a live post, then Buffer's connected channels, then asks for a time (`YYYY-MM-DD HH:MM` local, at least 2 minutes out, or `now`) and a yes.
2. The plan re-checks everything before anything leaves:
   - the status is approved (or failed, to try again);
   - the approval signature verifies;
   - the file re-hashes;
   - the post-text hash matches the signed one;
   - each text fits the network limit: Instagram 2,196, Facebook 5,000, X 280, with X links counting 23 (`publish.buffer.limits.x` for Premium).

   After the yes it checks again that nothing changed while the operator was confirming.
3. `media.ensure_hosted` checks the public URL and uploads the file if it is missing, then checks again. Buffer has no upload endpoint and fetches the URL when the post goes out, so the URL must stay public and stable.
4. Under `post.lock`, the code writes one `posts` row and one `post_targets` row per channel and marks the video `scheduled`. Then it runs `createPost` per channel:
   - Instagram: `reel`, shared to feed, cover frame from `poster_at`;
   - Facebook: `reel` when vertical and 90 s or less, else `post`;
   - X: plain.

   An id is stored per target, and a refusal fails that target. When no channel accepted it, the post is cancelled and the video goes back to approved.
5. `post sync` asks Buffer only about targets that are due. `sent` records the URL, `error` records Buffer's message, and a missing post means it was deleted in Buffer. The post then settles to posted, partial or failed.
6. `post cancel ID` deletes the Buffer posts still queued and returns the video to approved. `post list` shows posts, titles and URLs, drafts included (human-only).

## Hosting (Railway)

| Part | Where | What |
|---|---|---|
| Bucket | Railway project ghobz-projects, bucket `social-studio-videos` (iad) | private S3-compatible storage (Tigris); virtual-hosted URLs at `https://<bucket>.t3.storageapi.dev`; keys `<prefix><sha256>.mp4` |
| Proxy | same project, service `social-studio-media`, `https://social-studio-media-production.up.railway.app` | `deploy/media-proxy/server.py`: GET and HEAD (ranges passed through) for video keys and the probe only; 404 for anything else; reads the bucket through Railway variable references; `/healthz` says ok or unconfigured |
| Setup | `deploy/media-proxy/setup.sh <project>` (operator) | creates the bucket, wires the proxy, waits, runs `channel connect media` with the keys in environment variables only |

Railway buckets cannot be public (docs.railway.com/storage-buckets). Buffer wants a direct URL, not a redirect to a presigned link, so the proxy streams the file. Bucket egress is free; the proxy's egress is billed as service egress.

## Invariants

- No agent command schedules, cancels, lists or sends a post. `agent calendar` shows when and where only.
- `publish.buffer.*` and `publish.media.*` are human-only config.
- Drafts publish nothing. Only a human scheduling them in Buffer makes them posts.
- `post sync` only reads Buffer.
- The database allows `review → posted|failed` only for a video on a `drafts` post (schema v3 trigger).
- Drafts hold no time slot. The slot index allows one live post per channel and second, and covers `pending` and `posted` only. A post has one target per Buffer channel (schema v4), so several accounts on one network fit in one post.
- The terminal route still offers Instagram, Facebook and X only. Drafts take every connected channel.
- Mutations are never retried, because createPost has no idempotency key.
  - A network error during createPost fails that target with "check Buffer's queue/drafts".
  - The next sync fails a target that has no id, with the same note.
- Buffer HTTP reads happen outside database write transactions. One posting process runs at a time through `post.lock`.
- `posts.video_id UNIQUE`: one live post per video. A failed or withdrawn post releases its video.
- Agent views never show which video sits in a post.
- Live use:
  - Buffer channels: Instagram ghobz.studio and X GHOBZstudio on 2026-10-07; Facebook not connected.
  - The schema read live: PostStatus is draft, error, needs_approval, scheduled, sending, sent; CreatePostInput has saveToDraft, and needsApproval, which works only when a channel's posting policy requires approval.
  - The first live draft is job J26.
  - SigV4 matches the AWS get-vanilla test vector.

## Rules and open work

- Rules: R14 (who approves and how posts leave), R4 (signed approval, post text included).
- Ledger:
  - F9: approval in Buffer (merged 2026-10-07);
  - F10: drafts to every connected channel (J29);
  - J26: the intro video's live post (operator task T5);
  - F7: terminal UI;
  - F8: several accounts;
  - T1: approval key;
  - J15: launchd and schtasks timers.
- Research: [[buffer-api-coverage]]; [[social-platform-apis]] (the removed direct route, kept as reference).
