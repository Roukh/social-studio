---
name: social-studio
description: Make short motion-graphics videos for social media, each with its full post text, with the social-studio CLI; the operator approves them and posts them through Buffer. Use when asked to create social videos, check what is waiting for review, or what is ready to post.
---

# social-studio (agent guide)

`social-studio` makes videos in isolated, sandboxed agent sessions and keeps each one in a library
with its full post: title, description, captions per network, hashtags. A human approves the video
and its text together, then posts it through Buffer with `social-studio post`. Agents never post.
Add `--json` to any command for machine-readable output.
Errors come back as `{"error": {"code", "message", "hint"}}` with a non-zero exit code.

Run it from the project folder (it holds `social-studio.toml`), from a folder with a `social/`
project below it, or pass `--project <dir>`. `social-studio --json config path` shows where
everything is.

## What you can do

| Goal | Command |
|---|---|
| See the state of things | `social-studio --json agent status` |
| Make videos | `social-studio --json make -n 3` (add `--title`, `--subject`, `--topic`, `--pillar`, `--notes`, `--preset`, `--set key=value`) |
| Pick the format for this batch | `make --aspect 16:9 --fps 60 --duration 15 --sound bed+sfx` (aspect 9:16, 4:5, 1:1 or 16:9; sound none, sfx, bed+sfx, sfx+voice or bed+sfx+voice) |
| Make a showreel in the house reel look | `social-studio --json make --preset reel` (16:9, 60 fps, 15 s, synthesized bed and effects) |
| Remake a video a human sent back | `social-studio --json make --revise <id>` (the new version replaces the old one's files) |
| Find a video's file to show the operator | `social-studio --json library path <id>` |
| Show or move the library (inside the repo) | `social-studio --json library dir [folder]` |
| List videos not yet posted | `social-studio --json agent videos` |
| Topics already covered (avoid repeats) | `social-studio --json agent topics` |
| See what goes out when (read-only; when and where, not which video) | `social-studio --json agent calendar` |

Posting through Buffer (Instagram, Facebook, X) is the operator's: `social-studio post` at their
terminal picks an approved post, its channels and a time. When `agent status` shows
`ready_to_post` above zero, tell the operator to run it.

## What you cannot do, by design

- Approve, reject or mark videos for revision. Only the human can, in their own terminal
  (`social-studio review`). Approval is a passphrase signature; it cannot be done for them.
- Schedule, post, list or cancel posts (`social-studio post`), or pick which video goes out or
  when. A scheduled video disappears from everything you can list.
- Change where posts and videos go (`publish.buffer`, `publish.media`), see or change scheduled and
  posted videos, or connect accounts.
- Write outside the repo that holds the project. Running without the sandbox, installing the
  timer, and installing a skill outside the repo are human-only.

If a command answers `denied` (exit 77), it is human-only: tell the operator which command to run.

## Typical flow

1. `agent status` to see how many videos wait for review and how many are ready to post.
2. `make -n <count>` if the library is short of approved or pending videos.
3. Tell the operator to run `social-studio review` to approve them (the video and its post text).
4. Tell the operator to run `social-studio post` to schedule approved ones through Buffer.
