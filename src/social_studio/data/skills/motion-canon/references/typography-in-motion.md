# Typography in motion

## One idea per beat

Each kinetic-type beat should carry exactly one word, phrase, or number — the moment a second idea enters the frame, the viewer has to choose what to read and loses the rhythm. Build the beat sheet (see SKILL.md step 2) at the idea level first, then assign words to beats, not the reverse.

## Hold duration

Guidance converges on ~3 words/second as a legibility ceiling for continuous reading, and holding a key message 2-3 s so it registers before the cut. In a beat-driven reel a single word may hold one beat, because the music carries it. Average adult reading speed is ~300 wpm (≈5 words/sec, ≈0.2s/word, ≈6f@30fps/12f@60fps) — treat that as a *floor*, not a target: a word held for exactly its minimum reading time reads as a flash-beat in a montage, not a statement.

Use motion itself as a hierarchy signal in ad-style kinetic type:

| Role | Motion speed | Hold |
|---|---|---|
| Hook | fastest motion, hardest cut-in | shortest hold (10-20f@30fps / 20-40f@60fps) |
| Benefit / supporting idea | medium motion | medium hold (20-40f@30fps / 40-80f@60fps) |
| Claim / core statement | motion settles to a clear pause | longest hold before the pause (≥36f@30fps / ≥72f@60fps) |
| CTA | slowest, most deliberate | longest total screen time |

Source: kinetic typography guidance, https://www.nemovideo.com/blog/kinetic-typography-product-ads and https://canvas.santarosa.edu/courses/28549/pages/week-11-page-7-kinetic-typography

## Tracking, weight, and scale as emphasis tools

- **Tracking (letter-spacing)**: tighten (-1 to -3%) on large display type to read as confident/premium; open tracking (+5-15%) on small caps/mono labels (HUD readouts, SMPTE timecode, scene counters) reads as technical/systemic. Animate tracking narrow→normal on a word's entrance for a "snapping into focus" feel — cheap on every word, effective on exactly one per piece.
- **Weight**: use weight contrast, not just size contrast, to separate a hero word from supporting words in the same frame — e.g. hero at 800, support at 400, same type size.
- **Scale**: reserve the largest scale jump in the piece for the single most important word; if every word gets a big scale pop, none of them read as more important than the others.

## Variable-font weight wave

The `wght` axis (typically 100-900) and other registered axes (width `wdth`, slant `slnt`, italic `ital`, optical size `opsz`) interpolate continuously, and CSS `font-variation-settings` is directly animatable — this gives a true weight wave with one font file, no cross-fading discrete weight instances.

```css
.wave-word { font-variation-settings: "wght" 400; }
```

```js
gsap.to(".wave-word", {
  fontVariationSettings: '"wght" 850',
  duration: 0.5,
  ease: "power2.inOut",
  stagger: { each: 0.03, from: "start" } // one letter/word after another = the "wave"
});
```

For a true letter-by-letter wave, split the text first (GSAP SplitText, free since 2024) so each character is its own tween target, then stagger across characters with `each: 0.02-0.04`. Larger `each` reads as a slower, more deliberate wave; below ~0.02s the wave reads as a single soft pulse rather than a travelling wave.

Source: variable font axis behavior, https://helpx.adobe.com/lt/after-effects/desktop/variable-font-axes/work-with-variable-font-axes/variable-font-axes-support.html

## Reading time vs. hold time — the actual tradeoff

A word's hold time should be the *larger* of: (a) the minimum reading-time floor above, and (b) the time the idea needs to land emotionally. A one-syllable punchline ("Shipped.") can hold near the reading-time floor because its meaning lands instantly; a longer or more abstract phrase needs extra hold beyond pure reading time for the idea to register, not just be decoded.

## Tells of cheap kinetic type

- Every word gets the exact same hold duration regardless of length or importance.
- Every word enters with the same fade/scale combo — no weight, tracking, or scale hierarchy at all.
- Tracking/letter-spacing never changes — a missed opportunity for the "snap into focus" cue.
- Two unrelated ideas visible in frame at once because a hold ran long and the next cut's text pre-rendered underneath.
- Mono/caps HUD-style type used for a hero statement (or vice versa — a soft humanist weight used for a technical readout) — mismatched type register for the content's register.
