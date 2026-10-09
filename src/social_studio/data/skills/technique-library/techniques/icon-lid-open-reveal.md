# icon-lid-open-reveal

**Family:** reveal, transition. **Wants:** 2-3 s. **Source:** prompt-motion.com's gallery
(twoclipping-221cab), studied 2026-10-09.

## Looks

A simple rounded shape, a pill or a square, on an empty field morphs into a small square icon with a hinged
lid. The lid tips open and a tiny, glowing diorama scene sits inside it: a figure, a doorway, a light source,
small enough to feel like a peephole into another world. The camera does not move; the box does the revealing.

## Build

- The pill-to-icon morph is a shape tween (`border-radius` and `width/height`) on `power3.inOut`.
- The lid is a separate DOM or SVG layer with its own `transform-origin` at the hinge edge, rotating open on
  `back.out` for a small overshoot.
- The scene inside is a small, self-contained render (a tiny canvas or a cropped video) that only starts
  playing once the lid has opened past a threshold angle.

## Sound

A soft mechanical click as the shape resolves into the icon, a creak on the lid opening, and a faint ambient
tone from the scene inside.

## Adapting

Use it as a teaser open for any generative or AI-image product: the box is the product, the diorama is a
sample of what it makes. Keep the inside scene small and slightly mysterious; the next shot pays it off at
full size.
