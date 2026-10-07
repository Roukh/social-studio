# Attribution

The `motion-doctrine` skill is **distilled and edited from** the open-source
**HyperFrames** project:

> https://github.com/heygen-com/hyperframes
> tag `v0.8.106`, package `hyperframes` (`packages/cli`), licensed Apache-2.0.

A copy of the Apache License, Version 2.0 is in `LICENSE` in this directory, as
required by §4 of that license. This NOTICE file is informational and does not
modify the License (Apache-2.0 §4(d)).

## Why this skill exists

This repository mounts five HyperFrames engine skills into its video-maker
session: `hyperframes-core`, `hyperframes-animation`, `motion-graphics`,
`hyperframes-cli`, `hyperframes-creative` (2.77 MB total). Three of those —
`hyperframes-animation`, `hyperframes-creative`, `motion-graphics` — teach
opacity-led entrance animations as the default vocabulary (e.g.
`hyperframes-animation/transitions/overview.md` lines 21-24: "Every scene uses
entrance animations… opacity" / "Exit animations are BANNED"), while the
engine's own doctrine *against* fade-led motion lives in two skills that are
not mounted: `product-launch-video` and `hyperframes-keyframes`. This skill
replaces the three fade-teaching skills with a short, curated guide distilled
from the two un-mounted doctrine sources (plus a hand-picked, patched subset of
`hyperframes-animation`'s blueprint library), so the maker session reads
doctrine instead of the giveaway. `hyperframes-core` and `hyperframes-cli`
remain mounted separately and are untouched by this change.

## Modifications

Every file in this skill is a **derived, edited work**, not a verbatim copy.
Per source file:

| This skill's file | Derived from (upstream path, tag `v0.8.106`) | What changed |
|---|---|---|
| `SKILL.md` §1 (doctrine) | `skills/product-launch-video/references/motion-language.md` Part 2 (the four doctrine rules, lines ~91-126) | Condensed to numbered rules; reworded to drop the old hard "exits are banned" stance (this repo allows exits that hand off motion) and to add the keyframe pose contract (next row) as rule 8; brand-neutral throughout. |
| `SKILL.md` §1 rule 8 (pose contract) | `skills/hyperframes-keyframes/SKILL.md` line 16 ("Keyframes are a pose contract…") and the Contract list, lines 60-71 | Condensed to four bullets; reworded for the maker's shot-list/element-id workflow rather than the keyframes skill's own CLI-proof workflow. |
| `SKILL.md` §2 (cut catalog) | `skills/product-launch-video/references/cut-catalog.md` (all sections) | Condensed from 220 lines to one table + four technique summaries + an anti-pattern list; numeric values (durations, blur px, stagger gaps) kept exact; dropped the full worked phase-by-phase breakdowns. |
| `SKILL.md` §4 (springEase) | `skills/hyperframes-animation/adapters/gsap-easing-and-stagger.md` lines 59-136 ("Spring Eases") | The `springEase()` function is copied verbatim (it is the load-bearing artifact — a closed-form, seek-safe damped-spring ease); the surrounding guidance prose is condensed and reworded. |
| `SKILL.md` §5 (hard rules) | `skills/product-launch-video/references/motion-language.md` Part 3 ("the seek-safe core") and `skills/hyperframes-keyframes/SKILL.md` ("Runtime Rules" / "Never use for render-critical motion") | Merged and condensed both sources' determinism rules into one list. |
| `blueprints.md` | `skills/hyperframes-animation/blueprints-index.md` | Re-selected to 13 of the original 22 blueprint ids (see below); table format changed; coverage note added. |
| `blueprints/<id>.md` (13 files) | `skills/hyperframes-animation/blueprints/<id>.md` (same ids) | Each rewritten and condensed; every file's own top comment states its specific patch. In general: `rule mapping` sections citing `hyperframes-animation/rules/<id>.md` are **removed and replaced with self-contained "build notes"**, because that skill is not mounted here and those rule files are not reachable; opacity-led entrance options are removed or reworded to lead with a transform, per file. |

## Blueprint selection

13 of the source's 22 blueprints were kept: `kinetic-type-beats`,
`typewriter-reveal`, `spatial-pan-stations`, `camera-journey`,
`zoom-out-workspace-reveal`, `constellation-hub`, `grid-card-assemble`,
`logo-assemble-lockup`, `ticker-takeover`, `titlecard-reveal`,
`comparison-split`, `fixed-anchor-cycle`, `cta-morph-press`. Excluded:
`cursor-ui-demo`, `device-surface-showcase`, `prompt-type-submit-generate`,
`agent-progress-theater`, `panel-edit-live-sync`,
`transcript-scroll-artifact-reveal`, `dataviz-countup`, `overwhelm-surround`,
`video-text-pivot` (see `blueprints.md` for why). Ids are unchanged from the
upstream index so a maker's shot-list citation stays stable.

## No trademark or brand grant

Per Apache-2.0 §6, this NOTICE and the License grant no rights to any
HyperFrames or heygen.com trade name, trademark, or product name beyond
identifying the origin above. Nothing under `src/social_studio/data/` in this
repository names any brand, colour, font, or product of any company.
