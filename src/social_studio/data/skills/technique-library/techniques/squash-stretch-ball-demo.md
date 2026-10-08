# squash-stretch-ball-demo

**Family:** physics, annotation. **Wants:** 1.5-2 s. **Source:** Himanshu's 15 s showreel
(x.com/himanshutwtxs/status/2103495232637882858), studied 2026-10-07.

## Looks

A ball falls and leaves a trail of ghost circles, so the spacing between frames is visible: wide while it is
fast, tight near the top. It squashes on landing and stretches on the rebound, and each phase is labelled by
hand.

## Build

- One 2D canvas from the master clock.
- Draw N trailing copies of the ball at its positions from earlier frames (computed from the same motion
  function at `t - k * dt`), with falling opacity.
- The squash and stretch scale the ball along its velocity, preserving its area.

## Sound

A thump on the squash.

## Adapting

The ball can be any object in the film (the through-line dot, a product, a logo mark). Pair it with
`annotated-diagram-overlay.md` for the labels.
