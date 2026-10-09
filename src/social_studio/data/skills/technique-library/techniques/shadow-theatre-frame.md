# shadow-theatre-frame

**Family:** frame, through-line. **Wants:** the whole film. **Source:** prompt-motion.com's gallery
(x4b47x-9cc84f), studied 2026-10-09.

## Looks

A decorative stage-curtain border, striped fabric top and sides, hangs around every shot like a puppet
theatre's proscenium. The scene inside it is built entirely from flat black silhouettes, layered at different
depths for parallax, against a soft gradient sky that drifts slowly from one time of day to the next across
the film. A single rope or thread hangs down one side as the opening and closing gesture, pulled to open the
first shot and released to close the last.

## Build

- The curtain is a fixed DOM frame (a repeating striped texture top and sides) layered above every scene for
  the whole runtime, same persistence as `hud-frame.md`.
- Each silhouette element (ground, buildings, figures, trees) is a flat SVG or canvas shape at a fixed depth;
  parallax comes from each depth layer panning at its own slow rate.
- The sky is a gradient whose stops interpolate over the whole film's clock, dusk to full night, with a moon
  or sun sprite moving along its own slow arc.
- The rope is a simple line that tweens out of frame on open (`power2.in`) and back in on close.

## Sound

A soft fabric rustle as the curtain opens and closes, a quiet ambient bed (wind, distant birds) under the
whole film, no hard hits.

## Adapting

Use it for any narrative, story-led or mood piece that wants a hand-made, storybook register instead of a
digital one. The curtain and the silhouette technique are inseparable; keep both or use neither.
