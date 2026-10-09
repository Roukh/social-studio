# ring-breakout-orbit

**Family:** physics, generative. **Wants:** 1.5-2.5 s per ring, repeatable as a loop. **Source:**
prompt-motion.com's gallery (kantamk-61f410), studied 2026-10-09.

## Looks

A ball on a tether orbits inside a set of concentric rings, each ring broken by one open gap. The ball swings
out, finds the current ring's gap, and passes through it in a small burst of particles; that ring then
dissolves or fades, a counter ticks down ("n rings left"), and the whole palette shifts a step around the hue
wheel. The pattern repeats ring by ring until just one remains, each pass a little faster and brighter than the
last.

## Build

- Rings are arcs with a seeded gap angle (`strokeDasharray` leaving one open segment); outer rings are static
  decoration (thin, dim, not interactive), only the current innermost ring matters for the pass.
  the ball orbits on a radius just inside the current ring (`x = cx + r*cos(theta)`, `y = cy + r*sin(theta)`,
  theta driven by the master clock), with a thin tether line from the centre dot to the ball.
- The "pass" is timed to when `theta` crosses the gap's angle: spawn 8-16 small particles radiating outward
  from that point, fade the passed ring's opacity to 0 over 200-300ms, and step the counter and the hue (`hue
  += 360/ringCount`) on that same beat.
- Each ring's pass can run slightly faster than the previous (`orbit speed *= 1.05`) so the loop accelerates
  toward the end.

## Sound

One note per ring, stepping up a scale (pentatonic reads well) so the whole sequence plays as a short melody;
a soft swoosh under the orbit, a brighter chime on the final ring's pass.

## Adapting

Any countdown or multi-step unlock reads well this way: stages, levels, steps in a checklist. Keep the gap
angle seeded (not literally random each render) so the pass always looks intentional, never lucky.
