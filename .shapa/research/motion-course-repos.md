---
id: motion-course-repos
type: reference
created: "2026-10-03T00:00:00Z"
consequence: 7
locus: output
summary: Repo-by-repo notes on the 8 repos/docs linked from the Opus 5.5 motion-course article, with licence status, reusable patterns, dataset findings.
scope: repo
status: active
---

# Motion-course linked repos

Part of [[motion-course]]. The verbatim prompts, PDoom's `ANIMATION_GUIDE.md` and claude-animation-skill's `sound.md` are in [[motion-course-prompts]].

## Question

What do the 8 repos/docs the motion-course article links to contain: licence, version, reusable patterns, dataset findings?

## Method

Cloned or fetched each repo at its HEAD SHA on the dates below, read its LICENSE file (or lack of one) and key scripts/docs. For heygen-com/hyperframes, compared the pinned version (0.8.106) against the latest tag and changelog. For the two dataset repos, read their data files directly.

## Findings

### Summary table

| Repo | HEAD SHA | Licence | Stars | Purpose | Reusable pattern |
|---|---|---|---|---|---|
| JohnHeibel/PDoomVideo | `fa546a38` (09-25) | none | 1,716 | 156.6s watercolor music video, code-only | subagent-per-chapter; contact-sheet critique |
| JohnHeibel/ClaudeAnimationBase | `0ac8bf2b` (09-24) | MIT | 721 | p5.js/p5.brush starter, 31 emotions | GPU-probe for headless Chrome, GPU-less hosts |
| buildwithhanif/claude-animation-skill | `4ddb8c80` (09-23) | MIT | 27 | Node-canvas plugin: rigs, pens, sound | timeline-cue SFX synthesis; stable-seed determinism |
| heygen-com/hyperframes | `835e0c16` (10-03) | Apache-2.0 | 55,964 | HTML-to-MP4 render framework, skills | native audio mix/ducking + beat-grid skill, post-0.8.106 |
| remotion.dev AI skills | n/a (docs) | Free ≤3 employees; Company/Automator above | n/a | 12 Claude Code skills for Remotion | "Automators" ($0.01/render) = paid prompt-to-video model |
| WinterArc21/Battle-of-Austerlitz-Film | `86dae32d` (09-24) | none | 18 | 5-min WebGL historical film, offline TTS | distance/pan sound cues from scene state |
| guanmo-ai/awesome-ai-motion | `2ff3da3f` (10-02) | MIT (code/docs; prompts/media excluded) | 191 | Curated gallery, verbatim prompts | 5 prompts in [[motion-course-prompts]] |
| athemeroy/awesome-opus-5-5-videos | `497986b6` (10-02) | CC-BY-4.0 | 427 | 1,401-file classified corpus, 168 cases | "brief contagion" overlap method; brief template |

[[preproduction-options]] already excludes PDoomVideo, ClaudeAnimationBase and remotion-dev/skills from vendoring. PDoomVideo has **no licence at all** — stricter than "excluded" implies, nothing in it may be vendored or copied verbatim. ClaudeAnimationBase is MIT (reusable by licence; excluded anyway by prior decision).

### 1. JohnHeibel/PDoomVideo

HEAD `fa546a38092e75f2b079e6a86d6abc54dd525d17`, pushed 2026-09-25. No LICENSE file, no licence statement → **none**. 1,716 stars.

Pipeline: pure code render, no video model — p5.js + p5.brush painting, headless Chrome + ffmpeg. No audio generation; a found song is muxed in; no TTS, no SFX synthesis. Storyboard: Opus wrote `STORYBOARD.md` after a first pass, told to use P5 brushstrokes and make every scene transition into the next. Subagent pattern: `ANIMATION_GUIDE.md` was "written by Opus to brief the subagents it ran in parallel" — one subagent per chapter file, each an IIFE, forbidden from editing shared files. Determinism: every shot is a pure function of `t`; no `Math.random()`, only `hash(i)`/`jit(a)` (reseeded 12x/s for "boiling" ink). Critique: `node render.mjs --sheet=t1,t2,...` renders a contact sheet checked for first/last frame per shot, continuity, transitions, text clearance.

Reusable — `ANIMATION_GUIDE.md`@`fa546a38`: subagent-per-file ownership transfers directly to multi-scene renders; contact-sheet probing before a full render is the cheapest critique primitive here.

### 2. JohnHeibel/ClaudeAnimationBase

HEAD `0ac8bf2b31942376cb6b8c4074715595d512acd2`, pushed 2026-09-24. **MIT** (`LICENSE`, copyright 2026 John Heibel). 721 stars.

Pipeline: same p5.js/p5.brush stack as PDoomVideo, generalized. No audio pipeline (silent demo). `render.mjs` adds `--soft-gl` and `--gpu-angle=gl-egl|vulkan` for headless-Linux GPU rendering; `gpu_probe.mjs` reports which renderer a flag set actually produces — useful on a cloud worker with no dedicated GPU. README: "storyboards first, builds shot by shot, renders contact sheets to check its own work."

### 3. buildwithhanif/claude-animation-skill

HEAD `4ddb8c80fdec96dc9f55d4b9bdee60bde6f0134b`, pushed 2026-09-23. **MIT** (`LICENSE`, copyright Hanif / @hanifproduktif). 27 stars.

A Claude Code plugin at `plugins/claude-animation/skills/claude-animation/`. Pipeline: node-canvas (`@napi-rs/canvas`) + ffmpeg, no browser. `film.mjs` gives `run({...})` → `render / sheet / strip / verify`. Audio fully synthesized: `scripts/sound.mjs` synthesizes SFX (pop, thump, whoosh, riser, step, fall, chime...) from timeline cues (contact frame − ~0.03s, pitch jittered 0.9–1.3x), two-pass loudnorm to −16 LUFS/−1.5 dBTP; `scripts/music.mjs` makes an original ukulele bed; `scripts/chiptune.mjs` makes a game soundtrack with named sections. No video-model or TTS step; `references/sound.md` rejects a continuous "pencil-scratch" bed as tested and rejected. Hard rule "stable seeds": seeded from a name, never frame index, so re-renders are pixel-identical.

### 4. heygen-com/hyperframes

HEAD `835e0c16ec62681008682934c4751e630d9d5d7b` (2026-10-03). **Apache-2.0**. 55,964 stars.

**Version gap:** latest tag `v0.8.114` (2026-10-02) vs pinned `v0.8.106` — **8 releases behind**, all shipped in one day.

Changes since 0.8.106: **v0.8.107** — video sound stays on its clip by default; hosts can run Studio's agent tools on their own edit session. **v0.8.108–v0.8.110** ("Studio audio, 2–8/8") — full audio subsystem: audible preview (Web Audio groups/meters/carve), loudness normalize + voice-ducking with limiter report, speed/voice/crop presets + freeze frame, waveform strip + video-as-beat-source, A/V sync + repair, audio-gain hotkey. **v0.8.112** — a **motion-blur-streak skill** ("per-frame-driven form for elements riding a baked track"). **v0.8.113–v0.8.114** — bugfixes (GSAP `set()` alignment, rename scoping, keyframe isolation, <8ms/frame edits). No release mentions "spring." No storyboard-stage changes since 0.8.106.

**`npx hyperframes skills`** lists **21 published skills**: a core/router set plus `media-use`, `motion-graphics`, `music-to-video`, `general-video`, `faceless-explainer`, `product-launch-video`, `talking-head-recut`, `slideshow`, `pr-to-video`, `embedded-captions`, `figma`, `remotion-to-hyperframes`.

All audio/music capability is post-0.8.106: `hyperframes-audio` is mixing-only (fades, crossfade, gain, ducking, EQ/compressor/limiter/reverb via `data-fx-chain`, `<hf-audio-group>` submix buses) — no sourcing or generation. `media-use` ("Agent Media OS") resolves BGM/SFX/voice from a bundled catalog (19-file SFX library) or generates via TTS/music models when the catalog misses; voice TTS uses "HeyGen free-usage path; optional local Kokoro" — not ElevenLabs. `music-to-video` turns a track into a beat-synced video with zero required assets: a beat-grid analysis script, a storyboard-format doc, a `frame-worker` subagent, a motion-primitive library.

### 5. Remotion AI skills (remotion.dev/docs/ai/skills)

12 skills: `/remotion-best-practices` (umbrella) plus 11 task skills (create, markup, studio, render, maps, captions, saas, interactivity, docs, upgrade, multimedia). The skills page states no licence terms.

Remotion's licence (`remotion-dev/remotion/LICENSE.md`): two-tier. **Free** — individuals, non-profits, for-profit orgs with **up to 3 employees**, or anyone evaluating fit — commercial use allowed, but may not "copy or modify Remotion code for the purpose of selling, renting, licensing, relicensing, or sublicensing" a derivative. **Company License** required for 4+ employees, priced at remotion.pro/license: Company License (support + $250 Mux credits); **"Remotion for Automators"** — "$0.01 per render, $100/mo minimum" (10,000 renders/$100), for "companies launching applications and systems; such as video editors, prompt-to-video apps"; Creators ($25/mo/seat); Enterprise ($500+/mo). Automators is the licence social-studio would need if it rendered through Remotion at scale instead of HyperFrames.

### 6. WinterArc21/Battle-of-Austerlitz-Film

HEAD `86dae32d20f0a0f2395e7dc8938846fd51e355a6`, pushed 2026-09-24. No LICENSE file, no description → **none**. 18 stars.

Pipeline: 5:01 WebGL2 film on real SRTM terrain, narration via **offline Kokoro TTS** (`tools/tts.py`), synthesized score + sound design (`tools/mix.py`), sound cues derived from the picture (`web/events.js`: "each gun, volley, gallop, fire, with distance and pan," modeled at 343 m/s). Render via Playwright Chromium + ffmpeg, resumable chunks. No subagent pattern — fixed sequence `fetch_terrain.py → tts.py → export.mjs → mix.py → render.mjs`. Reusable: panned, distance-attenuated sound cues derived from scene/camera state.

### 7. guanmo-ai/awesome-ai-motion

HEAD `2ff3da3f72385c7944f53faac253f2a6f5bbf936`, pushed 2026-10-02. **MIT** for the repo's own code/docs (confirmed in `LICENSE`; GitHub's API reports `NOASSERTION` since the repo mixes code with third-party content). `THIRD_PARTY.md`: third-party videos, tracks, covers, **prompts**, and brand assets are excluded from the MIT grant; rights stay with the original X creators. 191 stars.

The prompt-library repo: per-case Markdown (`cases/<id>.{md,en.md}`) and plain-text prompts (`prompts/<id>.txt`), as a browsable gallery. Five verbatim prompts extracted into [[motion-course-prompts]]: @twoclipping (UI morph loop + a Hooklab ad), @verbove (MakerMap), @kloss_xyz (piano reel), @oozn (Steve Jobs), @achxvi (Pocketsflow/ElevenLabs). @pradeepXkapoor's "Pip" 19k-char brief is **not** reproduced — the catalog links to the source reply instead.

Correction: the task's original post-ID list for Tony Dinh/TypingMind, @twoclipping and @verbove didn't match these creators here — see [[motion-course-prompts]]/[[motion-course-showcase]] for the mapping found (e.g. `2102436464323661880` is @devteamdrew's post, not @twoclipping's).

### 8. athemeroy/awesome-opus-5-5-videos

HEAD `497986b6bcacf20a998f2dd271f818688bb2f756`, pushed 2026-10-02. **CC-BY-4.0**. 427 stars. The given slug redirects to the renamed repo `athemeroy/awesome-claude-5-5-videos`.

Dataset: 1,511 deduplicated candidate posts → 1,401 SHA-256-distinct classified MP4s → 1,119 labeled `yes`/`likely` for Opus involvement → 168 manually reviewed cases (Gemini 3.8 Flash classifier, text + 9 sampled frames). Leading domains: games/interactive (230), ads/launches (215). Leading styles: motion graphics/UI (350), 3D render (324). **152 of 168** curated cases disclose code-rendered production; only **8 of 168** used an external video model (Seedance/Kling). `docs/production-brief.md` ships a copyable brief template (goal/delivery, rights, shots, acceptance gates, cost/disclosure).

**"Brief contagion" finding** (the article's term; repo calls it "prompt propagation"/"token overlap"): `data/prompt-overlap.json` records @anjmaxx's later 20s MV commission (public prompt, 5,594 chars/1,015 words) sharing **87.0%** of its unique five-word sequences with @donaldjewkes's earlier 12-hour MV commission (public prompt, 9,554 chars/1,750 words, posted first). Repo caveat: "shared wording alone cannot establish who read or copied what, or which steps were executed."

Length/effort: five selected public commissions span **172-17,664 characters**; @donaldjewkes's prompt supplies a reference video, song, source code and a project directory, undercutting "one short prompt." @mablesjoseph's watercolor short: 163 model calls, ~6h45m elapsed, ~1.5h human time, 62.7M tokens (96% cache reads), ~$34 API-equivalent. Median preview: 39.2s all files vs 52.4s curated; explainers longest at 102.3s of seven paths.

## Sources

github.com/{JohnHeibel/PDoomVideo, JohnHeibel/ClaudeAnimationBase, buildwithhanif/claude-animation-skill, heygen-com/hyperframes, WinterArc21/Battle-of-Austerlitz-Film, guanmo-ai/awesome-ai-motion, athemeroy/awesome-opus-5-5-videos} (HEAD SHAs above); remotion.dev/docs/ai/skills. [[preproduction-options]], [[motion-course]], [[motion-course-article]], [[motion-course-prompts]], [[motion-course-showcase]].

## Date

Gathered 2026-10-03; condensed 2026-10-06 for the format 4 wiki.
