# progress-path-climb

**Family:** data, establishing. **Wants:** 2-2.5 s per waypoint, 3-5 waypoints. **Source:**
prompt-motion.com's gallery (marklaunches-3b9492), studied 2026-10-09.

## Looks

A dotted path winds up across an illustrated landscape (a mountain, a coastline, a skyline); a glowing marker
travels along the path as a cumulative total climbs in the corner. Named waypoints along the route light up and
label themselves in turn as the marker reaches them, and the final waypoint pays off with a glowing title over
the illustration once the total completes.

## Build

- The path is a fixed SVG route pre-drawn into the illustration; the marker's position is `getPointAtLength`
  driven by the same value powering the cumulative counter, so marker and number always agree.
- Waypoint labels are pill badges fixed at points along the path; each cross-fades from dim to lit the instant
  the marker passes it, with a short pulse on arrival.
- The payoff title (the final waypoint's name, large) fades/scales in over the illustration once the total
  reaches its target, holding a beat longer than the other waypoints did.

## Sound

A soft ambient wind/atmosphere bed under the whole climb, a chime on each waypoint unlocking, a fuller,
resolving chord on the final payoff.

## Adapting

Works for any cumulative team or personal goal told as a journey: a fundraising climb, an onboarding path, a
multi-week streak. Keep waypoint count to 3-5 so each one still feels like a milestone.
