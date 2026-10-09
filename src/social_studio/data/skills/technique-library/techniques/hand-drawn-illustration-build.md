# hand-drawn-illustration-build

**Family:** reveal, annotation. **Wants:** 4-8 s, synced to a narration line. **Source:** prompt-motion.com's
gallery (ajith-io-c52e09), studied 2026-10-09.

## Looks

A whiteboard-style illustration draws itself stroke by stroke, growing a piece at a time as a caption line
beneath it highlights word by word in sync, as if the narration is drawing the picture. A plant sketch, for
example, starts as two water drops and a root tangle, then a stem and first leaves ink in, then more leaves
and small labelled callouts, each new part appearing exactly when its word is spoken.

## Build

- Each illustration part is its own SVG path (or group of paths) with `strokeDashoffset` revealing the ink,
  then a flat fill fading up right behind the stroke.
- Drive each part's start time from the caption's word timings, not from a fixed clock offset, so drawing and
  narration always stay in sync even if the line is edited.
- The caption itself plays karaoke-style: already-spoken words are solid, the current word is the accent
  colour, unspoken words are dimmed.

## Sound

A soft marker-on-whiteboard scratch under each stroke, synced to the voice track, not a separate hit.

## Adapting

Use it for anything that benefits from being explained by being drawn: a process, a system, a concept. Keep
one illustration building per beat; cut to the next only once the current one is complete.
