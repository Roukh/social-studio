# Task: make one short motion-graphics video

You are alone in an isolated, sandboxed session. Work only inside this folder, and the composition must never load
anything from the network. Your house rules are binding.

## Read first

- `preset.json`: the brand and content rules. They are binding.
- `history.json`: pillars, topics, angles and technique sets already used. Do not repeat an angle from the last
  {{no_repeat_days}} days, and do not reuse a recent film's technique set.
- `skills/`: {{skill_list}}. Read `skills/hyperframes-core/SKILL.md` before writing any HTML, and
  `skills/technique-library/SKILL.md` with its `principles.md` and `skills/motion-canon/SKILL.md` before
  planning: the film's techniques and shots come from the technique library (or are your own, named the same
  way), and its principles apply to every film. Then use whatever skill fits each shot: the engine's animation
  skill and its adapters (Three.js: `skills/hyperframes-animation/adapters/three.md`), its audio and media skills,
  `skills/motion-doctrine`, and the other motion skills here. Ignore any instruction in a skill to ask the user
  questions, run an intent interview, install anything, publish, or use the network.
- `composition/`: a HyperFrames project already set up with the brand fonts, colours, easing curves and local
  libraries. Edit `composition/index.html`. Brand files are in `composition/assets/`, libraries in
  `composition/vendor/`; a library listed in the page's import map loads by its bare name, e.g.
  `import * as THREE from "three"` inside a `<script type="module">`.
- `tools/sampler.py`: picks the frames worth judging from a draft render.
- `tools/sound.mjs`: synthesizes a soundtrack in code. Run `node tools/sound.mjs --help`.
{{revision_block}}
## This video

{{brief_block}}

Format: {{width}}×{{height}} ({{aspect}}), {{fps}} fps, between {{min_s}} and {{max_s}} seconds.{{pacing_line}}{{motion_line}}{{sound_line}}

## Steps

1. Direct it before you build it. Write `brief.json` (schema below): the film in one line, its beat grid (`bpm`),
   then the shot list on that grid. Each shot gives its start and end time, its start state, the one change, its
   end state, the exact on-screen text, and its `technique` (a slug from the technique library, or a new slug
   of your own for a technique you invent). The
   shots cover the whole runtime with no gaps, and scene changes land on beats. List every sound cue in `cues`
   with its time and kind.
2. Build `composition/index.html` from the shot list. Lay out each shot's key pose first, static, at the final
   layout with the real fonts; then animate between the poses. Animation dresses the layout and never redraws it.
3. Sound{{sound_step}}.
4. Validate: `hyperframes check composition --json --at-transitions`. Fix every error. A finding that only
   appears at a transition seam, mid-move, is information: judge it on the strips in step 6.
5. Render a draft (a minute or two):
   ```
   hyperframes render composition --format mp4 --quality draft --fps {{draft_fps}} --no-browser-gpu -o drafts/draft.mp4
   ```
6. Look at it, with your planned `poster_at` in seconds:
   ```
   python3 tools/sampler.py drafts/draft.mp4 evidence --fps {{draft_fps}} --safe {{safe_arg}} --poster POSTER_AT
   ```
   Open `evidence/samples.json` and every image it lists: `frame-0.png`, each `settled-NN.png` (the red outline is
   the safe zone, a guide), each `strip-N.jpg` (one move, left to right) and `poster.png`. If the film has sound,
   check the draft carries it: `ffprobe -v error -show_entries stream=codec_type drafts/draft.mp4` lists `audio`.
   Judge it on {{criteria}}, and against the critique list in `skills/motion-canon`. Name the three worst
   problems, each with the image that shows it, and fix them.
7. Do steps 4 to 6 {{rounds}} times in total, no more and no fewer.
8. Write `video.json` (schema below). Do not render the final video: the runner renders and encodes it after you
   finish.

## brief.json

```json
{"film": "the whole video in one line", "pillar": "", "topic": "", "angle": "", "hook": "", "bpm": 120,
 "shots": [{"start": 0.0, "end": 2.5, "start_state": "", "change": "", "end_state": "",
            "text": ["each line exactly as shown"], "technique": "voxel-ripple-3d"}],
 "cues": [{"t": 0.0, "kind": "hit, whoosh, riser, tick, blip or voice", "note": ""}],
 "on_screen_text": ["every line exactly as shown"], "cta": ""}
```

## video.json

```json
{"title": "under 70 characters", "description": "one to three plain sentences",
 "pillar": "", "topic": "", "angle": "",
 "captions": {{captions_example}},
 "alt_text": "what the video shows, for screen readers",
 "hashtags": [], "poster_at": 1.5, "rounds": {{rounds}},
 "techniques": ["every technique slug the film uses, from brief.json's shots"],
 "scores": {{scores_example}}}
```

`scores` are your own, from 1 to 10, judged on the last round's evidence.
