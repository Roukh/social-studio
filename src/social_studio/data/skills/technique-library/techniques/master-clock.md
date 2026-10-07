# master-clock

**Family:** build pattern. **Wants:** the whole film. **Source:** built in
`examples/reel-2026-10-06.html`, `// ===== master render` and `// ===== timeline`.

## What it solves

HyperFrames renders frame by frame, seeking to each time. GSAP tweens seek themselves, but canvas, WebGL and
any text set by code do not. One clock makes every such scene a pure function of time, so any frame renders the
same way at any seek, in any order.

## Build

```js
const tl = gsap.timeline({ paused: true });
const clock = { t: 0 };
tl.to(clock, { t: DUR, duration: DUR, ease: "none", onUpdate: () => render(clock.t) }, 0);

let lastT = -1;
function render(t) {
  if (Math.abs(t - lastT) < 1e-7) return;
  lastT = t; window.__lastT = t;
  renderHud(t); renderGrain(t);
  if (t < 1.72) drawS1(t);                                       // 2D canvas scenes
  if (t >= 2.68 && t < 4.73 && window.__s3render) window.__s3render(t);  // three.js, from the module script
  // ... one guarded call per procedural scene
}
window.addEventListener("hf-seek", (e) => render(Number(e.detail && e.detail.time) || 0));
window.__timelines["main"] = tl;
tl.seek(0); render(0);
```

- Guard each scene by its time window, so only live scenes draw.
- In the module script, render once on load if the clock is already inside the 3D window, because modules load
  after classic scripts (`if (window.__lastT >= a && window.__lastT < b) window.__s3render(window.__lastT)`).
- Randomness comes from `kit.rng(seed)` only, and anything frame-dependent is seeded by the frame number.
- DOM motion stays as ordinary tweens on `tl`. The clock is for what tweens cannot reach.
