# reticle-lock-decode

**Family:** frame, annotation. **Wants:** 2-3 s. **Source:** reflex-cloud-72ffe5
(prompt-motion.com/reflex-cloud-72ffe5), studied 2026-10-09.

## Looks

A macro subject fills the frame while a thin bracket reticle locks onto one point of interest and tightens as
the camera pushes in. Beside the bracket, a small mono label flickers through scrambled characters before
locking into a real status word, with a live numeric readout ticking beside it — so the shot reads as something
actively measuring the subject, not just captioning it.

## Build

- A DOM bracket (two or four corner marks) sits over the target point; its corner gap narrows on `power2.out`
  as the background plate scales up slowly for the push-in.
- The label uses the same scramble-then-lock mechanic as `end-card-decode.md`: each character shows a seeded
  random glyph per frame (`kit.rng(frame * 31 + i * 7)`) until its own staggered lock time, then holds its real
  glyph.
- The numeric readout under the label is a pure function of time with no easing, the same mechanic as
  `live-readout-hud.md` (`kit.setText` from `floor(rate * t)`).

## Sound

A soft electronic chirp as the bracket tightens and locks, a few data ticks as the readout updates.

## Adapting

Works for any product that frames itself as perceiving or measuring: a camera, a sensor, a vision model, a
scanner. The subject can be an eye, a lens, a material sample, a cityscape — anything the brand "looks at."
