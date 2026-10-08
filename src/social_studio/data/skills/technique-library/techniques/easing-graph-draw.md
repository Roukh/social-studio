# easing-graph-draw

**Family:** data, annotation. **Wants:** 2.5-3 s (a building shot may hold longer). **Source:** Himanshu's 15 s
showreel (x.com/himanshutwtxs/status/2103495232637882858), studied 2026-10-07.

## Looks

A position-over-time graph draws a straight line, labelled as the wrong way ("linear = robotic"), then
redraws it as an S-curve with a check mark. Under it, a row of small boxes marches along a timeline and bunches
and spreads to match the curve, so the curve and its effect are visible at once.

## Build

- One 2D canvas from the master clock.
- The curve draws with a progressive `lineTo` reveal up to the current time.
- The marching boxes' x positions are the same ease function the graph shows (`kit.ease.p3io`, for example),
  so the picture is the maths.
- Use the accent colour only for the correct curve.

## Sound

A quiet bed with a tick per box.

## Adapting

Any before/after of a curve works: growth, cost, speed, a load time.
