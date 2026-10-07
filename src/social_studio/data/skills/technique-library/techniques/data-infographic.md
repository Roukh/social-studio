# data-infographic

**Family:** data. **Wants:** 2-2.5 s, plus at least 0.8 s of settled read time. **Source:** the 2026 Opus
showreels; built in `examples/reel-2026-10-06.html`, S5.

## Looks

On a light ground, shutters rise into place, then the infographic builds:

- a big percentage rolls up with blurred digits;
- a donut draws its track and fills to its value;
- twelve bars grow from a baseline on an uneven stagger, with the last bar in the accent colour;
- a spline draws across with a travelling dot and a value pill that springs up at the end.

Mono labels clip in beside each element, and a "Sample" tag marks the numbers as illustrative.

## Build

- Donut: an SVG circle with `strokeDasharray = 2πr`, and `strokeDashoffset` animated from `C` to
  `C * (1 - value)` on `power3.out`.
- Bars: `scaleY 0 -> 1` from a bottom origin. The stagger is `0.042 * (1 + 0.3 sin(2.1 i))`, uneven on
  purpose.
- Spline: a Catmull-Rom curve through points just above the bar tops, converted to cubic Béziers (control
  points at `p1 + (p2 - p0) / 6`). It draws with `strokeDashoffset`, and the dot follows `getPointAtLength`,
  driven by the clock.
- The number roll-up: the digits slide on the timeline under a vertical `feGaussianBlur`
  (`stdDeviation="0 N"`) whose strength follows their speed.
- The value pill uses a spring ease, with response about 0.36 and damping about 0.78.

## Sound

Blips on each bar on the sixteenth grid, a rising tone under the roll-up, and a pop on the pill.

## Adapting

Use real numbers only when the brief gives them. Otherwise, use labelled samples. In 9:16, stack the number
over the chart.
