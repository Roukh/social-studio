---
id: reference-leonabboud-showreel
type: reference
created: "2026-10-06T18:30:00Z"
consequence: 8
locus: output
summary: Operator's target look - Leon Abboud's 15 s Opus 5.5 showreel - measured shot by shot: palette, type, HUD, audio grid, and what blocks social-studio from it.
scope: repo
status: active
---

# Reference: Leon Abboud's Opus 5.5 showreel (the operator's target look)

The operator, 2026-10-06: "This is great if you can build like this." This note measures the video shot by shot. It is part of [[motion-course]]; for the other showreel runs see [[motion-course-showcase]].

## Question

What exactly does the operator's reference video look and sound like (palette, type, HUD, shot grammar, audio grid), and what does matching it require?

## Method

Downloaded the source post and measured the video directly: `ffprobe` for format, `ebur128` for loudness, a spectrogram/waveform and `onsets.py` for the audio grid, 2 fps and 6 fps contact sheets plus full-resolution key frames for the shot list, and by-eye font identification. Local copy in `.local/refs/leonabboud-2103576084499358051/` (gitignored): `video.mp4` (1080p60 source), `tweet.json`, `sheets/`, `frames/`, `onsets.py`.

## Findings

### Source

- Post: https://x.com/leonabboud/status/2103576084499358051, 2026-09-25. 123K views, 762 likes, 858 bookmarks (api.fxtwitter.com, 2026-10-06).
- Prompt, verbatim: "make a dynamic 15-second motion graphics video that shows what an incredible motion designer you are, like it's your showreel for a résumé. go all out." Same one-liner as @stephanlivera, @himanshutwtxs and @robj3d3.
- Claimed effort: "one shot this in 15 minutes." No effort level stated.
- Stack, per the video's own credit line at 14.8 s: "MADE ENTIRELY IN CODE — REACT · REMOTION · THREE.JS — 0 KEYFRAMES DRAGGED".

### Measured

| Property | Value | Source |
|---|---|---|
| Duration | 15.06 s | ffprobe |
| Format | 1920×1080, 16:9, 60 fps, H.264 | ffprobe |
| Audio | AAC stereo 48 kHz, -13.9 LUFS integrated, LRA 1.1 LU | ebur128 |
| Audio type | synthesized bed: riser into a hit at ~1.2 s, ticks on a 0.21 s grid, whoosh swell into each scene, pitched blips under UI/data scenes, fade-out from 13.3 s; no voice | spectrogram, waveform |
| Onset grid | 46 onsets; median spacing 0.209 s → a 16th grid at ~72 BPM or 8ths at ~143 BPM | `onsets.py` |
| Scenes | intro, 7 numbered scenes ("SCENE 0N / 07"), end card | HUD |
| Cut timing | every scene change lands on an onset: 3.34, 5.02, 5.43, 5.85, 6.27, 6.48, 8.15, 9.81, 10.01, 11.48, 13.26 | onsets vs 6 fps sheet |
| Pace | new technique every ~1.6 s; kinetic words hold one beat (~0.42 s) each | sheet |
| Hard cuts (>0.25 scene change) | 5, all within 5.0-6.25 s; every other change is a wipe or morph | ffmpeg scene filter |

### Style guide

- **Palette** (sampled from pixels): ink #070711; signal orange #FD4920; cream #F0EFE6; electric blue #2E49F0 (lines), #2A3DDB-#2847EA (radial background). One full-bleed field per scene, rotating dark → orange → dark → cream/black/blue/orange → cream → dark → blue → orange → dark. Orange is the constant accent.
- **Type** (by eye, medium confidence): heavy neo-grotesk display, Inter Display Black-like, for titles/numbers, with animated variable weight ("CLAUDE." shows thin "CL" against black "AUDE" mid-wave). Italic serif, Instrument Serif-like, for "motion designer" and "on purpose.". Wide-tracked mono, JetBrains Mono-like, for every label and the HUD.
- **HUD frame on every scene:** corner bracket marks; top-left "● CLAUDE — MOTION REEL 2026"; top-right "SCENE 04 / 07"; bottom-left section name ("IDENTITY / TYPE", "DATA / INFOGRAPHICS", "UI / PRODUCT MOTION", "KINETIC TYPOGRAPHY", "GENERATIVE / PARTICLES"); bottom-right four progress squares (current one orange) and a running SMPTE timecode ("00:00:07:36").
- **Texture:** fine grain, radial vignette on every flat field, soft glow on the orange dot, ghosted outline type in the background ("MOTION ✦ DESIGN", a repeating "SINGLE" wall).

### Shot list (times in s)

| t | Scene | What happens | Transition out |
|---|---|---|---|
| 0.0-0.5 | intro | near-black field, dot grid; orange dot drops in and squashes (sub-thump at 0.43) | — |
| 0.5-1.0 | intro | mono caption types "claude / motion reel — 2026"; dot stretches into a horizontal line | — |
| 1.0-1.5 | intro | line becomes a travelling sine wave (riser) | line thickens into a band that floods orange (1.5-1.65) |
| 1.65-3.2 | 01 identity/type | "CLAUDE." drops in letter by letter with blur; "motion designer" serif slides under; "SHOWREEL ——— 2026" kicker; variable-weight wave runs across letters | blurred black circle wipe from the right (3.2-3.35) |
| 3.35-5.0 | 02 3D | Three.js voxel grid, tilted; at 3.6 a ripple lifts blocks in an orange-to-violet gradient; chrome sphere with orbit ring bounces centre; camera orbits | hard cut |
| 5.0-6.45 | 03 kinetic typography | one word per beat: "EVERY" black on cream → "SINGLE" orange on black over an outline-word wall → "FRAME" white on blue, skewed/motion-blurred in viewfinder brackets → "on purpose." italic serif on orange | hard cuts |
| 6.48-8.15 | 04 data/infographics | cream; "+312%" rolls up from +106% with blurred digits; donut fills 0→78% "RETENTION"; 12 bars grow; blue spline draws with a dot and "↑ 4.7k" pill; last bar orange | staircase pixel-block wipe to black (8.15-8.3) |
| 8.3-9.8 | 05 generative/particles | flow field of white/orange/blue streaks → converges into a sphere of sticks → collapses into concentric dotted rings with x/y readouts → radial burst around a blue dot (9.83) | burst |
| 10.0-11.48 | 06 UI/product motion | blue radial field, dot grid; glass cards stack; "Render queue" card springs up ("● LIVE", "showreel_v1.mp4 · 900 frames"); cursor flips "Motion blur" on, picks 60 fps; "Render" becomes orange progress fill ("Rendering… 73%") then "Done ✓"; toast "900 frames rendered" | orange circle wipe from centre, soft edges |
| 11.5-13.2 | 07 shape/morph | black metaball splits into 8 blobs inside a thin cream outline; outline morphs circle → triangle → wobbly star → blob; blobs merge into one dot, grows into a wipe to black | dot wipe |
| 13.26-15.06 | end card | orange dot pulses with glow ring; "Claude" decodes in with a letter scramble; "motion designer" serif, a hairline, orange mono "EVERY FRAME, ON PURPOSE.", credit line; audio fades out | — |

### Pre-iteration-1 gap list (superseded)

The table below was written before the social-studio reel preset existed. It is kept short as a historical gap list; the decisions that closed most of these gaps now live in [[reference-look-decisions]] (iteration 1, built 2026-10-06: reel preset with this reference's palette, OFL faces, `--aspect`/`--fps`/`--duration`/`--sound` flags, a code sound synth, vendored Three.js via import map, variable font weight ranges, loosened creative rules).

| Element of the reference | Blocker at the time |
|---|---|
| Synthesized music bed plus SFX, cut on onsets | no audio path at all |
| 60 fps with motion blur | preset `video.fps` fixed at 30, no subframe blending |
| Three.js 3D scene | engine had an adapter, but no preset wired it in |
| 16:9, 7 techniques in 15 s | format was 9:16 only; hold-time rule too slow for one-beat words |
| HUD in corners, variable-font weight | safe-zone/min-text-size rules rejected it; no variable font in any preset |

### Read-outs for the planner (still useful)

- The reference is the same one-liner that produced unrelated looks for @stephanlivera and @himanshutwtxs ([[motion-course-showcase]] #11, #14): the look came from the run, not the prompt. Matching it repeatably needs this note as reference input (palette, type, HUD, shot grammar, audio grid), not the prompt alone.
- Four house gates would have failed this video outright: frame 0, reading time, safe zone with minimum text, and the 9:16 format — now addressed per [[reference-look-decisions]].

## Sources

- https://x.com/leonabboud/status/2103576084499358051 (video, tweet.json via api.fxtwitter.com).
- Local measurement artifacts: `.local/refs/leonabboud-2103576084499358051/{video.mp4,sheets/,frames/,onsets.py}` (ffprobe, ebur128, ffmpeg scene filter).
- [[motion-course]], [[motion-course-showcase]], [[reference-look-decisions]].

## Date

Gathered 2026-10-06; condensed 2026-10-06 for the format 4 wiki.
