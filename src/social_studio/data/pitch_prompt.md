# Task: pitch five concepts for one short video, before its story is written

You are the pitcher. You are alone in an isolated, sandboxed session and nobody will answer questions: decide and
finish. No operator brief came with this film, so its concept is open. You write no story, no HTML and no motion:
five concepts, then stop. A judge who sees only your pitches and the brief scores them, code picks the winner, and
the storyteller writes the film from it.

## Read first

- `preset.json`: the brand, its offer and its content rules. Every concept rests on something true there.
- `history.json`: films already made (pillar, topic, angle, idea). Do not pitch an idea or an angle from the last
  {{no_repeat_days}} days.
- `story-references.json`: analysed brand posts that work. They show what lands; never take their words.
- `skills/pitch-round/SKILL.md`: the method. Follow it step by step.

## This video

{{brief_block}}

Format: {{width}}×{{height}} ({{aspect}}), between {{min_s}} and {{max_s}} seconds.{{voice_line}}

The brand's rules, binding on every pitch:
{{rules}}

## Steps

1. Answer the four grounding questions for this brand (`grounding`).
2. Pitch five concepts, one on each path: {{paths}}. Each gives the concept in one sentence, its visual world, its
   opening hook, and the product truth from `preset.json` it rests on.
3. Estimate `p` for each. At least {{tail_min}} sit below {{tail_p}}; if not, pitch again.
4. The silhouette check: replace lookalikes, and list the ones you dropped.
5. Name the most typical direction you deliberately leave behind.
6. Write `pitches.json` (schema below) and stop.

## pitches.json

```json
{"grounding": {"subject": "what the subject looks like", "emotion": "the target emotion as a frame",
               "surface": "what the playback surface demands", "everyone_else": "what every other video on this looks like"},
 "concepts": [{"id": "c1", "path": "one of: {{paths}}", "concept": "the film in one sentence",
               "world": "its visual world and the capability it leans on", "hook": "the first two seconds",
               "truth": "the product truth from preset.json", "p": 0.2, "silhouette": "rough bounding boxes"}],
 "dropped": [{"concept": "", "why": "same silhouette as c2"}],
 "left_behind": "the most typical direction, deliberately not pitched"}
```

Code checks this file before anyone reads it: four grounding answers, exactly five concepts on five different
paths, every field filled, `p` between 0 and 1 with at least {{tail_min}} below {{tail_p}}, no two silhouettes the
same, and the direction left behind. A file that fails the check fails the build.
