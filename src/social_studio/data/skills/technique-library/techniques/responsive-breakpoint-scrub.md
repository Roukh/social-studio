# responsive-breakpoint-scrub

**Family:** data, interface. **Wants:** 2-3 s. **Source:** a Lism CSS release video in prompt-motion.com's
gallery (prompt-motion.com/ddryo-loos-300829), studied 2026-10-09.

## Looks

A ruler or scale along the top of a UI sample extends from a narrow width to a wide one, with small pill
markers popping in at each breakpoint it crosses (`sm 480`, `md 800`, `lg 1120`). As the ruler passes each
marker, the sample itself reflows live: a single stacked column of elements springs apart into a row of three
or four, each settling into its new slot.

## Build

- The ruler is a DOM line whose width tweens on the clock; breakpoint ticks are positioned as percentages of
  its max width, and each pill fades/scales in exactly when the ruler reaches it.
- The sample's layout is driven by the same clock value: interpolate each element's `x` and width between its
  narrow-layout slot and its wide-layout slot, `power2.inOut`, so the reflow and the ruler stay in lockstep.
- A highlighted marker (the active breakpoint) uses the brand's accent colour; passed markers dim.

## Sound

A tick on each breakpoint crossed, pitched slightly higher each time.

## Adapting

Use it for any responsive, adaptive or scalable claim: a design system's breakpoints, a pricing table
collapsing on mobile, a dashboard's column count. The reflow must be a real, legible layout change, not just a
resize.
