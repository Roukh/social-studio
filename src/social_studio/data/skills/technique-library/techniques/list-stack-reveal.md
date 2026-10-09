# list-stack-reveal

**Family:** type. **Wants:** 0.5-1 s per line, 1.5-3 s total. **Source:** a Lightspark social promo in
prompt-motion.com's gallery (prompt-motion.com/davidmarcus-a28a60), studied 2026-10-09.

## Looks

A short list builds top to bottom, one line at a time, on the beat. Each new line arrives at full weight and
full contrast while every earlier line in the stack desaturates to a dim secondary colour, so the eye always
lands on the newest line. The list can be a headline breaking across lines ("Money / still moves / like it's"),
a run of features ("Dollar accounts. / Stablecoins. / Bitcoin. ...") or a value proposition ("Open. / Neutral. /
Global."). The last line often stays at full brightness instead of dimming, as the shot's payoff.

## Build

- One DOM block of line spans. Each line fades/slides in (`opacity 0 -> 1`, `y: 8px -> 0`) on its own beat,
  `power2.out`, 0.25-0.35 s.
- On the same beat, every previously-landed line's colour tweens from the primary ink to a dim secondary
  (about 35-45% opacity or a grey token), except the final line of the list, which is left at full contrast.
- Stagger lines evenly on the beat grid; do not ease the dimming separately from the next line's arrival, so the
  two read as one motion.

## Sound

A soft tick per line landing, slightly louder on the last.

## Adapting

Works for a headline, a feature list, a value-prop triad, or any short list a script reads as a build-up to one
final word. Pairs with `kinetic-word-run.md` where the message needs harder cuts instead of a stack.
