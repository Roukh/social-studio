# radial-progress-anticipation

**Family:** data, interface. **Wants:** 1.5-2 s. **Source:** Himanshu's 15 s showreel
(x.com/himanshutwtxs/status/2103495232637882858), studied 2026-10-07.

## Looks

A ring fills while a percentage counts up, with loose squares orbiting it. Before each step forward, the leading
dot pulls back a little, then advances. That is true anticipation, not just a tween.

## Build

- An SVG ring with `strokeDashoffset`, or a canvas arc, with the counter text set from the clock.
- Each step is a small negative move (about 10 % of the step) on `power2.in`, then the forward move on
  `power3.out`.
- The orbiting squares sit at seeded angles and rotate at different rates.

## Sound

A tick on each step of the percentage.

## Adapting

Any loading, building or counting moment. It is the clearest way to show the anticipation principle on screen.
