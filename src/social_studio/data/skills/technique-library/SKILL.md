---
name: technique-library
description: The library of proven motion-graphics techniques and shots every video draws from, plus the principles every video applies. Read it before writing brief.json; pick the set of techniques and shots for this film from it, and record the set in video.json.
---

# Technique library

Every film is built from techniques: a 3D voxel field, a particle flow, a kinetic word run, a morph, a wipe.
This library holds the ones that have proven themselves on screen. Each entry gives what it looks like, how
long it wants, how it was built, and where its working code is. They were grown from reference films the
operator chose, and more are added as new references arrive.

A brand gives a film its colours and fonts. Everything else (the shots, the techniques, the motion, the
layout) comes from here and from your own direction, and is yours to push as far as the film can take.

## How to use it

1. Read `principles.md`. It applies to every video.
2. Find the candidates. With a story (`story.json`), `techniques.json` already lists, for each beat, the
   techniques and reference scenes the store ranked best for it, with why and a general prompt: start there. The
   store holds every entry and every scene: `python3 tools/store.py --db store.db search "text" --tag role=hook`
   searches it, `... search --kind technique -n 100` lists every technique, `... show ID` prints one item. Each
   technique's full recipe is `techniques/<id>.md` in this skill.
3. Pick the set: for a 20 to 25 s film, usually six to nine shot techniques, plus the transitions and texture
   that tie them together. Choose for the idea and for range: no two neighbouring shots from the same family, and
   at least one shot that only code can do (3D, particles, generative). `history.json` lists the sets used
   recently. Do not reuse the same set; a technique may come back with a new treatment.
4. Adapt each technique to this film: the brand's colours and fonts, this format (a 9:16 frame stacks
   vertically what a 16:9 frame spreads sideways), this message. An entry is a recipe and a scene's prompt is a
   direction, not a script: never copy another film's words or rebuild its frames.
5. Invent when the film needs it. A shot of your own is welcome. Name it in `brief.json` and add it to
   `techniques` in `video.json` under a new slug; good ones become entries.
6. Record it. Each shot in `brief.json` names its technique by slug (a scene's techniques, not the scene).
   `video.json` carries `"techniques": [slugs]` for the set the film uses.

## The store

Two kinds of items, tagged by story role, purpose, content, energy, format, family and complexity:

- A **technique** is one atomic move (a wipe, a voxel field, a word run). Its recipe here says what it looks
  like, how long it wants, how to build it in this stack, the sound under it and its source.
- A **scene** is one shot of a reference film, studied frame by frame: what it looks like, how it is built, the
  techniques it combines, and a general prompt that builds something in its spirit for any brand.

## The worked example

`examples/reel-2026-10-06.html` is the composition of the first film built this way (a 15 s, 16:9 showreel
judged "a major improvement" by the operator on 2026-10-06). It uses fourteen techniques, from dot-drop-flood to
master-clock; each of those recipes points to its section there: search for the `<!-- S1 · ...` markup comment or
the `// ===== S1 · ...` code comment. The other recipes have no worked example yet. It
reads `assets/reel-kit.js` as `window.reel`; in your composition the same helpers are `window.kit` (also
`window.reel`), from `assets/motion-kit.js`.

## Growing the library

A reference film the operator shares is split into scenes and studied shot by shot; each scene becomes a store
item with its tags and general prompt, and a move no technique covers yet becomes a new technique with a recipe
here. A technique the operator rejects is removed, not kept as a warning.
