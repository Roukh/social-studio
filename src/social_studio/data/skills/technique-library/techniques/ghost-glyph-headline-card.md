# ghost-glyph-headline-card

**Family:** type, open. **Wants:** 1.7-2.5 s per card. **Source:** prompt-motion.com's gallery
(jesscaroline7-1ff7cb), studied 2026-10-09.

## Looks

A flat colour card holds a short, punchy headline over a single huge punctuation mark or glyph, ghosted behind
the type at low opacity purely for scale and mood. A small icon sits under the headline, and a thin row of
dashes along the bottom tracks position in a short sequence, one dash filled per card. The card hard-cuts to a
near-identical one with new copy, same layout, same rhythm.

## Build

- The ghost glyph is one oversized character (the type's own punctuation, a symbol) at 12-18% opacity, scaled
  2-4x the headline's cap height, positioned so it reads behind rather than beside the text.
- Cards are hard cuts, not cross-fades, timed to the beat; the headline itself can have a small amount of
  built-in lift (`y: 6px -> 0`, under 0.2 s) so the cut doesn't feel completely static.
- The dash rail is `n` short rects; the active one is wider/solid, previous ones dim, future ones hollow.

## Sound

A dry tick on each card's arrival; nothing under the hold.

## Adapting

Use 2-3 cards for a quick question-and-answer or problem-framing beat; more than that and the rhythm drags.
Pair with a whip-pan or blur-scale out (see `transitions.md`) into the next section.
