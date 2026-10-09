---
name: key-poses
description: How to lay out a short film's keyframe board - one static key pose per shot at the final layout, the pose contract the animator inherits, and what makes a board sheet readable for approval. Read it before building a board.
---

# Key poses

A board is the plan layer of a film: an ordered set of key moments, built as real frames before any motion. Its
frames are keyframes, not slides. Each is the pose a shot must reach, at the final layout, so approving the board
approves the film's look, copy and order, and the animation that follows only moves between approved poses. Two
poses that hold the same element describe that element's state through time: the animator moves the element
between them; nobody plays the poses as a slideshow.

## The order: outline, built, animated

A frame starts as an outline (a line of intent), becomes **built** when its layout is confirmed with no motion yet,
and is **animated** last. A board is the built rung for every shot at once. Nothing on it moves; everything on it
is final.

## The pose contract

- **One shot, one key pose:** the state that proves the shot, usually its end state (the word landed, the number
  counted, the interface showing its result). Never a half-way state, a blur or a transition.
- **Final, not a sketch:** layout, fonts, colour tokens and copy exactly as the film will show them. A board laid
  out with placeholder text approves nothing.
- **Name the moving subject** of each shot and give it one element id across every shot it lives in, so the
  animator moves it instead of redrawing it.
- **The last pose is part of the film, not cleanup:** the end card or call to action holds its final state.
- **Hold what must be read:** a pose with text leaves the viewer the shot's seconds to read it, at a size a phone
  can read.
- **Different at a glance:** two poses that read the same are one shot. Change the frame's weight, scale or
  subject from one shot to the next.

## What the operator sees

Code snapshots each pose at its shot's midpoint and tiles them into one board sheet no wider or taller than
2000 px. Each tile is labelled with its shot, beat, time, technique and on-screen text; a 9:16 film gets the
platform safe zone drawn over every tile. So:

- Text the viewer must read sits inside the safe zone.
- The sheet is seen small. A pose that only works at full size has too weak a hierarchy.
- The labels come from `brief.json`: its times, techniques and text must match what the poses show.

## After approval

A new session gets the approved board's composition and shot list and animates between the poses: layout first
(it is already there), then motion. It keeps every pose, id and line of copy, and adds only the moves between them.
