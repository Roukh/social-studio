# noise-dissolve-logomark

**Family:** identity, particles. **Wants:** 1-1.5 s. **Source:** a brand reveal in prompt-motion.com's
gallery, studied 2026-10-07.

## Looks

A mark or a name condenses from scattered points into a solid shape, instead of dropping or wiping in. The
points arrive at different times, and the shape fills in as the last ones land.

## Build

- One 2D canvas from the master clock.
- Sample the mark into seeded points: draw the text or path to an offscreen canvas and take the filled pixels on a grid.
- Each point eases from a seeded start position to its target on `power3.out` or `expo`, with a seeded
  delay, and its opacity ramps up as it nears the target.
- Crossfade to the crisp DOM or SVG mark in the last 0.1 s.

## Sound

A shimmer that resolves into a soft hit as the mark completes.

## Adapting

An identity open or close that sits between `wordmark-assemble.md` and `end-card-decode.md`.
