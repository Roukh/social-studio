# ticker-tape-marquee

**Family:** data, texture. **Wants:** the whole shot, or the whole film. **Source:** prompt-motion.com's
gallery (aistocksavvy-3fb9f5), studied 2026-10-09.

## Looks

A thin strip along the top or bottom edge scrolls a continuous row of short data tokens (symbols and
values, or any short label/number pair) sideways at a steady speed, like a stock ticker or a news wire. It
never eases and never stops, so it reads as a live feed running under the main scene rather than as a
decoration.

## Build

- A DOM row of tokens, duplicated end to end so the loop is seamless, inside an `overflow: hidden` strip.
- `translateX` runs linearly (no easing) from the clock: `x = -(t * speed) % loopWidth`.
- Keep its contrast low and its type small; it is a texture under the main content, not something to read.

## Sound

None, or a very quiet high-frequency tick bed under it.

## Adapting

Any domain with a live-feeling stream of short facts works: prices, scores, headlines, log lines, order IDs.
Pair it with `hud-frame.md` or `live-readout-hud.md` for a fully instrumented frame.
