# Attribution

The pitch round (this skill, `data/pitch_prompt.md`, `data/judge_prompt.md` and the rubric in `pitch.py`) is
**distilled and edited from** two sources.

## HyperFrames (Apache-2.0)

> https://github.com/heygen-com/hyperframes
> tag `v0.8.106`, licensed Apache-2.0.

A copy of the Apache License, Version 2.0 is in `LICENSE` in this directory, as required by §4 of that license.
This NOTICE file is informational and does not modify the License (Apache-2.0 §4(d)).

| This repository's file | Derived from (upstream path, tag `v0.8.106`) | What changed |
|---|---|---|
| `SKILL.md` §1-6 | `skills/hyperframes/references/pitch-round.md`, "The sampling gate" (the four questions, the five paths, the tail constraint, the silhouette check) and "The gate, alone" (the most typical direction left behind) | Reworded for an autonomous session that writes `pitches.json` instead of presenting pitches to a user; added the product-truth rule (§3) from this tool's own films; the probabilities and paths are kept from the judge instead of from a user |
| `data/pitch_prompt.md` | the same sections | Condensed into the pitcher's task and the `pitches.json` schema |

## The operator's design-tournament skill

The operator's own `design-tournament` skill, distilled at the operator's direction (it is not third-party code
and none of it is copied): independent candidates given the same facts, one shared rubric, "distinguish working
behavior from attractive prose", and a stable winner chosen from the scores.

| This repository's file | What it takes |
|---|---|
| `data/judge_prompt.md` | a fresh judge that sees the same facts for every candidate and scores each on the same rubric |
| `pitch.py` (`RUBRIC`, `check_verdict`) | the rubric's criteria rewritten for a short product film; code, not the judge, picks a stable winner from the scores |

## No trademark or brand grant

Per Apache-2.0 §6, this NOTICE and the License grant no rights to any HyperFrames or heygen.com trade name,
trademark, or product name beyond identifying the origin above.
