# wordmark-assemble

**Family:** identity, type. **Wants:** 1.3-2.5 s. **Source:** the 2026 Opus showreels; built in
`examples/reel-2026-10-06.html`, S2.

## Looks

The name drops in letter by letter from above, starting at the centre and spreading outward, each letter
clearing from a heavy blur as it lands. An italic serif phrase wipes in under it from the left. A mono kicker
types on. Then a weight wave runs across the letters: each one thins and swells back to black in turn.

## Build

- Split the word into letter spans. For letter `i`, the delay grows with its distance from the centre:
  `dist * 0.032 s`, plus a small odd/even jitter so the run is not mechanical.
- Each letter moves `y: -(200 + dist * 22) -> 0` and `filter: blur(18px) -> blur(0)` over about 0.36 s on
  `power3.out`. A 0.07 s opacity snap goes on top.
- The serif line reveals with `clipPath: inset(0 100% 0 0) -> inset(0)` plus a small x slide.
- The weight wave tweens `fontVariationSettings: '"wght" 300'`, then `900`, per letter at 0.03 s steps. It
  needs a variable font; with a static font, use scaleY or letter-spacing as the wave instead.
- Leave on a blurred circle wipe (see `transitions.md`).

## Sound

A soft tick per letter on the sixteenth grid, a swell under the serif line, and a whoosh into the wipe.

## Adapting

Use the brand's display font at its heaviest weight and tight tracking, and the brand's serif or italic for the
phrase if it has one.
