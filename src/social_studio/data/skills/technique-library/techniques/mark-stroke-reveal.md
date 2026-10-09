# mark-stroke-reveal

**Family:** identity, open. **Wants:** 1.5-2.5 s. **Source:** prompt-motion.com's gallery
(jesscaroline7-1ff7cb), studied 2026-10-09.

## Looks

A lone accent dot sits still in a dark field, then a thick geometric stroke draws itself outward from that
point until it completes the brand's mark. The wordmark types in beside or under it the instant the stroke
lands, as one settled block rather than letter by letter, so the whole open reads as "the mark is built, then
named."

## Build

- SVG `path` for the mark with `stroke-dasharray` set to its length and `stroke-dashoffset` tweened from the
  length to 0 on `power2.out`, 0.5-0.7 s.
- The anchor dot is a small filled circle at the path's start point with a soft radial glow (`filter:
  blur()` layer behind it at low opacity); it never moves.
- The wordmark is a single block (not staggered per letter) that fades and rises in (`y: 8px -> 0`,
  `opacity: 0 -> 1`) starting the instant the stroke's dashoffset reaches 0.

## Sound

A soft low swell under the draw, one clean hit exactly as the stroke completes.

## Adapting

Works for any single-stroke or few-stroke mark; a mark with disconnected pieces can draw each piece on its own
short stagger instead of one continuous path. Keep the anchor dot as a through-line element if the film reuses
it elsewhere (see `through-line.md`).
