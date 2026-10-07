---
id: schedule-publish
type: reference
created: "2026-10-06T23:59:00Z"
consequence: 7
locus: output
summary: Box schedule-publish - calendar slots people or agents set, code-picked fill, post run with lock, re-verification and backoff, platform adapters and drafts.
scope: repo
status: active
---

# Box: schedule-publish

Part of [[index]]. People and agents choose when; code chooses which approved video; the timer posts it.

| Field | Value |
|---|---|
| Purpose | Turn approved videos into posts on the dates someone set, idempotently, on every connected platform |
| Owned paths | `src/social_studio/schedule.py` (165 lines), `publish.py` (109 lines), `platforms/` (`__init__.py` HTTP, OAuth with PKCE, captions; `meta.py`, `youtube.py`, `x.py`, `bluesky.py`); `<project>/drafts/` |
| In | `schedule add DATE TIME [-p PLATFORM] [--every 2d|12h|1w --count N]`, `post run` from the systemd user timer, `channel connect|test`; approved videos from [[library]]; `publish.*` preset keys |
| Out | `posts` and `post_targets` rows; platform post ids and URLs; draft folders (video, poster, caption) |

## Platforms

| Platform | Adapter | Upload |
|---|---|---|
| instagram, facebook | `meta.py` | Meta resumable upload (rupload) |
| youtube | `youtube.py` | resumable; uploads stay private until the API audit passes |
| x | `x.py` | v2 chunked media upload, 4 MB chunks |
| bluesky | `bluesky.py` | blob |
| linkedin, tiktok | `Draft` | a folder under `drafts/` to post by hand: LinkedIn API Terms forbid automated posting; TikTok's audit rejects in-house upload tools |

Captions come from `video.json` per platform plus UTM-tagged links on `x`, `linkedin`, `facebook`, `bluesky`, `youtube`. Tokens live in the project `.env`.

## Invariants

- `schedule add` parses local time in the configured timezone, rejects past times and clashes, claims under `BEGIN IMMEDIATE`, then fills (rule R3).
- Fill takes the oldest approved video (by approval time) that is not on any post and whose signature verifies and file re-hashes; `posts.video_id UNIQUE` posts each video once (rule R4).
- `post run` holds `post.lock` (flock), fills open slots, sweeps past-due open slots to `missed`, then per due pending target: skip if `platform_post_id` is set, re-verify approval (a mismatch fails the target with `blocked:`), call the adapter, record, else back off 5 min, 30 min, 2 h, then fail; it settles the post as posted, partial or failed.
- Agent views never show which video fills a slot; `schedule list --videos` is human-only.
- Known gap: a crash after a successful upload and before the database write can duplicate one post on retry (job J13).

## Rules and open work

- Rules: R3 (code picks videos), R4 (signed approval).
- Ledger: F4 (live tests per platform: J10-J12; duplicate window J13), T1 (approval key), J15 (launchd and schtasks timers).
- Research: [[social-platform-apis]].
