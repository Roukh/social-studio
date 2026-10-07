---
id: motion-course
type: reference
created: "2026-10-03T01:00:00Z"
consequence: 8
locus: output
summary: Entry note for the 0xMovez Opus 5.5 motion course research - read order, key numbers, and each technique mapped to its status in social-studio.
scope: repo
status: active
---

# Motion course: entry note

Start here for the course research gathered on 2026-10-03 from "How to build motion design studio with Opus 5.5 (Full-course)" (@0xMovez, 2026-09-27): its 21 embedded posts measured, its 16 code blocks, and its 8 linked repos. The decisions it led to are in [[reference-look-decisions]].

## Question

What do the most-viewed Opus-made motion videos do (length, fps, sound, cuts, prompts, effort, tools), and which of those techniques does social-studio have?

## Method

- The article read in full through the api.fxtwitter.com mirror (x.com returned HTTP 402), as text, all 16 code blocks and all 15 diagrams.
- Every embedded video downloaded and measured with ffprobe, ebur128 loudness, the ffmpeg scene filter and spectrograms.
- The 8 linked repos read at pinned SHAs for licence, pipeline and reusable parts.
- Status column re-checked against `src/` on 2026-10-06, after iteration 1.

## Findings

### Read order

| # | File | Holds |
|---|---|---|
| 1 | [[reference-leonabboud-showreel]] | the operator's target look (2026-10-06), measured shot by shot |
| 2 | this file | numbers and the technique map |
| 3 | [[motion-course-article]] | the 12 steps condensed, diagrams transcribed, named sources, banned looks, critique criteria, gates, caveats |
| 4 | [[motion-course-code]], [[motion-course-code-2]] | the 16 code and prompt templates verbatim |
| 5 | [[motion-course-showcase]] | the 21 posts measured |
| 6 | [[motion-course-repos]] | 8 repos: SHA, licence, reusable parts, the HyperFrames version gap |
| 7 | [[motion-course-prompts]] | the prompts behind the showcase posts, by level |

### Key numbers

- **Audio is universal.** All 17 Opus-made showcase videos carry audio, 15 of 17 at -12 to -16 LUFS ([[motion-course-showcase]]).
- **Length.** Median 29.0 s, range 14-157 s; six are 15 s.
- **Cut families.** Continuous or morph films run 0-0.7 cuts per 10 s (11 videos); montage films 3.4-10.7 (6 videos). Nothing sits between.
- **Frame rate.** 60 fps in 8 of 17, including every UI and product piece but one.
- **Route.** Code-drawn in 15 of 17; the athemeroy dataset agrees (152 of 168 code-rendered, 8 of 168 used a video model).
- **Top by views.** Donald 3.82M (141.5 s mixed-route music video, 9.5K-char brief, 12 h run); Stephan 2.24M (15 s one-liner at max effort). Median of the 17: 286K. Top by bookmarks: twoclipping's XML template (20.0K) and Rexan's 6-step workflow thread (18.0K).
- **Prompt-size ladder.** L1 ~150 chars, 15-50 min; L2 ~350 chars, 30-45 min; L3 1.5-3K chars, 1-2 h; L4 9.5-19K chars, 6-12 h. One disclosed iterative run: 163 calls, 62.7M tokens (96 % cache), ~$34, ~6¾ h.
- **Effort.** Every viral one-shot ran at xhigh or max; the harness default is medium (article L91).
- **Variance.** The same one-liner gave two unrelated films (#11, #14); the same brief with another reference gallery gave a different film (#21).

### Technique map (status 2026-10-06)

| Technique | Evidence | Status in social-studio |
|---|---|---|
| Effort xhigh or max | article L91; #2, #11, #14 | reel preset runs xhigh (decision 9); `--effort` per run |
| Long director brief (logline, refs, keys, beat sheet, gates, critique, deliverables) | CODE 13; #1 | TASK.md plus house rules plus flags; no brief file yet |
| Reference to `style_guide.md` | CODE 7; #12; #4, #21 | written `reel-look` skill instead; import deferred (decision 11) |
| Real product assets and screenshots | CODE 2; #12 step 3 | not built; the jail has network, capture not wired |
| Story, storyboard, animatic gates | CODE 13; #12 steps 4-5 | ruled (6-7), not built (feature F2) |
| Beat grid | CODE 5; CODE 15; #16 | by construction in `reel-kit.js`; librosa not installed |
| Music synthesized or supplied | 17/17 have audio; #6, #15, #16 | `data/tools/sound.mjs` synthesizes bed and SFX |
| SFX on cues | claude-animation-skill `sound.mjs` (cue = contact frame - 0.03 s); `media-use` catalog | `brief.cues` plus audio and loudness gates |
| Voice | #8 ElevenLabs mascot (1.12M) | allowed (ruling 12); none for reel makes (decision 4) |
| Closed-form springs | CODE 3, CODE 11; Snappy k320/d30, Default 170/26, Heavy 90/20, Playful 220/14 | `reel-kit.js` springs; GSAP eases in motion-doctrine |
| Motion blur | CODE 6 `tmix` with 4 subframes; motion-blur-streak (0.8.112) | velocity helper `attachMotionBlur` (decision 7) |
| 60 fps | 8/17 | `--fps 60`; reel preset |
| Critique: contact sheet, strip, phone test, loop check, at least 3 rounds until all ≥ 8 | CODE 10, 12, 13 | fixed rounds (reel 3) plus `tools/sampler.py`; self-scores not gated |
| Long runs | L4 6-12 h | reel 90 min, 300 turns; the login must outlast the timeout |
| Subagents per chapter | PDoom (no licence) | none |
| One timeline, several formats | CODE 2; #9 | `--aspect` per run; single-timeline multi-render not built |
| Generate-then-trace (video-model base, JS overlay) | #5, #21 | none; no keyed provider in use |
| HyperFrames 0.8.114 | Studio audio, motion-blur-streak | deferred (job J4) |

### Licence and rights

| Source | Licence | Use |
|---|---|---|
| HyperFrames | Apache-2.0 | vendorable |
| claude-animation-skill, ClaudeAnimationBase | MIT | vendorable |
| athemeroy dataset | CC-BY-4.0 | attribution required |
| guanmo-ai/awesome-ai-motion | MIT, prompts excluded | quote prompts for study only |
| PDoomVideo, Austerlitz | none | read only |
| Remotion | free up to 3 employees; Automators $0.01/render, $100/mo minimum | not used |

## Sources

- https://x.com/0xMovez/status/2104216919033192746 (via api.fxtwitter.com)
- The posts and repos cited in [[motion-course-showcase]] and [[motion-course-repos]].

## Date

Gathered 2026-10-03; status column updated and planning brief removed (answered by [[reference-look-decisions]]) on 2026-10-06.
