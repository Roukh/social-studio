<!-- Distilled by social-studio from heygen-com/hyperframes (tag v0.8.106, Apache-2.0),
     skills/hyperframes-animation/blueprints-index.md. See NOTICE.md. -->

# Blueprint index

13 blueprints selected from the engine's 22, kept because their signature move
is spatial/transform-led (a slide, a tilt, a wipe, a camera move, a collision,
a stroke draw-on) rather than opacity-led. Each was re-checked against the
doctrine in `../SKILL.md` §1 and, where the original used a fade/crossfade/idle
"breathing" as part of an entrance, patched to lead with a transform instead
(see the file's own provenance line for what changed).

Excluded (not carried into this skill): `cursor-ui-demo`, `device-surface-showcase`,
`prompt-type-submit-generate`, `agent-progress-theater`, `panel-edit-live-sync`,
`transcript-scroll-artifact-reveal`, `dataviz-countup`, `overwhelm-surround`,
`video-text-pivot` — mostly multi-step UI-demo shapes that are heavier than a
10-20s vertical short needs, plus two (`video-text-pivot`'s hero "breathes",
`device-surface-showcase`'s "dissolves from a title card" option) that would
have needed the heaviest patching for the smallest doctrine payoff.

Name the `id` column exactly in the shot list. Never use the same id twice in
a row.

| id | roles | what it does | file |
|---|---|---|---|
| `kinetic-type-beats` | Hook, Problem, Product_Intro, Benefits, CTA, Brand_Outro | Flat centered bold type; the motion IS the words — a fixed line hard-cuts a token, or a statement builds across full-screen beats to a spring-pop payoff. The workhorse; reach for it when there's no set or surface, just words. | `blueprints/kinetic-type-beats.md` |
| `typewriter-reveal` | Hook, Brand_Outro | A live caret types (and edits) a line, then collapses it into a brand payoff, or holds a persistent mark while a sub-line types into the CTA. | `blueprints/typewriter-reveal.md` |
| `spatial-pan-stations` | Hook, Problem, Product_Intro | Labeled stations pre-placed on one oversized canvas, visited by a single virtual camera panning stop to stop, landing held on the last. | `blueprints/spatial-pan-stations.md` |
| `camera-journey` | Benefits, Key_Feature | The camera itself is the storyteller — a multi-leg motivated journey (dive → beat fires → travel to the consequence → landing push) across one continuous world. | `blueprints/camera-journey.md` |
| `zoom-out-workspace-reveal` | Hook, Benefits | Open tight on one full-bleed detail, let it perform, then ONE continuous decelerating zoom-out reveals the containing whole; frame locks and element-level payoff continues. | `blueprints/zoom-out-workspace-reveal.md` |
| `constellation-hub` | Hook, Social_Proof, CTA | Nodes spring into a ring around a center; resolves by a camera push-in on the core, a held hub with orbiting satellites, or (CTA) a click that collapses the orbit into the product demo. | `blueprints/constellation-hub.md` |
| `grid-card-assemble` | Key_Feature, Benefits, Social_Proof | N items self-assemble in a staggered cascade into a grid/list and hold; an optional camera zoom-out reveals the array inside a vaster whole. | `blueprints/grid-card-assemble.md` |
| `logo-assemble-lockup` | Product_Intro, CTA, Brand_Outro | A brand mark comes to exist on screen — built from parts, drawn on stroke-by-stroke, or arrived at via a camera push-through — and resolves into a centered lockup. | `blueprints/logo-assemble-lockup.md` |
| `ticker-takeover` | Hook, Brand_Outro | A typed lead-in plus a cycling accent word, then a hero crashes in from off-screen and physically shoves the text aside — a collision, not a fade. | `blueprints/ticker-takeover.md` |
| `titlecard-reveal` | Benefits, Social_Proof, CTA, Product_Intro | The calm breather beat — one clean title or proof card revealed by exactly one restrained transform move (a slide, or a wipe-away-to-reveal), then a still hold. | `blueprints/titlecard-reveal.md` |
| `comparison-split` | Key_Feature | Two paired items arrive from opposite wings with mirrored 3D book-open tilts and hold side-by-side; a badge spring-pops on each to punctuate. | `blueprints/comparison-split.md` |
| `fixed-anchor-cycle` | Hook, Benefits, Brand_Outro | One element enters once and never moves again while the region around it cycles through many discrete states (hard-cut swaps, a carousel, a per-word highlight step), resolving into a completed lockup. | `blueprints/fixed-anchor-cycle.md` |
| `cta-morph-press` | CTA, Hook | A resting brand mark condenses at the same center into a brighter CTA, then a cursor arrives and lands a human-aimed click with feedback. | `blueprints/cta-morph-press.md` |

Coverage check: every role (Hook, Problem, Product_Intro, Key_Feature, Benefits,
Social_Proof, CTA, Brand_Outro) has at least two options above.
