---
name: pitch-round
description: How to pitch five distinct concepts for one short product film before its story is written - four grounding questions, five sampling paths, the tail constraint, the silhouette check, a product truth under every concept, and the typical direction left behind. Read it before writing pitches.json.
---

# Pitch round

Nobody gave this film a brief, so its concept is open. The danger is the median: the film any model would make
from this preset, the one that looks like every other video on the subject. The pitch round samples wide on
purpose. A judge who never sees your reasoning then scores the pitches on one shared rubric, code picks the winner
from the scores, and the storyteller writes the film from it. Nobody is present to say "this looks like every other
video", so the round has to say it.

## 1. Ground it: four questions, answered for this brand, never generically

1. **What does the subject look like?** The product's own visual world: its interface, its output, its numbers,
   its materials. This vocabulary drives the layouts.
2. **What does the target emotion look like as a frame?** Relief is a crowded frame going empty; urgency is
   compression; awe is one element too large for the canvas.
3. **What does the playback surface demand?** A vertical feed fights for its first second, sound off, thumb
   moving. A wide frame on a site is watched on purpose but still skimmed.
4. **What does every other video on this subject look like?** That is the anti-pattern. Name it concretely.

## 2. Five concepts, one from each path

| Path | The concept comes from |
|---|---|
| `subject` | the product's own world (question 1) |
| `emotion` | the feeling the viewer leaves with, as a frame (question 2) |
| `audience` | the viewer's expectation, met exactly or broken on purpose |
| `anti-pattern` | question 4, inverted |
| `format` | an unusual container: a letter, a countdown, a recipe, a front page, a map, a receipt |

Each pitch has four parts, written so that someone who read only the brief understands it:

- `concept`: the film in one sentence.
- `world`: its visual world, naming the one or two capabilities it leans on in plain words ("the price counts
  down on the beat", "the interface builds itself line by line"). A capability that would fit all five pitches is
  decoration; name it only where this concept depends on it.
- `hook`: what the first two seconds show.
- `truth`: the product truth it rests on (next section).

## 3. Every concept rests on a product truth

A concrete fact about the product from `preset.json`: what it does, a feature, the offer in its exact words, a
number the brand gives. The film shows that truth working. A mood, a value or a metaphor with nothing of the
product in it is not a concept. The film this tool lost with (2026-10-08) morphed an abstract shape through design
pieces and had nothing to sell; the films that were kept showed a concrete offer working. Never invent a feature,
a client, a result or a number.

## 4. The tail constraint

Estimate for each concept the probability `p` that a model handed this preset would make it. The numbers are
directional, not calibrated; they exist to enforce one rule: **at least two of the five sit below 0.10.** If all
five clear 0.10, every pitch is the median: start over.

## 5. The silhouette check

Sketch each concept's major elements as rough bounding boxes ("one huge number across the top half, a product card
below it"). Two concepts with the same silhouette are one concept: replace one, and list the dropped one with why.

## 6. Name what you leave behind

The most typical direction for this brief, the one you deliberately do not pitch (`left_behind`). The storyteller
is told not to drift back to it, and the film's record keeps it.

## What the judge sees

Only each pitch's `concept`, `world`, `hook` and `truth`, under a letter, in shuffled order, with the brief. Not
your grounding answers, your probabilities, your paths, your silhouettes or what you dropped. So each pitch stands
on its own words. The judge scores what the film would show, not how well the pitch is written.
