# layer-stack-collapse

**Family:** structure, 3d. **Wants:** 2-2.5 s. **Source:** a Lism CSS release video in prompt-motion.com's
gallery (prompt-motion.com/ddryo-loos-300829), studied 2026-10-09.

## Looks

A deck of flat, translucent shapes (cards, diamonds, planes) sits stacked with a slight 3D offset, each one
named by a small label and a leader line (a rule, a layer, a step in an order of precedence). One outlined,
unfilled shape near the top is called out as the exception. The whole stack then compresses straight down into
a single solid, opaque shape of the same silhouette: the many rules read as one simple result.

## Build

- Each layer is a DOM or SVG shape (`transform: translateY + translateZ` via a shared `perspective`), stacked
  with a small, even vertical and depth offset, decreasing opacity toward the back.
- Labels sit beside the stack on thin leader lines that fade in with their layer, staggered top to bottom or
  bottom to top on the beat.
- The collapse tweens every layer's `y` and `z` to 0 and its opacity to 1 on `power3.in`, finishing as one flat
  shape; the labels fade out just before impact.

## Sound

A soft layered hum while the stack is held, and a single solid thump on the collapse.

## Adapting

Use it for anything built from ordered rules or steps that should feel simple in the end: CSS cascade layers,
a permissions hierarchy, a pipeline, a design system's token tiers.
