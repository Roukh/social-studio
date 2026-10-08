# dual-voice-type

**Family:** type. **Wants:** 1.5-2.5 s per note. **Source:** Framer's "skills" ad
(instagram.com/p/DdtwW_Ws0Xx), studied 2026-10-07.

## Looks

Two kinds of words, in two faces that never mix:

- a human note (a request, an aside, a label), typed in a marker or handwritten face with a blinking cursor;
- the product's or the film's own voice, in the brand's clean sans.

The difference in face tells the viewer who is speaking.

## Build

- DOM text revealed per character at a steady typing rate (`kit.typeOn`).
- Load the second face only for the note layer. Without a handwritten face in the preset, use the brand's
  italic or serif for the note, and its sans for the rest.
- The cursor blinks on the beat, not on a timer.

## Sound

A light typing clack per character, softer than the ticks under kinetic words.

## Adapting

The note voice suits a prompt, a request, a question or the founder's voice. The brand voice is for the answer.
