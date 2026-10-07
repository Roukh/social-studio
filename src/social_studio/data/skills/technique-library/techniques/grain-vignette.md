# grain-vignette

**Family:** texture. **Wants:** the whole film. **Source:** the 2026 Opus showreels; built in
`examples/reel-2026-10-06.html`, `// ===== grain` and the FX layer.

## Looks

Fine film grain over everything at 3-6 % opacity, moving every frame. A radial vignette darkens the edges of
every flat field. Behind kinetic words, walls of ghost outline type (a 1 px stroke at 6-10 % opacity) drift.
Together they stop a flat colour field from reading as a slide.

## Build

- Grain:
  - fill a 256 x 256 canvas with seeded noise once (`kit.rng(7)`) and use it as a repeating background image
    on a full-frame layer;
  - each frame, offset `background-position` by values from `kit.rng(1000 + frame)`, so the grain moves but
    renders identically every time;
  - apply it with `mix-blend-mode: overlay` or a low opacity.
- Vignette: a `radial-gradient(transparent 55%, rgba(0, 0, 0, .35))` layer per field, tinted toward the
  field's darkest colour.
- Outline walls: `-webkit-text-stroke: 1px` with a transparent fill, drifting slowly on a linear ease.

## Adapting

Drive the grain harder at impact frames or a glitch beat; never apply it statically at a uniform strength.
