<!-- Distilled by social-studio from heygen-com/hyperframes (tag v0.8.106, Apache-2.0),
     skills/hyperframes-animation/blueprints/constellation-hub.md. See ../../NOTICE.md.
     Patched: rule-id citations replaced with self-contained build notes. No fade content to
     patch — entrances are spring-pop scale, the finishers are camera push/orbit/drift. -->

# constellation-hub

**roles**: Hook, Social_Proof, CTA
**duration**: 5-8s (a scatter-drift end-card variant runs ~2.5s as a closing beat)

**intent**: Labeled/iconned nodes spring into a ring/cluster around a center, then the shot
resolves on the core — either the camera pushes INTO the center (depth-of-field collapsing onto
it), a hub mark holds while satellites ORBIT it, or (CTA) a click COLLAPSES the orbit into the
product demo.

**shot structure**

- **Scene 1 (0.0-~1.5s)**: on a dark/space field, primary nodes (circles carrying an icon +
  label) SPRING-POP in (scale 0→1, a bounded overshoot, staggered) arranged in a wide ring/cluster
  around an empty or marked center.
- **Scene 2 (~0.7-2.5s, overlapping)**: smaller secondary nodes pop in with the same spring,
  filling gaps; optional thin connector lines / an orbit ring draw from hub to nodes. Camera
  holds.
- **Scene 3 (~2.5s-end, the resolve)** — pick one finisher:
  - _push-in_ (Hook): a continuous, smooth camera push toward the center — inner nodes stay sharp
    while outer nodes are pushed toward the edges and progressively blur (depth-of-field); holds
    magnified on the core.
  - _orbit_ (Social_Proof): the center brand mark snaps in via a quick 3D rotate that decelerates
    and settles; partner badges spring onto a drawn orbit ring and revolve clockwise, staying
    upright, under a continuous slow camera zoom-out (ecosystem reveal).
  - _collapse_ (CTA): icons drift slowly around an empty central CTA; a click implodes the whole
    orbit toward the click point and the product demo springs OUT of that collapse.
  - _scatter-drift end card_ (Social_Proof, no ring): a two-line headline builds in place at
    center (not a mark); ~20 app icons pop in scattered frame-wide in a quick stagger, then drift
    very slowly outward to the end. Camera fully static — the "everything around one center" read
    comes from the drift vectors, not from geometry.

**build notes**:
- Nodes sit on a pre-computed elliptical ring (`cos`/`sin` from each node's index and the ring
  radius) with a thin SVG line from each node to the center, drawn via `stroke-dashoffset`.
- The spring-pop entrance is a scale/transform tween with a bounded overshoot (`springEase` at
  `dampingFraction` 0.6-0.7, or `back.out(≤2)`) — never an opacity fade-in.
- The push-in and zoom-out finishers are both single `cam.scale` tweens on one `.world` wrapper;
  depth-of-field on the outer nodes during the push-in is a proxy-tweened blur amount at the same
  timeline position as the push, not a separate effect pass.
- The orbit's clockwise revolve is a continuous but FINITE angular tween over the hold (not
  `repeat: -1`) — compute the end angle from the hold's duration so it never needs to loop.
- The scatter-drift variant's outward drift is a slow, finite translate per icon toward
  pre-computed off-center targets — bounded, never a `yoyo`.
