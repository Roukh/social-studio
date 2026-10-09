# prompt-bar-generate

**Family:** interface, type. **Wants:** 2-3.5 s. **Source:** prompt-motion.com's gallery
(rossaxbt-3085b7), studied 2026-10-09.

## Looks

A minimal, rounded prompt bar sits alone on an open field. A short phrase types on into it character by
character with a blinking cursor, then a round submit button presses down and springs back. The instant it
releases, a generated result (an image, a card) pops up just below or beside the bar, soft-focus to sharp, with
a small labelled chip naming the style or mode used, as the payoff.

## Build

- The input is DOM text revealed per character with `kit.typeOn`, same mechanic as `dual-voice-type.md` but one
  voice, in the brand's UI font, inside a pill with a soft ambient glow behind it.
- The submit button scales `1 -> 0.88 -> 1` on `power3.out` across the press.
- The result pops in at `scale: 0.92 -> 1` with `filter: blur(6px) -> blur(0)`, 0.2-0.3 s, right after the
  press resolves.
- The chip fades/slides up 4-6 px after the result lands, same timing family as `terminal-type-on.md`'s status
  line.

## Sound

A soft key tick per character, a click on the press, and a light pop as the result resolves.

## Adapting

Use it for any "ask it, get it" product moment: an image generator, a copy generator, a code generator, a
search. Keep the typed phrase short (2-5 words) and the result honestly generic, not a real brand's output.
