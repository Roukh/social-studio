# Transitions and editing grammar

## BPM to cut grid, in code

```js
const bpm = 143;
const secPerBeat = 60 / bpm;              // 0.4196s
const secPerHalfBeat = secPerBeat / 2;    // 0.2098s  <- the brief's 0.21s grid
const framesPerBeat30 = secPerBeat * 30;  // ~12.6f
const framesPerBeat60 = secPerBeat * 60;  // ~25.2f
```

General formula: `cutInterval = 60 / (BPM / beatMultiple)`. At 120 BPM, cutting every 2 beats gives `60 / (120/2) = 1.0s/cut`; converting to frames is `(60/BPM) * fps` per beat (120 BPM at 30fps = 15f/beat = 0.5s). Source: https://nofilmschool.com/2017/06/watch-rhythmic-editing and https://beatsyncpro.ai/blog/beat-synced-video-clips-free-download-pillar.html

**Build the grid, then break it.** Snap every cut's start time to the nearest half-beat, then manually lengthen 2-3 cuts per 15s (hold through 2-4 beats instead of 1) at the midpoint and at the final beat before the payoff — a timeline where literally every cut lands on literally every half-beat reads as a metronome, not a video. Vary which half of the beat pair gets the longer hold.

## Cut-length ranges by BPM

| BPM | sec/beat | sec/half-beat | Typical cut-per-beat length | Typical cut-per-half-beat length |
|---|---|---|---|---|
| 90-100 (slow) | 0.60-0.67s | 0.30-0.33s | 18-20f@30fps | 9-10f@30fps |
| 120-130 (medium) | 0.46-0.50s | 0.23-0.25s | 14-15f@30fps | 7f@30fps |
| 140-150 (fast, this brief) | 0.40-0.43s | 0.20-0.21s | 12-13f@30fps / 24-26f@60fps | 6f@30fps / 12-13f@60fps |
| 160+ (very fast) | <0.38s | <0.19s | 11f@30fps or less | pairs of cuts start to blur into a single flicker-cut |

## Editing-grammar vocabulary, in code terms

- **Cut on action**: trigger the cut at the frame where a moving element crosses a threshold (e.g. a card reaches full scale), not at an arbitrary timeline tick — continues perceived momentum across the cut.
- **Match cut / graphic match**: the outgoing frame's dominant shape or color should closely match the incoming frame's — e.g. a circular progress ring wipes to reveal a circular badge in the same screen position.
- **Whip / wipe**: a directional blur-and-slide of the whole frame; implement as a very short (4-8f@30fps, 8-16f@60fps) `translateX`/`translateY` + `blur()` on a full-screen layer, timed so the blur peaks mid-transition and clears by the new frame's first visible frame.
- **J/L cut equivalent (audio leads/trails picture)**: start the next beat's sound cue 1-3 frames *before* its visual cut, or let the previous beat's sound tail 1-2 frames past its visual cut — a hard simultaneous audio+video cut on every single transition reads as mechanical over a full piece.
- **Rhythm**: alternate cut lengths in a pattern (e.g. short-short-long) rather than a flat repeating interval, mirroring how music phrases rarely repeat identical note lengths for 15 seconds straight.

## Transition techniques in HTML/CSS/GSAP

**Circle wipe** — animate a `clip-path: circle()` radius from 0 to beyond the viewport diagonal:
```js
gsap.fromTo(el, { clipPath: "circle(0% at 50% 50%)" }, { clipPath: "circle(150% at 50% 50%)", duration: 0.5, ease: "power2.inOut" });
```

**Staircase pixel-block wipe** — tile a grid of divs (or a single `<canvas>`), stagger each cell's opacity/scale with `grid: "auto"` and `from: "edges"` or a directional index-based delay so blocks reveal in a diagonal/staircase order:
```js
gsap.to(".block", { opacity: 0, stagger: { each: 0.015, grid: [rows, cols], from: "start", axis: "x" }, duration: 0.2 });
```

**Band flood** — a full-width colored `div` scaled from `scaleY: 0` (origin top or bottom) to `1` then back to `0` on the opposite edge, covering and uncovering the frame; duration 8-14f@30fps / 16-28f@60fps total for a fast flood.

**Metaball split/merge** (for shape morphs) — overlap two+ soft circles, apply `filter: blur(Npx) contrast(20)` (CSS) or an SVG `feGaussianBlur` + `feColorMatrix` stack (sharper control), then animate the circles' positions apart (split) or together (merge). Source: https://freefrontend.com/javascript-gooey/ and https://dev.to/antogarand/svg-metaballs-35pj

**MorphSVG shape morph** (GSAP plugin, free since 2024) — morph directly between two path `d` strings for logo/icon transforms:
```js
gsap.to("#shapeA", { morphSVG: "#shapeB", duration: 0.6, ease: "power2.inOut" });
```

## Motion blur / shutter angle in a rendered-frame pipeline

The 180°-shutter default (shutter speed ≈ 1/(2×fps)) is what makes live-action motion blur look natural; a rendered/code-driven piece has no physical shutter, so blur must be simulated. For fast moves (>300px/s on screen), ramp a CSS `filter: blur()` up only during the high-velocity portion of the move (not statically applied) — roughly 1-3px at 60fps for a 200-400px/s move — or render 2-3 trailing ghost copies at decreasing opacity along the motion path. Skip blur on HUD/UI elements entirely; a blurred HUD readout looks broken, not cinematic. Source: https://www.diyphotography.net/?p=309010 (the rule is a default, not a law — it "breaks down" at extreme frame rates or deliberately stylized sharp cuts, per https://provideocoalition.com/the-180-shutter-angle-rule-is-broken).

## Tells of cheap editing

- Every cut lands on exactly the same beat subdivision for the whole piece — no held beats, no variation.
- Transitions are 100% dissolves/fades — no match cuts, no motivated wipes.
- A wipe or whip transition used with no directional or graphic relationship to what's on either side of it.
- Audio cue and visual cut always land on the exact same frame, every time, with no J/L offset anywhere.
