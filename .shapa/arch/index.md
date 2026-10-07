---
id: index
type: reference
created: "2026-10-06T23:59:00Z"
consequence: 9
locus: output
summary: social-studio system diagram for agents - what it is, the ten boxes, the edges between them, and the make, approve, schedule and post flows.
scope: repo
status: active
---

# social-studio: system diagram

A local, stdlib-only Python 3.11+ CLI that makes short motion-graphics videos for social media, one isolated LLM harness session per video, keeps them in a SQLite library, and posts the ones a human approved on the dates someone set. Brand-neutral tool; the operator's brand preset lives in the project folder.

## System

| Field | Value |
|---|---|
| Goal now | Made videos look the way the operator wants (memory M17, feature F1); target [[reference-leonabboud-showreel]]; decisions in [[reference-look-decisions]] |
| Goals | brand-true videos from presets; any LLM through the operator's harness; isolation per try; unforgeable human approval; people or agents pick dates, code picks videos; usable by humans and agents |
| Non-goals | hosted SaaS or multi-user; engagement automation (likes, follows, comments, DMs); API posting where the platform forbids it (LinkedIn, unaudited TikTok); AI people |
| Code | `src/social_studio/` (package), `tests/`, `pyproject.toml` (no runtime dependencies, hatchling build). Python over Rust: faster to build, less code, fewer files; Rust's smaller binary is dwarfed by the renderer's Node and Chrome |
| Run | `uv run social-studio ...` or `.venv/bin/social-studio ...` (editable install in `.venv`); `uv tool install --editable .` puts it on PATH |
| Tests | `uv run pytest` (basetemp `.dev/pytest`); QA calibration fixtures in `tests/fixtures/qa/` need the engine |
| Operator project | a folder outside this repo (`social-studio config path`, `$SOCIAL_STUDIO_PROJECT`): `social-studio.toml`, `.env`, the operator's brand preset, `library/`, `.studio/` (rule R5) |
| Engine | HyperFrames 0.8.106 pinned per preset, with its own Chrome, GSAP 3.14.2 and skills, under `<project>/.studio/engine` |
| Agent limits | makes cannot start from an agent session (issue I2); writes stop at the git work tree (R5) |

## Boxes

| Box | Owns | Job |
|---|---|---|
| [[cli]] | `cli.py`, `__main__.py`, `data/SKILL.md` | argparse noun-verb tree, `--json`, exit codes, human gates, doctor, timer, completion |
| [[core]] | `core.py`, `mcp.toml` contract | project discovery, config, `.env`, write boundary, presets and `--set`, validation, formats, MCP registry |
| [[library]] | `db.py`, `approval.py` | SQLite schema, trigger-enforced statuses, append-only events, signed approval |
| [[runner]] | `runner.py` | one jailed harness session per video: prepare, run, render, encode, QA, review, file, trim, purge |
| [[engine]] | `engine.py` | pinned HyperFrames and Chrome, bubblewrap argv, master render, delivery encode, loudness, poster and sheet |
| [[maker-kit]] | `data/house.md`, `data/session_prompt.md`, `data/skills/`, `data/tools/` | what the maker reads and runs: house rules, task, skills, sound synth |
| [[presets]] | `presets/example`, `presets/reel`, preset keys | brand, fonts, assets, video, content, agent, review, render, encode, publish settings |
| [[review]] | `review.py`, `sampler.py`, `data/anchors.json`, `data/review_prompt.md` | independent reviewer session, settled-frame sampler, verdict validation, rescore |
| [[qa]] | `qa.py`, `data/qa-probe.mjs`, `tests/fixtures/qa/` | report-only quality gates written to `qa.json` |
| [[schedule-publish]] | `posting.py`, `schedule.py`, `publish.py`, `platforms/` | Buffer posting (pick, upload, createPost, sync); calendar slots, fill, `post run`, platform adapters and drafts |

## Edges

| From | To | What flows |
|---|---|---|
| cli | core | `Ctx` (project, config, `.env`, boundary), presets, `require_human` |
| cli | runner | `make` options (`MakeOpts`: count, parallel, preset, `--set`, format flags, effort, revise) |
| cli | library | review walk, approve (signs), reject, revise, `library dir` |
| cli | schedule-publish | `post` (pick, schedule, list, sync, cancel), `schedule add|list|cancel`, `post run`, `channel connect|test`, `timer` |
| core | runner | frozen `Preset`, `format_sets`, vetted `mcp_registry` |
| runner | maker-kit | fills `house.md` and `TASK.md`; mounts skills and `tools/` into the session |
| runner | engine | `bwrap_argv`, `render_master`, `encode`, `poster_and_sheet` |
| runner | qa | rendered video, composition, `brief.json` -> `qa.json` and `videos.meta.qa` |
| runner | review | maker session plus video -> `verdict.json` |
| runner | library | `sessions` rows, video row as `review`, parent `superseded` |
| library | schedule-publish | approved videos with verifiable signatures; post and target rows |
| schedule-publish | platforms (external) | uploads, captions, platform post ids |
| schedule-publish | Buffer, media bucket (external) | GraphQL createPost/post/deletePost; signed S3 PUT and public HEAD |

## Flows

- **make:** cli -> core (load, validate) -> engine (ensure engine, skills) -> runner per try: prepare session -> harness in bubblewrap -> `video.json` -> master render -> encode -> poster and sheet -> qa -> optional reviewer -> library row `review` -> trim sessions; a revision purges its parent's files.
- **approve:** `review` walk at a TTY shows each network's full post text -> `ssh-keygen -Y sign` over id, sha256 and post-text hash (one passphrase per batch) -> approvals row -> `approved` -> fill open slots.
- **post through Buffer (the route in use, rule R14):** `post` at a TTY -> pick an approved video, channels, a time -> re-verify signature, file and post text -> check text limits -> upload to the public bucket under its sha256 -> post and targets (`via buffer`) -> GraphQL createPost per channel -> Buffer publishes -> `post sync` (or the timer) records sent, error or deleted and settles post and video.
- **schedule (direct route):** `schedule add DATE TIME` -> reject past and clashing slots -> post and targets -> fill with the oldest approved video whose signature verifies and file re-hashes.
- **post (direct route):** timer -> `post run` -> lock, fill, sweep past-due to `missed` -> per due direct target: re-verify, adapter call, record or back off -> settle post and video -> then a Buffer sync.

## Elsewhere

- Work: `shapa ledger list` (features F1-F5). Standing rules: rows R1-R13 (operator rulings 1-19). Gotchas: issue rows tagged with a box name.
- Research (not loaded at start; search it): the motion course ([[motion-course]]), measurements ([[maker-measurements]]), the 2026-10-01 design research ([[harnesses-and-providers]], [[cli-conventions-and-isolation]], [[render-and-encoding]], [[social-platform-apis]]).
