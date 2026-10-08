# timeline-scrubber-hud

**Family:** frame, structure. **Wants:** the whole film. **Source:** Himanshu's 15 s showreel
(x.com/himanshutwtxs/status/2103495232637882858), studied 2026-10-07.

## Looks

A bar along the bottom of the frame, like an editor's timeline: a track, a playhead moving across it, and
diamond keyframe markers at each scene's start. The markers behind the playhead are filled and the ones ahead
are hollow. It shows the film's structure while it plays.

## Build

- One DOM or SVG bar. The playhead sits at `t / duration` of the width, set from the master clock with no
  easing.
- One marker per scene start, taken from `brief.json`'s shots. A marker fills when the playhead passes it.

## Adapting

An alternative to `hud-frame.md`'s corner brackets: use one or the other. In 9:16, the bottom 35 % is the
platform's own interface, so the bar sits above it or at the top.
