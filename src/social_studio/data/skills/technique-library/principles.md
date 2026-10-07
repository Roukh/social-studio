# Principles for every video

These apply to every film, whatever the brand or the techniques. They come from the reference films the
operator chose and from the operator's calls on what was made. `skills/motion-canon` holds the numbers behind
them (timing, easing, staggers, sync).

## Ambition

- **Make a film, not a slideshow.** Every shot shows something only motion can show. A screen of text that
  fades in is not a shot.
- **Range.** Every film has at least one shot that only code can do (3D, particles, a generative field, a
  morph) and moves through several families: physics, type, 3D, data, interface, shape.
- **Spend effort on every frame.** Each shot has foreground, midground and background, texture, and a HUD
  or detail layer where it fits. A flat field with one element on it is the exception, and it is held on
  purpose.
- **A brand gives colours and fonts.** Use them fully: the palette's colours rotate as full-bleed fields, and
  the fonts carry the type in every weight they have. The rest of the look is the film's own.

## Rhythm

- Plan on a beat grid (about 120 BPM: a beat is 0.5 s). A new idea every five beats or so (about 2.5 s). The
  operator found 15 s at 143 BPM "a little too fast" and 20 to 25 s right (2026-10-06).
- Every shot lands, settles and holds before it leaves. Something always moves, but the eye always gets a
  landing spot.
- Cuts and wipes land on beats, and the big ones land on downbeats. Kinetic words take one beat each, with a
  longer hold on the last.

## Continuity

- One through-line carries the film (see `techniques/through-line.md`): the mark that ends one scene starts
  the next.
- Transitions are spatial (wipes, floods, morphs, a dot growing into the next ground). There are no
  crossfades.

## Motion quality

- Springs or `power3`/`expo` eases; linear only for continuous drift. Fast moves get motion blur. Overlap
  the moves, and vary staggers by 10-30 %.
- Anything drawn on canvas or in 3D is a pure function of time (see `techniques/master-clock.md`), seeded,
  never `Math.random`.

## Sound

- A synthesized bed plus effects (`tools/sound.mjs`), cued from the shot list: a hit on every landing, a
  whoosh into every wipe, ticks under type, blips under data and interface, a riser into the big moments, and
  a fade over the last 1.5 s.

## Words

- Few and earned: a title, one-word beats, labels and numbers as texture, and the end card's lines. A sentence
  on screen holds long enough to read: about 0.5 s plus 0.25 s per word.
- Every number, chart, interface and client in a shot is a labelled fictional sample unless the brief gives
  a real one.
