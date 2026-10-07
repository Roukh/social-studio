# end-card-decode

**Family:** close, type. **Wants:** 1.7-3 s. **Source:** the 2026 Opus showreels; built in
`examples/reel-2026-10-06.html`, S9.

## Looks

The through-line dot pulses with a glow ring. The name decodes in: each letter flickers through random glyphs
(`#%&*+/<>=?01X_`), some flashing the accent colour, then locks to its real letter on its own staggered time.
Then come an italic serif line, a hairline that draws across, and the call to action typing on in mono. A small
square marker spins in, and the audio fades out.

## Build

- Each letter is a span holding a hidden final glyph and a scramble glyph. `renderS9(t)` picks the scramble
  glyph from `kit.rng(frame * 31 + i * 7)`, so every frame renders the same way twice, and shows the final
  glyph once `t` passes that letter's lock time.
- The lock times are spread, not in order: `base + ((i * 7) % 13) * 0.026 s`.
- The tagline reveals with `clipPath` and an x slide, and the hairline with `scaleX`.

## Sound

Glitch ticks under the decode, a hit on the last lock, and the bed fading out over the last 1.5 s.

## Adapting

The call to action is the brand's, word for word. Hold the finished end card at least 1 s.
