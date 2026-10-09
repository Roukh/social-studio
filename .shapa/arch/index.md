---
id: index
type: reference
created: "2026-10-06T23:59:00Z"
consequence: 9
locus: output
summary: social-studio system diagram for agents - what it is, the eleven boxes, the edges between them, and the make, approve, post and sync flows.
scope: repo
status: active
---

# social-studio: system diagram

A local, stdlib-only Python 3.11+ CLI that makes short motion-graphics videos for social media, one isolated LLM harness session per video, keeps them in a SQLite library with their post text, and hands each new video to Buffer as drafts that a human approves there (or posts ones a human signed at the terminal, at the times the human picks). Brand-neutral tool; the operator's brand preset lives in the project folder.

## System

| Field | Value |
|---|---|
| Goal now | Made videos look the way the operator wants (memory M17, feature F1); target [[reference-leonabboud-showreel]]; decisions in [[reference-look-decisions]] |
| Goals | brand-true videos from presets; any LLM through the operator's harness; isolation per try; human approval agents cannot fake (in Buffer, or a signature at the terminal); only the human schedules and sends posts, through Buffer; usable by humans and agents |
| Non-goals | hosted SaaS or multi-user; engagement automation (likes, follows, comments, DMs); posting straight to each platform's API (Buffer does it); AI people |
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
| [[runner]] | `runner.py` | one jailed sandbox per video: prepare, storyteller then designer session, render, encode, QA, review, file, trim, purge |
| [[story]] | `story.py`, `pitch.py`, `store.py`, `data/store/`, `data/skills/storyteller/`, `data/skills/pitch-round/` | the pitch round (no operator brief), the storyteller session and the tagged SQLite reference store (techniques, film scenes, brand story posts) with per-beat retrieval |
| [[engine]] | `engine.py` | pinned HyperFrames and Chrome, bubblewrap argv, master render, delivery encode, loudness, poster and sheet |
| [[maker-kit]] | `data/house.md`, `data/session_prompt.md`, `data/skills/`, `data/tools/` | what the maker reads and runs: house rules, task, skills, sound synth |
| [[presets]] | `presets/example`, `presets/reel`, preset keys | brand, fonts, assets, video, content, agent, review, render, encode, publish settings |
| [[review]] | `review.py`, `sampler.py`, `data/anchors.json`, `data/review_prompt.md` | independent reviewer session, settled-frame sampler, verdict validation, rescore |
| [[qa]] | `qa.py`, `data/qa-probe.mjs`, `tests/fixtures/qa/` | report-only quality gates written to `qa.json` |
| [[schedule-publish]] | `posting.py`, `platforms/` | Buffer posting: drafts approved in Buffer, or pick, upload, createPost; sync, cancel, withdraw; account registry (buffer, media) |

## Edges

| From | To | What flows |
|---|---|---|
| cli | core | `Ctx` (project, config, `.env`, boundary), presets, `require_human` |
| cli | runner | `make` options (`MakeOpts`: count, parallel, preset, `--set`, format flags, effort, revise) |
| cli | library | review walk, approve (signs), reject, revise, `library dir` |
| cli | schedule-publish | drafts after `make`; `post` (draft, pick, schedule, list, sync, cancel), withdraw on reject or revise, `channel connect|test buffer|media`, `timer` (runs `post sync`) |
| core | runner | frozen `Preset`, `format_sets`, vetted `mcp_registry` |
| runner | maker-kit | fills `house.md` and `TASK.md`; mounts skills and `tools/` into the session |
| runner | story | a prepared session -> pitches.json and the checked pitch verdict (no operator brief), story.json, techniques.json and the designer brief for TASK.md; `store.db` in every session |
| runner | engine | `bwrap_argv`, `render_master`, `encode`, `poster_and_sheet` |
| runner | qa | rendered video, composition, `brief.json` -> `qa.json` and `videos.meta.qa` |
| runner | review | maker session plus video -> `verdict.json` |
| runner | library | `sessions` rows, video row as `review`, parent `superseded` |
| library | schedule-publish | approved videos with verifiable signatures; post and target rows |
| schedule-publish | Buffer, Railway bucket and media proxy (external) | GraphQL createPost/post/deletePost; signed S3 PUT to the bucket; public HEAD/GET through the proxy (`deploy/media-proxy`) |

## Flows

- **make:** cli -> core (load, validate) -> engine (ensure engine, skills, registry) -> runner per try: prepare session -> with no operator brief, the pitch round (pitcher, then a judge in its own folder; code checks both and picks the winner) -> storyteller in bubblewrap -> `story.json` checked -> store retrieval per beat -> designer in the same sandbox -> `video.json` -> master render -> encode -> poster and sheet -> qa -> optional reviewer -> library row `review` -> trim sessions; a revision purges its parent's files.
- **approve in Buffer (default, rule R14):** `make` ends -> the CLI uploads each new video -> a `drafts` post and one draft per connected channel -> GraphQL createPost with `saveToDraft` -> the operator schedules, edits or deletes the drafts in Buffer.
- **approve at the terminal:** `review` walk at a TTY shows each network's full post text -> `ssh-keygen -Y sign` over id, sha256 and post-text hash (one passphrase per batch) -> approvals row -> `approved`.
- **post a terminal-approved video:** `post` at a TTY -> pick an approved video, channels, a time -> re-verify signature, file and post text -> check text limits -> upload to the Railway bucket under its sha256 (read publicly through the media proxy) -> post and targets (`via buffer`) -> GraphQL createPost per channel -> Buffer publishes.
- **sync:** timer -> `post sync` -> under `post.lock`, ask Buffer about due targets and every draft -> record approved (scheduled), sent (URL), error, deleted (failed, or turned down for a draft) -> settle post and video (`review -> posted` for a drafts post).

## Elsewhere

- Work: `shapa ledger list` (features F1-F7). Standing rules: rule rows (operator rulings 1-19, and R14 for posting). Gotchas: issue rows tagged with a box name.
- Research (not loaded at start; search it): the motion course ([[motion-course]]), measurements ([[maker-measurements]]), the 2026-10-01 design research ([[harnesses-and-providers]], [[cli-conventions-and-isolation]], [[render-and-encoding]], [[social-platform-apis]]); posting through Buffer ([[buffer-api-coverage]]).
