---
id: motion-quality-diagnosis
type: reference
created: "2026-10-02T06:30:00Z"
consequence: 8
locus: output
summary: Why the 2026-10-02 videos were "fine but not great" - 8 harness findings, options A-J for the maker pipeline, which were built, and what stayed open.
scope: repo
status: active
---

# Motion quality diagnosis (2026-10-02)

The diagnosis behind the first maker-quality upgrade. The operator rated the output "fine but not great" on 2026-10-02. Measured against the 0xMovez Opus 5.5 course and the operator's SOP §5a/§6, the gap was the harness, not the model. Its built options are now in the [[runner]], [[review]], [[qa]] and [[maker-kit]] boxes; the later reference-look work is in [[reference-look-decisions]].

## Question

Why do the made videos read as generic, and which changes to the maker pipeline (brief, effort, self-critique, motion doctrine, evidence, gates, measurement, sound) fix it?

## Method

- Read the course article ([[motion-course-article]]; thesis: "The prompt is 10% of the video. The other 90% is the harness").
- Read the session transcripts, compositions and contact sheets of videos 1-3 (2026-10-01), the mounted engine skills (`E/skills/`, 2.77 MB) and the runner code with line refs.
- Compared against the operator's social studio SOP (2026-09-29) and design-principles ledger (the operator's own files, not in this repo).

## Findings

### The eight findings

| # | Finding | Evidence (2026-10-02) |
|---|---|---|
| 1 | All makers ran at medium effort; reviewers at high. No `--effort` was passed and the jail does not inherit the operator's setting | transcript `"effort":"medium"` |
| 2 | Self-scores were a harness bug: `revision.json` handed the maker its predecessor's scores, video 3 echoed them (8/8/8/8/9/8), and the loop ended on the maker's own score. The reviewer gave 8/5/7/4/6/6 | session_prompt, events 128-149 |
| 3 | The mounted skills taught the giveaway: "Every scene uses entrance animations... opacity", "Exit animations are BANNED", templates start from `opacity: 0`. The doctrine against fades lived in unmounted skills (`product-launch-video`, `hyperframes-keyframes`). Under 1 % of the mounted 2.77 MB was read | `E/skills/hyperframes-animation/transitions/overview.md` L21-24 |
| 4 | The preset licensed only opacity-led entrances while banning fade cascades; time-paced "ink from 14 %" dipped contrast to 1.37:1 for about 2 frames per word | composition helpers |
| 5 | Web-page scale: static header for 11 s, content in the top ~60 %, 26 px labels and an 18 px pill (below the 11 pt HIG minimum, ~30 px at 1080 wide), a 6-word caption held 1.1 s, the end card took 32 % of the runtime, a ghost frame 0, a poster mid-tap. "Keep everything they did not ask to change" froze it all on revision | contact.jpg, CSS |
| 6 | No enforced gate: `render --strict` is static lint only; `check` audits were optional and misfired on per-word spans and mid-wipe frames, while the real dip at 13.0 s went unflagged | `E/dist` render L649-654 |
| 7 | The reviewer was a noisy instrument: fixed sample times landed on transitions, a history bug inflated "variety", it passed video 1's black background | runner review sampling |
| 8 | Silent video although the SOP allows SFX; `.word-mark` named Georgia, so the renderer fetched EB Garamond over the network | preset |

### Options and what happened to them

| Option | Content | Outcome |
|---|---|---|
| A2 measurement | code-picked settled holds plus strips around the 3 biggest motion peaks; anchors tied to observable failures; variety split from repeats; CSS given to the reviewer; `verdict.json` validated in Python; `review rescore ID --times N` | built 2026-10-02 (`sampler.py`, `review.py`, `data/anchors.json`); noise floor in [[maker-measurements]] |
| B2 director's brief | film in one line, shots on a beat grid (start state, change, end state, text, cue, blueprint id, never the same twice in a row), reading-time and frame-0 rules, capped end card; house rules through each harness's system channel, never `work/CLAUDE.md`; "never ask; draft renders are pre-approved" | built; the creative rules became defaults in iteration 1 (ruling 16) |
| C1 / C2 self-critique | C1: fixed round count, previous scores never shown, `min_score` hidden. C2: a claude-only critic subagent, only if self-scores ran 2+ above the reviewer | C1 built; C2 not triggered |
| D1 effort per role | `agent.effort` and `review.effort` read only by their own role; `--effort`, `--review-effort` | built |
| E2 motion doctrine | unmount the fade-leaning skills; ship a short guide distilled from `product-launch-video`, `hyperframes-keyframes`, `blueprints-index.md` (Apache-2.0) | built as `data/skills/motion-doctrine` (13 blueprints); the engine skills came back in iteration 1 |
| F1 in-session evidence | the maker draft-renders and samples frames in the jail (pages at most 2000 px, safe-zone overlay, strips, frame 0, poster); the maker cannot write `render/` | built (`tools/sampler.py`) |
| G1 / G2 gates | G1 report-only gates: copy lint, `check` errors, settled contrast, safe zone, min px, frame 0, poster window, audio when cues exist; calibrated on fixtures. G2: enforce with one automatic retry, never auto-reject | G1 built (`qa.py`, `qa.json`); G2 open (ledger J5) |
| H references | H1 owned captures of the brand site; H2 external launch films, grammar only | superseded by the reference look (decision 11 deferred import) |
| I sound | ElevenLabs ruled (9); no-model-can-hear, so sync is checked in code | superseded by iteration 1's code synth (decision 4) |
| J later | 4:5, 1:1, 16:9 recompositions; motion blur through `tmix` (~8x render time); best-of-N with `hyperframes compare` | formats built in iteration 1; blur via velocity helper (decision 7) |

### Decisions taken on 2026-10-02

- Motion signature, pacing and effort per role are set per run from the CLI ("let it be set in cli"): `make --motion`, `--pacing`, `--effort`, `--review-effort`; `review rescore --effort`. Unset: the doctrine's spatial arrivals, no pacing line, the harness default effort.
- Still open from this plan: the drop policy for gate failures (J5), the reviewer model (task T2).

### Verification it set

- pytest: effort per role; one house channel per backend and no `work/CLAUDE.md`; no unfilled `{{...}}`; no brand tokens in `data/`; `revision.json` carries no scores; the sampler lands in settled windows; pages at most 2000 px; copy lint; WCAG math (21:1; #6b6b6b on #fafafa about 5.1); the poster window; the round loop never auto-rejects and `--revise` never drops.
- Calibration fixtures (need the engine; `tests/fixtures/qa/`): pass a tight two-line per-word title, a spatial entrance and a wipe over text; fail purple on purple, a 26 px label, an 18 px pill, text at y=1500, overlap across blocks, Georgia with the network off.

## Sources

- Article: https://x.com/0xMovez/status/2104216919033192746 (2026-09-27; read through api.fxtwitter.com).
- The operator's SOP and design-principles ledger (not in this repo).
- Engine `<project>/.studio/engine/hyperframes-0.8.106/` (`dist/`, `skills/`).
- Baseline evidence: `~/.local/share/social-studio/` (untrimmed sessions and the pre-move database; whether to keep it is the operator's call).
- Apple HIG typography: https://developer.apple.com/design/human-interface-guidelines/typography

## Date

Diagnosed and planned 2026-10-02; options A2-G1 built 2026-10-02 to 10-03. Folded from the former `arch/motion-quality-plan.md` on 2026-10-06.
