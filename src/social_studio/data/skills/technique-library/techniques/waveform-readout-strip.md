# waveform-readout-strip

**Family:** texture, data. **Wants:** the whole shot, or the whole film as a persistent layer. **Source:**
prompt-motion.com's gallery (kloss-xyz-15182a), studied 2026-10-09.

## Looks

A thin ribbon of waveform bars sits along one edge of the frame, each bar's height riding the track's actual
amplitude at that instant, in the accent colour at low opacity so it reads as texture rather than a UI widget.
It makes whatever type is on screen feel like it's being said out loud, not just captioned.

## Build

- A row of thin bars (40-80 across the frame width), each bar's height driven by a band of the audio's
  analysed amplitude at the current time (precomputed offline into a lookup array keyed by frame, since there is
  no live audio API at render time).
- Smooth bar heights with a short attack / slower release (`height = max(newHeight, height * 0.85)`) so the
  strip pulses rather than jitters.

## Sound

It visualises whatever is already playing; it adds nothing of its own.

## Adapting

Works as a one-off accent under a closing statement, or as a through-line layer (see `through-line.md`) that
runs the whole film at very low opacity.
