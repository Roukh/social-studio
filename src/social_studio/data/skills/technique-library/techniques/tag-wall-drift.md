# tag-wall-drift

**Family:** data, texture. **Wants:** 2.5-5 s. **Source:** prompt-motion.com's gallery (techyoutbe-945b56),
studied 2026-10-09.

## Looks

A dense wall of small rounded pills, each naming a different topic or skill, fills the frame in several rows
and drifts sideways at a slow, steady speed, different rows moving at slightly different speeds. A bold
headline sits perfectly still on top of the drift, so the wall reads as depth and breadth behind a single,
held claim.

## Build

- Pills are a repeating DOM or canvas row, duplicated and looped so the drift reads endless (`x` wraps modulo
  the row's total width).
- Each row's speed is a small multiple of a base rate (`row speed = base * (0.8 + 0.1 * rowIndex)`), uneven on
  purpose, for parallax.
- The headline is a fixed DOM layer above the pills with a soft drop shadow or a translucent backing so it
  stays legible over the moving colour.

## Sound

A soft, continuous low shimmer under the drift, with no individual hits.

## Adapting

Use it for breadth claims: topics covered, integrations supported, languages spoken, use cases served. Keep
the held headline short; it is the one thing that should not move.
