# pixelate-resolve

**Family:** reveal, texture. **Wants:** 2-3 s. **Source:** prompt-motion.com's gallery
(anthonyriera-9b1b2a), studied 2026-10-09.

## Looks

A portrait or scene starts as a coarse block of large, blurred pixels with almost no detail, then sharpens in
large discrete steps rather than a smooth blur-out, as if a connection is warming up. Supporting UI (chat
bubbles, labels) populates around it while it is still coarse, so the scene reads as live before the image
itself is legible.

## Build

- Render the source image at a very low resolution (8-16 px blocks) onto a canvas, then step the resolution up
  2-4 times at discrete intervals (not a continuous tween) until it reaches full detail.
- `image-rendering: pixelated` on the scaled-up canvas keeps each step blocky instead of smooth.
- Time the supporting UI (bubbles, labels) to arrive during the coarsest 1-2 steps, so the viewer has
  something to read while the image is still resolving.

## Sound

A soft digital static or modem-like texture that clears as the image sharpens.

## Adapting

Use it for "warming up," "connecting," or "getting to know you" beats: a new account, a cold start, a profile
that still needs data. Avoid it for anything that should feel instantly ready.
