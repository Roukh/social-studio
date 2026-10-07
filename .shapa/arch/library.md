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

## Data model (schema v1, `PRAGMA user_version`, WAL, foreign keys on)

| Table | Holds |
|---|---|
| `sessions` | each harness run: kind (make, review), preset and hash, backend, model, sandbox, dir, status, cost, video_id |
| `videos` | the library; status review, approved, rejected, revision, superseded, scheduled, posted, failed; identity is the file's sha256 |
| `video_events` | append-only status history with the actor from `ss_actor()` |
| `approvals` | video_id, sha256, payload, ssh signature |
| `posts` | slot at (UTC), `video_id UNIQUE`; status open, scheduled, posting, posted, partial, failed, cancelled, missed |
| `post_targets` | per platform: status, `platform_post_id` (unique per platform), url, attempts, next_try_at |

| From | Allowed to |
|---|---|
| review | approved, rejected, revision, superseded |
| revision | approved, rejected, superseded, review |
| rejected | review |
| approved | scheduled, rejected, revision |
| scheduled | posted, failed, approved |
| failed | approved, scheduled, rejected |

Views for the agent surface: `agent_videos` (only review, approved, rejected, revision), `agent_topics` (topic, angle, pillar, day; no superseded), `agent_calendar` (slots and platforms, never which video).

## Invariants

- Triggers enforce legal transitions; `approved` and `scheduled` need an approvals row with the same sha256 (rule R4).
- `video_events` cannot be updated or deleted; `ss_actor()` is registered only by the tool, so a raw `sqlite3` edit of status fails.
- Approval: an ed25519 key with a passphrase, created by `init` at a terminal; `ssh-keygen -Y sign` under namespace `social-studio-approval` over `social-studio approval v1 / video:ID / sha256:HASH / approved_at:TIME`; `check_video` verifies the signature, the sha256 and an on-disk re-hash.
- A board approval (feature F2) must use a separate namespace or TTY gate and never count as a video approval.
- Schema changes add a new `SCHEMA` entry; never edit v1. Planned v2: `sessions.parent_id`, `sessions.meta`, a `boards` table, `videos.board_id`.

## Rules and open work

- Rules: R3 (code picks videos), R4 (signed approval).
- Ledger: T1 (the operator creates the approval key in the project folder).
