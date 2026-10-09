# social-studio

A local command-line tool that makes short motion-graphics videos with an LLM agent, keeps each one
in a library with its full post text, and hands each new video to [Buffer](https://buffer.com) as a
draft, where you approve, edit or delete it.

- **One isolated sandbox per video, story first.** Each try runs your harness (Claude Code, OpenCode or
  Codex) headless, in a fresh throwaway home, inside a bubblewrap sandbox that cannot see your library,
  your database or your keys. Two sessions run there back to back: a storyteller writes the film's idea
  and its beats (no motion), learning from analysed brand posts; then a designer builds the motion from
  that story. Set `story.enabled = false` in a preset to skip the storyteller.
- **A pitch round when you give no brief.** Without `--title`, `--subject`, `--topic` or `--notes`, the
  story stage opens with five concepts pitched on five different paths (the product's world, the emotion,
  the audience, the usual video inverted, an unusual format), each resting on a concrete fact about the
  product. A judge in its own fresh session, seeing only the pitches and the brief, scores them on one
  rubric; code checks the verdict, picks the winner and hands it to the storyteller. The pitches, the
  verdict and the typical direction left behind stay with the video. `story.pitch = false` skips it.
- **Keyframe boards, when you want to see the film first.** `sclstdio build --boards` runs the story stage,
  then has the designer lay out each shot's key pose as a still at the final layout (real fonts, colours
  and copy, no motion). Code snapshots the poses and tiles them into one board sheet, labelled shot by shot,
  with the platform safe zone drawn at 9:16, and the build stops there. You decide the board at your
  terminal (`sclstdio board approve|revise|drop ID`); `sclstdio build --from-board ID` then animates the
  approved poses into the video. Approving a board never approves a video. Without `--boards`, a build
  runs to the end on its own.
- **A tagged store of techniques.** A shipped SQLite store holds atomic techniques (a 3D voxel field, a
  particle flow, a kinetic word run, a morph, wipes, each with a proven recipe) and scenes extracted shot
  by shot from reference films, each tagged by story role, purpose, content and energy with a general
  prompt. Code retrieves the best few for each story beat and hands them to the designer, who records
  the set it used, so the next film differs. Every composition has GSAP (with SplitText, MorphSVG and
  DrawSVG), three.js and a small motion kit; every session has the engine's block registry, pinned.
- **Presets make it consistent.** One TOML file pins the brand (colours, fonts, assets, easing),
  the content rules, the agent (backend, model, MCP servers, skills, plugins), the render engine
  version and the encode settings. Override any value per run with `--set key=value`.
- **Deterministic renders.** Compositions are HTML rendered frame by frame by
  [HyperFrames](https://github.com/heygen-com/hyperframes) (Apache-2.0) at a pinned version with its
  own pinned Chrome to a near-lossless master, then encoded to H.264 sized for social platforms.
- **A human approves; agents never post.** Once Buffer is connected, code puts each finished video
  into Buffer as a draft on every connected channel, and you approve it there. Drafts publish
  nothing. You can also approve at the terminal instead: a passphrase-protected signature over the
  exact file and its post text, then `sclstdio post pick` picks the post, its channels and a time.
- **Two ways in.** Run it yourself, or let an agent in any harness drive it through the CLI
  (`--json` everywhere, a shipped `SKILL.md`).
- **One folder, no sprawl.** A project folder holds config, keys, presets, the library and all
  internal state. Nothing is written outside the git repository that holds it, and a revision
  replaces the previous version instead of piling up copies.

## Install

Needs Python 3.11+, Node.js 22+, ffmpeg, OpenSSH (`ssh-keygen`), and bubblewrap on Linux.

```sh
uv tool install social-studio        # or: pipx install social-studio
sclstdio init social                 # a project folder: config, .env, presets/, library/, .studio/
cd social && sclstdio doctor
```

The command is `sclstdio` (`social-studio` still works as an alias). A bare `sclstdio` prints the menu of
commands, and `sclstdio help <command>` prints that command's options. A bare command shows what it
holds: `sclstdio library` lists every video whose file is on this disk, with its path; `review` and
`post` list their queues (`review walk` and `post pick` are the interactive ones). At a terminal, reads
first sync with Buffer, so a draft deleted there shows here as rejected without waiting for the timer.

## Quick start

```sh
sclstdio preset new mybrand                 # then edit presets/mybrand/preset.toml
sclstdio channel connect buffer             # your Buffer personal API key (human only)
deploy/media-proxy/setup.sh social          # Railway bucket + read-only proxy Buffer fetches videos from
                                            # (or `channel connect media` for any S3-compatible bucket)
sclstdio timer install                      # systemd user timer: `post sync` every 10 minutes records Buffer's results
sclstdio build -n 3 --preset mybrand        # three videos, three isolated sessions, each one a Buffer draft
                                            # then approve, edit or delete the drafts in Buffer
sclstdio library                            # every video on this disk: id, status, title, path
sclstdio library 4 post                     # what Buffer does to a post, from here (signed): post, schedule
                                            #   [--at '2026-10-09 09:00'; else Buffer's queue], cancel, delete
sclstdio post list                          # drafts, queued and sent posts, with post URLs
sclstdio review walk                        # watch here; reject or send back with notes (takes the drafts out)
sclstdio review rescore 4 --times 2         # re-run the independent reviewer to see how much its scores move
sclstdio build --boards                     # stop at a keyframe board: the poses on one sheet, no motion yet
sclstdio board                              # the boards waiting for you, with their sheet paths
sclstdio board approve 3                    # (or: revise 3 --notes '...', drop 3) at your terminal only
sclstdio build --from-board 3               # animate the approved board into the video
sclstdio build --boards --from-board 3      # lay out again a board you sent back with notes
```

## Concepts

A project is any folder holding `social-studio.toml`. Commands find it from the current folder
(or a `social/` folder below it), from `--project <dir>`, or from `$SOCIAL_STUDIO_PROJECT`.

| Thing | Where (inside the project) | Notes |
|---|---|---|
| Config | `social-studio.toml` | `sclstdio config get/set` |
| Secrets | `.env` (0600) | model keys, the Buffer API key, the media bucket keys |
| Presets | `presets/<name>/preset.toml`, then `preset_paths`, then built-ins | `extends = "other"` to inherit |
| Library | `library/<date>-<slug>-<id>/` | `sclstdio library dir <folder>` moves it, inside the repo only |
| State | `.studio/`: `library.db`, `approval/`, `sessions/`, `engine/`, `cache/` | SQLite in WAL mode; engine, Chrome and npm cache included |

`init` writes a `.gitignore` that keeps `.env`, `.studio/` and `library/` out of git;
config and presets can be committed.

A finished session is trimmed to what explains it (task, brief, metadata, contact sheet, gzipped
logs); a failed one also keeps its composition. A successful `make --revise <id>` deletes the
previous version's files and sessions and keeps its row as history (`superseded`).

Video statuses: `review → posted` when approved in Buffer, or `review → approved → scheduled → posted`
when approved at the terminal, with `rejected`, `revision` (a human's notes, then
`make --revise <id>`), `superseded` and `failed`. The database enforces the legal transitions,
refuses `approved` without an approval for the exact file, allows `review → posted` only for a video
that went to Buffer as drafts, and keeps an append-only event log.

Board statuses: `review → approved`, `revision` (your notes, then `build --boards --from-board <id>` lays
it out again and the old board is replaced) or `dropped`. Boards live in their own table: deciding one
needs your terminal and signs nothing, and a video made from a board still needs its own approval.

## LLM backends

| Backend | Use | Auth |
|---|---|---|
| `claude` | Claude Code, headless | your Claude login (each session gets a private copy of only that login, and only while it outlives the session), `claude setup-token`, or `ANTHROPIC_API_KEY` |
| `opencode` | any provider OpenCode supports: xAI Grok, DeepSeek, OpenAI, Gemini, OpenRouter, Ollama ... | the provider's API key from the .env |
| `codex` | Codex CLI | `OPENAI_API_KEY`, or a private copy of your Codex login inside the sandbox |

`sclstdio model set opencode xai/grok-4` switches the default, and
`sclstdio model key XAI_API_KEY` stores a provider key in the .env. It prompts, so only a
human at a terminal can run it. Anthropic allows a Claude
subscription only through the unmodified `claude` binary, which is exactly how this tool uses it.

## Posting through Buffer

Instagram (as a Reel), Facebook (Reel when vertical and 90 s or less, else a video post) and X go
out through [Buffer's GraphQL API](https://developers.buffer.com) with a personal API key, on any
Buffer plan. Buffer has no upload endpoint and fetches the video from a URL when the post goes out,
so `post` first uploads the file to an S3-compatible bucket under its sha256, signed with SigV4, and
checks the public URL answers.

Railway buckets are private, so `deploy/media-proxy` is a small standard-library service that streams
only those video keys from a Railway bucket to a public URL (GET and HEAD, ranges passed through;
everything else is a 404). `deploy/media-proxy/setup.sh <project>` creates the bucket in the Railway
project its folder is linked to, points the proxy at it, and connects the project, passing the bucket
keys through environment variables only. A bucket that is public on its own (Cloudflare R2, AWS S3)
needs no proxy: run `sclstdio channel connect media` instead.

**Approval in Buffer** (the default once Buffer is connected; `publish.buffer.drafts = false` turns
it off). After a make, code uploads each new video and creates one Buffer draft (`saveToDraft`) for
every channel connected in Buffer: any network Buffer serves (Instagram, Facebook, X, LinkedIn,
TikTok, YouTube, Threads, Bluesky, Pinterest and the rest) and every account on it, so a channel you
connect later gets the next video. `publish.buffer.channels` narrows the list. Each draft carries that
network's caption (or the default one); a text over the network's limit is skipped.
Drafts publish nothing. In Buffer you approve a draft by scheduling or queueing it, edit it, or delete
it. `post sync` (the timer runs it) follows each draft: approved becomes scheduled, sent records the
post URL and marks the video posted, and a video whose drafts were all deleted is rejected.
Rejecting, revising or superseding a video here, or `post cancel ID`, takes its drafts back out of
Buffer. `post draft ID` sends a video that waits for review by hand, for example after a failed upload.

**Approval at the terminal.** Before anything leaves, `post` re-checks the approval signature,
re-hashes the file, checks that the post text is the one approved, and checks each network's length
limit. `post sync` reads back what Buffer did: the post URL, or Buffer's error. `post cancel ID`
removes queued posts from Buffer. Buffer is the only posting route; Buffer's API does not read or
reply to comments.

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
  videos, connect accounts, decide boards) need an interactive terminal, and approval also needs the
  passphrase.
  Never add the approval key to ssh-agent.
- `post` re-verifies the signature, re-hashes the file and checks the signed post text before every
  upload. The `publish.buffer` and `publish.media` settings are human-only, and no agent command
  schedules or sends a post. The maker agent never sees the Buffer key: drafts are created by the
  CLI after the agent's session has ended, and a draft goes out only when a human schedules it in
  Buffer.

## For agents

`sclstdio skill install --target claude` (or `opencode`, `codex`, a folder) installs the agent
guide. Agents use `sclstdio --json agent status|videos|topics|calendar|boards` and `build`; posting
and deciding boards stay with the human.
