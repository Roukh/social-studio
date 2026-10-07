---
id: reference-look-decisions
type: reference
created: "2026-10-06T23:30:00Z"
consequence: 9
locus: output
summary: Video quality decision record - the 13 reference-look design decisions (ruling 18) with their basis, options weighed, and what iteration 1 built.
scope: repo
status: active
---

# Reference-look decisions (video quality)

The decision record for making videos look like [[reference-leonabboud-showreel]]. Under ruling 18 (rule R13, calibrate-by-outcome) the agent takes these design decisions, records them here with their basis, and revises them from the operator's feedback on rendered videos. Any agent working on video quality reads the decisions table first and appends to it.

## Question

What has to change in social-studio for a make to look like the reference showreel (15 s, 16:9, 60 fps, synthesized bed, seven techniques on a beat grid), and which option was taken for each design choice?

## Method

- 2026-10-06: every claim checked against `src/` and the pinned engine `E` = `<project>/.studio/engine/hyperframes-0.8.106/`.
- Options gathered per area, with the wide candidate sweep in [[mcp-skill-candidates]] and the course material in [[motion-course]].
- The operator handed the 13 open decisions back (ruling 18). Each was decided by what leading practitioners do ([[motion-course-showcase]], [[motion-canon-research]]).
- Iteration 1 was built the same day and verified with the real 0.8.106 engine.

## Findings

### Decisions, iteration 1 (2026-10-06)

The operator handed the 13 design decisions back (ruling 18). Each was decided by what leading practitioners do, recorded here with its basis, and is revised from feedback on the rendered video.

| # | Decision | Taken | Basis |
|---|---|---|---|
| 1 | Rules | The render contract stays law. Frame 0, the reading-time hold, the text floor and the blueprint-per-shot rule become defaults with reasons (house.md). The safe-zone note shows only at 9:16. The redirect is gone. The anchors no longer demand a subject at frame 0. | ruling 16; every top reel breaks the four rules |
| 2 | Look source | A built-in `reel` preset: the reference palette, three OFL faces (Inter variable as "Reel Sans", Instrument Serif, JetBrains Mono), and a `reel-look` skill written in our own words | the reference; CODE 7, "grammar, never content" |
| 3 | Sound placement | `<audio id>` in the composition, mixed by the engine; the runner normalizes to -14 LUFS | how the course's reels and HyperFrames do it |
| 4 | Sources and voice | `tools/sound.mjs` synthesizes the bed and effects in code, the engine's 19 Pixabay files are on hand, and no voice for reel makes | the reference is a synthesized bed with no voice; Rob Hallam, twoclipping and Voxyz synthesize in the same run |
| 5 | Skills | 11 vendored skills on the reel preset, plus the engine's animation, audio, media-use, music-to-video and product-launch-video skills, plus motion-canon and the doctrine | ruling 19 |
| 6 | Key entry | Unchanged (MCP config only); iteration 1 needs no key | nothing keyed in use |
| 7 | Blur | The engine's velocity blur helper (`attachMotionBlur` in music-to-video), named in `reel-look` | works at 0.8.106, at no render cost |
| 8 | 16:9 text floor | Scaled from the short side: 30 px | broadcast and phone-landscape viewing |
| 9 | Effort and budget | The reel preset runs at xhigh, 3 rounds, 90 min and 300 turns | every viral one-shot ran at xhigh or max |
| 10 | CLI against agent | Flags: `--aspect`, `--fps`, `--duration`, `--sound`, `--rounds`; the agent picks BPM, shots, techniques and cues | ruling 15 |
| 11 | Reference import | Deferred. The look comes in as a written style skill; no third-party frames are shipped | rights |
| 12 | Benchmark | One make, judged by the operator in the library | ruling 18 |
| 13 | Engine upgrade | Deferred. 0.8.106 already renders everything the reel needs (verified below) | fewer moving parts |

New decisions and revisions go below this table as dated rows: `| # | Decision | Taken | Basis (with the operator's correction, quoted) |`.

### Operator outcomes (calibration log)

| Date | Video | Operator, verbatim | Filed as |
|---|---|---|---|
| 2026-10-06 | video 4, the first reel (15 s, 143 BPM, about 1.6 s per scene) | "Its a major improvement. MAJOR. its a little too fast, can be slowed to liek 20-25s." | reel preset `video.duration` [20, 25] and `video.pacing`; reel-look shot grammar retimed to 120 BPM, about 2.5 s a scene, a hold on the last kinetic word; motion-canon default scene length 2.5 s. The ghobz preset gets the same pace. |

| 2026-10-06 | the ghobz preset, before its first make | "bg music and sound effects" | ghobz sound = music bed + effects, no voice |
| 2026-10-06 | video 4 again | "The test video in the library was about social-studio with a seamingly random theme and story." | ghobz makes take their story from a ghobz pillar; first test `--pillar the-path` |
| 2026-10-06 | the ghobz preset | "I care about the design. Ui should match the theme of ghobz.com, same components, fonts, styles, vivid cards, gradients, blurs, spacing, grids, etc" | the ghobz-ui kit ([[brand-site-design-kit]]) |

The operator called the reel as a whole a major improvement and flagged only its speed, so everything else from iteration 1 stays.

How the ghobz-ui kit turns the brand's own site into the video's design system: [[brand-site-design-kit]].

### Options that were weighed

| # | Options considered |
|---|---|
| 1 | Per rule (frame 0, reading-time hold 0.5 s + 0.3 s per word, safe zone, 11 pt text floor, motion-doctrine redirect, one blueprint per shot, the preset's three-objects rule): drop, move into a guidance skill, keep per format, or `make --rules strict|loose`; the per-shot `blueprint` field becomes a free-text `technique` |
| 2 | The operator's brand in the reference's grammar, or a built-in reel look |
| 3 | Agent places `<audio>` in the composition; runner mixes after the render (`adelay`, `amix`, `sidechaincompress`) from `brief.json` cues; or both |
| 4 | Code synthesis (claude-animation-skill `sound.mjs`/`music.mjs`, MIT), the engine catalog, ElevenLabs REST (ruling 9), local Kokoro via `hyperframes tts`, keyed services in [[mcp-skill-candidates]] |
| 5 | Engine skills on disk, outside skills (DirectorSKILL, anthropics canvas/frontend-design, impeccable, emil-design-eng, writing-beats/shape, athemeroy production brief), MCP servers from the sweep |
| 6 | Keys through the session's MCP config only (the agent can read it), env passthrough of declared names for REST from Bash, or a runner-side proxy that adds keys outside the jail. OAuth-only servers cannot run in the jail |
| 7 | Velocity CSS blur in the composition; the engine's `MotionBlurAccumulator` (no CLI flag at 0.8.106); subframes plus `tmix` (about N times the render time); `motion-blur-streak` from 0.8.112 |
| 8 | 30 px (short side), 54 px (long side), or none |
| 9 | xhigh default, max default, or per run only |
| 10 | Which of aspect, fps, duration, reference, sound, effort, rounds, blur and brief are flags |
| 11 | A human `ref add URL|FILE` outside the jail (frames, 2 and 6 fps sheets, spectrogram, onsets into `<project>/refs/<id>/`), an in-session `style_guide.md` from read-only `refs/`, or both |
| 12 | Three makes per arm against today's pipeline forced to 16:9/60 fps, scored in code against the reference's properties plus a side-by-side sheet and a re-measured noise floor |
| 13 | Upgrade before the sound and blur work, or alongside it |

### Engine and code facts, verified 2026-10-06

1. The pinned 0.8.106 engine already ships `music-to-video` (with `scripts/analyze-beatgrid.py`), `media-use` (19 Pixabay SFX, commercial use without attribution per its `CREDITS.md`; TTS references for Kokoro, HeyGen, ElevenLabs, Gemini), `hyperframes-audio` (the mixer) and `hyperframes-animation/adapters/three.md`. The CLI ships `hyperframes tts` (local Kokoro). Sound and 3D do not wait for the upgrade.
2. 0.8.106 renders `<audio>` elements; one without an `id` renders silent (`E/skills/hyperframes-core/SKILL.md:65`), so ids are the contract. The encode normalizes any audio to -14 LUFS in two passes.
3. Motion blur exists inside the engine (`MotionBlurAccumulator`, `resolveMotionBlurPlan`, `job.config.motionBlur`) but 0.8.106's CLI has no flag for it. `music-to-video` ships the velocity CSS helper `attachMotionBlur` (`templates/logo-split-lockup-pulse/index.html:21-28`).
4. The jail already has the network: `bwrap_argv` defaults to `network=True` (`--share-net`). "No web" only disallows WebFetch and WebSearch. An HTTP MCP server or `curl` reaches the internet.
5. Three.js must be vendored: the adapter imports it from cdn.jsdelivr.net and house rules forbid remote URLs. Built as `render.esm` with an import map.
6. The reviewer encoded the rules being loosened (anchors, review prompt); loosening house.md alone would have scored the reference look down. Fixed in iteration 1.
7. The text floor `round(11 x width / 393)` assumed a portrait phone (54 px at 1920 wide). Now scaled from the short side (decision 8).
8. The operator's brand preset mounts `hyperframes-animation`, `motion-graphics` and `hyperframes-creative`, which the old prompt told the maker to skip. The redirect is gone (decision 1).
9. librosa is not installed on the host; `analyze-beatgrid.py` needs librosa, numpy and soundfile. The reel builds its beat grid by construction instead (`reel-kit.js`).
10. Ruling 10 (accent italic) is not applied to the operator's brand preset; it still embeds Sentient. The reel preset uses Instrument Serif.

### The reference against the pipeline before iteration 1

| Property | Reference | Before 2026-10-06 |
|---|---|---|
| Format | 1920x1080, 60 fps, 15.06 s | 1080x1920, 30 fps, 10-18 s |
| Audio | synthesized bed plus SFX, -13.9 LUFS, LRA 1.1, no voice | no audio stream |
| Grid | 46 onsets, 0.209 s median; all 11 scene changes on an onset | a time grid only |
| Techniques | 7 in 15 s: type, Three.js voxels, kinetic words, data, particles, UI, morph | one of 13 blueprints per shot |
| Pace and opening | words hold one beat (~0.42 s); opens near-black with a dot | hold 0.5 s + 0.3 s/word; frame 0 must show the subject |
| HUD | corner marks, labels, scene counter, timecode, ~18-20 px mono, ~4 % from the edges | safe zone; 30 or 54 px floor |
| Type and palette | heavy neo-grotesk with animated weight, italic serif, wide mono; ink #070711, orange #FD4920, cream #F0EFE6, blue #2E49F0 | static brand faces and colours |

### Built in iteration 1 (`src/social_studio/`)

- Format flags: `core.format_sets` adds `FORMATS`, `TITLE_SAFE`, `SOUNDS`; `cli.py` exposes them.
- `render.esm` loads ES modules by bare name through an import map, vendored side by side.
- Variable fonts declare a weight range such as `"100 900"`.
- Files inside built-in presets pass the boundary check; secrets never do. Every file in `data/tools/` is copied into the session.
- `house.md`, `session_prompt.md`, `anchors.json` and `review_prompt.md` rewritten.
- QA: the audio gate reads `brief.cues`; a loudness gate checks -14 +/- 1 LUFS; text floors scale from the short side.
- `data/tools/sound.mjs`: a deterministic Node synth, about 0.3 s for 15 s of audio.
- `data/skills/motion-canon` (from [[motion-canon-research]]); `data/skills/vendor/` with 16 packs (28 skills) pinned in `skills.lock.json`, mounted by name through `agent.package_skills`.
- `presets/reel/`: fonts, `reel-kit.js` (springs, seeded noise, timecode, beat grid), `skills/reel-look`.
- `tests/test_reel.py`, 13 tests; 102 passed.

**Verified with the real engine.** A prepared reel session with one test shot passed `--strict` at 1920x1080, 60 fps: the weight wave runs 100 to 900; Three.js voxels render under software GL (llvmpipe); the reel-kit timecode runs in Reel Mono; the soundtrack mixes into AAC; the delivery encode reads -14.6 LUFS; capture takes about 34 ms per frame (about 30 s for a 15 s film). Gotcha found: issue I3 (Chrome cleanup).

### Not built (ledger)

- Feature F1: runner split (J2), doctor hash check for vendored skills (J3), HyperFrames 0.8.114 (J4), gate-triggered retry (J5), filing the operator's corrections (J1).
- Feature F2: story and board stages (rulings 6-7).
- Feature F3: network allowlist and log redaction for keys (ruling 17).
- Deferred by decision: reference import (11), a scored benchmark (12).

## Sources

- [[reference-leonabboud-showreel]]; local copy `.local/refs/leonabboud-2103576084499358051/` (gitignored).
- [[motion-course]], [[motion-course-code]], [[motion-course-code-2]], [[motion-course-showcase]], [[motion-course-repos]].
- [[mcp-skill-candidates]], [[motion-canon-research]].
- The pinned engine at `<project>/.studio/engine/hyperframes-0.8.106/`.

## Date

Verified and decided 2026-10-06; iteration 1 built 2026-10-06. Folded from the former `arch/reference-look-plan.md` (its sections 1-8) on 2026-10-06.
