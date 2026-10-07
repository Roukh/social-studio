# through-line

**Family:** structure. **Wants:** the whole film. **Source:** the reel of 2026-10-06, whose angle was "One dot
as the through-line: every scene starts from the last scene's mark (dot, band, circle, sphere, block, blue dot,
button, blob), so the cuts read as one continuous move across eight techniques."

## Looks

One mark travels the whole film and changes form at each scene: a dot becomes a band, the band a flood, a
circle wipe, a sphere, a block, a button, a blob, and a dot again on the end card. Where a scene ends, its mark
is where the next scene starts. The techniques change, but the eye never loses its place.

## Build

- Choose the mark in `brief.json` before the shots: a dot in the accent colour works for almost any film.
- For every shot, write its end state as the next shot's start state: position, size and colour match across
  the cut.
- At each seam, the outgoing scene leaves the mark where the incoming scene picks it up. Build the seams
  first, then the scenes between them.

## Sound

A recurring sound motif on the mark (one blip pitch) ties the film together across techniques.
