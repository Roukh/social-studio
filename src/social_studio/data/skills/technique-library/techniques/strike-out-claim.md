# strike-out-claim

**Family:** type, open. **Wants:** 1.5-2.5 s. **Source:** prompt-motion.com's gallery (kmasiff-cc72cb),
studied 2026-10-09.

## Looks

A short headline sets up the problem, then a hand-drawn-style line strikes through the one word naming it, the
way someone would cross a line off a list. The rest of the headline lands around the struck word, often ending
on an accent-coloured word that states the fix, so the whole line reads as problem-named-then-negated in one
breath.

## Build

- The headline is one or two text rows, set before the strike so it never reflows. The struck word gets a
  single diagonal or horizontal stroke drawn across it (`strokeDashoffset` 0 -> length reversed, i.e. the line
  draws on, not fades), 200-300ms, with a slight hand-wobble on the path (2-3 control points, not a straight
  line) so it reads as drawn, not generated.
- The struck word can drop slightly in opacity (100% -> 60%) once the strike lands, while the rest of the
  headline (and its accent-coloured closing word) holds at full strength.

## Sound

A single marker-pen scribble/whoosh exactly as the strike draws on.

## Adapting

Use it once per film, on the headline that frames the core problem. Overusing the strike dilutes it into a
tic rather than a punctuation mark.
