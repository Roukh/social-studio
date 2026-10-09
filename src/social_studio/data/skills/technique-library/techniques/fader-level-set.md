# fader-level-set

**Family:** interface, data. **Wants:** 2-3 s. **Source:** rneayan-474bcf (prompt-motion.com/rneayan-474bcf),
studied 2026-10-09.

## Looks

A row of vertical sliders, one per named control, animate their handles to new positions at different times,
as if someone were mixing a board live — showing that each part of the process can be pushed up or down
independently, rather than left on an unseen default.

## Build

- DOM tracks with a handle positioned by `translateY`, each handle tweening to its target value on its own
  beat (`power2.out`, 0.3-0.4 s), staggered 0.1-0.2 s apart so they never move in unison.
- A short label sits under each track naming what it controls.

## Sound

A soft mechanical slide per handle, landing on a faint click as each settles.

## Adapting

Use for any "you stay in control of the mix" claim: a pipeline's stages, a set of settings, a blend of inputs.
Name the controls after the brief's own levers, not generic placeholders.
