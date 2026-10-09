# leaderboard-bar-race

**Family:** data. **Wants:** 2-3 s per rank update, 1-2 updates. **Source:** founder.page's launch film in
prompt-motion.com's gallery (prompt-motion.com/ratheejaisal-1f4538), studied 2026-10-09.

## Looks

A small ranked list of horizontal bars (an avatar chip, a name, a bar, a dollar value) sits under a dated
header card. As a date ticker advances from one cut to the next (Sep 9, then Sep 17, then Sep 30), the bars
regrow to new lengths and the values roll to new numbers, and rows that overtake each other swap position. A
big, soft background watermark of the current date sits behind the card and crossfades on each step.

## Build

- One row per rank, a flex DOM row with an avatar chip, a bar (`scaleX` or `width` tween from its old value to
  its new one) and a value span.
- On each date step: re-sort rows by their new value and tween each row's vertical position to its new slot
  (FLIP-style, about 0.3 s, `power2.inOut`); tween the bar width on the same beat; re-roll the value digits
  with a blurred roll-up (see `data-infographic.md`'s counter).
- The background date watermark text crossfades/slides behind the card on each cut, never in front of it.

## Sound

A tick per row that re-sorts, a soft riser under the bars regrowing, and a slightly louder tick on the date
flip.

## Adapting

Use for any ranked or competitive metric that changes over time: a leaderboard, top sellers, trending items,
a standings table. Keep to 5-7 rows; more than that is unreadable at a glance. The ranks and values should be
samples unless the brief gives real ones.

## Variants

The same move, as other reference films staged it:

- **live race leaderboard** (prompt-motion.com's gallery (marklaunches-3b9492), studied 2026-10-09.): A large race-clock readout counts down over a checkered-flag strip, above a row of player chips (an avatar, a name, a live number) ranked left to right by position. The current player's chip glows with an outline and a small flame or marker rising from it. A status banner beneath states the gap to first place in plain language, updating as the numbers change. As the clock ticks down across several cuts, the chips reorder and the gap narrows or widens.
