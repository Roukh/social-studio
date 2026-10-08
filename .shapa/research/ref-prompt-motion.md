---
id: ref-prompt-motion
type: reference
created: "2026-10-08T23:07:28Z"
consequence: 7
locus: output
summary: prompt-motion.com is a crowd-submitted gallery of Claude-made motion videos with real prompts; six examples studied for technique and prompt craft.
scope: repo
status: active
---

# Reference: prompt-motion.com

Operator-shared reference, 2026-10-07: "analize each in sonnet subagents, let them extract principles and
place them in .shapa rules and memories, thats how we'll build it, then implement it." This note is the
study; rows below are the extracted principles and the memory of the reference itself. Entries become
techniques later.

## Question

What does prompt-motion.com show about making 20-25 s motion graphics with prompts, beyond what
[[motion-course]] already found, and which of its moves generalise or belong as library techniques?

## Method

Fetched `https://prompt-motion.com/` (887,800 bytes) and six detail pages, saved under
`.local/refs/prompt-motion/` (gitignored). Found the real "prompt" text is not in the rendered HTML but in
a Next.js RSC stream chunk inside each detail page (an `id="entry-prompt"` div, or a `N:T<hexlen>,` payload
marker); wrote small scripts to decode it. Picked six entries for range: a meta self-promo, a 3D-style
mecha combine, a logo/brand reveal, a science explainer, a cinematic character shot, and a game-UI piece.
Downloaded each entry's small homepage-grid preview (42-275 KB, 4 s loops); for four of the six also
downloaded the full video (1-7.5 MB) for real duration and cuts. Ran ffprobe, the ffmpeg scene-cut filter,
and a `fps=4,scale=320:-1,tile=6x5` contact sheet per video, viewed directly.

## Findings

### What the site is

Not a course (that's [[motion-course]]'s @0xMovez thread) and not a prompt library with a fixed syllabus.
It is a submission gallery, curated by @p4nthera_, of videos people posted on X showing off what Claude
Opus 5.5 can do for motion graphics, each with a "Submit" button, a Model/Stack/Posted (sometimes
"Iterations") block, and often the original prompt verbatim, linked back to its X post. 230+ entries.
Prompts range wildly in sophistication: some are one-liners ("make a 20-second video about anything,
your call; make it crazy"; "paint the most complex, most exquisite pelican riding a bicycle you can, take
your time"), others are full tagged briefs. This is new information, not in [[motion-course]]: the same
model produces the full range from a one-line prompt, if given room and time, not only from long briefs.

### The site's own prompt (meta)

One entry is the site's own 23 s promo video, built in Remotion, with its prompt shown in full. It uses a
tagged structure new to our research: `<inputs>` (what to ask the operator for), `<direction>` (banned
looks, one accent rule, "one continuous camera... never two camera moves at once"), `<structure>`
(BPM and beat ranges, e.g. "b21-26: that tile blooms into its entry page"), `<build>` (numbered stack
steps, explicitly "no magic numbers"), and `<gotchas>` (real failure modes found while making it: a tile
matching the page background disappears; a camera push can drift header text into the edge bands). This
mirrors our own `principles.md` + `techniques/*.md` split, but adds a named gotchas habit we don't have.

### Per-example

- **Prompt Motion site promo** (antonio-kodheli, Remotion, 23 s, few hard cuts at 0.3 threshold - mostly
  continuous camera). The contact sheet shows a pull-back from one full-bleed preview to the live grid
  (3-column masonry of autoplaying real tiles: a red "CLAUDE" card, "EVERY FRAME ON PURPOSE", a spinning
  record, a lime "TYPE IN MOTION" interlocking-rings card, a blue circle/triangle scene), a whip into one
  tile until full-bleed, then a match cut back into its own tile. Corner radius visibly goes to 0 as a
  tile fills the frame.
- **Anime robot combining sequence** (allforbigfire, 3D CG, ~25 s, 12 hard cuts). Cel-shaded vehicles
  (jet/car/tank) each get their own reveal card with a bottom-left colour-coded label chip ("1号機 JET",
  "2号機 CAR", "3号機 TANK"), held a beat, hard-cut to the next, then a rain transition and a
  "3機合体！！" (3-unit combine) burst title. No crossfades; every cut is instant and labelled.
- **Rankhog / Reddit marketing tool launch** (anthonyriera, 52.8 s at 60 fps, cuts cluster near 28 s only).
  Black background; a spiky orange logomark materialises from scattered dissolve-noise dots converging
  into a solid silhouette (not a drop or a wipe), then "Meet Rankhog." and "Promote one product with many
  🐽 Reddit accounts." build word by word with the brand name in the accent colour.
- **Photon journey from the Sun** (apoorvjain25, from a one-line "make it crazy" prompt). Dark red/brown
  particle-noise field; a white core flash, then a live top-left HUD readout (YEARS TRAPPED, DEPTH km,
  TEMP °C, BOUNCES SEEN, all incrementing) runs continuously under kinetic captions landing one at a
  time ("ABSORBED." "RE-EMITTED." "WRONG WAY." "AGAIN."), while a thin accent polyline draws itself,
  segment by segment, tracing the photon's bounce path as it happens.
- **Pelican riding a bicycle** (axtonliu, from "the most complex, most elaborate pelican on a bike you can,
  take your time"). A near-static, photoreal/painterly pier-at-sunset establishing shot: a pelican on a
  bicycle, warm backlit grade, a streetlight lens flare, gulls drifting across at different depths, barely
  any camera motion. The stillness reads as premium because of the atmosphere layers, not movement.
- **Pixel-art card battle game** (aisongman, "Create a 1-on-1 card game like Hearthstone... in pixel art
  style"). A playable game UI screen-recorded across many near-identical turns; no camera, no cuts, no
  beat structure. Useful only as a style data point (clean pixel art is achievable), not as a technique:
  it is an interactive artifact, not an authored film, so it is excluded from the technique candidates
  below.

### Overlap with motion-course

Confirms motion-course's finding that hard cuts (no crossfades) and labelled HUD elements are common, and
that effort/time, not just prompt length, drives quality. New here: the tagged brief format with a named
gotchas list, the "one camera move at a time" rule stated explicitly, a gallery-grid zoom/match-cut
structure, a noise-dissolve identity reveal, a live incrementing HUD under a narrative (not just a data)
beat, a path-draws-itself trajectory, and a held establishing shot carried by atmosphere alone.

## Principles

- **One camera move at a time.** Whatever moves the frame as a whole (a three.js camera, a DOM
  scale/translate pseudo-camera, a canvas viewport) does one move - a push, a pan, or a whip, never
  combined - and holds before the next starts. The site's own promo states this as a hard rule and the
  contact sheet confirms it: the pull-back finishes, then the whip starts. Apply it to every camera-like
  move in a 20-25 s film, 9:16 or 16:9.
- **Full-bleed colour needs a hairline.** `principles.md` already has the palette rotate as full-bleed
  fields; this reference's own gotchas list names the consequence: a tile or shape whose colour matches
  its background disappears mid-move. Give any flat-colour card, panel or shape a 1 px hairline distinct
  from its field, especially right before or during a push/zoom.
- **Write the build with a gotchas list.** The site's tagged prompt ends every brief with named failure
  modes actually seen while rendering (a tile vanishing, text drifting into the edge band on a push), not
  just the happy path. Give a film's own build notes (or a new technique entry) a short gotchas line: the
  one or two ways this specific shot breaks, found by looking at the render.
- **Structure beats length.** Several of the gallery's strongest results came from one-line prompts
  ("make it crazy", "take your time") rather than long briefs; sophistication tracked the room and time
  given, not prompt size. Don't cap a shot's ambition because the operator's brief was short - the
  existing beat grid and technique set is enough structure to carry it.
- **A hold can be carried by atmosphere alone.** The pelican shot has almost no motion but reads as
  premium: parallax motes/birds at different depths, a warm grade, one flare. `principles.md` already
  allows "a flat field with one element... held on purpose"; when a shot is deliberately calm, spend the
  effort on 2-3 thin atmosphere layers instead of movement.

## Techniques (candidates)

- **gallery-zoom-tour** - structure, transition. One tile fills the frame, the camera pulls back to a
  grid of other live tiles, whips into a different tile until full-bleed, then match-cuts back to that
  tile's own card. Wants 4-8 s. Build: absolute-positioned DOM cards (or planes) in one large world
  container; GSAP drives a pseudo-camera as (focusX, focusY, logScale); corner-radius tweens to 0 as a
  tile reaches full-bleed. Sound: a whoosh on each whip, a soft shift on the pull-back.
- **mecha-cut-reveal** - type, reveal. A hard cut per unit (a vehicle, a part, a feature), each on its own
  full-bleed card with a colour-coded label chip holding for a beat, ending in a flash/burst title. Wants
  1.5-2.5 s per unit, 0.5-1 s burst. Build: flat-shaded SVG/canvas art per card, GSAP hard-swaps (no
  crossfade) driven by a stepped index; reuse `hud-frame`'s label-chip styling per unit, `wordmark-
  assemble`'s slam-in for the burst title.
- **noise-dissolve-logomark** - identity, particles. A mark condenses from scattered points into a solid
  silhouette, instead of dropping or wiping in. Wants 1-1.5 s. Build: canvas 2D; sample the mark's path
  into seeded points (`kit.rng(seed)`), ease each from a random start position to its target with
  power3/expo, ramp opacity as it nears target; pure function of time per `master-clock`.
- **live-readout-hud** - data, texture. A persistent corner readout (a counter, a depth/temp pair, a
  running count) increments continuously through a narrative beat, independent of word captions landing
  over it. Wants: the whole shot. Build: a monospace DOM/canvas text block, each value a pure function of
  `t` (e.g. `floor(rate * t)`), low enough contrast not to fight the main captions.
- **bounce-path-draw** - data, physics. A thin polyline draws itself, segment by segment, tracing an
  object's path as it moves or bounces. Wants 2-3 s. Build: canvas 2D; sample (x, y, t) from the object's
  motion function each frame, stroke a path up to the sample matching current `t` (progressive reveal),
  thin accent stroke with a slight glow.
- **cinematic-atmosphere-hold** - texture, close/establish. A near-static, photoreal or painterly frame
  carried by atmosphere: parallax motes/birds at different depths, a warm grade, one flare. Wants 2-3 s.
  Build: a static or barely-panning background layer, 2-4 sprite layers drifting at different speeds as
  functions of `t`, the existing `grain-vignette` pass, one bloom sprite pinned to the brightest point.

## Sources

- https://prompt-motion.com/
- https://prompt-motion.com/antonio-kodheli-490109 (site's own promo, full prompt)
- https://prompt-motion.com/allforbigfire-86ff3c
- https://prompt-motion.com/anthonyriera-9b1b2a
- https://prompt-motion.com/apoorvjain25-d24184
- https://prompt-motion.com/axtonliu-0b861d
- https://prompt-motion.com/aisongman-71ffac
- [[motion-course]] (prior reference, for overlap)

## Date

Studied 2026-10-08.
