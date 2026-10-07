---
id: library
type: reference
created: "2026-10-06T23:59:00Z"
consequence: 8
locus: output
summary: Box library - the SQLite schema, trigger-enforced video statuses, append-only events, agent views, and the ssh-keygen approval signature.
scope: repo
status: active
---

# Box: library

Part of [[index]]. The source of truth for every video, session, approval and post.

| Field | Value |
|---|---|
| Purpose | Store videos and their history so no agent can approve, schedule or rewrite them; prove human approval |
| Owned paths | `src/social_studio/db.py` (216 lines), `src/social_studio/approval.py` (118 lines); `<project>/.studio/library.db`, `<project>/.studio/approval/` |
| In | session and video rows from [[runner]]; status changes from `review` commands in [[cli]]; post rows from [[schedule-publish]] |
| Out | approved videos with a verifiable signature; agent views; `check_video` verdicts for fill and publish |

## Data model (schema v4, `PRAGMA user_version`, WAL, foreign keys on)

v2 (2026-10-06, feature F6) only adds three `post_targets` columns, so a process still running v1 code keeps working against a v2 file. v3 (2026-10-07, feature F9) replaces two schema objects so approval can happen in Buffer: the transition trigger, and the slot index, which no longer covers drafts. v4 (2026-10-07, feature F10) rebuilds `post_targets` with the same columns. Targets become unique per (post, Buffer channel) instead of per (post, platform), so several accounts on one network fit in one post. The slot index becomes one live post per channel and second. The `agent_calendar` view is recreated unchanged. A v2 copy of the ghobz library upgraded to v4 with every row kept and a clean integrity check.

| Table | Holds |
|---|---|
| `sessions` | each harness run: kind (make, review), preset and hash, backend, model, sandbox, dir, status, cost, video_id |
| `videos` | the library; status review, approved, rejected, revision, superseded, scheduled, posted, failed; identity is the file's sha256 |
| `video_events` | append-only status history with the actor from `ss_actor()` |
| `approvals` | video_id, sha256, payload, ssh signature |
| `posts` | when (UTC), `video_id UNIQUE`, `created_by` (`drafts` for a video sent to Buffer as drafts); status `open` (drafts waiting in Buffer), scheduled, posting, posted, partial, failed, cancelled (`missed` was the removed calendar's and is no longer written) |
| `post_targets` | per Buffer channel (v4; per platform before): status (`draft` waits for approval in Buffer, pending, posted, failed, cancelled), `platform_post_id` (unique per platform; the Buffer post id), url, attempts, next_try_at; v2: `via` (always buffer now; `direct` was the removed route), `channel_id` (Buffer channel), `text` (exactly what was sent) |

| From | Allowed to |
|---|---|
| review | approved, rejected, revision, superseded; posted or failed only while on a `drafts` post (v3) |
| revision | approved, rejected, superseded, review |
| rejected | review |
| approved | scheduled, rejected, revision |
| scheduled | posted, failed, approved |
| failed | approved, scheduled, rejected |

Views for the agent surface: `agent_videos` (only review, approved, rejected, revision), `agent_topics` (topic, angle, pillar, day; no superseded), `agent_calendar` (Buffer posts: when, status and platforms, never which video).

## Invariants

- Triggers enforce legal transitions; `approved` and `scheduled` need an approvals row with the same sha256 (rule R4). A video approved in Buffer has no approvals row: Buffer's own app is that gate, and only `post sync` reading a sent draft moves it to posted.
- `video_events` cannot be updated or deleted; `ss_actor()` is registered only by the tool, so a raw `sqlite3` edit of status fails.
- Approval: an ed25519 key with a passphrase, created by `init` at a terminal; `ssh-keygen -Y sign` under namespace `social-studio-approval` over `social-studio approval v2 / video:ID / sha256:HASH / post:HASH / approved_at:TIME`, where the post hash covers title, description and the captions, hashtags and `poster_at` from `video.json`; `check_video` verifies the signature, the sha256 and an on-disk re-hash, and with `post=True` (the Buffer route) the post hash too. A v1 approval must be approved again before it can go through Buffer.
- A board approval (feature F2) must use a separate namespace or TTY gate and never count as a video approval.
- Schema changes add a new `SCHEMA` entry; never edit an earlier one. Planned v3: `sessions.parent_id`, `sessions.meta`, a `boards` table, `videos.board_id`.

## Rules and open work

- Rules: R3 (code picks videos), R4 (signed approval).
- Ledger: T1 (the operator creates the approval key in the project folder).
