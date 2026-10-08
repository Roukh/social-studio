# annotated-diagram-overlay

**Family:** type, annotation. **Wants:** 0.8-2.5 s per label; works over any shot. **Source:** Himanshu's
15 s showreel (x.com/himanshutwtxs/status/2103495232637882858), studied 2026-10-07.

## Looks

A short hand-drawn label and arrow pop onto the exact element being shown (a bounce, a curve, a stagger) and
name what it is doing: "squash", "ease out", "follow-through". The labels arrive on the beat in a casual script
face, distinct from the display type, so they read as a designer's notes over the work, not as a caption bar.

## Build

- The label is DOM text in a second, handwritten or marker face, with its own role (see `dual-voice-type.md`).
- The arrow is an SVG path drawn on with `strokeDashoffset` and a small arrowhead that pops in at the end.
- Each label sits in the timeline at the onset it explains, and leaves before the next one arrives.
- Never more than one label in motion at a time. Point at the thing, not at empty space.

## Sound

A tick on each label's arrival.

## Adapting

The label names the mechanism of this film's idea: a step of a process, a feature, a number. It works for an
explainer as well as for a showcase.

## Gotchas

A label placed by guesswork drifts off its element when the element moves. Anchor it to the element's
position from the same clock.
