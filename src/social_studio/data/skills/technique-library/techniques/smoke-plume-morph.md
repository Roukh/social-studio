# smoke-plume-morph

**Family:** generative, physics. **Wants:** 2-3 s. **Source:** prompt-motion.com's gallery
(lexnlin-038035), studied 2026-10-09.

## Looks

A monochrome plume of smoke or ink curls and billows across the frame, and for a moment its drifting form
reads as a recognisable silhouette (a bird's head, a wing) before dissolving back into abstract wisps. A single
thin accent line traces alongside it like a flight path, with one small accent dot riding its tip.

## Build

- A fluid/smoke simulation (a stable-fluids solver or a cheap curl-noise advected particle field rendered as
  overlapping soft strokes) driven toward a target silhouette mask at its peak-legibility frame, then released
  back to free drift.
- The accent line is a separate hand-eased path (not part of the sim) so it stays crisp and readable against
  the organic noise of the smoke.
- Render in monochrome ink-on-paper style (no colour in the smoke itself) to match a restrained, editorial
  palette; only the accent dot and line carry colour.

## Sound

A very soft, low whoosh under the plume's motion, nothing sharp or percussive.

## Adapting

This is an expensive, bespoke shot — reserve it for a single hero moment, not a repeatable beat. A cheaper
stand-in is a curl-noise particle field with no target silhouette, just organic drift.
