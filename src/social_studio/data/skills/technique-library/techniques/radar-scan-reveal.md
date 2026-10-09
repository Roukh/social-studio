# radar-scan-reveal

**Family:** data, particles. **Wants:** 2.5-5 s. **Source:** prompt-motion.com's gallery (xelandre-363f00),
studied 2026-10-09.

## Looks

Concentric rings sit centred on a bright anchor dot, like a radar or sonar display. Small dots light up one at
a time at scattered positions inside the rings, each a signal being detected, some near the centre, some out
toward the edge. A thin sweeping line or wedge of light passes slowly around the rings, and a dot brightens
and holds the instant the sweep crosses it.

## Build

- Rings are SVG circles, evenly spaced radii, low opacity, static.
- Each signal dot sits at a seeded `(r, theta)` position (`r = R * sqrt(random())` for even density); it
  fades/scales in only once the sweep's current angle passes its `theta`.
- The sweep is a wedge or line rotating continuously (`rotate` tied to the clock, linear, no easing, since a
  radar sweep is mechanical, not organic).
- A detected dot can grow a short connecting line out to a small label card, same mechanic as
  `annotated-diagram-overlay.md`'s anchored callouts.

## Sound

A soft, continuous low sweep tone, a distinct ping each time the sweep lands on a dot.

## Adapting

Use it for any "always watching, always finding" claim: leads, signals, mentions, anomalies. Keep the sweep
slow and even; a fast or eased sweep reads as decorative rather than mechanical.
