# pipeline-chip-flow

**Family:** interface, structure. **Wants:** 2-3 s. **Source:** prompt-motion.com's gallery
(prasad-pilla-2c0cba), studied 2026-10-09.

## Looks

A short run of rounded step chips, a word and a small mono sub-label each, builds left to right, a thin arrow
drawing on between each pair as it lands. Once the whole line is built, a subset of chips (the steps already
done) swaps to an active fill colour and a one-line caption clips in beneath the row to name what changed.

## Build

- Chips are DOM cards in a flex row with fixed gaps; each chip pops in (`scale 0.92 -> 1`, `opacity 0 -> 1`) on
  `power3.out`, staggered 0.12-0.18 s left to right.
- The connecting arrow between chip `i` and `i+1` is a thin line or chevron that draws on (`strokeDashoffset`
  or a `scaleX` reveal) right after chip `i` lands, before chip `i+1` starts.
- The active-state swap recolours a chip's fill and border on `power2.inOut` under 0.3 s, left to right if more
  than one chip changes.
- The caption beneath uses a `clip-path` inset collapsing to 0, timed just after the swap.

## Sound

A soft click per chip landing, a short tick on each arrow draw, a brighter chime on the active-state swap.

## Adapting

Use for any multi-step process: a pipeline, a workflow, an onboarding sequence. Three to five chips read best
on one line; more should wrap to a second row in 9:16.

## Variants

The same move, as other reference films staged it:

- **pipeline icon strand** (rneayan-474bcf (prompt-motion.com/rneayan-474bcf), studied 2026-10-09.): A single stroke draws itself across the frame under a headline, then small labelled icon-dots pop onto it one at a time in sequence, each naming one stage of a process, so many steps read as beads on one continuous line instead of a list or a grid.
