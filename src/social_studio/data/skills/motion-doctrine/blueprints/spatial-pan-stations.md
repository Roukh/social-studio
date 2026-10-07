<!-- Distilled by social-studio from heygen-com/hyperframes (tag v0.8.106, Apache-2.0),
     skills/hyperframes-animation/blueprints/spatial-pan-stations.md. See ../../NOTICE.md.
     Patched: rule-id citations replaced with self-contained build notes. No fade content to
     patch — the shape is camera-pan-led by construction. -->

# spatial-pan-stations

**roles**: Hook, Problem, Product_Intro
**duration**: 7-10s

**intent**: Pre-place a sequence of labeled stations on one oversized canvas, then traverse it
with a single virtual camera — repeated lateral/diagonal pans that center each station in turn
and reveal a callout at every stop, landing held on the final station.

**shot structure**: one oversized flat canvas on a solid bg; all stations pre-placed in world
space; one virtual `.world` camera pans ease-in-out between stops; each station holds ~1.0s.

- **Scene 1 (0.0-~1.0s)**: camera opens on station 1, centered. A reveal lands on it (see
  variants below). Camera then begins panning toward station 2, sliding station 1 out of frame.
- **Scene 2 → N-1 (~1.0s each)**: camera pans (ease-in-out) to center the next station; on
  arrival its label is revealed. Repeat per station.
- **Scene N (final)**: one last pan lands on the terminal station; the final callout reveals and
  HOLDS to the end. Camera goes static on the punchline.

**variants**:
- _Hook_ — stations are evenly-spaced markers on a thin horizontal timeline (lower third); pans
  are LEFT-only along one axis. Each callout is a bordered box + triangle tip that SPRING-POPS up
  (scale 0→100%, a deliberate, bounded overshoot, transform-origin at the triangle tip) reading
  the label; a secondary label (e.g. a year) rises above it. Final scene lands on "now," springs,
  holds.
- _Problem_ — stations scatter across a 2D web; pans are DIAGONAL, steered by hand-drawn
  connecting lines that draw toward the next station as the camera follows. Each station is a
  plain line-icon + label, revealed by the pan alone (no box). Final scene: the connecting line
  spirals into a dense scribble knot; camera holds static on the tangle.

**build notes**:
- The pan is one `.world` wrapper with a single `{x, y, scale}` camera state, tweened between
  pre-measured station coordinates (`power2.inOut`) and sequenced stop-to-stop on the one timeline
  — not a separate tween per station layer.
- A station's callout/label pop is a scale/position tween (spring-pop or `power3.out`), never an
  opacity-only arrival; it lands exactly as the pan settles on that station, not before.
- Hand-drawn connecting lines are an SVG `stroke-dashoffset` draw, timed to the pan's travel
  between the two stations it connects.
