# grid-wave-morph

**Family:** generative, shape, build-pattern. **Wants:** 1.5-2.5 s. **Source:** prompt-motion.com's gallery
(ndhabarde11-f155b4), studied 2026-10-09.

## Looks

A regular grid of identical rounded shapes sits over a flat colour field. A wave of transformation sweeps
across the grid from one corner: each shape's rotation and roundness (a diamond relaxing into a square, or
back) shifts at a time offset set by its distance from the wave's origin, so the change visibly travels corner
to corner. A small mono readout names the easing function and the shape/function count, like a caption on a
generative-art sketch.

## Build

- Shapes sit on a regular grid, `(col * spacing, row * spacing)`.
- Each shape's progress is `ease(t - k * distanceFromOrigin)`, where `k` is a small constant; progress drives
  rotation and a scale/corner-radius lerp between two states (for example diamond to rounded square).
- A small mono caption states the formula and the shape/function count, set once from the same constants that
  drive the grid.
- Optionally run a `ticker-tape-marquee.md` strip of a short repeating label behind or around the grid for
  texture.

## Sound

A soft granular patter as the wave crosses the grid, with a faint tick as each shape settles.

## Adapting

Use to show systematic, parametric craft: a grid of product icons, feature tiles or a texture swatch, all
driven by one small, readable function instead of hand-placed keyframes.
