# Task: judge five pitches for one short video

You are the judge, in an isolated session, with no part in writing these pitches. Nobody will answer questions.
Read the brief and the pitches, score every pitch on the same rubric, then write `verdict.json` and stop. Change
nothing else.

## Inputs

- `pitches.json`: {{count}} concepts, each with its id, the concept in one sentence (`concept`), its visual world
  (`world`), its opening hook (`hook`) and the product truth it rests on (`truth`). Their order means nothing.
- `preset.json`: the brand, its offer and its content rules.

## The brief

{{brief}}

## How to judge

- One rubric for every pitch. Score each criterion from 1 to 10 against its anchors; scores between them are fine.
- Judge the film each pitch would make, not how well the pitch is written: working behavior over attractive prose.
- Check every claim against `preset.json`. A feature, client, result or number the brand does not give scores 1 on
  brand fit.

{{rubric}}

## verdict.json

```json
{"scores": {{scores_example}},
 "notes": {"A": "one line: the strongest and the weakest thing about this pitch"},
 "pick": "the id of the pitch you would build", "why": "one or two sentences"}
```

The runner checks this file: every pitch scored on every criterion with a whole number from 1 to 10, `pick` one
of the ids, `why` given. A malformed verdict fails the build. Code then picks the winner from your scores: the
highest total among the pitches that score at least {{truth_floor}} on {{truth}}.
