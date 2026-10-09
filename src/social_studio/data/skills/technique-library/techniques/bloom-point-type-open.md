# bloom-point-type-open

**Family:** open, type. **Wants:** 1.3-2 s. **Source:** prompt-motion.com's gallery (oliahmed205-3e31c4),
studied 2026-10-09.

## Looks

A single point of soft bloom light sits alone in a near-black field. In well under a second it blooms outward
and a two-line headline resolves already in focus around it, with no letter-by-letter build: the whole block
arrives together. One glyph in the headline keeps the point's glow and renders in the brand's gradient, a first
sighting of the mark to come. A short tagline fades up beneath a beat later.

## Build

- The bloom is a radial-gradient sprite (canvas or CSS) scaled from near-zero to its full size with a blur
  falloff, under 0.3 s, `power2.out`.
- The headline is one DOM block; it resolves with a short blur-to-sharp pass (`filter: blur(12px) -> blur(0)`,
  `opacity 0 -> 1`) timed to land as the bloom peaks, not staggered letter by letter.
- One chosen glyph sits in its own span, filled with the brand's gradient (`background-clip: text`) instead of
  the solid ink colour, and keeps a soft glow so it reads as the point's light made solid.
- The tagline reveals on its own 0.2-0.3 s delay after the headline settles, a small `y`-slide under it.

## Sound

A soft rising shimmer that resolves into a quiet hit as the headline comes into focus, then silence under the
tagline.

## Adapting

Use it as a cold open before any product footage. Pick the glyph that will recur in the end card's mark, so the
bloom reads as a first sighting of the logo, not a one-off flourish.
