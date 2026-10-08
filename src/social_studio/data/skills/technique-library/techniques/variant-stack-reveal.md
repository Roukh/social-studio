# variant-stack-reveal

**Family:** data, interface. **Wants:** 2-2.5 s. **Source:** Framer's "skills" ad
(instagram.com/p/DdtwW_Ws0Xx), studied 2026-10-07.

## Looks

Three or four near-identical panels fan out behind a main panel, each slightly offset in position and
rotation, then settle. One shot shows that many were made, where cutting between single variants would not.

## Build

- DOM panels, or three.js instanced planes. Each panel's offset (x, y, rotation, small scale) comes from
  `kit.rng(seed)`.
- Stagger the entrances by 10-30 %, uneven, on springs (`kit.springEase`).
- The variants differ in small, visible ways: a colour, a headline, a layout.

## Sound

A soft cluster of hits, one per panel.

## Adapting

For scale or choice: designs, versions, options, results. Pair it with `ui-tilt-card.md` for depth.
