---
id: runner
type: reference
created: "2026-10-06T23:59:00Z"
consequence: 9
locus: output
summary: Box runner - one jailed harness session per video (or per keyframe board) - session folder, backends and logins, prepare, rounds, render, QA, review, filing, trim and revision purge.
scope: repo
status: active
---

# Box: runner

Part of [[index]]. Turns `make` into videos: one isolated harness session per try, then the outside-the-jail steps.

| Field | Value |
|---|---|
| Purpose | Prepare a session, run claude, opencode or codex headless in bubblewrap, then render, encode, QA, review and file the video |
| Owned paths | `src/social_studio/runner.py` (about 1000 lines; split planned as `backends.py` and `prepare.py`, job J2), `src/social_studio/boards.py` (keyframe boards, the `board` command); `<project>/.studio/sessions/<id>/` |
| In | `MakeOpts` from [[cli]]; a frozen `Preset` and `format_sets` from [[core]]; templates, skills and tools from [[maker-kit]] |
| Out | `sessions` and `videos` rows in [[library]] (status `review`); library folder with `video.mp4`, poster, contact sheet, `qa.json`; calls to [[engine]], [[qa]], [[review]] |

## Session folder contract (`<project>/.studio/sessions/<id>/`)

| Path | Holds |
|---|---|
| `home/` | throwaway HOME: harness config, skills, the login copy, caches; `home/house.md` (house rules, never in `work/`) |
| `work/` | the agents' only writable folder: `TASK.md`, `preset.json`, `history.json`, `skills/`, `tools/` (`sampler.py`, `store.py`, everything in `data/tools/`), `store.db`, `registry` (link to the engine's pinned registry), `composition/`, `drafts/`, `evidence/`, `brief.json`, `video.json`; from the pitch round `PITCH.md`, `pitches.json`, `pitch-verdict.json`; from the storyteller `STORY.md`, `story-references.json`, `story.json`, `techniques.json`; on a revision `revision.json` and `scaffold.reference.html` |
| `judge/` | the pitch round's judge, only while it runs: its own `home/`, `work/` (`JUDGE.md`, `preset.json`, the pitches' own words) and `logs/`; the logs move to `logs/`, the folder is removed |
| `render/` | `master.mp4` (CRF 10, opaque), written by the runner, deleted after the encode; the maker's jail cannot write it |
| `logs/` | `pitch.*`, `judge.*`, `story.*`, `agent.*` (`.out` and `.err`, gzipped at trim); the session's cost is the sum of their `result` events |
| `<id>-review/` | the reviewer's sibling: `frames/`, `contact.jpg`, `verdict.json` |

Agent outputs: `brief.json` = `film`, `pillar`, `topic`, `angle`, `hook`, `bpm`, `shots[{start, end, start_state, change, end_state, text[], technique}]`, `cues[{t, kind (hit, whoosh, riser, tick, blip, voice), note}]`, `on_screen_text[]`, `cta` (schema in `data/session_prompt.md`). `video.json` = `title` (required), `description`, `pillar`, `topic`, `angle`, `captions{platform}`, `alt_text`, `hashtags[]`, `poster_at`, `rounds`, `scores{}` (the maker's own, never fed back). `revision.json` = `previous` (old `video.json` without scores or rounds), `reviewer` (issues, summary), `notes`.

## Keyframe boards (`boards.py`, J7, opt-in)

- `build --boards` (`boards.run_board`): the story stage as usual (pitch round, storyteller, retrieval), then the designer (role `agent`, its own limits) in boards mode: TASK.md from `data/board_prompt.md` plus the `key-poses` skill; it writes `brief.json`, lays out each shot's key pose static at the final layout in `composition/index.html` (one clip per shot, no tweens, ids kept across shots), and finishes with `board.json` (title, note).
- Code checks the shots (1 to 16, in order, no overlap, technique and text each, inside the runtime), snapshots each pose at its shot's midpoint with `hyperframes snapshot --at ... --no-end` inside bubblewrap with no network, and tiles them: an HTML sheet (`sheet_layout`, `sheet_html`) the engine's Chrome snapshots once into `sheet.png`, no wider or taller than 2000 px, each tile labelled with shot, beat, time, technique and on-screen text (type scaled with the tile, 15-28 px), the safe zone dashed over each tile at 9:16.
- Filing: `library/<id8>-board-<slug>-<id4>/` (`sheet.png`, `poses/NN.png`, `composition/`, `brief.json`, `story.json`, `techniques.json`, `story-references.json`, pitch files, `board.json`, `designer-brief.md`) and a `boards` row in review; no video, nothing to Buffer. The build stops.
- `build --from-board ID` (approved only; `--count` becomes 1): `prepare(board=...)` copies the board's composition over the scaffold, its story, techniques, shot list and `board.png`, and TASK.md says to keep every pose, id and line and animate between them (layout first, then motion); the story stage is skipped and the board's `designer-brief.md` is the brief; the board's frame (`meta.format`) applies unless the run sets its own; render, encode, QA, review and filing as usual, with `videos.board_id` and `meta.board`. A revision of that video keeps its `board_id`.
- `build --boards --from-board ID` (a board sent back for revision): the board session again with the old board staged and the operator's notes in TASK.md; the old board becomes superseded and its files and session are purged.
- `--revise` takes neither flag. Without `--boards` a build never stops (memory M42).

## Backends

| Harness | House rules channel | Notes |
|---|---|---|
| claude | `--append-system-prompt-file` | `--effort`, `--max-budget-usd`, `--disallowedTools WebFetch WebSearch` unless `allow_web`, `--strict-mcp-config` (with the registry's MCP file or none); login: a 0600 copy of only `claudeAiOauth`, only while the token outlives the timeout plus 5 min, else refuse (use Claude Code once, or `auth = "token"`) |
| codex | `$CODEX_HOME/AGENTS.md` | gets a copy of its `auth.json` |
| opencode | `instructions` in its config | provider keys from `PROVIDER_KEYS` |

## Invariants

- Every session runs in bubblewrap with a throwaway HOME; unsandboxed is human-only (rule R2). `engine.safe_root` never mounts a folder that is or contains home or the project.
- One sandbox, back-to-back sessions (F15): with no operator brief the pitcher and the judge ([[story]], roles `pitch` and `judge`), then the storyteller (role `story`), then the designer (role `agent`), in the same session folder with no operator step; the judge alone works in `judge/` with its own home, so it never sees the pitcher's reasoning. Each gets only its own skills in the harness config, and the session's cost is the sum of all. Limits are per role (`agent.*`, `story.*`, `pitch.*`, `judge.*`, `review.*`; `MAX_TURNS`, `TIMEOUT_MIN`).
- The library folder of a video made after a pitch round also holds `pitches.json` and `pitch-verdict.json`.
- Every designer session mounts the kit skills on top of the preset's: `KIT_ENGINE_SKILLS` (hyperframes-creative, motion-graphics, product-launch-video, hyperframes-registry) and `KIT_VENDOR_SKILLS` (launch-video, product-demo-video, short-form-video, explainer-video).
- Rounds are fixed (`agent.rounds`, 1-5); scores and rounds are never shown to a later session.
- Pillars rotate across a batch, least recently used first; the history the maker sees covers `content.no_repeat_days` (default 30) so angles do not repeat.
- A finished session keeps only an allowlist (`work/*.md`, `work/*.json`, `contact.jpg`, gzipped logs); a failed one also keeps `work/composition/`. Deletes go through `remove_within`.
- A successful revision marks the parent `superseded`, purges its library folder and sessions, keeps the row; cleanup errors only warn (rule R5).
- Draft renders inside the session run through the shell tool with `BASH_TIMEOUT_MS` 600000.
- The harness exits without `video.json` -> the session fails, its folder is kept, other tries continue. The render fails (a lint error under `--strict`) -> the session fails and the composition stays in `work/`.

## Rules and gotchas

- Rules: R1 (drive harnesses), R2 (isolation, keys), R5 (boundary), R6 (story and boards, both built by F15).
- Issues: I1 (preset overrides), I2 (makes start from a terminal, not an agent session), I6 (one root HTML).
- Ledger: J2 (split), F15 (J6 pitch round, J7 boards), F3 (network allowlist, log redaction), F5 (own API loop).
- Research: [[motion-quality-diagnosis]], [[harnesses-and-providers]].
