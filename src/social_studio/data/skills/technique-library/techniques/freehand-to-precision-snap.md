# freehand-to-precision-snap

**Family:** annotation, reveal. **Wants:** 2-3 s. **Source:** prompt-motion.com's gallery
(adamdesgns-478d6d), studied 2026-10-09.

## Looks

A loose, hand-drawn squiggle (a sketch, a rough idea) is traced on screen by a small pen or cursor glyph at
its tip, over a faint isometric or grid field. The instant it finishes, it snaps into a precise, straightened
version of the same shape: clean right angles, with length and angle callouts popping in at each vertex and a
small "cleaned up" confirmation chip. The rough and the precise read as the same idea, before and after.

## Build

- Rough path: an SVG path with a hand-jittered point set (seeded noise offsets on an otherwise straight
  route), stroked on with `strokeDashoffset`; a small circular glyph rides the tip.
- Snap: cross-fade or morph the rough path's points to their straightened target points (resample both to the
  same point count, lerp on `back.out` for a slight overshoot snap) over 0.2-0.3 s.
- Callouts (angle arcs, length labels) key in right after the snap, staggered 0.05-0.08 s apart, anchored to
  each vertex.

## Sound

A soft pencil scratch under the sketch, then a single crisp snap hit as it straightens, with a tick per
callout.

## Adapting

Use it for any "messy input, precise output" beat: a sketch becoming a spec, a rough note becoming a
structured record, an idea becoming a measured plan.
