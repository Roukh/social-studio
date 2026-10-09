# geo-pulse-globe

**Family:** data, 3d. **Wants:** 2-3 s. **Source:** a dub.co launch promo shared by @steventey
(x.com/steventey/status/2103625902211088880), studied 2026-10-09.

## Looks

A dotted wireframe globe sits low in the frame, lit from within by a warm glow, a thin vertical beam pinned to
one point on it like a location marker. Above it a huge number rolls up live, counting a real-time total (visits,
events, signups) as if the globe beneath it is the source of the count.

## Build

- The globe is a sphere of seeded dot points (three.js `Points` or a 2D-projected dot field), lit by a radial
  gradient from one hemisphere.
- The beam is a thin vertical gradient line pinned to one dot's screen position, pulsing in opacity on a slow
  sine independent of the clock's easing.
- The number uses `data-infographic.md`'s blurred digit roll-up, landing on `power3.out`, its last couple of
  digits still ticking as the shot ends to read as genuinely live.

## Sound

A low, warm drone under the globe, a soft tick as the beam pulses, and a rising tone under the counting number.

## Adapting

Use it for any claim about global reach, scale or real-time activity: total users, requests served, countries
reached. The beam's location should feel specific, not generic.
