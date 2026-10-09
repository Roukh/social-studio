# medallion-stat-stamp

**Family:** identity, data, type. **Wants:** 0.6-1 s per word or number, 2.5-4 s for a run of 4-6. **Source:**
prompt-motion.com's gallery (micheleharmonic-77628e), studied 2026-10-09.

## Looks

The brand's flat mark tips into 3D and thickens into a glossy chrome coin, tilted three-quarter and turning
slowly on its own axis. A bold sans word or number sits stamped in front of it, filling most of the frame; it
hard-cuts straight to the next word or number with no crossfade, so a run of stats or claims reads as the same
coin being struck again and again rather than a new graphic each time.

## Build

- The coin: an extruded, bevelled ring or disc with a chrome/metal material, a rim light and a soft specular
  highlight that sweeps as it turns (three.js torus/lathe, or a pre-rendered faux-3D sprite swapped per cut if
  staying in 2D).
- Keep the coin rotating continuously under the master clock across the whole run, so the hard cuts read as
  repeated impacts on one object, not a restart.
- Each word/number is its own DOM or canvas layer, heavy weight, cut exactly on the beat (`kit.beat(n, bpm)`),
  with a drop shadow so it reads over the chrome. A thin mono kicker under the coin can carry a unit label.

## Sound

A metallic stamp or clang on each cut, pitched slightly differently per hit, over a low rumble from the
continuous spin.

## Adapting

Build the coin from the brand's own mark, icon or monogram instead of a generic ring, so every stat lands as
proof stamped by the brand itself. Good for a rapid list of numbers, claims or features that should feel
certified rather than typed on.
