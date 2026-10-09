# script-accent-underline

**Family:** type. **Wants:** 1.5-2.5 s. **Source:** a Momwise parenting-app hype video in
prompt-motion.com's gallery (prompt-motion.com/francoxavier33-d2dfd2), studied 2026-10-09.

## Looks

A short serif or display headline types on character by character with a blinking cursor, in a warm, editorial
voice. The one emphasised word in the line switches to a loose cursive script face as it lands, and a
hand-drawn underline swash draws itself beneath that word a beat later, like a note underlined by hand.

## Build

- The headline types on with `kit.typeOn`, one voice, with a blinking `::after` cursor that advances with the
  text (same mechanic as `terminal-type-on.md`, in a serif face instead of mono).
- The emphasised word is a separate span in a script/cursive font, landing with the same typing rhythm as the
  rest of the line.
- The underline is an SVG path under the word, revealed with `strokeDashoffset`, hand-wobbled (a few extra
  control points, not a straight line), drawn after the word finishes on `power2.out`.

## Sound

A soft typewriter clack per character, and a light pen-on-paper swish under the underline draw.

## Adapting

Use it for any warm, human-voiced brand (family, wellness, craft) that wants a typed headline to feel personal
rather than corporate. The cursive word should be the one idea the shot is about.
