---
id: story
type: reference
created: "2026-10-09T06:00:00Z"
consequence: 9
locus: output
summary: Box story - the storyteller session that runs before the designer in the same sandbox, and the tagged SQLite reference store (techniques, film scenes, brand story posts) both draw from.
scope: repo
status: active
---

# Box: story

Part of [[index]]. Feature F15 (operator spec M40, decisions M42): a build runs story first, and its techniques come from a tagged store grown scene by scene from reference films.

| Field | Value |
|---|---|
| Purpose | Write the film's story before any motion (idea, story references, beats, banned looks), then hand the designer each beat with the store's best techniques for it |
| Owned paths | `src/social_studio/story.py`, `src/social_studio/store.py`, `data/story_prompt.md` (STORY.md template), `data/skills/storyteller/`, `data/store/` (`facets.json`, `techniques/`, `scenes/`, `stories/`, one JSON file per item), `scripts/split_scenes.py` (film to scenes, for extraction sessions) |
| In | a prepared session from [[runner]]; the preset (brand text, `story.*`, `video.duration`, `video.sound`); `history.json` (recent technique sets, ideas) |
| Out | `work/story.json` (checked and normalised), `work/techniques.json` (per-beat candidates), the designer brief that [[runner]] puts in TASK.md; `videos.meta.story` (idea, structure, beats, references) |

## Flow (`story.tell`)

1. `store.stories_for` ranks the story references against the brand (goal 2, product 2, format 1, FTS text up to 2) and writes the top 8 to `story-references.json`.
2. STORY.md, the storyteller skill and the vendored `launch-video` skill; the session runs with role `story` (`story.*` limits: 30 turns, 15 min by default; no MCP, plugins or house file).
3. `story.check`: 2-8 beats with a role, seconds and a job; seconds inside `video.duration` (±0.5 s); cited references exist; tag values outside `facets.json` dropped, not fatal; rule R41's banned looks always added.
4. `store.for_beats`: per beat, facet score (role 3, purpose 2, content 1.5, energy 1, format 1) plus FTS bm25 up to 2, minus 2 when a recent film used the item's techniques; an item serves one beat; plus three `whole-film` layers.
5. `story.designer_brief` renders the beats, copy, voice lines, candidates with why and general prompts, and the banned line.

## The store (`store.py`)

- Items are JSON files (reviewable diffs, parallel extraction sessions never share a file); SQLite is built from them on first use per process: `items`, `tags(item, facet, value)` many-to-many, `uses(scene, technique)`, FTS5 `fts`. `open_store` refuses a store with any problem.
- Kinds: `technique` (atomic move; recipe `data/skills/technique-library/techniques/<id>.md`), `scene` (one shot of a reference film: looks, build, sound, general prompt, the techniques it uses, source film and time range), `story` (one analysed brand post: object, message, moments with roles, CTA, why).
- Stdlib only and runnable alone: every session gets `tools/store.py` and `store.db` to search.
- Licence (rule R43): items paraphrase and cite; no frames, clips, transcripts or verbatim prompts in the repo. Films and frames stay in `.local/refs/`.

## Invariants

- A revision skips the storyteller; `story.enabled = false` skips it everywhere. The storyteller uses the designer's backend and model unless `story.backend` or `story.model` is set.
- The designer never sees a story that failed its check: the build fails with every problem listed.
- A tag value exists only in `facets.json`; `python -m social_studio.store check` lists every problem by file.

## Rules and open work

- Rules: R41 (banned looks), R43 (prompt-motion licence), R6 (story and boards; boards still open, J7).
- Ledger: F15 (J40-J45); F2's J6 (pitch round) and J7 (boards) overlap.
