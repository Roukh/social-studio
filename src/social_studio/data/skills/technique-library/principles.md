# Principles for every video

These apply to every film, whatever the brand or the techniques. They come from the reference films the
operator chose and from the operator's calls on what was made. `skills/motion-canon` holds the numbers behind
them (timing, easing, staggers, sync). References: the 2026 Opus showreels (studied 2026-10-06), and on
2026-10-07 Himanshu's principles reel, Framer's "skills" ad, the prompt-motion.com gallery and an
explainer-film prompt shared by @0xMovez.

## Ambition

- **Make a film, not a slideshow.** Every shot shows something only motion can show. A screen of text that
  fades in is not a shot.
- **Range.** Every film has at least one shot that only code can do (3D, particles, a generative field, a
  morph) and moves through several families: physics, type, 3D, data, interface, shape.
- **Spend effort on every frame.** Each shot has foreground, midground and background, texture, and a HUD
  or detail layer where it fits. Even a calm, near-still hold carries two or three thin atmosphere layers
  (drifting motes, a grade, grain, one flare); it is never an empty frame.
- **A short brief is no ceiling.** Quality comes from the structure and the rounds of looking and fixing,
  not from the length of the request. Treat a one-line brief as permission to go all out.
- **Show the thing itself.** When the film is about what something does (a capability, a service, a
  process), the shot's subject is that thing happening, labelled, not an unrelated scene that only looks
  impressive.
- **Match the genre.** A showreel spends technique freely. An explainer uses each technique where it
  explains, and drops spectacle that does not (such as stock 3D blobs, floating particles or neon glow with
  no reason).
- **A brand gives colours and fonts.** Use them fully. The rest of the look is the film's own.

## Rhythm

- Plan on a beat grid (about 120 BPM: a beat is 0.5 s). A new idea every five beats or so (about 2.5 s). The
  operator found 15 s at 143 BPM "a little too fast" and 20 to 25 s right (2026-10-06).
- Every shot lands, settles and holds before it leaves. Something always moves, but the eye always gets a
  landing spot.
- Cuts and wipes land on beats, and the big ones land on downbeats.
- Time follows the content when it must:
  - a shot that is visibly still building (a curve drawing, a dial counting up) may hold 2-3 s past the grid;
  - a text-heavy shot holds for its reading time, about 0.5 s plus 0.25 s per word, and 3-7 s for a short
    paragraph.
- A rapid word montage (one word per hard cut, every 0.4-0.5 s) is one scene with its own inner beat grid,
  not several scenes. The last word holds longer.

## Camera and space

- One camera move at a time: a push, a pan or a whip, never combined, and each one settles before the next
  begins.
- Flat interface content sits on a shallow 3D tilt (8-15 degrees on two axes), not flat to the lens
  (see `techniques/ui-tilt-card.md`).
- To show scale or volume, fan three or four near-identical panels in one shot, rather than cutting between
  single variants (see `techniques/variant-stack-reveal.md`).

## Colour and type

- The palette can rotate as full-bleed fields. A restrained alternative, two neutrals and one accent with a
  second colour kept only for annotation ink, is equally valid. Choose one per film.
- One glow accent marks only what is live, the element the action is on, never decoration
  (see `techniques/provenance-glow-stroke.md`).
- Two layers of meaning get two faces: a human note in a handwritten or italic face, and the film's or the
  product's own voice in the brand's sans. One face never does both jobs (see `techniques/dual-voice-type.md`).
- A flat card on a field of the same colour gets a 1 px hairline edge, so it never disappears.

## Continuity

- One through-line carries the film (see `techniques/through-line.md`). The mark that ends one scene starts
  the next, and it changes meaning at each stop (a dot becomes a node, a label becomes an axis).
- Transitions are spatial (wipes, floods, morphs, a dot growing into the next ground). There are no
  crossfades.

## Motion quality

- Springs or `power3`/`expo` eases; linear only for continuous drift. Fast moves get motion blur. Overlap
  the moves, and vary staggers by 10-30 %.
- Anything drawn on canvas or in 3D is a pure function of time (see `techniques/master-clock.md`), seeded,
  never `Math.random`. Prove it: the same time rendered twice gives the same frame.

## Sound

- A synthesized bed plus effects (`tools/sound.mjs`), cued from the shot list: a hit on every landing, a
  whoosh into every wipe, ticks under type, blips under data and interface, a riser into the big moments, and
  a fade over the last 1.5 s.
- Mix to the house loudness, -14 LUFS integrated for social (the quality gate checks ±1), with true peaks at or
  below -1.5 dBTP. A web explainer would sit nearer -16 LUFS.

## Words

- Few and earned: a title, one-word beats, labels and numbers as texture, and the end card's lines. At most two
  lines of text on screen at once. Words anchor what the picture shows; they never transcribe a voice or
  narrate it.
- When a shot shows a mechanism, label it in the frame, on the beat, in the note face, pointing at the thing
  itself (see `techniques/annotated-diagram-overlay.md`).
- Every number, chart, interface and client in a shot is a labelled fictional sample unless the brief gives
  a real one.

## Check before done

- Look three ways: a still at every beat read at phone width, the whole film watched muted, and its sound
  heard alone. Fix what fails, and look at the frame again after each fix.
- Accessibility: text and the ground under it reach a contrast of 4.5:1 or more, colour is never the only
  signal, and nothing flashes more than three times a second. With a voice, the words are burned in as
  captions.

## Growing the library

- A new technique entry ends with its gotchas when they are known: the real ways it failed while rendering.
