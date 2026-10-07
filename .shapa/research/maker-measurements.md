---
id: maker-measurements
type: reference
created: "2026-10-01T23:28:00Z"
consequence: 7
locus: output
summary: Measured runs of the maker pipeline 2026-10-01 to 10-03 - first build day, the reviewer's noise floor, and the new-vs-old benchmark - with costs and times.
scope: repo
status: active
---

# Maker pipeline measurements

What real runs of the maker cost and scored between 2026-10-01 and 2026-10-03, and how noisy the reviewer is. Use it before trusting a score change, and as the baseline for the next benchmark.

## Question

How long and how much does a make take, how much does the independent reviewer's score move between runs on the same video, and did the 2026-10-02 maker changes beat the old pipeline?

## Method

- **Build day, 2026-10-01.** Three real makes: the operator's brand preset, Claude Opus maker, Sonnet reviewer, bubblewrap on.
- **Noise floor, 2026-10-02 18:11-18:50.** Scratch project inside the repo (the old baseline was off-limits), example preset, Sonnet maker and reviewer, effort unset. `make -n 3 --parallel 3`, then `review rescore ID --times 2` per video.
- **Benchmark, 2026-10-02/03.** Same setup. Videos 1-3 old pipeline; 4-6 new (B2, C1, D1, E2, F1, G1 from [[motion-quality-diagnosis]]). Each video reviewed twice.
- Costs are notional (subscription usage). All runs were launched from the operator's shell (issue I2).

## Findings

### Build day, 2026-10-01

| Video | Result |
|---|---|
| 1 "One button, before and after" | 14.0 s, 1.83 MB, H.264 1080x1920 30 fps; reviewer pass; superseded (black background) |
| 2 "Visitor to call" | 16.0 s, 1.95 MB; reviewer fail; superseded by 3 |
| 3, revision of 2 | 16.0 s, 2.26 MB; reviewer fail (tagline contrast at 13 s) |

- Time per video 14-21 min: agent 9-17, render plus encode about 1, review about 4.
- Cost per video: maker $0.91-1.37, reviewer about $0.65.
- Codex verified in the sandbox with the ChatGPT login; OpenCode unverified (no provider key).
- Defects found and fixed: opaque master (issue I5), font aliasing (I4), revise kept the old idea's pillar, topic and angle, mount exposure (`engine.safe_root`), reviewer now measures contrast on pixels. Later that evening: composition root (I6) and the credentials bind (only the login entry enters the jail).

### Reviewer noise floor, 2026-10-02

| Video | Verdicts | Spread (hook, read, comp, variety, brand, motion) |
|---|---|---|
| 1 | pass, pass | 0, 1, 0, 1, 1, 1 |
| 2 | fail, fail | 0, 1, 0, 1, 1, 0 |
| 3 | fail, fail | 1, 0, 1, 3, 0, 1 |

- Verdicts agreed on all 3 videos. Five criteria moved 1 point at most (mean spread 0.33-0.67). **Treat a 1-point change as noise.**
- Variety moved 3 points on video 3 because one run missed the same plain fade in all three strips.
- Both runs found a blank frame 0 and an empty settled hold at 6.83 s.
- Cost: makes $1.39-1.98 each (11.5 min for three in parallel); reviews $0.53-0.87 each, 6-8 min; total $8.77.
- Limits: 3 videos, example preset, Sonnet maker; the old reviewer's noise was never measured.

### Benchmark, new pipeline against old

| | Old | New |
|---|---|---|
| Reviewer pass | 2/6 | 4/6 |
| Mean of 6 criteria | 8.64 | 9.22 |
| Hook | 7.50 | 9.17 (+1.67) |
| Composition, motion, variety | 8.17, 8.67, 8.17 | 9.00, 9.17, 8.50 |
| Make cost, each | $1.39-1.98 | $2.35-3.10 |
| Wall time, 3 parallel makes | 11.5 min | 37 min |
| Gate failures | frame 0 blank, poster mid-move | one real overlap |

- Only the hook gain exceeds the noise floor; the other gains sit inside it.
- Self-scores never ran 2 or more above the reviewer (the new maker scores itself 0.4-1.3 lower), so the critic subagent (C2) was not triggered.
- Video 6 scored highest, 9.83; videos 5 and 6 passed both reviews.
- Gate fixes the run exposed: the probe hides a clip outside its `data-start`/`data-duration` window, as the player does; a word inside its own line no longer counts as overlapping it; the example accent `#2f6bff` (4.499:1 on white) became `#2b66f5`.
- Limits: 3 videos per arm, example preset only, one run each.

### What these numbers mean now

- The benchmark videos used the neutral example brand with a Sonnet maker at medium effort; none of them aimed at the target look ([[reference-leonabboud-showreel]]).
- Since ruling 18 the operator judges makes in the library; a scored benchmark is optional (decision 12 in [[reference-look-decisions]]).

## Sources

- Library and session data in the operator's project folder (outside this repo) and the scratch project (since removed).
- Former wiki notes `build-log`, `noise-floor` and `benchmark` (git history of this wiki, before 2026-10-06).

## Date

Measured 2026-10-01 to 2026-10-03; merged into one research file 2026-10-06.
