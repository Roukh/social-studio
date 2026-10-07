# 3D and camera (Three.js)

## Camera language in 2.5D/3D

Treat the camera as a character with its own anticipation/ease/follow-through, not a static mount:

- **Push-in on a reveal**: ease the camera's `position.z` (or `fov` for a cheaper fake-dolly) with `"power2.out"` over 20-40f@30fps / 40-80f@60fps — a push that starts fast and settles reads as purposeful; a push that's linear the whole way reads like a slider being dragged.
- **Whip-pan between beats**: rotate `camera.rotation.y` (or orbit-controls target) fast (6-10f@30fps / 12-20f@60fps) with motion blur simulated via a short trail of rendered ghost frames, then hard-cut at the whip's peak velocity, not at its end — this is the 3D equivalent of a whip-transition cut-on-action.
- **Parallax depth** (2.5D): give foreground/midground/background layers different `z` positions and move the camera slightly on `x`/`y` (2-8px of apparent parallax) even during an otherwise "static" hold — a beat with zero camera drift over 1-2s reads flat next to beats that have motion.
- **Anticipation on camera cuts**: a tiny counter-move (a few degrees of rotation, opposite direction, 3-6f) before a big whip-pan, mirroring the anticipation principle applied to the camera itself.

## Theatre.js vs. hand-coded GSAP camera moves

Theatre.js (`@theatre/studio` + `@theatre/core`, or `@theatre/r3f` for React Three Fiber) gives a visual timeline for scene state — camera transforms, material params, light intensity — exported as baked JSON. Use it when a camera move needs hand-tuned keyframes that are easier to drag on a timeline than to compute; use hand-coded GSAP tweens on `camera.position`/`camera.rotation`/`camera.fov` when the move is simple enough to express as 2-4 numeric targets with a named ease, since that keeps the whole composition in one GSAP-driven timeline (matching the HyperFrames pause/scrub model) rather than splitting state across two systems.

## Voxel ripple recipe (Three.js + GSAP)

```js
const voxels = []; // InstancedMesh or individual meshes on a grid
// ripple outward from center using distance-based stagger delay
voxels.forEach((v, i) => {
  const dist = Math.hypot(v.gridX - centerX, v.gridY - centerY);
  gsap.to(v.position, {
    y: v.baseY + amplitude,
    duration: 0.4,
    delay: dist * 0.03,       // larger multiplier = slower-traveling ripple
    ease: "power2.inOut",
    yoyo: true,
    repeat: 1
  });
});
```

Prefer `THREE.InstancedMesh` over individual meshes once the grid exceeds ~200-500 voxels for frame-render performance; GSAP can still tween per-instance matrix data by writing to the instance's transform and calling `instanceMatrix.needsUpdate = true` inside an `onUpdate` callback.

## Particle flow field (converging into a shape)

Standard algorithm: sample a 2D (Perlin-noise or custom) vector field at each particle's current position, normalize the direction, step the particle along it each frame. To converge into a target shape (logo, wordmark) by a specific beat:

1. Spawn particles at random positions with flow-field-driven motion for the first portion of the beat.
2. At a chosen frame, blend each particle's velocity from "follow the flow field" toward "seek its assigned target point on the shape" — a simple linear blend of the two velocity vectors driven by a single `progress` value tweened by GSAP from 0 to 1.
3. Ease the blend with `"power2.inOut"` so the convergence itself decelerates into the final shape rather than snapping.

Implementable in Canvas2D/p5.js for a few hundred particles, or Three.js/WebGL (shader-driven position updates, or `InstancedMesh`/points with a `BufferGeometry` attribute updated per frame) for particle counts in the thousands. Source: https://sighack.com/post/getting-creative-with-perlin-noise-fields and https://clicktorelease.com/code/generative-lines-flow-fields

## Metaball split/merge in 3D

For a 3D (not SVG) metaball look, use a marching-cubes or signed-distance-field approach (e.g. `three-forcegraph`-style or a custom SDF shader) rather than trying to fake it with overlapping meshes and blur — overlapping 3D meshes with a post-process blur reads muddy rather than fused. If a true SDF/marching-cubes implementation is out of scope for the render budget, the 2D SVG/CSS metaball technique (see `transitions-and-editing.md`) composited as a billboard/sprite in the 3D scene is a reasonable substitute for a short beat.

## Lighting and material as contrast tools, not decoration

- Use a single clear key light direction per beat (even if simplified to a gradient/rim-light shader) so forms read as 3D rather than flat-lit; flat, shadowless 3D renders are one of the fastest tells of an unconsidered 3D beat.
- Reserve bloom/glow post-processing for the one or two moments in the piece meant to feel like a climax (a reveal, a hit) — bloom applied uniformly across every 3D beat stops reading as emphasis.

## Tells of cheap 3D/camera work

- A camera that only ever moves linearly, with no ease, no anticipation, no parallax drift during holds.
- Particle/voxel effects that never resolve into anything meaningful — motion without a destination.
- Flat, shadowless lighting on every 3D object regardless of material.
- Bloom/glow applied globally and statically rather than at a single motivated climax moment.
