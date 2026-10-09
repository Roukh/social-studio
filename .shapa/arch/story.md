---
id: story
type: reference
created: "2026-10-09T06:00:00Z"
consequence: 9
locus: output
summary: Box story - the pitch round (no operator brief), the storyteller session that runs before the designer in the same sandbox, and the tagged SQLite reference store (techniques, film scenes, brand story posts) both draw from.
scope: repo
status: active
---

# Box: story

Part of [[index]]. Feature F15 (operator spec M40, decisions M42): a build runs story first, and its techniques come from a tagged store grown scene by scene from reference films.

| Field | Value |
|---|---|
| Purpose | Pick the film's concept when nobody gave one (the pitch round), write its story before any motion (idea, story references, beats, banned looks), then hand the designer each beat with the store's best techniques for it |
| Owned paths | `src/social_studio/story.py`, `src/social_studio/pitch.py`, `src/social_studio/store.py`, `data/story_prompt.md` (STORY.md template), `data/pitch_prompt.md` (PITCH.md), `data/judge_prompt.md` (JUDGE.md), `data/skills/storyteller/`, `data/skills/pitch-round/` (method, Apache-2.0 LICENSE and NOTICE), `data/store/` (`facets.json`, `techniques/`, `scenes/`, `stories/`, one JSON file per item), `scripts/split_scenes.py` (film to scenes, for extraction sessions) |
| In | a prepared session from [[runner]]; the preset (brand text, `story.*`, `pitch.*`, `judge.*`, `video.duration`, `video.sound`); `history.json` (recent technique sets, ideas) |
| Out | `work/pitches.json` and `work/pitch-verdict.json` (pitch round only), `work/story.json` (checked and normalised), `work/techniques.json` (per-beat candidates), the designer brief that [[runner]] puts in TASK.md; `videos.meta.story` (idea, structure, beats, references; `pitch`: winner id, path, concept, product truth, the direction left behind, points) |

## Flow (`story.tell`)

1. `store.stories_for` ranks the story references against the brand (goal 2, product 2, format 1, FTS text up to 2) and writes the top 8 to `story-references.json`.
2. The pitch round (`pitch.run`, J6, rule R6 ruling 6) when there is no operator brief (`content.title`, `subject`, `topic` and `notes` all unset) and `story.pitch` is not false:
   - The pitcher (role `pitch`, 30 turns, 15 min) in the build's own folder writes `pitches.json`: four grounding answers, five concepts on the five paths (subject, emotion, audience, anti-pattern, format), each with a concept line, visual world, hook, product truth (memory M27), `p` and a silhouette; the dropped lookalikes; the typical direction left behind. `check_pitches` lists every problem: exactly five, five distinct paths, at least two below p = 0.10, no shared silhouette, every field filled.
   - The judge (role `judge`, 15 turns, 10 min) runs in `<session>/judge/` with its own home and work, so it sees only `JUDGE.md` (the brief and the rubric), `preset.json` and the pitches' own words (concept, world, hook, truth) under letters A-E in an order shuffled by the session id; never the pitcher's grounding, probabilities, paths or transcript. It scores six criteria 1-10 (product truth, clarity, hook, distinctiveness, brand fit, buildable) and names a pick.
   - `check_verdict` (as `review.check_verdict`): every pitch on every criterion a whole number 1-10, a pick among the ids, a reason; a malformed verdict fails the build with every problem listed. Code picks the winner: the highest total among pitches scoring 5 or more on product truth (ties: product truth, distinctiveness, the judge's pick); none eligible fails the build. A pick that differs from the scores is recorded as `checked`. The judge's logs join the build's (`logs/judge.*`), its folder is removed.
   - STORY.md is written again with the winning concept and the direction left behind; the storyteller builds the story from it.
3. STORY.md, the storyteller skill and the vendored `launch-video` skill; the session runs with role `story` (`story.*` limits: 30 turns, 15 min by default; no MCP, plugins or house file).
4. `story.check`: 2-8 beats with a role, seconds and a job; seconds inside `video.duration` (±0.5 s); cited references exist; tag values outside `facets.json` dropped, not fatal; rule R41's banned looks always added.
5. `store.for_beats`: per beat, facet score (role 3, purpose 2, content 1.5, energy 1, format 1) plus FTS bm25 up to 2, minus 2 when a recent film used the item's techniques; an item serves one beat; plus three `whole-film` layers.
6. `story.designer_brief` renders the beats, copy, voice lines, candidates with why and general prompts, and the banned line.

## The store (`store.py`)

- Items are JSON files (reviewable diffs, parallel extraction sessions never share a file); SQLite is built from them on first use per process: `items`, `tags(item, facet, value)` many-to-many, `uses(scene, technique)`, FTS5 `fts`. `open_store` refuses a store with any problem.
- Kinds: `technique` (atomic move; recipe `data/skills/technique-library/techniques/<id>.md`), `scene` (one shot of a reference film: looks, build, sound, general prompt, the techniques it uses, source film and time range), `story` (one analysed brand post: object, message, moments with roles, CTA, why).
- Stdlib only and runnable alone: every session gets `tools/store.py` and `store.db` to search.
- Licence (rule R43): items paraphrase and cite; no frames, clips, transcripts or verbatim prompts in the repo. Films and frames stay in `.local/refs/`.

## Invariants

- A revision skips the storyteller; `story.enabled = false` skips it everywhere. The storyteller uses the designer's backend and model unless `story.backend` or `story.model` is set; the pitcher and the judge use the storyteller's.
- The pitch round is part of the story stage: no story, no pitch round. An operator brief or `story.pitch = false` skips it.
- The designer never sees a story that failed its check, and the storyteller never sees pitches or a verdict that failed theirs: the build fails with every problem listed.
- No operator step anywhere in the story stage (memory M42).
- A tag value exists only in `facets.json`; `python -m social_studio.store check` lists every problem by file.

## Rules and open work

- Rules: R41 (banned looks), R43 (prompt-motion licence), R6 (story and boards).
- Ledger: F15 (J40-J47; J6 the pitch round and J7 the boards, folded in 2026-10-09).
- Sources: the engine's `pitch-round.md` (Apache-2.0) and the operator's design-tournament skill, distilled; attribution in `data/skills/pitch-round/NOTICE.md`.
