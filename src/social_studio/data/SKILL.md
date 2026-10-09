---
name: social-studio
description: Make short motion-graphics videos for social media, each with its full post text, with the social-studio CLI; each new video becomes a Buffer draft the operator approves there. Use when asked to create social videos, check what is waiting for review, or what is ready to post.
---

# social-studio (agent guide)

`sclstdio` (alias `social-studio`) makes videos in isolated, sandboxed agent sessions and keeps each one in a library
with its full post: title, description, captions per network, hashtags. Once Buffer is connected,
the CLI puts each finished video into Buffer as a draft on every connected channel, and a human
approves, edits or deletes it there. Drafts publish nothing, and agents never post.
Add `--json` to any command for machine-readable output.
Errors come back as `{"error": {"code", "message", "hint"}}` with a non-zero exit code.

Run it from the project folder (it holds `social-studio.toml`), from a folder with a `social/`
project below it, or pass `--project <dir>`. `sclstdio --json config path` shows where
everything is.

## What you can do

| Goal | Command |
|---|---|
| See the state of things | `sclstdio --json agent status` |
| Make videos | `sclstdio --json build -n 3` (add `--title`, `--subject`, `--topic`, `--pillar`, `--notes`, `--preset`, `--set key=value`); each film picks its techniques from the shipped technique library and lists them in its `video.json`. With none of `--title`, `--subject`, `--topic`, `--notes`, a pitch round picks each film's concept first (five pitches, a judge); give one of them when the operator asked for something specific |
| Pick the format for this batch | `make --aspect 16:9 --fps 60 --duration 15 --sound bed+sfx` (aspect 9:16, 4:5, 1:1 or 16:9; sound none, sfx, bed+sfx, sfx+voice or bed+sfx+voice) |
| Make a showreel in the house reel look | `sclstdio --json build --preset reel` (16:9, 60 fps, 20-25 s, synthesized bed and effects) |
| Remake a video a human sent back | `sclstdio --json build --revise <id>` (the new version replaces the old one's files) |
| Show the operator the film's key poses before any motion (only when asked: it stops the build) | `sclstdio --json build --boards`: a board sheet, filed as a board, no video. Then tell the operator its `sheet` path and that they decide it in a terminal |
| Boards waiting, approved or sent back | `sclstdio --json board` (with sheet paths), `sclstdio --json board show <id>`, `sclstdio --json agent boards` |
| Animate a board the operator approved | `sclstdio --json build --from-board <id>` (the video records the board; it still needs its own approval) |
| Lay out again a board the operator sent back | `sclstdio --json build --boards --from-board <id>` (their notes are in it; the old board is replaced) |
| Every video file on this disk, with its path | `sclstdio --json library` (`library <id>` shows one) |
| Find a video's file to show the operator | `sclstdio --json library <id> path` |
| Put a video waiting for review into Buffer as drafts | `sclstdio --json library <id> draft` (a make already does this) |
| Show or move the library (inside the repo) | `sclstdio --json library dir [folder]` |
| List videos not yet posted | `sclstdio --json agent videos` |
| Topics already covered (avoid repeats) | `sclstdio --json agent topics` |
| See what goes out when (read-only; when and where, not which video) | `sclstdio --json agent calendar` |

A `build` result carries `buffer`: the drafts it left in Buffer, or why they did not get there. Tell
the operator the drafts are waiting in Buffer. Approving them is the operator's, in Buffer. When
Buffer is not connected, the operator approves at the terminal instead: `sclstdio review walk`,
then `sclstdio post pick` picks an approved post, its channels and a time. When `agent status`
shows `ready_to_post` above zero, tell the operator to run it.

## What you cannot do, by design

- Approve, reject or mark videos for revision. Only the human can: in Buffer for drafts, or in
  their own terminal (`sclstdio review walk`), where approval is a passphrase signature that cannot
  be done for them.
- Approve, revise or drop a keyframe board (`sclstdio board approve|revise|drop`): human-only, at a
  terminal. An approved board is not an approved video.
- Schedule, post, list or cancel posts (`sclstdio post`, `library <id> post|schedule|cancel`), delete
  videos (`library <id> delete`), or pick which video goes out or when.
  A scheduled video disappears from everything you can list. (`post draft ID` only puts a video that
  waits for review into Buffer's drafts, which publish nothing; a make already does this itself.)
- Change where posts and videos go (`publish.buffer`, `publish.media`), see or change scheduled and
  posted videos, or connect accounts.
- Write outside the repo that holds the project. Running without the sandbox, installing the
  timer, and installing a skill outside the repo are human-only.

If a command answers `denied` (exit 77), it is human-only: tell the operator which command to run.

## Typical flow

1. `agent status` to see how many videos wait for review and how many are ready to post.
2. `make -n <count>` if the library is short of approved or pending videos.
3. Tell the operator the new drafts wait in Buffer to be approved, edited or deleted there.
4. Without Buffer drafts: tell the operator to run `sclstdio review walk` to approve them (the
   video and its post text), then `sclstdio post pick` to schedule approved ones through Buffer.
