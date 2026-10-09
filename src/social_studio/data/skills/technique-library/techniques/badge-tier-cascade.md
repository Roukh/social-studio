# badge-tier-cascade

**Family:** data, reveal. **Wants:** 2-4 s for a set of 3 badges. **Source:** prompt-motion.com's gallery
(jesscaroline7-1ff7cb), studied 2026-10-09.

## Looks

A short vertical list of status icons (a badge, a medal, a shield), each labelled with a name and a tier word.
Each icon's material and colour steps up through its tier ladder (bronze to silver to gold to a cool diamond
blue) while, beside it, a stat line fills in under the label. The icons step up out of sync with each other so
the read feels earned rather than simultaneous, and the last frame holds with every badge at its top tier and
every stat in place.

## Build

- One icon per row, same silhouette throughout; only its fill gradient and rim-light colour swap per tier
  (`kit.lerpColor` through the tier stops, not a hard cut, so it reads as upgrading, not replacing).
  Swap on `power2.inOut` under 0.3 s per step.
- Stagger the rows: row 2 starts its climb 0.15-0.25 s after row 1, row 3 after row 2, so the cascade reads
  left-to-right-then-down or top-to-bottom, never all at once.
- The stat line (a count, a label) clips in under the badge name only once that badge reaches its top tier,
  `clip-path` inset collapsing to 0, with the digits rolling up in the last 0.2 s.

## Sound

A light chime per tier step, pitching up with each tier, and a slightly longer chime on the final (top) tier
per badge.

## Adapting

Three to four badges read best; more than that, cut to the top two and hold. In a shorter film, skip the lower
tiers and only show the final, top-tier state arriving with a single swap-and-settle.
