# blur-echo-statement-card

**Family:** type, texture. **Wants:** 2-5 s. **Source:** prompt-motion.com's gallery (sachaarbonel-8f14f4),
studied 2026-10-09.

## Looks

A short eyebrow label and a two-line statement, a plain first line and a softer, muted italic second line,
fade and rise into a flat, airy gradient field. The exact art that proves the line (a UI shot, a photo) sits
enlarged and heavily blurred behind the text as a soft colour echo, never sharp enough to read. The card holds,
then hard-cuts to the next beat's label, lines and echoed art together.

## Build

- The eyebrow label fades in first, about 0.15 s; the first line rises 6-8 px in on `power2.out`; the second,
  italic line follows after a short pause at a lower opacity.
- The background is the same raster used elsewhere in that beat, scaled 1.15-1.3x with a heavy blur
  (`filter: blur(40-60px)`) and a soft gradient wash over it; it cross-fades to the next beat's source the
  instant the cut lands, so colour continuity carries across the hard cut.
- Keep the text block itself perfectly still; all the motion is the fade/rise-in and the background cross-fade.

## Sound

A soft intake on the label, a light rise under each line landing, and silence held through the hold.

## Adapting

Use it as connective tissue between data or product beats in any explainer. Keep the eyebrow label short (one
to three words) and the second line the softer, more human one. Pair it with whatever technique the beat's own
UI or data needs; this covers only the surrounding card.
