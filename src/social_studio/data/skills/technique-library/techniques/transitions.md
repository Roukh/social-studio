# transitions

**Family:** transition. **Wants:** 0.2-0.5 s each, landing on a beat. **Source:** the 2026 Opus showreels;
built in `examples/reel-2026-10-06.html`.

A transition is part of a shot, not a gap between shots. Every scene change uses one of these, and none is a
crossfade.

| Transition | Looks | Build |
|---|---|---|
| Circle wipe | the next scene opens as a circle from a point (hard or blurred edge) | a CSS variable radius in `clip-path: circle(var(--r) at x y)` or a mask, tweened `0 -> past the corner` on `power2.in`; S2 into S3 opens from the em dash |
| Soft circle wipe | the same with a feathered edge | a `radial-gradient` mask with a soft stop, or a blurred circle; S7 out |
| Pixel staircase wipe | blocks fill the frame in a diagonal staircase order | blocks drawn on a canvas, each with a start time from `(col + row) * step` plus seeded jitter; S6 out |
| Band flood | a line thickens into a band that fills the frame | the band's height grows on `power3.in` to the frame size; S1 out |
| Shutters | vertical slats rise into the next ground | `scaleY 0 -> 1` from a bottom origin, staggered per slat; S5 in |
| Dot into ground | the through-line dot grows into the next field | a circle scaled past the corners, in the next scene's colour; S8 out |
| Whip | the frame moves sideways with motion blur | the outgoing and incoming layers translate together with a growing `blur()` and a skew |
| Push in | the camera dives into an object, blurring | a 3D camera dolly with an fov change, and the canvas `filter: blur()` grows; S3 out |
| Hard cut | an instant change on the beat | kinetic word runs only |

Sound: a whoosh into each wipe, a glitch on the pixel wipe, and a hit on the flood.
