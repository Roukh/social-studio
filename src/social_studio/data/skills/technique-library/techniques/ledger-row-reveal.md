# ledger-row-reveal

**Family:** data. **Wants:** 2-2.5 s, plus hold time to read. **Source:** prompt-motion.com's gallery
(palashbagchi11-0a4b6b), studied 2026-10-09.

## Looks

A short, ranked data table builds row by row under a blunt headline stating the finding. Each row carries a
rank number, a label (with a dim sub-label), a small status pill (a colour-coded word) and a value, right
aligned. Rows land top to bottom on a stagger. The worst rows (a dead link, a zero value) are picked out in the
accent or warning colour so the eye finds the damage without reading every cell.

## Build

- One DOM table/list; each row is a flex line with a rank, a label (+ a dim URL-style sub-label), a pill
  (rounded chip, coloured by status) and a value column.
- Rows reveal on `y: 6px -> 0`, `opacity 0 -> 1`, staggered 0.06-0.09 s apart, `power2.out`.
- A row whose status is the bad case (dead, missing, zero) gets its pill and value tinted in the warning/accent
  colour and a faint background tint strip; every other row stays neutral ink on the ground colour.
- The headline above states the row data as a plain sentence (a percentage, a count) and lands just before the
  rows start, not after.

## Sound

A dry tick per row landing, a slightly harder tick on a bad-status row.

## Adapting

Use for any audit, leaderboard or receipt beat: broken links, failed checks, worst performers. Keep it to 3-5
rows; more than that and the read drags. The ranks, labels and values should be samples unless the brief gives
real ones.
