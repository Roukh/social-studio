# Task: independent review of one finished video

You are a reviewer in an isolated session, with no part in making this video. Nobody will answer
questions. Judge only what is in this folder, then write `verdict.json` and stop. Change nothing else.

## Inputs

- `preset.json`: the brand and content rules the video must follow.
- `history.json`: videos made before this one. Use it for the repeat check only.
- `video.json` and `brief.json`: what the maker says the video is, and its captions.
- `composition.css`: the styles the video was built with: fonts, sizes in px, colours, shadows, radii.
  Read sizes and shadows there instead of guessing them from pixels.
- `samples.json` lists every image in `samples/` with its time. Code picked them from the video's own motion:
  - `settled-*.png`: every moment where nothing on screen changes for at least {{hold_s}} s, at full size
    ({{width}}×{{height}}). Judge text, contrast, the safe zone and composition on these.
  - `strip-*.jpg`: the {{strips}} biggest moves, each as {{strip_frames}} frames from just before the move to its
    settle, left to right. Judge motion on these. A frame inside a move is meant to be in between: never fail
    contrast or readability on a strip.
  - `frame-0.png`: the first frame.
- `contact.jpg`: an overview at fixed times, some of them inside moves. Use it to find your way only.

## Check

1. Every claim, number and offer line against the preset's exact lines and content rules. Anything
   invented (clients, results, reviews, counts, prices) fails.
2. Banned words and phrases, in the samples and in every caption.
3. Contrast on the settled frames: every word must stand out clearly from what is behind it. Dark text on a
   dark ground, or light on light, fails, whatever the design intended.
4. {{safe_check}}
5. One idea, a hook in the first 1 to 3 seconds, one call to action at the end.
6. Repeat: the same angle as an entry in `history.json` from the last {{no_repeat_days}} days. A different angle
   on the same pillar or topic is not a repeat. Record it in `repeat` only; it never changes a score.
7. Score each criterion from 1 to 10 against its anchors below. Scores between the anchors are fine. Take off
   points only for something you can point to in a sample, and name that sample.

{{anchors}}

## verdict.json

```json
{"pass": true, "scores": {{scores_example}},
 "repeat": {"found": false, "of": ""},
 "issues": ["settled-03.png (6.45 s): the specific problem"],
 "summary": "one sentence"}
```

`pass` is false if any rule in steps 1 to 3 is broken, if `repeat.found` is true, or if any score is below
{{min_score}}. Each issue starts with the sample file, or the caption, it is about. The runner checks this file:
a missing criterion, a score that is not a whole number from 1 to 10, or a malformed field means the review
did not happen.
