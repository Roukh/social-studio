---
name: social-studio
description: Make short motion-graphics videos for social media and put approved ones on the posting calendar, with the social-studio CLI. Use when asked to create social videos, check what is waiting for review, or schedule posts for given dates and times.
---

# social-studio (agent guide)

`social-studio` makes videos in isolated, sandboxed agent sessions, keeps them in a library, and
posts the ones a human approved. Add `--json` to any command for machine-readable output.
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
| List videos not yet on the calendar | `social-studio --json agent videos` |
| Topics already covered (avoid repeats) | `social-studio --json agent topics` |
| See the calendar (when, not which video) | `social-studio --json agent calendar` |
| Put posts on the calendar | `social-studio --json agent schedule 2026-10-05 09:00 -p instagram -p youtube` |
| Several posts on a cadence | `social-studio --json agent schedule 2026-10-05 09:00 -p instagram --every 2d --count 5` |

Dates are `YYYY-MM-DD`, times are `HH:MM` 24-hour in the operator's time zone. You decide the
dates and times from the operator's request ("every other day at 9", "spread 6 posts over two
weeks"): work the dates out yourself and call `agent schedule` once per post, or once with
`--every` and `--count` for a fixed cadence.

## What you cannot do, by design

- Approve, reject or mark videos for revision. Only the human can, in their own terminal
  (`social-studio review`). Approval is a passphrase signature; it cannot be done for them.
- Choose which video goes into a slot. The scheduler fills each slot with the oldest approved
  video, and a filled slot's video disappears from everything you can list. A slot with no
  approved video stays open and fills when the next video is approved.
- See or change scheduled and posted videos, or connect social accounts.
- Write outside the repo that holds the project. Running without the sandbox, installing the
  timer, and installing a skill outside the repo are human-only.

If a command answers `denied` (exit 77), it is human-only: tell the operator which command to run.

## Typical flow

1. `agent status` to see how many videos wait for review and how many slots are open.
2. `make -n <count>` if the library is short of approved or pending videos.
3. Tell the operator to run `social-studio review` to approve them.
4. `agent schedule` the dates and times they asked for.
