# kinetic-word-run

**Family:** type. **Wants:** 1.7-2.5 s (four words). **Source:** the 2026 Opus showreels; built in
`examples/reel-2026-10-06.html`, S4a to S4d.

## Looks

Four words, one per beat, with hard cuts between them. They are the only hard cuts in the film. Each word gets
its own field colour and its own motion, so the run shows four different kinds of movement:

- **Glide:** the word slides in from off-frame on `expo.out`. Its letters arrive spread apart and close up,
  and their weight rises from 200 to 900 as they settle.
- **Slam:** the word drops in at 1.8x scale and -7 degrees and snaps to rest on `back.out(2.4)`. Behind it, a
  wall of outline words (1 px stroke, 6-10 % opacity) drifts.
- **Whip:** the word whips in sideways, skewed -32 degrees and settling to -12, with motion blur, inside
  viewfinder brackets with a REC dot.
- **Cascade:** an italic phrase falls in letter by letter, each letter rotating from 14 degrees. The gap
  between letters shrinks as the line goes, so the line speeds up.

The last word holds one beat longer.

## Build

- One clip per word on the timeline, cut exactly on the beat (`kit.beat(n, bpm)`).
- Use the brand's fonts. Animate weight only on a variable font; otherwise animate scale and tracking.

## Sound

A hit on each cut, a tick under the glide, a slam hit, a whoosh on the whip, and a cascade of ticks.

## Adapting

Choose words that are the film's message, not technique names. In 9:16, stack longer words on two lines.
