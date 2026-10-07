# social-studio

A local command-line tool that makes short motion-graphics videos with an LLM agent, keeps each one
in a library with its full post text, and posts the ones a human approved through
[Buffer](https://buffer.com) at the times you pick.

- **One isolated session per video.** Each try runs your harness (Claude Code, OpenCode or Codex)
  headless, in a fresh throwaway home, inside a bubblewrap sandbox that cannot see your library,
  your database or your keys.
- **Presets make it consistent.** One TOML file pins the brand (colours, fonts, assets, easing),
  the content rules, the agent (backend, model, MCP servers, skills, plugins), the render engine
  version and the encode settings. Override any value per run with `--set key=value`.
- **Deterministic renders.** Compositions are HTML rendered frame by frame by
  [HyperFrames](https://github.com/heygen-com/hyperframes) (Apache-2.0) at a pinned version with its
  own pinned Chrome to a near-lossless master, then encoded to H.264 sized for social platforms.
- **A human approves and posts; agents never do.** Approval is a passphrase-protected signature over
  the exact file and its post text. `social-studio post` at your terminal picks an approved post,
  its channels and a time; code uploads the file and schedules it through Buffer's GraphQL API.
- **Two ways in.** Run it yourself, or let an agent in any harness drive it through the CLI
  (`--json` everywhere, a shipped `SKILL.md`).
- **One folder, no sprawl.** A project folder holds config, keys, presets, the library and all
  internal state. Nothing is written outside the git repository that holds it, and a revision
  replaces the previous version instead of piling up copies.

## Install

Needs Python 3.11+, Node.js 22+, ffmpeg, OpenSSH (`ssh-keygen`), and bubblewrap on Linux.

```sh
uv tool install social-studio        # or: pipx install social-studio
social-studio init social             # a project folder: config, .env, presets/, library/, .studio/
cd social && social-studio doctor
```

## Quick start

```sh
social-studio preset new mybrand            # then edit presets/mybrand/preset.toml
social-studio make -n 3 --preset mybrand    # three videos, three isolated sessions
social-studio review                        # watch, then approve / reject / send back with notes
social-studio review rescore 4 --times 2    # re-run the independent reviewer to see how much its scores move
social-studio channel connect buffer        # your Buffer personal API key (human only)
social-studio channel connect media         # a public S3-compatible bucket Buffer fetches videos from
social-studio post                          # pick an approved post, channels, a time; confirm
social-studio post list                     # what is queued or sent, with post URLs
social-studio timer install                 # systemd user timer: `post sync` every 10 minutes records Buffer's results
```

## Concepts

A project is any folder holding `social-studio.toml`. Commands find it from the current folder
(or a `social/` folder below it), from `--project <dir>`, or from `$SOCIAL_STUDIO_PROJECT`.

| Thing | Where (inside the project) | Notes |
|---|---|---|
| Config | `social-studio.toml` | `social-studio config get/set` |
| Secrets | `.env` (0600) | model keys, the Buffer API key, the media bucket keys |
| Presets | `presets/<name>/preset.toml`, then `preset_paths`, then built-ins | `extends = "other"` to inherit |
| Library | `library/<date>-<slug>-<id>/` | `social-studio library dir <folder>` moves it, inside the repo only |
| State | `.studio/`: `library.db`, `approval/`, `sessions/`, `engine/`, `cache/` | SQLite in WAL mode; engine, Chrome and npm cache included |

`init` writes a `.gitignore` that keeps `.env`, `.studio/` and `library/` out of git;
config and presets can be committed.

A finished session is trimmed to what explains it (task, brief, metadata, contact sheet, gzipped
logs); a failed one also keeps its composition. A successful `make --revise <id>` deletes the
previous version's files and sessions and keeps its row as history (`superseded`).

Video statuses: `review → approved → scheduled → posted`, with `rejected`, `revision` (a human's
notes, then `make --revise <id>`), `superseded` and `failed`. The database enforces the legal
transitions, refuses `approved` without an approval for the exact file, and keeps an append-only
event log.

## LLM backends

| Backend | Use | Auth |
|---|---|---|
| `claude` | Claude Code, headless | your Claude login (each session gets a private copy of only that login, and only while it outlives the session), `claude setup-token`, or `ANTHROPIC_API_KEY` |
| `opencode` | any provider OpenCode supports: xAI Grok, DeepSeek, OpenAI, Gemini, OpenRouter, Ollama ... | the provider's API key from the .env |
| `codex` | Codex CLI | `OPENAI_API_KEY`, or a private copy of your Codex login inside the sandbox |

`social-studio model set opencode xai/grok-4` switches the default, and
`social-studio model key XAI_API_KEY` stores a provider key in the .env. It prompts, so only a
human at a terminal can run it. Anthropic allows a Claude
subscription only through the unmodified `claude` binary, which is exactly how this tool uses it.

## Posting through Buffer

Instagram (as a Reel), Facebook (Reel when vertical and 90 s or less, else a video post) and X go
out through [Buffer's GraphQL API](https://developers.buffer.com) with a personal API key, on any
Buffer plan. Buffer has no upload endpoint and fetches the video from a URL when the post goes out,
so `post` first uploads the file to an S3-compatible bucket with public read (Cloudflare R2,
AWS S3, Backblaze B2, MinIO) under its sha256, signed with SigV4, and checks the public URL answers.

Before anything leaves, `post` re-checks the approval signature, re-hashes the file, checks that the
post text is the one approved, and checks each network's length limit. `post sync` (the timer runs
it) reads back what Buffer did: the post URL, or Buffer's error. `post cancel ID` removes queued
posts from Buffer. Buffer is the only posting route; Buffer's API does not read or reply to comments.

## Security model

- The agent session runs with an empty home, the session folder as its only writable path, and
  no path to the database, the library or the .env. Only the chosen backend's own login enters
  the sandbox, as a copy inside the session, because the harness itself makes the model calls.
- Nothing is written outside the repo holding the project: the library cannot move outside it,
  and the engine, Chrome, npm cache and temp files live in `.studio/`. Running without the
  sandbox (by flag or config), installing the timer, and installing a skill outside the repo
  are human-only.
- Network inside the sandbox is open (the harness needs its API). Domain allowlisting is planned.
- Human-only commands (approve, reject, revise, schedule, list or cancel posts, reveal scheduled
  videos, connect accounts) need an interactive terminal, and approval also needs the passphrase.
  Never add the approval key to ssh-agent.
- `post` re-verifies the signature, re-hashes the file and checks the signed post text before every
  upload. The `publish.buffer` and `publish.media` settings are human-only, and no agent command
  schedules or sends a post.

## For agents

`social-studio skill install --target claude` (or `opencode`, `codex`, a folder) installs the agent
guide. Agents use `social-studio --json agent status|videos|topics|calendar` and `make`; posting
stays with the human.
