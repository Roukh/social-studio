---
id: review
type: reference
created: "2026-10-06T23:59:00Z"
consequence: 7
locus: output
summary: Box review - the independent reviewer session, the settled-frame sampler, anchored criteria, verdict validation in Python, and rescore for the noise floor.
scope: repo
status: active
---

# Box: review

Part of [[index]]. A fresh session, ideally on another model, that never saw the maker's context and scores what code shows it.

| Field | Value |
|---|---|
| Purpose | Score a finished video against anchored criteria and return a validated verdict; measure the reviewer's own noise |
| Owned paths | `src/social_studio/review.py` (159 lines), `src/social_studio/sampler.py` (158 lines, also copied into every maker session as `tools/sampler.py`), `data/anchors.json`, `data/review_prompt.md` |
| In | the maker session's `preset.json`, `history.json`, `video.json`, `brief.json`; the video; the composition CSS; `review.*` preset keys |
| Out | `<id>-review/verdict.json` = `pass`, `scores{criterion: 1-10}`, `repeat`, `issues[]`, `summary`, plus `model`, `effort`, `cost_usd` from the runner; `review rescore` returns runs, per-criterion spread and mean |

## Sampler (code picks what the reviewer sees)

- Motion curve on a 180x320 grey difference; a step is still below 2.0; a settled hold lasts at least 0.3 s; up to 10 settled samples, at least 3 (calmest frames added and marked).
- 3 strips of 6 frames around the biggest motion peaks (at least 1.0 s apart, at most 0.75 s either side), plus frame 0.
- Pages shown to a model are at most 2000 px on either side; at 9:16 a red safe-zone outline is drawn.

## Invariants

- Criteria default to: hook in the first 2 seconds, readability on a phone, composition, variety, brand accuracy, motion quality. Each has anchors at 10, 7, 4, 1 tied to observable failures, not technique quotas (`data/anchors.json`).
- The text floor in anchors is `round(11 x short side / 393)`; the safe-zone check applies only to portrait frames; HUD labels, counters and texture type are exempt (rule R12).
- `check_verdict` validates shape, 1-10 scores for every criterion, and that `pass` agrees with the scores and the repeat check; a verdict that fails is an error, never a pass.
- A reviewer fail never rejects a video; it goes to the human with its verdict.
- Treat a 1-point score change as noise ([[maker-measurements]]); re-measure the noise floor whenever the anchors change.
- Each role reads only its own keys (`review.*`); `review.effort` and `--review-effort` are separate from the maker's.

## Rules and open work

- Rules: R12 (skills over rules), R13 (the operator, not a score, judges the look).
- Ledger: T2 (try a Codex reviewer).
- Research: [[motion-quality-diagnosis]] (option A2), [[maker-measurements]].
