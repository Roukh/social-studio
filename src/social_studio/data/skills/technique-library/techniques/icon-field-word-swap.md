# icon-field-word-swap

**Family:** open, type. **Wants:** 1.5-2.5 s. **Source:** an investing-platform demo film in
prompt-motion.com's gallery (prompt-motion.com/rammanq-f5a90f), studied 2026-10-09.

## Looks

Small brand or category icon bubbles sit scattered loosely across the frame, drifting gently, behind one bold
word set large and centred. The word hard-cuts to a second word naming a sibling category (one asset class to
another, one mode to another), while the icon field holds its loose arrangement underneath. Then the icons
drift apart toward the frame's edges and fade, clearing the frame down to a single small accent dot, which
becomes the film's through-line marker for the rest of the piece.

## Build

- Icon bubbles are DOM or SVG chips at seeded positions (`kit.rng(seed)`), with a slow idle drift (a sine
  offset of a few px) so the field never sits dead still.
- The headline is one DOM block per word, hard-swapped (no crossfade) on the beat, `kit.beat(n, bpm)`.
- On the clearing beat, each icon bubble tweens from its seeded position to a far edge or corner on
  `power3.in`, staggered 20-40 ms apart, with opacity dropping as it leaves frame. The last element left on
  screen is one small accent dot, held.

## Sound

A soft ambient hum under the drift, a hit on each word swap, and a whoosh as the icons clear.

## Adapting

Use to open a film that covers two or three sibling categories or modes before the product's real UI appears.
Reuse the surviving accent dot as the through-line dot in later scenes if the film has one (see
`through-line.md`).
