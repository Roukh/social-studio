---
id: presets
type: reference
created: "2026-10-06T23:59:00Z"
consequence: 8
locus: output
summary: Box presets - the built-in example and reel presets, the operator's brand preset outside the repo, and every preset key the code reads, by role.
scope: repo
status: active
---

# Box: presets

Part of [[index]]. A preset sets everything about a video: brand, fonts, assets, format, content rules, the maker and reviewer, the engine and the encode.

| Field | Value |
|---|---|
| Purpose | Hold brand and run settings as data, so the tool stays brand-neutral |
| Owned paths | `src/social_studio/presets/example/preset.toml`; `src/social_studio/presets/reel/` (`preset.toml`, `assets/fonts/` with OFL texts, `assets/reel-kit.js`, `skills/reel-look/SKILL.md`) |
| In | loaded and validated by [[core]] (`extends`, `--set`, `format_sets`) |
| Out | the frozen `preset.json` in each session; values filled into [[maker-kit]] templates; keys read by [[runner]], [[engine]], [[review]], [[qa]], [[schedule-publish]] |

## Presets

| Preset | Where | Settings |
|---|---|---|
| `example` | built in | neutral starter: black on white, one accent, 9:16 1080x1920, 30 fps, 10-20 s, Sonnet maker, 2 rounds, reviewer off |
| `reel` | built in | the reference-look preset (decision 2): 16:9 1920x1080, 60 fps, 14-16 s, `sound = "bed+sfx"`, ink/cream/signal/blue palette, Reel Sans (Inter variable 100-900), Reel Serif (Instrument Serif), Reel Mono (JetBrains Mono variable); `reel-kit.js` (springs, seeded noise, timecode, beat grid); three@0.181.2 through `render.esm`; Opus at xhigh, 3 rounds, 90 min, 300 turns; 11 vendored skills plus `music-to-video` and `product-launch-video`; Sonnet reviewer on |
| the operator's brand preset | the operator's project folder, outside this repo | the operator's file; agents do not write it. Still embeds Sentient (rule R9) |

## Keys the code reads

- `preset.*`; `brand.{name, colors, fonts, css, rules}`; fonts as files with a weight or a range (`"100 900"`) and optional style.
- `video.{width, height, fps, duration, background, safe_zone, end_card_max, pacing, motion, sound}`. `motion` is a signature that wins over the doctrine.
- `content.{pillars, rules, banned, exact_lines, cta, no_repeat_days, title, subject, topic, pillar, notes, language}`.
- `assets.files`; `render.{engine, version, libraries, vendor, esm, scripts}`; `encode.{crf, preset, tune, maxrate, bufsize, audio_bitrate, loudness}`.
- `agent.{backend, model, effort, rounds, timeout_min, max_turns, allow_web, max_budget_usd, engine_skills, package_skills, skills, mcp, plugins}`.
- `review.{independent, backend, model, effort, criteria, min_score, timeout_min, max_turns, allow_web, max_budget_usd}`; each role reads only its own keys (`review.max_rounds` is only a fallback for `agent.rounds`).
- `story.{enabled, pitch, backend, model, effort, timeout_min, max_turns, allow_web, max_budget_usd, goal, product}`; `story.pitch` (default true) runs the pitch round when no operator brief is set. The pitch round's roles read only their limits, `pitch.{effort, timeout_min, max_turns, allow_web, max_budget_usd}` and the same under `judge.`, and use the storyteller's backend and model.
- `publish.{platforms, link, link_platforms, bio_note}`.

## Invariants

- Fonts ship as files under a family the preset owns; never Helvetica, Arial or another aliased name (issue I4). Accent italics are OFL (rule R9).
- `render.version` is an exact pin; the engine, Chrome and skills follow it.
- Guarded keys (`agent.mcp`, `agent.plugins`, `agent.skills`, `agent.engine_skills`, `assets`, `brand.fonts`, `render`) come only from presets in the presets folders or from a human (issue I1).
- Format details follow the run's `--aspect` (rule R11); the reel's own safe zone is 5 % title-safe.
- Reel content is fictional sample data: never a real client, brand, product or person; the reference's grammar, never its words or marks.

## Rules and open work

- Rules: R9 (accent italic), R11 (format per run), R13 (calibrate by outcome: corrections may land as preset changes).
- Ledger: J1 (the operator's corrections), J4 (`render.version` to 0.8.114).
- Research: [[reference-look-decisions]], [[reference-leonabboud-showreel]].
