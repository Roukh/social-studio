---
id: qa
type: reference
created: "2026-10-06T23:59:00Z"
consequence: 7
locus: output
summary: Box qa - report-only quality gates run after the final render (copy, contrast, safe zone, min px, overlap, fonts, frame 0, poster, audio, loudness, check).
scope: repo
status: active
---

# Box: qa

Part of [[index]]. Measures the finished video and its composition and reports; it never rejects or retries.

| Field | Value |
|---|---|
| Purpose | Find observable defects in code so neither the maker nor the reviewer has to notice them |
| Owned paths | `src/social_studio/qa.py` (405 lines), `data/qa-probe.mjs` (headless-Chrome probe of the built timeline), `tests/fixtures/qa/` (9 calibration fixtures), `tests/test_qa.py` |
| In | the delivery video, `composition/`, `brief.json`, `poster_at`, preset values (`video.safe_zone`, `content.*`, `encode.loudness`) from [[runner]] |
| Out | `qa.json` in the library folder = `version`, `gates{copy, check, contrast, safe_zone, min_px, overlap, fonts, frame0, poster, audio, loudness: ok|fail|skipped}`, `findings[{gate, t, detail}]`, `settled[]`, `lufs`; the gate summary also in `videos.meta.qa` |

## Gates

| Gate | Measures | Source |
|---|---|---|
| contrast, safe_zone, min_px, overlap | on settled holds only (never the sampler's "calmest" fallbacks, which are mid-motion) | probe nodes |
| fonts | every rendered family is declared in `index.html` | probe nodes |
| frame0 | frame 0 has visible text or is not near-uniform | probe plus pixels |
| poster | `poster_at` sits inside a settled hold | sampler holds |
| copy | banned words, exact lines, near-miss spellings | probe text plus `brief.on_screen_text` |
| audio | an audio stream exists when `brief.cues` lists cues | ffprobe |
| loudness | integrated loudness within -14 +/- 1 LUFS (`encode.loudness`) | ebur128 |
| check | `hyperframes check --json` | engine, in the jail |

## Invariants

- Report-only: a finding never stops, rejects or retries a video (rule R12). Enforcing with one automatic re-make is job J5 and must never auto-reject.
- The probe and `hyperframes check` run in the same jail as the render, with no network.
- Text floors scale from the frame's short side: `round(11 x short / 393)` (30 px at 1080); WCAG ratios 4.5 normal, 3.0 large (24 pt regular, 18.66 pt bold at weight 600).
- The probe hides a clip outside its `data-start`/`data-duration` window, as the player does; a word inside its own line is not an overlap; overlaps under 4 px are ignored.
- Calibration fixtures: pass a two-line per-word title, a spatial entrance, a wipe over text, sequential clips; fail purple on purple, a small label pill, off-screen text, overlap across blocks, a Georgia font with the network off. Fixture verdicts must hold across engine upgrades (job J4).

## Rules and open work

- Rules: R8 (loudness), R12 (report-only creative gates).
- Ledger: J4, J5.
- Research: [[motion-quality-diagnosis]] (option G), [[maker-measurements]] (gate fixes).
