---
id: ghobz-vs-reel-diagnosis
type: reference
created: "2026-10-07T21:30:00Z"
consequence: 8
locus: output
summary: Why the ghobz intro (video 5) is far weaker than the reel (video 4) - same model and rounds, different preset - measured, with options to close the gap.
scope: repo
status: active
---

# Why the ghobz intro is weaker than the reel

## Question

The operator, on 2026-10-07, compared the ghobz intro (video 5) with the social-studio reel (video 4):

> "significantly lower in quality, underwhelmingly boring, and visually not it ... some ui components from the website were taken and stiched together with some motion. But the first one was dynamic, complex, visually stunning motion graphics. The firts one was off of a reference video i shared"

Is there a reason, and how can the ghobz videos match the reel?

## Method

- Compared the two presets: `src/social_studio/presets/reel/preset.toml` and its `reel-look` skill, and the installed `ghobz_projects/social/presets/ghobz/preset.toml`.
- Compared the two finished compositions in the ghobz library, counting animation calls and technique markers with a script.
- Compared the two library rows and their sessions.

## Findings

| | Reel (video 4) | ghobz intro (video 5) |
|---|---|---|
| Maker | opus, xhigh, 3 rounds, 98 min, $9.05 | opus, xhigh, 3 rounds, 58 min, $11.35 |
| Brief | pillar "showreel": "A new technique every couple of seconds ... Go all out." | my brief: introduce ghobz with 5 site lines, the 3 "Why ghobz" points, and the site's hero, vivid cards and phone story |
| Look skill | `reel-look`, studied shot by shot from the operator's reference ([[reference-leonabboud-showreel]]): 9 scenes, each a different technique (3D voxel grid, kinetic words, data, particles, UI, morph), a HUD, grain, wipes on the beat | `ghobz-house` (palette, type, wordmark) and `ghobz-ui` (copy the site's sections onto a 360 px stage); no shot grammar, no reference |
| Motion rules | "go all out", one new idea every five beats | "calm and decisive", "Nothing overshoots", "at most one big title and three objects per frame", "one idea per video" |
| Libraries | GSAP, three.js, `reel-kit.js` helpers | GSAP only |
| Composition | 1,262 lines, 107 animation calls, 16 timed clips | 412 lines, 30 animation calls, 7 timed clips |
| Techniques found | three.js 39, SVG paths 19, clip-path wipes 24, canvas 4, variable-font weight motion 8 | three.js 0, canvas 0, particles 0, weight motion 0; site component classes 7, blur 14 |
| AI reviewer | failed to finish (out of turns) | passed, motion quality 9/10 |

Causes, in the order the data supports them:

1. **No reference and no shot grammar for ghobz.** The reel's quality came from a skill built out of the operator's reference video. It names nine technique scenes and the texture layers. The ghobz preset has brand rules but no film to make.
2. **The ghobz rules ask for restraint.** They were taken from the website's design rules (calm, nothing overshoots, three objects at most) and fit a website, not a showreel.
3. **The brief and the kit pointed at the website.** The brief I wrote for the intro asked for five site lines, three points and three site sections. The ghobz-ui kit tells the maker to copy the site's sections. The result is site sections with entrance motion, which is what the operator saw.
4. **No 3D or generative tools.** ghobz has no three.js and no helper kit, so even an ambitious maker had only DOM and GSAP.
5. **The reviewer cannot see "boring".** It checks brand accuracy and readability, so a safe video passes at 9/10 and the three rounds never push for spectacle.

## Options to match the reel

| Option | What it is | Cost and trade-off |
|---|---|---|
| A. ghobz inherits the reel | the ghobz preset says `extends = "reel"` and overrides only brand (palette, fonts, wordmark, 9:16, copy rules) | smallest change; the grammar and libraries come free; the reel grammar was written for 16:9 and an ink ground, so some scenes need re-staging for a phone and ghobz's light canvas |
| B. A ghobz look skill from a reference | the operator shares a reference for ghobz; it is studied the same way (shot by shot) into a `ghobz-look` skill; three.js and a helper kit are added | the same path that made the reel good; needs one reference and one study session |
| C. Reference per make | `make --reference <video>`: the CLI extracts a contact sheet, cut times and the beat grid and hands them to the maker | general, works for any brand or account (fits the multi-account feature); new code; quality depends on the reference each time |
| D. Narrow the kit | the ghobz-ui kit becomes a source for one UI scene and the brand's details (cards, gradients, wordmark), not the whole film; the "interface is the site's own" rule applies only inside that scene | keeps the site's look where it shows UI; on its own it does not add spectacle |
| E. Less copy | a brief of one line, the wordmark and the call to action, so the 20-25 s go to motion | a brief change only; less said per video |
| F. A reviewer anchored to the reel | the reviewer scores ambition against the reel's contact sheet (or the reference's) and fails a safe video, so the rounds push harder | catches "boring" automatically; anchoring can pull every video toward one look |

The options combine: for example, A or B for the look, D and E for the content, and F to hold the bar.

## Sources

- Library rows, sessions and compositions in `ghobz_projects/social/library/` for video 4 (`...one-dot-nine-bars-0e92`) and video 5 (`...most-businesses-...-08fe`), measured 2026-10-07 with `.local/tmp/<session>/compare.py`.
- The two presets, read 2026-10-07.

## Date

2026-10-07.
