# voxel-ripple-3d

**Family:** 3D. **Wants:** 2-2.5 s. **Source:** the 2026 Opus showreels; built in
`examples/reel-2026-10-06.html`, S3 (the `<script type="module">` at the end).

## Looks

A 24 x 24 field of blocks on a tilted camera, lit like a studio product shot with fog into the ground colour.
A glossy chrome sphere with an orbit ring and a small satellite falls and bounces on it three times. Each
impact sends a ripple ring out through the blocks, lifting them and shifting their colour from the base colour
through the mid colour to the accent at the peak. The camera orbits slowly, then pushes into the sphere with a
growing blur to leave the scene.

## Build

- three.js from the import map: `import * as THREE from "three"`.
  - `WebGLRenderer` with `preserveDrawingBuffer: true`, soft shadows and `NeutralToneMapping`.
  - A PMREM environment built from coloured planes (the brand's colours as softboxes), so the chrome reflects
    the palette.
- One `InstancedMesh` of boxes, with heights and colours set per frame with `setMatrixAt` and `setColorAt`.
  Seed the base heights with `kit.rng(seed)`.
- Ripple height at radius `r`, `dt` seconds after an impact:
  `1.9 * exp(-1.7 dt) * (exp(-((r - 6.4 dt) / 0.75)^2) - 0.4 * exp(-((r - 6.4 dt + 1.4) / 0.6)^2))`.
- The sphere follows piecewise parabolic arcs between the impact times, and squashes on contact with
  `exp(-20 dt) * cos(38 dt)`.
- Expose `window.__s3render(t)`, and call it from the master clock (see `master-clock.md`). Every value is a
  function of `t`.

## Sound

Three thumps on the impacts, a low drone under the orbit, and a whoosh on the push.

## Adapting

In 9:16, tilt the camera down more and let the field fill the height. Take the block colours from the
brand's palette.
