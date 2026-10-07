# Easing and timing

Defaults with reasons, not rules. Every curve below is a GSAP ease string (or a cubic-bezier equivalent for CSS) you can swap in directly.

## Why ease at all

Nothing in the physical world starts or stops instantly — mass has to accelerate and decelerate. Disney's "slow in, slow out" principle is this fact applied to drawing; in code it's just the ease curve on a tween. Linear motion (`ease: "none"`) is correct for things that *pass through* frame without starting or stopping on screen (a scrolling ticker, a looping background pattern) — the "linear reads cheap" rule only applies to things that visibly begin or end their motion on screen.

## GSAP ease catalog, by intent

| Intent | GSAP ease | Why |
|---|---|---|
| Element arrives and settles (card in, text reveal) | `"power2.out"` | decelerates into rest — reads as arriving under its own weight |
| Snappier arrival, more energy | `"power3.out"` or `"power4.out"` | stronger deceleration curve, feels more urgent |
| Element leaves / dismisses | `"power2.in"` | mirrors the arrival curve, accelerates away |
| Symmetric move that both starts and stops on screen | `"power2.inOut"` | slow-fast-slow, the most "animated" default |
| Playful overshoot (icon pop, button press) | `"back.out(1.7)"` | overshoots target then settles; tune the number 1-3 for overshoot amount |
| Bouncy settle (drop-in, attention beat) | `"elastic.out(1, 0.3)"` | amplitude, period — raise period for a slower wobble |
| Pass-through, no start/stop on screen | `"none"` | constant velocity is *correct* here |
| HUD/counter/data readout tick | `"none"`, 1-frame duration | easing a "live" number makes it look decorative, not functional |
| Custom brand feel | `CustomEase.create("myEase", "M0,0 C0.2,0 0,1 1,1")` | GSAP's CustomEase plugin (free since 2024) takes an SVG-path-style bezier for a fully bespoke curve |

Source: GSAP eases documentation, https://gsap.com/docs/v3/Eases

## Spring-style motion (cards, cursor, progress fill, glass UI)

GSAP doesn't ship a named "spring" ease the way Framer Motion/react-spring do, but you can approximate one with a slightly overshot `back` ease, or use the physics2D/inertia-style trajectory by hand-tuning stiffness/damping conceptually:

- **Snappy, controlled** (default for UI cards, buttons): stiffness 300-400, damping 20-25 → roughly `"back.out(1.1)"` over 250-350ms (15-21f@60fps).
- **Playful, bouncy** (attention-getting pop): stiffness 100-200, damping 10-15 → `"elastic.out(1, 0.4)"` or `"back.out(2.2)"`.
- **Subtle, professional** (progress fills, cursor move): stiffness 300-400, damping 30-40 → `"power2.out"`, no overshoot at all.

Framer Motion's hard default is stiffness 100 / damping 10 / mass 1; react-spring's default is stiffness 170 / damping 26 — useful anchors if you're translating a spec from either library into a GSAP equivalent.

## Duration, in frames at 30fps and 60fps

Cross-referencing Apple HIG (UI animation: keep to 0.25-1.0s, shorter is imperceptible, longer blocks the user), IBM Carbon (duration scales with the distance/size of the moving element; "productive" motion is subtle, "expressive" is vibrant), and broadcast/title-sequence pacing conventions:

| Scale | Example | 30fps | 60fps | Seconds |
|---|---|---|---|---|
| Micro (icon, small UI state change) | cursor click feedback, checkbox toggle | 6-12f | 12-24f | 0.2-0.4s |
| Small (card hover, button press) | glass card elevation change | 8-15f | 16-30f | 0.27-0.5s |
| Medium (UI element enter/exit) | card slides in, progress fill starts | 15-30f | 30-60f | 0.5-1.0s |
| Large/hero (full-screen transition, title reveal) | wipe, scene change, logo reveal | 20-45f | 40-90f | 0.67-1.5s |
| Sustained read (data readout, held statement) | counter settles, donut completes | 24-36f minimum hold | 48-72f minimum hold | 0.8-1.2s minimum hold |

Rule of thumb: bigger / further-traveling elements get *slightly* longer durations, not proportionally longer — doubling distance should not double duration, or the piece feels sluggish.

## Stagger, as GSAP stagger objects

```js
// reading-order reveal (text lines, list items)
gsap.from(".line", { y: 20, opacity: 0, stagger: { each: 0.06, from: "start" }, ease: "power2.out", duration: 0.5 });

// 2D wave (variable-font weight wave, voxel grid, card grid)
gsap.to(".voxel", { y: -10, stagger: { each: 0.03, from: "center", grid: "auto" }, ease: "power2.inOut", duration: 0.4 });

// dramatic, deliberate reveal (hero credits, one-at-a-time emphasis)
gsap.from(".word", { opacity: 0, stagger: { each: 0.12, from: "start" }, ease: "power3.out", duration: 0.6 });
```

- `each` (seconds between each child's start) is more predictable than `amount` (total time split across all children) when the element count will change — `amount` silently speeds up stagger as you add elements.
- `from: "center"` or `"random"` reads less mechanical than `"start"` for anything that isn't literally meant to be read in order.
- `grid: "auto"` only works when elements visually occupy a grid; GSAP needs the row/column count (or `"auto"` to infer it) to compute 2D proximity.

Source: GSAP Staggers documentation, https://greensock.com/docs/v3/Staggers

## Anticipation and follow-through in code terms

- **Anticipation**: a small counter-move (5-15% of the main move's distance, opposite direction, 3-6f) before the main action starts. E.g. a card that will slide up first dips down 4px for 4f, then springs up.
- **Follow-through / overlapping action**: when a parent stops, staggered children settle 2-6f *after* the parent's stop frame, not simultaneously — e.g. a card lands, then its icon/badge settles a beat later.
- **Secondary action**: a smaller motion running concurrently with but independent of the main action (a card's shadow intensifying while the card itself moves) — implement as a separate tween on a separate property, not baked into the same tween.
