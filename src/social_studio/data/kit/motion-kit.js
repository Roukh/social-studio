// motion-kit: small, pure helpers every composition gets, loaded after the libraries as `window.kit` (and as
// `window.reel` when a preset has not set that name). Every function is a pure function of its arguments, so a
// frame drawn at time t is always the same frame. The technique library's entries and its worked example use
// them; see skills/technique-library.
(function () {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, u) => a + (b - a) * u;
  // Progress of t through [a, b], clamped to 0..1.
  const seg = (t, a, b) => clamp((t - a) / (b - a));

  // Closed-form damped spring from 0 to 1, t seconds after it starts. k = stiffness, d = damping.
  // Snappy 320/30, default 170/26, heavy 90/20, playful 220/14.
  function spring(t, k = 170, d = 26) {
    if (t <= 0) return 0;
    const w0 = Math.sqrt(k), z = d / (2 * w0);
    if (z < 1) {
      const wd = w0 * Math.sqrt(1 - z * z);
      return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + (z * w0 / wd) * Math.sin(wd * t));
    }
    return 1 - Math.exp(-w0 * t) * (1 + w0 * t);
  }

  // A value with several targets over time: [[t0, v0], [t1, v1], ...]. A sum of springs, never a restart, so a new
  // target mid-flight keeps the velocity it already had.
  function track(t, keys, k = 170, d = 26) {
    let v = keys[0][1];
    for (let i = 1; i < keys.length; i++) v += (keys[i][1] - keys[i - 1][1]) * spring(t - keys[i][0], k, d);
    return v;
  }

  // A damped spring as a GSAP ease: { duration, ease }. response is the period in seconds, dampingFraction 0..1+.
  function springEase({ response = 0.5, dampingFraction = 1 } = {}) {
    const w = (2 * Math.PI) / response, z = dampingFraction;
    let pos;
    if (z < 1) {
      const wd = w * Math.sqrt(1 - z * z);
      pos = (t) => 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + ((z * w) / wd) * Math.sin(wd * t));
    } else {
      pos = (t) => 1 - Math.exp(-w * t) * (1 + w * t);
    }
    const EPS = 0.001, rate = z <= 1 ? z * w : w, SCAN = 12 / rate, N = 4800;
    let T = SCAN;
    for (let i = N; i >= 0; i--) {
      const t = (i / N) * SCAN;
      if (Math.abs(1 - pos(t)) > EPS) { T = ((i + 1) / N) * SCAN; break; }
    }
    const xT = pos(T);
    return { duration: T, ease: (p) => pos(p * T) + p * (1 - xT) };
  }

  // Eases for code-driven motion (canvas, 3D, text set from the clock), named like GSAP's.
  const ease = {
    p2i: (u) => u * u,
    p2o: (u) => 1 - (1 - u) * (1 - u),
    p3i: (u) => u * u * u,
    p3o: (u) => 1 - Math.pow(1 - u, 3),
    p4o: (u) => 1 - Math.pow(1 - u, 4),
    p2io: (u) => (u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2),
    p3io: (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2),
    expo: (u) => (u >= 1 ? 1 : 1 - Math.pow(2, -10 * u)),
  };

  // Seeded noise (mulberry32). Never Math.random: a re-render must be identical.
  function rng(seed) {
    let s = seed >>> 0;
    return function () {
      s = (s + 0x6d2b79f5) >>> 0;
      let t = Math.imul(s ^ (s >>> 15), 1 | s);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // SMPTE-style timecode for a HUD: 00:00:07:36 at 60 fps.
  function timecode(t, fps = 60) {
    const f = Math.floor(t * fps + 1e-6), pad = (n) => String(n).padStart(2, "0");
    return [Math.floor(f / (3600 * fps)), Math.floor(f / (60 * fps)) % 60, Math.floor(f / fps) % 60, f % fps]
      .map(pad).join(":");
  }

  // Beat grid: the time of beat n at this tempo, and the nearest beat to t.
  const beat = (n, bpm) => (n * 60) / bpm;
  const snap = (t, bpm) => beat(Math.round((t * bpm) / 60), bpm);

  // Split an element's text into one span per character (class "ch"); returns the spans.
  function split(el) {
    const txt = el.textContent;
    el.textContent = "";
    return [...txt].map((ch) => {
      const s = document.createElement("span");
      s.className = "ch";
      s.textContent = ch === " " ? " " : ch;
      el.appendChild(s);
      return s;
    });
  }

  // Set text only when it changes (cheap to call every frame).
  function setText(el, s) { if (el.__s !== s) { el.textContent = s; el.__s = s; } }

  // Type text on at cps characters per second from t0, as a function of t.
  function typeOn(el, text, t, t0, cps) {
    setText(el, text.slice(0, clamp(Math.floor((t - t0) * cps), 0, text.length)));
  }

  const kit = { clamp, lerp, seg, spring, track, springEase, ease, rng, timecode, beat, snap, split, setText, typeOn };
  window.kit = kit;
  if (!window.reel) window.reel = kit;
})();
