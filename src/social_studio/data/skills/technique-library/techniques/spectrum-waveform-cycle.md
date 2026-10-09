# spectrum-waveform-cycle

**Family:** data, texture. **Wants:** 1.2-1.8 s per step, 2-3 steps per shot. **Source:** reflex-cloud-72ffe5
(prompt-motion.com/reflex-cloud-72ffe5), studied 2026-10-09.

## Looks

A full-bleed colour field shifts hue on each beat while a drawn oscilloscope line beneath it tightens and
quickens its oscillation, and a corner read-out climbs a value in lockstep — so the colour, the number and the
waveform all read as one quantity intensifying at once.

## Build

- Two or three overlapping canvas waveform paths, each `y = A sin(f t + phase)`, whose frequency `f` scales
  with a clock-driven value.
- The background hue interpolates across a fixed colour ramp (`kit.lerpColor`) keyed to that same value.
- A mono corner label ticks the raw number with no easing, the same mechanic as `live-readout-hud.md`.
- Cut on each step rather than crossfade, so every beat reads as a notch up, not a smooth slide.

## Sound

A tone that climbs in pitch with the value, a soft chime landing on each cut.

## Adapting

Use for any metric that should feel like it is accelerating or sharpening: processing speed, signal clarity,
confidence, throughput. The literal unit (THz, ms, %) can be swapped for whatever the brief measures.
