<!-- Distilled by social-studio from heygen-com/hyperframes (tag v0.8.106, Apache-2.0),
     skills/hyperframes-animation/blueprints/camera-journey.md. See ../../NOTICE.md.
     Patched: rule-id citations replaced with self-contained build notes. No fade content to
     patch — the shape is camera-travel-led by construction. -->

# camera-journey

**roles**: Benefits, Key_Feature
**duration**: 5.6-11.1s

**intent**: The real viewport camera is the storyteller — a multi-leg, motivated journey (dive in
→ a beat fires → travel to the consequence / reposition → landing push) across one continuous
world. Two sub-shapes: **(A) action roundtrip** — camera dives into a panel, an action fires, the
camera swoops to where the consequence renders as element motion; **(B) cursorless flight** — pure
cinematic 3D flight (motion blur, depth-of-field, tilt-to-flatten), no cursor anywhere. Reach for
this when the camera's own travel tells the cause→effect story — not when it's merely chasing a
cursor, and not when one single device/surface is the hero (that's a simpler held shot).

**shot structure**: one oversized world (a UI canvas, or a 3D-laid-out space) wrapped by a single
virtual camera; content animates as elements inside the world while the camera travels; every leg
is a sequential tween on the same camera state.

- **Scene 0 (optional, 0.0-~1.8s)** — static prologue: camera locked on an establishing beat
  (a typed headline, a wide shot of the app). Breaks by a hard cut as the first dive begins.
- **Scene 1 (~0.5-2.0s) — LEG 1: dive in.** Camera pushes in fast and tight onto the focal
  element (A: a flat push onto an actionable element as text finishes typing/streaming; B: an
  angled 3D close-up, motion-blurred during travel, neighbors soft under depth-of-field).
- **Scene 2 (~1.5-6.0s) — LEG 2: the hinge.** Camera holds/drifts while the content acts (A: a
  click fires and the acted element clears; B: the content self-acts — a dropdown self-expands,
  or the flight decelerates into focus on one card).
- **Scene 3 (~4.0-8.0s) — LEG 3: travel to the consequence.** Camera pulls back/swoops/pans to a
  new region while the consequence builds as element motion (A), or repositions — a slow
  tilt-to-flatten pull-back, or a motion-blurred whip sweep resolving into a flat pan (B).
- **Scene 4 (final ~1-2s) — LEG 4: landing.** Camera comes to rest on the payoff (A), or dives
  violently onto the CTA/hero card, ending tight or mid-dive (B).

**build notes**:
- Every leg is a tween on ONE camera state object (`{scale, x, y}` on a single `.world` wrapper),
  sequenced on the same timeline, never a separate camera per leg — this is what keeps a seek to
  any frame reproducing the exact mid-leg pose.
- Target points (the focal element center, the landing button) are measured ONCE at setup (after
  `fonts.ready`) and baked; never re-measure inside `onUpdate`.
- Motion blur rides the `.world` wrapper during a leg (a proxy-tweened blur amount, peaking at
  peak velocity, resolving sharp on landing) — never a CSS filter transition.
- Ease law: hard `*.out`-family on dives and landings (`power4.out` — violent arrival, sharp
  settle), `power2.inOut` on repositioning legs. No spring/overshoot on a camera move — it reads
  wrong on a viewport.
- Vary leg verbs — four identical pushes in a row reads as a slideshow, not a journey.
- Mark the moving `.world` wrapper `data-layout-allow-overflow` and keep `overflow:hidden` on the
  scene root, since a traveling camera deliberately moves content past the frame edges on every
  leg.
