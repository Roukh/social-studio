# karaoke-caption-sync

**Family:** type. **Wants:** the whole shot. **Source:** a Matra captions-app promo in prompt-motion.com's
gallery (prompt-motion.com/gautam-mer1-2ae354), studied 2026-10-09.

## Looks

Over real talking-head footage, a line of captions sits low in the frame. As the speaker says each word, that
word gets a highlight box or colour fill exactly on the syllable, while the words before it stay in the base
caption colour and the words after it are not yet visible (or sit dim, word-by-word reveal rather than
line-by-line). The highlight travels word to word in lockstep with the audio, never ahead or behind.

## Build

- One DOM line of word spans, each with a start and end time from a transcript (real or seeded).
- `renderCaptions(t)` walks the words and sets each one's class to past / active / future based on `t`; the
  active word gets a background fill or box that scales in (0.9->1, 0.08s) exactly at its start time, driven
  by the master clock, not a separate tween per word.
- No easing on the switch itself (a caption that eases late reads as laggy); the only motion is the small
  scale-pop on the active word's arrival.

## Sound

The real or simulated speech audio is the timing source; a very light tick on each word can reinforce it in a
silent preview.

## Adapting

Use it for any product that transcribes, dubs or captions speech. The words and their timings should look like
a real utterance, not a generic placeholder sentence.
