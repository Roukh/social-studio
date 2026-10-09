# chroma-split-glitch-wall

**Family:** texture, type. **Wants:** 0.5-1.2 s. **Source:** an "Overthinking" motion study in
prompt-motion.com's gallery (prompt-motion.com/gizakdag-cf4ae6), studied 2026-10-09.

## Looks

A word or image repeats full-bleed in a stack of horizontal bands, each band torn slightly out of alignment
with the one above it, and the red, green and blue channels offset from each other so every edge fringes with
colour. It reads as a system glitching under pressure, not a stylistic filter laid over calm content.

## Build

- The content (usually a repeated word) is drawn three times, in red, green and blue with alpha masking,
  each copy offset a few pixels differently on `kit.rng(frame)` so the offset itself judders frame to frame.
- The frame is sliced into 4-8 horizontal bands; each band's x-offset is an independent seeded jitter,
  re-rolled every few frames rather than tweened, so the tear reads as broken, not animated.
- Keep it short: this is a punctuation beat, not a resting state. Cut out of it hard, never fade.

## Sound

A harsh digital stutter or bitcrushed noise burst, cutting off sharply when the beat ends.

## Adapting

Use it as a one-beat punctuation for overload, error, or a system under stress, before a hard cut to calm. Never
hold it long enough to become comfortable.

## Variants

The same move, as other reference films staged it:

- **stutter echo type** (prompt-motion.com's gallery (ndhabarde11-f155b4), studied 2026-10-09.): A single word hard-cuts in, solid and bright, while several outlined, larger duplicate copies of the same word sit around and behind it at different scales and positions. A faint red/cyan channel-split offset sits on the edges of the letters, and a scatter of small square pixels drifts and blinks across the frame, unsynced from the word. Together it reads as the word glitching or stuttering into place rather than simply appearing.
