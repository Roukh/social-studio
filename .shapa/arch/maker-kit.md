---
id: maker-kit
type: reference
created: "2026-10-06T23:59:00Z"
consequence: 9
locus: output
summary: Box maker-kit - what the maker reads and runs - house rules, the task template, shipped and vendored skills with their lock, and session tools like sound.mjs.
scope: repo
status: active
---

# Box: maker-kit

Part of [[index]]. The prompts, skills and tools that decide how a made video looks. The main lever for feature F1; design choices here follow [[reference-look-decisions]].

| Field | Value |
|---|---|
| Purpose | Tell the maker how to work (house rules, task) and give it skills and tools inside the session |
| Owned paths | `data/house.md` (house rules template), `data/session_prompt.md` (TASK.md template with the `brief.json` and `video.json` schemas), `data/SKILL.md` (agent guide to the CLI), `data/skills/motion-doctrine/` (13 blueprints, Apache-2.0 NOTICE), `data/skills/motion-canon/` (non-AI canon), `data/skills/technique-library/` (principles, one entry per technique, the reel's composition as the worked example), `data/kit/motion-kit.js` (helpers in every composition as `window.kit`), `data/skills/vendor/` (20 packs, 43 skills, `skills.lock.json`, `NOTICE.md`), `data/tools/sound.mjs` |
| In | preset values filled into `{{...}}` by [[runner]] (`min_text_px`, `width`, `height`, `format_note`, `motion_rule`, `end_card_pct`, `rules`, `skill_list`, `brief_block`, `revision_block`); `agent.engine_skills`, `agent.package_skills`, `agent.skills` |
| Out | `home/house.md` (system channel), `work/TASK.md`, `work/skills/*`, `work/tools/*` in each session |

## Mounting order (`runner._skills`)

1. Shipped: `motion-doctrine`, `motion-canon`, `technique-library` (names reserved, with `storyteller`, which only the storyteller session mounts; see [[story]]).
2. Vendored skills named in `agent.package_skills`, then the kit's `KIT_VENDOR_SKILLS` (launch-video, product-demo-video, short-form-video, explainer-video), from `skills.lock.json`.
3. Engine skills from the pinned tag: `agent.engine_skills` (default `hyperframes-core`, `hyperframes-cli`, `hyperframes-animation`, `hyperframes-audio`, `media-use`), then the kit's `KIT_ENGINE_SKILLS` (hyperframes-creative, motion-graphics, product-launch-video, hyperframes-registry; the registry is the engine's pinned copy at `work/registry`).
4. Preset skills in `agent.skills` (inline text or a folder inside the repo; never `.env` files).

Vendoring: `scripts/vendor_skills.py OWNER/REPO SHA NAME --licence MIT --what ...` copies every SKILL.md folder under the repo's `skills/` at a full commit sha with its licence, and writes the lock entry with the tree hash the tests check. F15 added the iart-ai ad, tiktok, ecommerce and explainer packs (15 skills, MIT). The claudedesignskills siblings stay unvendored: each targets a library the engine does not load (anime.js, PixiJS, R3F, Babylon...).

## Invariants

- House rules state only the render contract as law: every frame a pure function of time on the paused GSAP timeline `tl` (or the time HyperFrames hands a canvas), no `Date`, unseeded `Math.random`, timers, rAF loops, CSS transitions or remote URLs; only files in `composition/`; sound as `<audio id>` on the timeline; only declared font families (rule R12).
- Everything else is a default with its reason: the text floor (`min_text_px`, 11 pt scaled from the frame's short side), first frames say something, no move twice in a row, the end card at most `end_card_max`. The safe-zone note shows only at 9:16 (decision 1).
- The maker works alone: every command in TASK.md is pre-approved; it never asks.
- Sound: `brief.json` lists `cues`; `tools/sound.mjs` synthesizes bed and effects in code (deterministic, ~0.3 s for 15 s); `skills/media-use/audio/assets/sfx/` has 19 Pixabay effects; `hyperframes tts` speaks offline. An `<audio>` without an `id` renders silent (rule R8).
- Vendored skills: each pack pinned to a commit with licence and `tree_sha256` in `skills.lock.json`; no-licence sources are never vendored (rule R7). Doctor does not verify the hashes yet (job J3).
- Templates stay brand-neutral; brand values come only from the preset.
- The technique library (operator, 2026-10-07): every film picks its set of techniques and shots from it, applies its `principles.md`, names each shot's technique by slug in `brief.json`, and lists the set in `video.json` `techniques`. `history.json` carries recent sets so the next film differs. A brand gives colours and fonts; the library gives everything else.
  - Since F15 the index is the reference store ([[story]]): each recipe in `techniques/` has a `technique` row, and scenes extracted from reference films sit beside them; the designer gets per-beat candidates in `techniques.json` and searches with `tools/store.py`.
  - Each recipe has a slug, its family, what it looks like, how long it wants, how to build it, its sound and its source; the first fourteen point into the worked example, `examples/reel-2026-10-06.html`.
  - A technique the operator rejects is removed.

## Rules and open work

- Rules: R7 (vendored skills), R8 (sound), R12 (skills over rules), R13 (calibrate by outcome).
- Ledger: J1 (file the operator's corrections), J3 (doctor hash check).
- Research: [[reference-look-decisions]], [[motion-canon-research]], [[motion-course]], [[mcp-skill-candidates]], [[motion-quality-diagnosis]].
