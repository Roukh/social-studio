# fan-out-branch-diagram

**Family:** data, structure. **Wants:** 2.5-3.5 s. **Source:** an AI Arena product promo in
prompt-motion.com's gallery (prompt-motion.com/ezshine-c90d73), studied 2026-10-09.

## Looks

One source block (a data file, a prompt, a request) sits on the left. Thin curved lines draw out from it to a
column of labelled endpoint chips on the right (model names, agents, recipients), each line a different
accent colour, arriving on a stagger. The shot closes on a short checklist beneath it: a few green checks for
what stays fair or constant, a red cross for the one thing that is never done (biasing a result, picking a
favourite).

## Build

- The source block is a DOM/code panel. Each branch line is an SVG bezier path (`strokeDashoffset` reveal) from
  the block's edge to its endpoint chip, staggered 0.08-0.12 s apart.
- Each endpoint chip fades/scales in exactly as its line arrives, coloured to match its line.
- The checklist rows reveal beneath on their own short stagger after the last branch lands; checks and the one
  cross use the same icon size, only the colour and glyph differ.

## Sound

A soft whoosh per branch line, a tick on each chip's arrival, and one lower tone on the checklist's cross item.

## Adapting

Use it whenever one input must visibly reach several parallel recipients under the same rules: a broadcast, a
fan-out job, a fairness or compliance claim, a single prompt sent to many models.

## Variants

The same move, as other reference films staged it:

- **branch select tree** (prompt-motion.com's gallery (macrohou-33959d), studied 2026-10-09.): A single completed node (a checkmark circle, a finished step) sits at the left with several thin lines branching out from it to a short list of candidate labels. One candidate bolds and solidifies while the rest stay faint and thin, as if the system is visibly weighing options and settling on the next one.
