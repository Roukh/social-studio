---
name: storyteller
description: How to write the story of a 15-30 s product video before any motion is designed - the one-line idea, learning from analysed brand posts, beats with a job each, copy and voice lines, and the looks to ban. Read it before writing story.json.
---

# Storyteller

A short product film works when it says one concrete thing and every few seconds changes what the viewer knows.
The motion comes later, from a designer who reads your story. Your story decides whether the film has anything
to say.

## What works here (measured on this tool's own films)

- The films the operator kept showed a concrete offer working (a site built against a 48-hour clock) and changed
  scene on every beat. The film that lost morphed one abstract shape through design pieces with nothing to sell,
  and spent half its runtime on a tagline and an end card (2026-10-08).
- So: a product, a feature or an offer, shown doing its job. Never a mood piece about a value.

## The idea in one line

"This video tells [audience] that [message]." (the echo line of Kenn Adams' Story Spine). If you cannot fill both
brackets with something specific, the film has no idea yet. Test it with And-But-Therefore (Randy Olson): the
viewer wants X, but Y gets in the way, therefore the product. A film that only says "and, and, and" is a list.

## Structures that fit 15-30 s

| Structure | Beats | Use when |
|---|---|---|
| intro-problem-solution-cta | who it is for, the pain, the product removing it, the ask | the product fixes a felt pain |
| intro-body-cta | the promise, two or three proofs or features, the ask | the product is new or broad |
| hook-demo-cta | a striking claim, the product doing it, the ask | the product is fast or visual |
| before-after-cta | the old way, the new way side by side, the ask | the difference is visible |
| list-cta | three things, one per beat, the ask | features of equal weight |
| montage-cta | a run of results on the beat, the brand, the ask | a launch or a recap |

Learn the structure from the closest analysed posts in `story-references.json`: where their problem sits, how
soon the product appears, what the last moment before the call to action does. Take their shape, never their
words.

## Timing for a 20-25 s film

- The first 2 s already say something: the claim, the pain, or the product in motion. The proposition is clear by
  3 s; short-form viewers decide that fast.
- The problem takes at most a quarter. The solution or demo takes the largest share.
- The call to action and wordmark take at most a fifth, and the beat before them earns them.
- 4 to 6 beats. Each beat is at least 2 s, so something can happen in it.

## A beat

One beat, one job: what the viewer must understand by its end. If two things must land, it is two beats. The
`emotion` is what they should feel (curiosity, relief, "that's fast", confidence), and it tells the designer how
hard to hit. `shows` says what is on screen in plain words: the product's interface doing X, a number climbing, a
before and after. The designer turns it into motion; you never name a technique.

The tags steer which techniques the store offers the designer for the beat:
- `purpose`: why the beat exists (reveal-product, show-ease, show-speed, explain-mechanism, build-tension, land-cta...).
- `content`: what is on screen (product-ui, data, type, logo, device, code...).
- `energy`: calm, build or punch. A film that is all punch has no punch: vary it, and build into the reveal.

## Copy and voice

- On-screen lines are short (six words or fewer reads on a phone), in the brand's own words, with verbs. The
  brand's exact lines and call to action are copied exactly.
- Never invent clients, results, reviews, prices or numbers. A number on screen comes from the brand's material.
- A voiced film: the voice carries the idea and the screen echoes its key words. About 2.5 spoken words a second,
  so a 3 s beat holds about seven words. The voice sets the timing.
- A silent film: every idea is on screen, and works with the sound off.

## Banned looks

List what would make this film generic, so the designer avoids it: crossfades, template glass-kit UI cards,
stock gradient blobs, a logo that just fades up, text that types on letter by letter with nothing else moving. Add
what this brand's competitors all do.

## Before you write story.json

- The idea line names a real audience and a concrete message.
- Every beat has a job, and the jobs build to the call to action.
- The seconds add up inside the film's range.
- The copy follows the brand's rules, word for word where they give exact lines.
