# particle-flow-sphere

**Family:** particles, generative. **Wants:** 1.5-2.5 s. **Source:** the 2026 Opus showreels; built in
`examples/reel-2026-10-06.html`, S6.

## Looks

About 1,800 streaks in white, the accent and the second colour ride a flow field across the frame. They
converge into a sphere of sticks, collapse into concentric dotted rings with x/y readouts, then burst out
radially around a single dot. The scene leaves on a staircase pixel-block wipe, drawn in the same canvas.

## Build

- One 2D canvas drawn by `drawS6(t)` from the master clock.
- Precompute everything once, seeded with `kit.rng(seed)`, so a frame depends only on `t`:
  - each particle's flow path, `STEPS` points integrated through a velocity field built from sines and cosines
    of x and y;
  - its target on a Fibonacci sphere, with golden angle `π(3 - √5)`;
  - its ring radius and angle;
  - its start delay.
- Per frame, interpolate each particle between its phases (flow, sphere, rings, burst) with eased segment
  progress, and draw short strokes from its previous position for streaks.
- The mono readouts clip in and out with `clipPath` on the timeline.

## Sound

A whoosh as the streaks converge, a rising shimmer into the sphere, ticks on the rings, a burst hit, and a
glitch on the pixel wipe.

## Adapting

In 9:16, make the flow vertical and centre the sphere in the upper third.
