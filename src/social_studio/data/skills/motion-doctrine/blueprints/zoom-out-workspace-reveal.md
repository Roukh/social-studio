<!-- Distilled by social-studio from heygen-com/hyperframes (tag v0.8.106, Apache-2.0),
     skills/hyperframes-animation/blueprints/zoom-out-workspace-reveal.md. See ../../NOTICE.md.
     Patched: the Scene-4 "file-attachment card fade-in" is changed to a scale/slide pop (opacity
     was the lead verb there); rule-id citations replaced with self-contained build notes. -->

# zoom-out-workspace-reveal

**roles**: Hook, Benefits
**duration**: 6.8-11s

**intent**: Open tight on one full-bleed detail — a graphic macro or a small UI region — let it
perform in close-up, then ONE continuous decelerating zoom-out reveals that everything seen so
far lives inside a containing whole (a design-tool workspace, a multi-pane agent workspace). The
frame locks at the wide and element-level payoff carries on. The zoom-out itself is the engine.

**hard rule carried from the source**: no zoom-in anywhere, and the camera is static outside the
one reveal. Before the reveal the camera holds, glides along the close-up surface, or is already
running the (only) pull-back; after it decelerates to a stop the frame is LOCKED — every later
change is element/layout motion, never camera. One zoom-out per shot.

**shot structure**: one oversized static world (the whole workspace, authored at final layout
from frame 0) with the camera starting scaled far in on the detail; the reveal is one scale
animation on the world.

- **Scene 1 (0.0-~2.5s)** — full-bleed detail performs in close-up (a graphic morphs/blooms, or
  UI rows pop in / a highlight steps down a list) — never a static hold.
- **Scene 2 (~2.5s-reveal start)** — the middle beat: the continuing pull resolves an
  intermediate composition (still full-bleed, still no chrome) or the close-up story advances at
  the same tightness (an adjacent panel, a new row).
- **Scene 3 (the reveal)** — the signature move: camera pulls back to scale 1 with strong
  exponential deceleration (`expo.out`/`power4.out`), revealing the containing whole. Always
  leaves a post-lock act — the deceleration-to-stop is what makes the lock legible.
- **Scene 4 (lock → end)** — element-level payoff on the locked wide: a cursor glides to click
  something, a playhead scrubs while the canvas animates, or a card pops/slides in → gets opened →
  a pane expands (layout motion, never camera) to land the deliverable. Long hold to the end.

**build notes**:
- Build the entire workspace at final layout inside one `.world` wrapper — there is no second
  set. The open is `cam.scale = S0` (4-12×) with a counter-translate centering the detail; the
  reveal tweens to `scale 1, translate 0` on one shared ease.
- Everything visible at the magnified open must survive S0 — author the detail in DOM/vector
  (text, SVG, CSS shapes), not a raster that'll shred at 8× zoom.
- A card or row arriving during the Scene-4 payoff pops or slides into place (scale/position); if
  it needs an opacity component, split it onto its own tween alongside the transform, never as
  the sole arrival verb.
- After the lock, no camera tweens exist on the timeline at all — any further motion is on
  element/layout properties.
