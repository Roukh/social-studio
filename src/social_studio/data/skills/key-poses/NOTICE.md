# Attribution

The `key-poses` skill and the board task (`data/board_prompt.md`) are **distilled and edited from** the
open-source **HyperFrames** project:

> https://github.com/heygen-com/hyperframes
> tag `v0.8.106`, licensed Apache-2.0.

A copy of the Apache License, Version 2.0 is in `LICENSE` in this directory, as required by §4 of that license.
This NOTICE file is informational and does not modify the License (Apache-2.0 §4(d)).

## Modifications

| This repository's file | Derived from (upstream path, tag `v0.8.106`) | What changed |
|---|---|---|
| `SKILL.md` opening | `skills/figma/SKILL.md` line 108 ("storyboard frames are KEYFRAMES, not slides") | Reworded for boards built as HTML in a session rather than read from a design file |
| `SKILL.md` "The order" | `skills/hyperframes/references/storyboard-format.md` (frame statuses `outline`, `built`, `animated`; `built` = layout confirmed, no motion) and `references/review-loop.md` (layout confirmed before motion) | Condensed; the board is every shot at the `built` rung at once, approved in a terminal instead of in chat |
| `SKILL.md` "The pose contract" | `skills/hyperframes-keyframes/SKILL.md` line 16 ("Keyframes are a pose contract") and its Contract list | Condensed and reworded for one static pose per shot; "different at a glance" added for the sheet |
| `SKILL.md` "What the operator sees", `data/board_prompt.md` | this repository's own sheet tiler (`boards.py`) | New text |

## No trademark or brand grant

Per Apache-2.0 §6, this NOTICE and the License grant no rights to any HyperFrames or heygen.com trade name,
trademark, or product name beyond identifying the origin above.
