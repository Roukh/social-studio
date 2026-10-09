# stage-numeral-marker

**Family:** structure, type. **Wants:** the whole shot, cycling 0.8-1.5 s per stage. **Source:**
prompt-motion.com's gallery (kyonax-on-tech-aabc1d), studied 2026-10-09.

## Looks

A huge outline or flat numeral sits in a corner of the frame beside a short all-caps label (01, 02 PARSE, 03
STYLE); as the process it names moves to its next step, the numeral and label cross-fade to the next pair while
the main content area swaps to match that stage (source code, then a tree diagram, then a rendered page). The
numeral is the one element that tells the viewer which step of the pipeline they're watching.

## Build

- Numeral and label are one fixed-position group; on each stage change the old pair slides up out of a mask as
  the new one slides in from below (150-200 ms, `power3.out`), rather than counting up, since steps are discrete
  named stages, not a continuous count. The source cross-faded; a spatial roll keeps the house motion language.
- The main content swap is cued on the same beat as the numeral change, so the two always read as cause and
  effect: new stage, new numeral, new content.

## Sound

A short digital blip on each stage change, pitched slightly differently per stage.

## Adapting

Use for any named multi-stage pipeline (parse, build, ship; upload, process, deliver). Keep stage count to
3-5; more than that and the numeral stops being readable at a glance.

## Variants

The same move, as other reference films staged it:

- **stage counter dot fill** (rneayan-474bcf (prompt-motion.com/rneayan-474bcf), studied 2026-10-09.): A two-digit stage number and its label cut forward through a sequence (step one, a middle step, a later step, the final step) while, beside it, a row of small dots fills in one by one to track progress. On the last step a diagonal banner sweeps across the frame announcing it is done.
