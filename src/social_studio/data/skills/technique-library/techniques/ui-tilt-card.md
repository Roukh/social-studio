# ui-tilt-card

**Family:** interface, 3D. **Wants:** 2-2.5 s. **Source:** Framer's "skills" ad
(instagram.com/p/DdtwW_Ws0Xx), studied 2026-10-07.

## Looks

An interface panel or screen is held at a fixed, shallow 3D tilt, 8-15 degrees on two axes, over a near-black
field, with a soft shadow under it. Its content slides or swaps in place while the tilt stays. Flat interface
content gains depth without looking like a screenshot.

## Build

- A DOM panel inside a parent with CSS `perspective` (about 1,200-1,800 px), with `rotateX` and `rotateY`, and
  a slow drift of a degree or two on the clock.
- For a real highlight sweeping across the glass, use a three.js plane with a `CanvasTexture` of the
  interface and a moving specular light.
- The shadow is a blurred, offset copy of the panel, tinted toward the field.

## Sound

A soft slide or whoosh as it enters.

## Adapting

Use it for any interface, product screen or document. Keep one tilt per shot (see the camera principle).
