# provenance-glow-stroke

**Family:** texture, through-line. **Wants:** the whole film. **Source:** Framer's "skills" ad
(instagram.com/p/DdtwW_Ws0Xx), studied 2026-10-07.

## Looks

One accent colour, as a soft glow around an edge, marks whatever is live: the active chip, the current
panel's border, a typing cursor. Everything else stays flat and neutral. The glow moves from element to element
as the work moves, so the eye always knows where the action is.

## Build

- A shared `.live` class with a `box-shadow` glow, or a blurred duplicate behind the element.
- Its intensity and colour are a pure function of the clock. It moves by fading out on one element as it
  fades in on the next, on the beat.
- Never more than one live element at a time.

## Adapting

Use the brand's most saturated colour. It can be the film's through-line instead of a dot (see
`through-line.md`).
