# Sound for motion

## Placement on a GSAP + `<audio>` timeline

Since sound in a HyperFrames composition is `<audio>` elements placed on the same paused GSAP timeline as the visuals, every sound cue is a timeline position, not a "fire and forget" call — treat it with the same frame-level precision as a keyframe.

- **Hits** (impact of a cut, a card landing, a shape completing a morph): place the hit's peak within **±1 frame at 60fps (±1/60s ≈ ±16.7ms) or ±2 frames at 30fps (±2/30s ≈ ±66ms)** of the visual impact frame. Looser than that and the hit reads as late, which is more noticeable than a slightly early hit.
- **Whooshes** (fast pans, wipes, whip transitions): start the whoosh 2-5 frames *before* the visual motion begins so the sound's attack leads the eye, and let it resolve at or just before the landing hit.
- **Risers** (building tension into a reveal or beat drop): start well before the payoff (0.5-1.5s lead is typical for a 10-30s piece) and make sure the riser's peak/cutoff lands *into* the hit frame, not a frame or two before it goes quiet — a riser that stops before the payoff lands feels like a dropped cue.
- **Ticks** (HUD counters, progress-square fills, scene-counter increments): one tick per unit of visible change, placed exactly on that change's frame with no lead/lag — ticks are a "live data" cue and any offset breaks the illusion of real-time counting.

## J/L-style offsets

A hard simultaneous audio+visual cut on every single transition reads as mechanical across a full piece. Letting a cue lead or trail its visual by 1-3 frames (the sound-for-picture equivalent of a J/L cut) on a subset of transitions reintroduces the sense that sound and picture are two tracks, not one baked-in effect.

## Loudness for social delivery

TikTok, Instagram Reels and YouTube converge on roughly **-14 LUFS integrated** as the practical normalization target for exported audio (some sources report Instagram/TikTok nearer -10 to -12 LUFS) — mix to that level rather than relying on the platform's own normalizer, which will silently attenuate an overly hot mix and make it sound quieter/weaker next to adjacent content. Source: https://openclip.app/learn/lufs and https://opus.pro/blog/best-loudness-normalizers

Practical mix order for a 10-30s piece: music bed first (set its overall level), then risers/whooshes 2-6dB under the music bed's peak so they accent rather than compete, then hits/ticks 1-3dB *above* the music bed's instantaneous level at their exact frame (a hit needs to momentarily cut through).

## Building a code-driven sound layer

- **Tone.js** (over the Web Audio API) is the standard choice for generative or precisely-scheduled sound design when cues need to be synthesized or dynamically timed rather than pre-rendered audio files — e.g. a tick sound whose pitch rises with a counter, or a riser whose length needs to exactly match a variable-duration beat.
- **Pre-rendered `<audio>` elements** are simpler and more predictable for fixed one-shot hits/whooshes/risers — place them as timeline-scoped elements with their `currentTime` or play-trigger scrubbed by the same GSAP timeline position as the visual cue, so that scrubbing the whole composition (for QA or re-render) keeps audio and visual in lockstep.

## Tells of cheap sound design

- Every cut has the exact same whoosh/hit sample with no variation in pitch, length, or character across the piece.
- A riser that cuts off abruptly 1-2 frames before the payoff instead of resolving into the hit.
- Sound cues that are audibly early or late relative to the visual (anything past the ±1-2 frame tolerance above).
- A mix that's clearly too quiet or clipping-hot because it was never checked against a -14 LUFS reference before export.
- Ticks/HUD sounds that don't line up 1:1 with visible counter/readout changes.
