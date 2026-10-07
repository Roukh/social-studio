# metaball-morph

**Family:** morph, shape. **Wants:** 2-2.5 s. **Source:** the 2026 Opus showreels; built in
`examples/reel-2026-10-06.html`, S8.

## Looks

A blob splits into about eight smaller blobs that drift inside a thin outline. The outline morphs through
four shapes: circle, triangle, star, then an organic blob. The blobs then merge back into one dot, which grows
into a wipe to the next ground.

## Build

- Outline morph:
  - resample every shape to the same number of points (160) along its perimeter, using a `resample(poly, n)`
    that walks the segments by arc length;
  - interpolate point by point between shapes on `power3.inOut`, one morph per beat;
  - rotate the whole shape slowly;
  - write the result to one SVG path's `d` every frame from the clock (`renderS8(t)`).
- Blobs:
  - nine SVG circles under a goo filter: `feGaussianBlur` with `stdDeviation` 15, then an `feColorMatrix` alpha
    threshold;
  - eight of the circles sit at evenly spaced points on the outline (`pts[k * NM / 8]`) and the ninth at the
    centre, so the blobs follow the morph;
  - small square vector handles on the same points sell it as a design tool.
- The merge lerps every centre back to the middle. The growing dot is a circle whose radius goes to about
  1,300 px on `pow(grow, 2.6)`.

## Sound

A soft wobble under the split, a tick on each outline change, a swell into the merge, and a whoosh on the wipe.

## Adapting

The shapes can carry meaning: a product's icon, the brand's mark, a letter.
