---
id: claude-motion-pipelines
type: reference
created: "2026-10-09T17:50:00Z"
consequence: 7
locus: output
summary: charliehills, Barty-Bart, whaleyxbt and shneural pipelines - stack, pace, density, colour, licence - against our slow, pale, one-screen video 8.
scope: repo
status: active
---

# Claude-made motion pipelines: charliehills, Barty-Bart, whaleyxbt, shneural (2026-10-09)

## Question

The operator found video 8 "too pale, on one screen, not enough happening and a lil slow"
([[kinetic-type-sound-and-pace]]). How do these four pipelines get pace, density, colour and several scenes into a
film? What is their exact stack, and what can we reuse, under which licence? Their sound practice is in
[[film-sound-practice]].

## Method

- One helper session per source, as in [[film-sound-practice]]. The repos were shallow-cloned into session scratch
  and their actual files read, not just the READMEs.
- shneural's film was downloaded from prompt-motion and measured. Its numbers below come from the baseline method
  (`measure.json`).

## Findings

### charliehills: "Claude Code motion graphics and video with Opus 5.5" (Substack, 2026-09-27)

- **Pipeline**:
  - Claude Code with Opus 5.5 picked through `/model`;
  - a one-line starter prompt: a dynamic 15-second showcase of great motion design, told to go all out;
  - one self-contained HTML file whose `window.seek(t)` drives every frame from a single clock, rendered with
    HyperFrames;
  - the model checks stills captured at named times, then runs `hyperframes check`;
  - edits are plain-English notes ("slow down scene 2").
- **Price quoted**: Opus 5.5 at $4 / $20 per million tokens in / out, with cache reads at $0.20.
- **Paywall**: the steps on building the film and on the brand design system sit behind a newsletter sign-up and
  were not read.
- **Linked skill pack** `charlie947/motion-graphics-skills` (MIT, 13 skills):
  - house rules: the hook in the first 3 s; no typewriter text, glow, bounce, text gradients or purple-to-blue
    backgrounds; the brand's real colours, never a default palette;
  - `launch-video`: 7 beats in 45 s, no two beats share a layout, and the first 10 s are built in 2-3 style
    variants before committing;
  - `apple-launch-film`: 6-8 scenes of about 2.5 s each;
  - `vox-explainer`: 8-14 shots over 30-60 s;
  - `motion-effects`: its 8 s loop is "too slow for a Reel", so use about 1.4 s of active move;
  - a `MOTION.md`, written from 3-5 reference frames, sets each film's look.
- **Applies**:
  - "no two beats share a layout" becomes the storyteller's field rule (job J52 in the plan): each beat names its own
    field;
  - the banned looks overlap rule R41 already;
  - the 2-3 style variants of the opening are not adopted: our pitch round (J6) already spends that kind of budget
    on concepts.

### Barty-Bart/motion-graphics (MIT; Geist fonts OFL, Lucide icons ISC)

- **Pipeline**: a Claude Code skill (`motion-broll`) that overlays motion on a talking-head video. Its steps:
  - inspect the footage, with ffprobe and a contact sheet;
  - estimate word times from an SRT, to about ±0.2 s;
  - write a plan table that a human approves;
  - write the clip HTML against a `seek(t)` engine;
  - check stills;
  - render with Playwright and headless Chromium, averaging 4 sub-frames per output frame (ffmpeg `tmix`) for motion
    blur;
  - composite onto the footage.
  The steps hand over `motion/plan.json`.
- **Pace**:
  - one shape that never cuts, morphing through states;
  - 4-7 clips a minute by default;
  - inside a clip, one change per spoken beat, 0.4-1.2 s apart;
  - full-frame cutaways of 3-10 s, with at least about 2 s of face between them.
- **Colour**: a warm grey canvas (`#E9E7E2`), ink black, white UI and one orange accent. It bans bounce, particles,
  glows, gradients on UI chrome and made-up data.
- **Applies**:
  - Its spine (one shape, never cut) is what video 8 did: one 22 s take on one page. ghobz's earlier film took the
    same rule ([[ref-x-motion-graphics-search]]). Our brief must stop defaulting to it.
  - For a voiced film, "one change per spoken beat, 0.4-1.2 s apart" is a usable density floor. ElevenLabs gives
    exact word times, which beat an SRT estimate.
  - The 4-sub-frame motion blur is a render idea outside this feature.

### whaleyxbt/claude-motion (MIT)

- **Pipeline**:
  - skills for any coding agent: `.claude/skills/` for Claude Code and Cursor, `AGENTS.md` for Codex and OpenCode;
  - Remotion 4.0.529 with React 19.2 for motion graphics;
  - a second "web-sims" path: three.js and canvas pages captured frame by frame with Playwright into ffmpeg
    (libx264, CRF 16);
  - a single `timeline.json` (`{fps, duration, s1:{beat: seconds}}`) is the contract between the scenes and the
    sound cue sheet;
  - the review loop draws a contact sheet with one frame 0.3 s after each beat (`scripts/sheet.mjs`) and a waveform
    with beat markers (`scripts/wave.mjs`). ElevenLabs appears only as an optional MCP example, never called from
    code.
- **Pace and type** (`.claude/skills/motion-design/SKILL.md`):
  - easing: entrances `bezier(0.16,1,0.3,1)`, exits `bezier(0.6,0,0.9,0.35)`, state changes `bezier(0.65,0,0.35,1)`;
  - springs: 14/140/0.8 by default, and one elastic accent per film;
  - staggers: 0.09 s between words, 0.2-0.25 s between list items;
  - durations: a word reveal takes about 0.8 s, and an exit takes about half its entrance;
  - reading holds: at least 1 s for a short phrase, +0.25 s for each word beyond three, at least 2 s for the final
    hook;
  - scenes overlap rather than cut. The shipped example has 4 scenes in 22 s, slower than our references;
  - liveliness: film grain at about 0.09 opacity reseeded on twos, a vignette, a drifting dot grid and a "line
    boil" filter;
  - type: display type about 138 px on a 1080 canvas.
- **Reusable code**, all stdlib-only and MIT:
  - `sims/beats.py`: tempo, beat grid, downbeats, kicks, energy per bar and the drop;
  - `sfx/loudness.py`: BS.1770 integrated loudness and a 4x-oversampled true peak;
  - the `master()` loop in `sfx/mix.py`.
  They fit our stdlib-only package: our `pyproject.toml` has `dependencies = []`.
- **Applies**:
  - port `beats.py` and `loudness.py` (with their MIT notice) into the new measure module (job J51);
  - the liveliness layers already sit in principles.md as atmosphere layers (rule R35). They also cut the share of
    still frames, which matters because video 8 was still for 58% of its frames;
  - its slow pace is not a model for us.

### shneural: "Bold kinetic type showreel" (X 2103151003272962130, prompt-motion `shneural-2abdfa`)

- **Prompt**: one line asking for a dynamic, roughly 15 s showreel of the model's own design skill, pushed to go
  all out. No scenes, palette or beat count. The author marked the prompt as shared to try; it has no licence.
- **Setup** (the operator's paste of the thread, consistent with the making-of post 2103472385563459833):
  - stock Claude Code, Opus on max reasoning, memory off, one shot, no edits;
  - the machine held a render environment the prompt never mentioned: a sample library, Surge XT, VST effects and
    a Blender MCP. Opus chose a 3D section in Blender on its own; Codex with the same access did not;
  - every frame is code: 2D in skia-python, 3D from a Blender script, and the audio from a Python sequencer to
    the beat grid;
  - about 1.5 h for Claude Code and about 35 min for Codex, render excluded. The making-of says 1 h 32 min and $81
    at API prices, for 900 frames. The delivered file has 1,910 frames at 60 fps, so it was probably
    frame-doubled on export.
- **Measured** (baseline method): 31.9 s at 1920x1080; 13 cuts (0.41 a second); frame change 0.056; 39% still
  frames; saturation 18.3; luma 88.6; -14.3 LUFS; LRA 3.2 LU; 140 BPM; 3.29 onsets a second; 85% of cuts on an
  onset. A looser cut threshold (scene > 0.15) finds a change about every 0.9 s.
- **Applies**:
  - tools available on the machine get used unprompted when they help, so the tools we give the designer matter
    (the measure tool, job J51). It already has three.js;
  - an open "go all out" brief yields more cuts than a brief that asks for one morphing shape
    ([[ref-prompt-motion]]);
  - max reasoning matches our preset's `xhigh`.

### Pace, set side by side

| Source | Seconds per scene or cut |
|---|---|
| The kinetic-type references (baseline) | median 2.5 s; top decile 1.37 s; zheke 0.56 s (1.73 cuts a second) |
| shneural | a hard cut every 2.4 s; a softer change about every 0.9 s |
| Barty-Bart | a change every 0.4-1.2 s inside one never-cut shape |
| charlie947 `apple-launch-film` / `vox-explainer` / `launch-video` | 2.5 s / 3-5 s / 6.4 s |
| whaleyxbt example | 5.5 s (4 scenes in 22 s, overlapping) |
| Our `technique-library/principles.md` "Rhythm" | a new idea about every 2.5 s; every shot lands, settles and holds |
| Video 8 | one 22 s take, 0 cuts, 58% still frames |

- The skill packs our sessions mount pace at 2.5-6 s a scene. The kinetic-type references cut every 1.4-2.5 s.
  Our own principles.md allows two looks: palettes rotating as full-bleed fields, or a "restrained" film of two
  neutrals and one accent. Video 8 took the restrained one, on a near-white page (luma 209, saturation 4.6).
- On 2026-10-06 the operator found 15 s at 143 BPM "a little too fast" and 20-25 s right. On 2026-10-09 the
  operator found video 8 "a lil slow". So the pace target falls between those two calls, not at zheke's extreme.

### What does not apply

- Remotion (whaleyxbt), skia-python and Blender (shneural), and footage compositing (Barty-Bart) are other render
  stacks. HyperFrames stays, and is also charliehills' renderer.
- Barty-Bart's `object-separation` skill (SAM 2.1 segmentation) has no bearing on this feature.

## Sources

- https://charliehills.substack.com/p/claude-code-motion-graphics, free part only.
- https://github.com/charlie947/motion-graphics-skills @4cd156a, MIT (Charlie Hills).
- https://github.com/Barty-Bart/motion-graphics @83355bb, MIT (Bart): `skills/motion-broll/SKILL.md:8-139`,
  `engine/motion.js:17`, `engine/render.js`, `reference/engine-api.md`.
- https://github.com/whaleyxbt/claude-motion @b2a30af, MIT (whaleyxbt): `.claude/skills/{motion-design,sound-design,
  review-loop}/SKILL.md`, `timeline.json`, `sims/beats.py`, `sfx/loudness.py`, `sfx/mix.py`.
- https://x.com/shneural/status/2103472490324648049, 2103151003272962130 and 2103472385563459833, through
  api.fxtwitter.com; https://prompt-motion.com/shneural-2abdfa (study only, rule R43).
- Ours: `src/social_studio/data/skills/technique-library/principles.md` ("Rhythm", "Colour and type");
  `story.py` `STORY_SKILLS`; video 8's `brief.json` and `story.json` in the ghobz library.
