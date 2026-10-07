# dot-drop-flood

**Family:** open, physics. **Wants:** 1.5-2.5 s. **Source:** the 2026 Opus showreels (reference studied
2026-10-06); built in `examples/reel-2026-10-06.html`, S1.

## Looks

A field of dots in perspective on a dark ground. One accent dot falls into it under gravity, with a mono
readout of its speed. It hits on the downbeat, squashes (about 1.48 x 0.62) and sends a shockwave ring through
the floor. Then it stretches into a line, the line carries a travelling sine wave on a riser, and the line
thickens into a band that floods the whole frame in the accent colour on the next downbeat.

## Build

- One 2D canvas drawn by `drawS1(t)` from the master clock (see `master-clock.md`). The floor dots project with
  `y = HZ + (CAM_H - lift) * FX / z` and `x = CX + X * FX / z`, and the shockwave lifts them as a ring
  travelling out from the impact.
- The fall is real physics, `y = y0 + v0 t + g t^2 / 2`, until the impact time. The squash is a damped
  oscillation after it, using `kit.spring`.
- Annotations (leader lines that draw on, labels that type on) collapse into the dot with a clip-path inset.
- The flood is the band's height going to the full frame on a `power3.in` ease, timed to the beat.

## Sound

A sub thump on the impact, a soft tick per readout update, a riser under the wave, and a hit on the flood.

## Adapting

In 9:16, drop the dot down the tall frame for a longer fall, and let the band rise from the bottom. The accent
dot is the film's through-line (see `through-line.md`): it can come back in every scene.
