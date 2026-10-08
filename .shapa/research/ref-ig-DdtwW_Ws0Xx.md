---
id: ref-ig-DdtwW_Ws0Xx
type: reference
created: "2026-10-08T23:02:17Z"
consequence: 7
locus: output
summary: Framer's "skills" ad shows tilted 3D UI cards, one glow accent marking AI-touched content, and dual typefaces for human notes vs product UI.
scope: repo
status: active
---

# ref-ig-DdtwW_Ws0Xx: Framer "Teach the Framer agent how to work like you using skills"

## Question

What can a product-demo reel (not a generated motion-graphics film) teach the technique library about depth,
colour signalling and type, and does any of it generalise to every 20-25 s film this stack makes?

## Method

Fetched `https://www.instagram.com/p/DdtwW_Ws0Xx/embed/captioned/` (default curl UA; a first attempt with a
spoofed desktop UA returned a bot-blocked SSR-disabled shell, ~629 KB, with no media data — the plain default
UA on the retry returned the real ~253 KB embed with `video_url` inside triple-JSON-escaped inline script data).
Unescaped and downloaded the mp4 to `.local/refs/ig-DdtwW_Ws0Xx/video.mp4` (2.0 MB, 30.12 s, 720x1280 9:16,
H.264 ~29.97 fps + AAC audio). Author: `@framer`. Caption: "Teach the Framer agent how to work like you using
skills." Built a 1 fps / 6x5 contact sheet, pulled 20 individual frames around scene-change points, ran
`ffmpeg … select='gt(scene,0.1)'` for cut times, and adapted `onsets.py` for onset/tempo/loudness. Looked at
every frame with the Read tool.

## Findings

The film is a screen-recording-style ad for an AI coding/design agent (Framer's), not a from-scratch generated
film: every "shot" is a UI panel (chat, website preview, settings) staged in a tilted 3D perspective on a
near-black field, not full 3D render or canvas work. Still useful: it is dense with reusable interface-shot
craft this library's `glass-ui-flow` family doesn't yet cover.

Hard scene-change cuts (scene score > 0.1) landed at: 1.07, 2.30, 6.97, 14.78, 17.75, 20.12, 25.29, 26.36 s —
only 8 over 30 s, i.e. one new scene every ~3.4 s on average. Most of the film's motion inside those long
holds is continuous (text typing out, panels sliding/duplicating, a chip's glow brightening), not more cuts.

| Time range | On screen | Technique | Transition | Sound (from onsets/RMS) | Build in this stack |
|---|---|---|---|---|---|
| 0.0-2.3s | Chat panel, "Agent / Style" tabs, "New chat", typed notes "No gradients." then "Use curly quotes." | Tilted 3D card, marker-font text typed with a blinking cursor | continuous (same card, text replaces) | dense low-level clicks (part of the 90 onsets) | DOM panel, CSS 3D transform, GSAP text reveal |
| 2.3-7.0s | "Use Inter Medium, never light." typed, then the card widens into a browser/site preview "Helping teams do better research" with sections What we're building / Our principles / How we work | Same tilted-card language carried from chat to website | whip/slide, no crossfade | typing clicks continue, loudness steady ~-20dB | same panel, content swap, not a new object |
| 7.0-14.8s | The About-page preview duplicates into 3-4 near-identical tilted cards side by side; a chat box types "Create a new About page for the site, use /design-system" with a glowing chip | Variant-stack reveal + command-chip | cards fan in on a stagger | onsets cluster tighter (~0.2-0.3s apart) around 8-11s | DOM/three.js instanced planes, per-instance jitter from a seeded RNG |
| 14.8-17.8s | "Research should be easier to check" page scrolls; duotone gradient "photo" blocks (blue-green-magenta aurora wash with a faint figure) sit inside the layout, next to body copy | Aurora-gradient placeholder imagery inside a UI mock | continuous scroll | steady | canvas 2D gradient + noise, or a generated image asset |
| 17.8-20.1s | Back to the notes panel: "Medium, never light." reconfirmed, model name "GPT 6 Astra" visible | Dual-voice type (marker notes vs. grid-sans chrome) | cut back to card A | steady | as shot 1 |
| 20.1-25.3s | Empty chat input, then "/skills" types in, pill chip brightens | Command-chip-cycle, glow ramps | hold-and-brighten | RMS climbs from -18 to -9dB (26-27s) — a riser into the payoff | DOM pill, CSS box-shadow + blurred duplicate layer for glow, driven by clock |
| 25.3-26.4s | "/skills" at full bright glow, large | payoff frame of the chip | cut to black | peak loudness (~-9dB) | same pill, scaled and intensified |
| 26.4-30.1s | Framer logo (white folded-flag mark) on pure black, held | end card | fade | RMS falls to -44dB by 29.5s — fade over final ~1.5s | DOM/SVG mark, opacity fade |

**Palette:** near-black field (`#000000`-`#0a0a0a`) throughout; one glow accent, a desaturated cyan-teal
(`~#378bad` core, `~#1d3d52`/`#00344d` falloff) used only on borders, active chips and the active panel's edge;
everything else (chrome, labels, inactive panels) stays flat grey/white. No warm colours anywhere.

**Type:** two voices at once — a loose marker/handwriting face for "the human's notes" ("No gradients.", "Use
curly quotes.") typed with a blinking cursor, and a clean grid sans (looks like Inter, matching the product's
own name for its font rule) for all product UI chrome, labels and body copy. The two are never mixed on one
string.

**Texture:** a single glow-stroke language (blurred duplicate border, same accent colour) is the through-line
texture — not grain or vignette like this library's existing `grain-vignette`, but a colour/stroke rule that
marks "what the agent is doing right now" across every cut.

**Camera:** no real camera; every panel is a flat screenshot/mock given a shallow fixed 3D tilt (roughly 8-15°
on two axes) so it reads as a card floating in space rather than a flat rectangle. The tilt angle barely
changes shot to shot — it's a staging convention, not a moving camera.

**Pacing:** 30.1 s total (longer than this house's 20-25 s target — this is a feature ad, not this project's
format). ~3.4 s per scene on average, well past this library's ~2.5 s beat. `onsets.py` found 90 onsets and
estimated ~178 BPM, but the loudness curve shows this is mostly dense typing-click foley, not a musical beat
grid — the one true musical gesture is the riser from -18dB to -9dB across 26-27s into the "/skills" payoff,
then a fade to -44dB by the last 1.5s, which matches this project's existing sound principle exactly.

## Principles

What generalises past this one ad, for the rules below:

1. **Tilt flat content into a card, don't show it flat-on.** A screenshot, UI mock, or any flat 2D content
   reads as an object in space with nothing more than a small fixed 3D rotation (8-15° on two axes) — cheap in
   DOM via CSS `perspective`/`rotateX`/`rotateY`, or as a textured plane in three.js. Flat-on only reads right
   for full-bleed colour fields, never for anything with its own frame.
2. **One glow accent marks "what the system is doing", not decoration.** Pick one accent colour, apply it only
   as a stroke/glow on the active element (a chip, an edge, a cursor), and keep everything else neutral. It
   does the through-line's job (the eye tracks the live thing across cuts) without needing a literal recurring
   mark.
3. **Two type voices for two layers of meaning.** When a shot carries both "a human's note" and "the product's
   own interface", give them visibly different type (e.g. a loose/marker face vs. the brand's grid sans)
   instead of one face doing both jobs; the contrast reads instantly, no caption needed.
4. **A shot of a generated-at-scale thing should show several, not one.** Fan 3-4 near-identical cards/panels
   with a small position/rotation jitter behind a primary one to say "many were made" in a single shot, instead
   of cutting between single-variant shots.
5. **Hold text-heavy shots to the reading time, not the beat.** Where a shot's job is to be read (a sentence of
   copy, a multi-line panel), hold it 3-7 s if that's what the words need; this project's existing "~0.5 s +
   0.25 s per word" formula already allows this per-sentence, this reference confirms it holds for whole
   paragraphs too, not just single lines.

## Techniques

Candidate library entries (not yet written into `technique-library/techniques/`; for the main session):

- **slug:** `ui-tilt-card` — **family:** interface — **looks:** a UI/screenshot panel held at a fixed shallow
  3D tilt (8-15° on two axes) on a near-black field, soft shadow under it, sliding or swapping its content
  in place. **wants:** 2-2.5 s. **build:** DOM panel with CSS `perspective` + `rotateX/rotateY`, animated with
  GSAP; or a three.js plane with a `CanvasTexture` of the UI for a real parallax highlight. **sound:** a soft
  slide/whoosh on entry.
- **slug:** `provenance-glow-stroke` — **family:** texture, through-line — **looks:** one accent colour as a
  blurred-duplicate border glow, applied only to whatever element is "live" (an active chip, the current
  panel's edge, a typing cursor); everything else stays flat neutral. **wants:** the whole film, like
  `grain-vignette`. **build:** a shared `.live` class with `box-shadow`/blurred-copy glow, its colour and
  intensity a pure function of the clock. **sound:** none (texture).
- **slug:** `dual-voice-type` — **family:** type — **looks:** a looped marker/handwritten face typing out a
  short note with a blinking cursor, next to or inside the brand's own clean grid sans running the UI chrome;
  the two never share a string. **wants:** 1.5-2.5 s per note. **build:** DOM text reveal, GSAP per-character
  stagger at a steady typed rate; a second webfont loaded only for the note layer. **sound:** a typing clack
  per character, lighter than `kinetic-word-run`'s ticks.
- **slug:** `variant-stack-reveal` — **family:** data, interface — **looks:** 3-4 near-identical panels fan out
  with a small seeded offset (position, rotation, 10-30% stagger) behind a primary panel, then settle. **wants:**
  2-2.5 s. **build:** DOM or three.js instanced planes, per-instance offset from `kit.rng(seed)`, staggered
  GSAP entrance. **sound:** a soft cluster of hits, one per panel.
- **slug:** `command-chip-cycle` — **family:** type, interface — **looks:** a glowing rounded pill (e.g. a
  slash-command) types in, optionally cycles through 2-3 names on a beat each, and the final one holds larger
  and brighter as the shot's payoff. **wants:** 1.7-2.5 s. **build:** DOM pill, CSS glow via box-shadow + a
  blurred duplicate layer, GSAP scale/opacity swap per beat, final value driven by the clock for the glow
  ramp. **sound:** a blip per swap, a riser into the final brighten.
- **slug:** `aurora-gradient-photo` — **family:** texture — **looks:** a duotone diagonal-wash gradient
  (blue-green through magenta) standing in for a photograph inside a UI mock, sometimes with a faint figure
  silhouette. **wants:** fills its panel, whole shot. **build:** canvas 2D linear/conic gradient plus seeded
  noise, or `blend-mode` layers; cheaper than sourcing a real photo. **sound:** none.

## Sources

- https://www.instagram.com/p/DdtwW_Ws0Xx/ (author `@framer`)
- Downloaded video: `.local/refs/ig-DdtwW_Ws0Xx/video.mp4` (gitignored scratch, not committed)
- Existing library: `src/social_studio/data/skills/technique-library/SKILL.md`,
  `.../principles.md`, `.../techniques/voxel-ripple-3d.md`

## Date

2026-10-08
