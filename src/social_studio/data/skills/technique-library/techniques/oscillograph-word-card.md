# oscillograph-word-card

**Family:** type, data. **Wants:** 1.2-3 s per card. **Source:** prompt-motion.com's gallery (rneayan-ea6129),
studied 2026-10-09.

## Looks

A short word or phrase hard-cuts onto a black field in a thin monochrome outline or mono font, and beside or
beneath it a small generative diagram -- a tangled knot of overlapping curves, a woven pair of threads, a pair
of spikes, a radial fan, a stepped pulse -- echoes what the word means: a knot for "complex," a weave for
"combined skill," a spike pair for "order," a sweep for "control," a step for "a process underway." A thin live
waveform strip runs the length of the frame's bottom edge throughout, breathing under every card.

## Build

- Each card is a DOM word/phrase (mono or thin outline face) hard-cut in with no easing, on the beat.
- The diagram is 2D canvas or SVG, generated from a small set of parametric curves (Lissajous-style knots, sine
  pairs, spike functions, stepped pulses) seeded per card so each shape is unique but reads as "the same
  instrument" throughout the run.
- Keep exactly one glyph per card; never animate two diagrams in the same card.
- Pair with `waveform-readout-strip.md` for the persistent bottom strip and `hud-frame.md` for the surrounding
  chrome.

## Sound

A soft blip or tick as each card cuts in; a very low synth hum under the waveform strip.

## Adapting

Pick the diagram family (knot, weave, spike, sweep, step) to match the word's sense, not at random -- the
mapping is the whole trick. Works for any technical, process-driven or data-literate brand voice.
