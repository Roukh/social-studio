# live-readout-hud

**Family:** data, texture. **Wants:** the whole shot. **Source:** a science explainer ("photon journey from
the Sun") in prompt-motion.com's gallery, studied 2026-10-07.

## Looks

A small corner readout (a counter, a pair of values, a running count) keeps changing through a story beat,
independent of the words landing over it. It makes the scene feel measured and alive.

## Build

- A monospace DOM text block. Each value is a pure function of time, such as `floor(rate * t)`, set with
  `kit.setText`, with no easing.
- Keep its contrast low enough not to fight the main words.

## Adapting

Use it under any scene that has a quantity: visitors, time saved, steps done. Real numbers only when the
brief gives them; otherwise they are samples.
