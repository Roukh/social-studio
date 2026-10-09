# lockup-close-card

**Family:** close, identity. **Wants:** 1.5-2.5 s. **Source:** prompt-motion.com's gallery
(justincooperman-e7bbc4), studied 2026-10-09.

## Looks

On a flat or softly gradient ground in the brand's colour, the mark and wordmark settle together, a short
tagline line fades in under it, and a small pill-shaped CTA button arrives last and holds. Nothing moves once
it's all in place; the frame simply sits on the lockup as the film ends.

## Build

- Mark and wordmark arrive together as one group (`y: 8-12px -> 0`, `opacity 0 -> 1`, power2.out, 300-400ms).
- The tagline fades in 150-200ms after the lockup settles, no motion beyond opacity.
- The CTA pill arrives last, 150-200ms after the tagline, with a touch of scale overshoot (`0.95 -> 1.02 ->
  1`) so it reads as the one interactive element in an otherwise static card.

## Sound

A soft low swell that fades out under the hold, no new hits once the pill lands.

## Adapting

This is a resting beat, not a feature beat: keep it under three seconds and resist adding more motion. In
9:16, stack mark above wordmark instead of beside it.
