// reel-kit: small, pure helpers for compositions built on the reel preset. Every function is a pure function of its
// arguments, so a frame drawn at time t is always the same frame. Loaded before the composition's own scripts as
// `window.reel`.
(function () {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, u) => a + (b - a) * u;

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

  window.reel = { clamp, lerp, spring, track, rng, timecode, beat, snap };
})();
