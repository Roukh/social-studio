---
name: motion-doctrine
description: Doctrine against fade-led arrivals for short vertical motion-graphics shots — spatial/transform entrances, velocity-matched cuts, the keyframe pose contract, and critically-damped spring easing; replaces hyperframes-animation, hyperframes-creative and motion-graphics for this session.
---

<!-- Distilled by social-studio from heygen-com/hyperframes (tag v0.8.106, Apache-2.0).
     See NOTICE.md for exact source paths and the licence text in LICENSE. This file is
     a derived/edited work, not a verbatim copy. -->

# Motion doctrine

This skill is the only source of motion guidance for this session. It replaces
`hyperframes-animation`, `hyperframes-creative` and `motion-graphics`: it does not
mount them, and their blueprint ids, rule ids, and `adapters/` recipes are not
reachable from here. Everything a shot needs — the doctrine, a cut catalog, a
blueprint menu, and the easing helper — is in this skill or in `blueprints/`.

Use `hyperframes-core` for the composition/timeline contract and `hyperframes-cli`
for command docs. This skill only covers *how things move*.

## 1. The doctrine

1. **Never fade an arrival.** An entrance is spatial or transform-led: a slide, a
   scale-in, a mask/clip-path wipe, a stroke draw-on, a 3D tilt or flip, a camera
   push/pan onto it, or a morph/collapse from another element. `opacity` may ride
   along as a *minor helper* on a transform tween (e.g. splitting a separate
   `opacity` tween at the same timeline position so a fast scale/position move
   doesn't look like it's "popping" through full brightness) — it never carries
   the arrival alone, and no element should ever go from `opacity: 0` to `1` with
   no accompanying transform. `fromTo` always states the from-state explicitly
   (never a CSS-hidden start — it flashes visible before the seek claims it).
2. **Exits are allowed, and they hand off motion.** Unlike older guidance in this
   codebase, an internal exit is not banned — but it is never a bare fade-out
   either. An exit either *is* a velocity-matched cut into the next beat (§2), or
   it is the frame's own hand-off to the harness `transition_in` on the final
   beat. A beat that just fades to black and waits is a bug, not a transition.
3. **No lazy breathing, no idle loops.** Scaling a card or a block of text up and
   down in a circular loop to look "alive" is the single cheapest tell in
   agent-made motion graphics — don't reach for it, ever, as a default. The only
   sanctioned aliveness during a hold is a **finite, low-amplitude jitter** —
   positional/scale/rotation, a few px or a few percent, never a `repeat`/`yoyo` —
   used sparingly, on at most one held hero, and only when the beat genuinely has
   nothing better to do. Prefer sequential reveal (rule 5) over any idle motion.
   Live internal SVG motion (rotating hands, dash-flow, pulsing dots) is fine
   because the subject is doing something, not because the frame is "breathing."
4. **No bad pan/push in the back half.** A slow camera pan or push running under
   the later ~50% of a beat disrupts the sightline and reads as eye strain, not
   production value. If a beat needs a camera move, motivate it (§3's
   `camera-journey`, `spatial-pan-stations`) and let it finish before the
   back-half reveal starts, or let it be the content-paced feature of the shot,
   not wallpaper under something else.
5. **Sequential reveal in the back ~50%, timed to the voiceover/caption beat.**
   Don't dump everything on screen in the first ~25% of a beat — that's the
   slideshow tell. Front-load only what's being said at t=0; let the rest of the
   elements wait for their own cue later in the beat. Fewer things on screen,
   each landing on its beat, reads better than a full canvas that animates once
   and freezes.
6. **Smooth beats bouncy.** `power3.out` (or `expo.out` for a fast arrival) is the
   default settle. The exact physical version of that same curve is the
   critically-damped `springEase` in §4 — reach for it when the settle itself is
   the shot (a wordmark landing, a final lockup). Overshoot (`back.out`,
   `elastic.out`, `bounce.out`, or `springEase` with `dampingFraction < 0.8`) is a
   rare, explicitly-playful register — never the house default, never used twice
   in the same video unless the whole piece is playful.
7. **Hold settled poses long enough to read.** The brief's reading-time rule
   (hold ≥ 0.5 s + 0.3 s per word of on-screen text) is the floor, not the
   target — a pose that resolves a beat gets at least that long before the next
   cut. The final frame of a hold is part of the animation, not cleanup: don't
   reset an element to rest and don't cut to black unless the shot explicitly
   calls for it.
8. **The keyframe pose contract.** Every shot is a pose ladder, not a redraw:
   - Name the moving subject and give it a **stable element id** that doesn't
     change across the shot list (the maker will cite these ids; the frame
     worker must find the same element every time).
   - Name the poses that prove the shot: a **start** pose, one or more **key**
     poses, and an **end** pose. Animation dresses a locked layout between these
     poses — it never re-lays-out or redraws the composition mid-shot.
   - Keyframe visible compositor channels only: `x/y/z`, `xPercent/yPercent`,
     `scale`, `rotation*`, `skew`, `transformOrigin`, `opacity`/`autoAlpha`,
     `clip-path`, masks, SVG path/dash values. Never animate layout/lifecycle
     channels (`top/left/width/height/margin/padding/display`) — those cause the
     redraw this contract forbids.
   - Preserve object identity: the same element that enters is the one that
     holds and exits. A crossfade between two *different* elements is only
     correct when the intent is a genuine replacement/dissolve (e.g. a discrete
     state swap, §3 `fixed-anchor-cycle`'s theme morph) — never as a default way
     to get an element on screen.

## 2. Cut catalog (within-shot seams)

A shot's own internal seam — a within-beat element swap, or a beat-to-beat cut
inside the same clip — should read as one continuous move, not a hard slideshow
cut. Four techniques, all built on the shot's own paused GSAP timeline. Pick by
what the seam is doing:

| Seam is... | Use | Axis |
|---|---|---|
| An unfinished idea continuing (multi-line text, a run of cards) | **Cut-the-curve** / **Waterfall** | x/y |
| A state change / new chapter (hook → context) | **Zoom-through** | Z, toward viewer |
| An arrival / payoff beat ("that changes today") | **Inverse zoom-through** | Z, away from viewer |

**The rule for all four: cut at peak velocity, match direction and speed on both
sides of the cut.** Nothing travels fully off-screen and nothing enters fully
off-screen — partial travel plus a fast fade sells the rest.

- **Zoom-through** — outgoing element scales `1.0→1.2` toward the viewer
  (`power3.in`, 0.2s) while its *own, separate* opacity tween dims `1.0→0.15` on
  `none` (linear — splitting it from the scale keeps the dim even); hard-cut
  (`tl.set`) both elements at peak blur (10px for text, 18-20px for a
  full-frame surface — never the other way, text smears at full-frame blur
  levels); incoming continues the same forward scale `0.75→1.0` on `expo.out`
  over 0.5s. Blur is on the wrapper, never on individual children, and both
  sides use the identical peak blur value.
- **Inverse zoom-through** — the mirror: outgoing recedes `1.0→0.8`, incoming
  arrives oversized `1.25→1.0` and retracts into place. Same timings/eases as
  zoom-through, same-direction rule preserved (both shrinking).
- **Cut-the-curve** — the default for all beat-to-beat cuts on x/y. Outgoing
  hero exits partway (`x: 0→-230`, `power4.in`, ~0.2-0.4s), incoming hero enters
  from the mirrored offset and continues the same direction (`x: +230→0`,
  `power4.out`, entry duration ≥ exit duration) — mathematically the two halves
  of one `power4.inOut`. The exit's opacity reaches 0 at ~25-30% of its travel
  (so it vanishes while still visibly accelerating); the entry fades in fast
  from ~35% of its own travel. Time the last fading element to die exactly at
  the cut — a gap with nothing moving reads as dead air.
- **Waterfall cut** — cut-the-curve at word granularity for a text-to-text seam.
  Each outgoing word ramps out on its own `power4.in` (0.34s, ~0.022s stagger,
  last word finishes fading right at the cut); each incoming word cascades in
  on the mirrored `power4.out` (0.3s) with a *shrinking* stagger gap (start
  ~0.05s, ×0.84 per word) so the cascade accelerates across the line. Pre-set
  all words to their start pose at build time (`immediateRender: false` alone
  is not enough — unstarted words sit visibly at rest otherwise).

**Anti-patterns:** two elements visible at once during a zoom-through (breaks
the Z illusion); blur that doesn't match on both sides of a cut; mismatched
travel direction across a cut; gentle `power2.out` on an entry that's supposed
to mirror a hard exit; a full off-screen exit/entry (wastes time, kills the
speed illusion); zoom-through on body text (unreadable at 0.75 scale — headlines
and short phrases only); any scene-to-scene cut that skips cut-the-curve
entirely and just hard-cuts two static frames together.

## 3. Blueprints

A blueprint is a time-coded shot template proven against real launch footage —
start from one instead of composing from scratch whenever a shot's role
matches. The index, with one line per blueprint and the file to read, is in
`blueprints.md`; the templates themselves are in `blueprints/<id>.md`. Name the
blueprint id in the shot list exactly as it appears in the index — **never use
the same id twice in a row**, even across different beats, since back-to-back
identical shapes are exactly what reads as a template. If nothing in the menu
fits, compose freely from §1's doctrine and §2's cut catalog rather than forcing
a wrong blueprint.

## 4. Easing — `power3.out` and the critically-damped spring

Entrances default to `power3.out`; exits that aren't a cut-catalog seam default
to `power2.in`/`power3.in`. For the rare beat where the settle itself is the
payoff (a wordmark landing, a final lockup, a CTA button arriving), use the
baked spring ease below instead of approximating it with `power3.out` — it is
the exact closed-form position curve of a damped spring, written as a pure
function of progress so it stays seek-safe (a *simulated*, stateful spring
cannot be seeked: it would have to integrate every prior frame to render frame
N; this is a closed form, not an integrator).

```javascript
// springEase — a damped spring's exact position curve as a GSAP ease.
// response         ≈ seconds one oscillation would take (0.3–0.6 for entrances)
// dampingFraction  1.0       = critically damped — smooth settle, NO overshoot (house default)
//                  0.80–0.85 ≈ "alive, not bouncy" — ~1–1.5% overshoot, felt not seen
//                  0.60–0.70 = explicitly playful — ~5–10% overshoot (rare; replaces back.out)
//                  < 0.55    = don't — cartoon-wobble territory
function springEase({ response = 0.5, dampingFraction = 1 } = {}) {
  const w = (2 * Math.PI) / response; // undamped natural frequency
  const z = dampingFraction;
  let pos; // x(t): 0 → 1, starting at rest (v0 = 0)
  if (z < 1) {
    const wd = w * Math.sqrt(1 - z * z);
    pos = (t) => 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + ((z * w) / wd) * Math.sin(wd * t));
  } else if (z > 1) {
    const wo = w * Math.sqrt(z * z - 1);
    pos = (t) =>
      1 - Math.exp(-z * w * t) * (Math.cosh(wo * t) + ((z * w) / wo) * Math.sinh(wo * t));
  } else {
    pos = (t) => 1 - Math.exp(-w * t) * (1 + w * t);
  }
  // Settle time: last moment the curve sits outside ±0.1% of target.
  // Fixed-step scan, runs once at setup — deterministic (no Math.random / Date.now).
  const EPS = 0.001;
  const rate = z <= 1 ? z * w : (z - Math.sqrt(z * z - 1)) * w; // slowest decay mode
  const SCAN = 12 / rate;
  const N = 4800;
  let T = SCAN;
  for (let i = N; i >= 0; i--) {
    const t = (i / N) * SCAN;
    if (Math.abs(1 - pos(t)) > EPS) {
      T = ((i + 1) / N) * SCAN;
      break;
    }
  }
  const xT = pos(T);
  return {
    duration: T, // use as the tween's duration — the settle time IS the physics
    ease: (p) => pos(p * T) + p * (1 - xT), // normalized so ease(1) === 1 exactly
  };
}
```

Usage — take **both** `duration` and `ease` from the helper (re-time via
`response`, not by overriding `duration`):

```javascript
const settle = springEase({ response: 0.4 }); // critically damped → duration ≈ 0.59s
tl.fromTo("#hero", { scale: 0, opacity: 0 }, { scale: 1, opacity: 1, duration: settle.duration, ease: settle.ease }, 0.2);
```

Guidance: `response` 0.25-0.35s for a tight snap (small UI), 0.35-0.50s for a
standard entrance, 0.50-0.70s for a weighted hero landing (check the reading-time
rule still clears at `t ≤ 0.5s` of visibility). At `dampingFraction < 1`,
overshoot belongs on transforms only — never on `opacity` (it would push past 1)
or color; split opacity onto its own `power2.out` tween at the same position. A
ζ=1 spring front-loads harder than `power3.out` (~67% vs ~58% travelled at
quarter-time) and settles on a longer tail — that tail is the "premium" read; use
it when the settle is the hero, not on every element in a beat.

## 5. Hard rules (non-negotiable, not doctrine — these break the render)

The composition is a **paused GSAP timeline seeked frame-by-frame**. Every
tween on it must be a pure function of time:

- No `Date.now()`, `performance.now()`, unseeded `Math.random()`, hover/scroll
  triggers, timers, async-created timelines, unregistered `requestAnimationFrame`,
  or infinite loops. Any variation (stagger, jitter) derives from the element's
  index, never from the clock or chance.
- No `repeat`/`yoyo`/infinite motion anywhere — "forever," "on loop," and
  "endlessly" are not renderable; any aliveness (§1 rule 3) is a finite tween
  over the hold.
- No CSS `transition`/`@keyframes` for render-critical motion — CSS animation
  runs on the browser clock, independent of the seek clock, and desyncs/flickers
  under a frame-by-frame render. Drive all motion on the paused `tl`.
- Build the timeline synchronously as `gsap.timeline({ paused: true })` and
  register it at `window.__timelines[data-composition-id]`; never call
  `tl.play()` for render-critical motion.
- `fromTo` states the from-pose explicitly; never rely on a CSS-hidden start.
