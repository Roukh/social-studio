---
id: cli
type: reference
created: "2026-10-06T23:59:00Z"
consequence: 7
locus: output
summary: Box cli - the argparse noun-verb command tree, --json output, exit codes, human-only gates, doctor, timer, completion and the agent surface.
scope: repo
status: active
---

# Box: cli

Part of [[index]]. The only entry point for humans, agents and the timer.

| Field | Value |
|---|---|
| Purpose | Parse commands, build `Ctx`, call the other boxes, print human text or `--json` |
| Owned paths | `src/social_studio/cli.py` (817 lines), `__main__.py`, `data/SKILL.md` (the agent's guide to the CLI) |
| In | argv; `--project` or `$SOCIAL_STUDIO_PROJECT` or the current folder; a TTY for human-only commands |
| Out | calls into [[core]], [[runner]], [[library]], [[review]], [[schedule-publish]]; stdout text or JSON |

## Commands

| Command | What | Gate |
|---|---|---|
| `init [DIR]` (`setup`) | config, `.env`, folders, database, approval key, engine | key creation human-only |
| `doctor` | python 3.11+, node 22+, npm, ffmpeg, ffprobe, ssh-keygen, bwrap, backends, project, `.env` mode; the buffer and media accounts (optional) | exit 1 on a failed required check |
| `config get|set|list|path` | `social-studio.toml` | `GUARDED_CONFIG` keys human-only; `paths.library` refused (use `library dir`) |
| `model list|set|key` | backends and models; `key` stores an API key into `.env` | `key` human-only |
| `preset list|show|validate|new` | presets | — |
| `engine install|status` | pinned HyperFrames | — |
| `make` | one session per video: `-n`, `--parallel`, `--preset`, `--backend`, `--model`, `--set`, `--title/--subject/--topic/--pillar/--notes`, `--effort`, `--review-effort`, `--pacing`, `--motion`, `--aspect`, `--fps`, `--duration`, `--sound`, `--rounds`, `--revise ID`, `--[no-]review` | `--no-sandbox` and guarded `--set` keys human-only |
| `library list|show|path|open|dir` | browse; `dir` moves the library inside the boundary | `--all` human-only |
| `review walk|list|approve|reject|revise|rescore` | human review; reject and revise first withdraw the video's Buffer drafts; approve refuses a video with live drafts (approve it in Buffer); `rescore ID --times N --effort` re-runs the reviewer | approve signs at a TTY |
| `agent status|videos|topics|calendar` | read-only agent surface: `status` gives approval_needed, ready_to_post and next_post; `calendar` gives when and where, never which video; agent views hide scheduled, posted and failed videos | — (agents never schedule) |
| `post draft ID`, `post [pick]`, `post schedule ID --at 'YYYY-MM-DD HH:MM'|now [-c instagram|facebook|x] [--yes] [--dry-run]`, `post list|sync|cancel ID` | the only posting route (rule R14): `make` sends each new video to Buffer as drafts by itself (`post draft` by hand); or pick an approved post, channels and time, then upload and createPost; sync reads back what Buffer did and follows drafts; cancel withdraws drafts | pick, schedule, list, cancel human-only; draft is not, and neither are the drafts a make sends (drafts publish nothing; operator 2026-10-07, while Buffer is the temporary route) |
| `channel list|connect|test|disconnect buffer|media`, `timer install|remove|status` | accounts; systemd user timer that runs `post sync` | connect, `publish.buffer.*`, `publish.media.*` and timer human-only |
| `completion bash|zsh`, `skill install|show`, `version` | shell completion (zsh wraps bash), install the agent skill into a harness | out-of-repo installs human-only |

## Invariants

- Every command supports `--json`; an error prints `{"error": {"code", "message", "hint"}}`.
- Exit codes: 0 ok, 1 failure, 64 usage, 65 data, 69 unavailable, 77 denied (human-only), 78 config, 130 interrupted.
- Human-only means `core.require_human`: a TTY on stdin and stdout and `SOCIAL_STUDIO_ROLE` not `agent`, else exit 77.
- Format flags map through `core.format_sets` (rule R11); never hard-code sizes here.
- `cli.py` stays near 800 lines; new command groups go in their own module.

## Rules and open work

- Rules: R10 (mcp serve unpublished), R11 (format per run).
- Ledger: J14 `mcp serve`, J15 launchd and schtasks timers, J16 native zsh and fish completion, J17 keyring opt-in; F2 adds `board` and `make --boards/--from-board`.
- Research: [[cli-conventions-and-isolation]].
