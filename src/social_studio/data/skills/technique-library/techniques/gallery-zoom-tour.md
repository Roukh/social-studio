# gallery-zoom-tour

**Family:** structure, transition. **Wants:** 4-8 s. **Source:** prompt-motion.com's own promo, in its
gallery of Claude-made motion films, studied 2026-10-07.

## Looks

One tile fills the frame. The camera pulls back to show it is one of a grid of live tiles, whips into a
different tile until that tile fills the frame, then match-cuts into that tile's own scene. It is one
continuous camera through many pieces.

## Build

- Absolutely positioned DOM cards (or three.js planes) in one large world container.
- GSAP drives a pseudo-camera as (focus x, focus y, log scale). The world's transform is
  `translate(-focus) scale(exp(logScale))`, so the zoom speed feels even.
- A tile's corner radius tweens to 0 as it reaches full-bleed.
- Each tile's content plays from the clock, even when small.

## Sound

A soft shift on the pull-back and a whoosh on each whip.

## Adapting

Use it for a portfolio, a set of features, or several clients' sites, each a sample. Keep one camera move at a
time (see the camera principle).
