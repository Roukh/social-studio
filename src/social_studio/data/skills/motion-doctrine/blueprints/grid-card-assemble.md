<!-- Distilled by social-studio from heygen-com/hyperframes (tag v0.8.106, Apache-2.0),
     skills/hyperframes-animation/blueprints/grid-card-assemble.md. See ../../NOTICE.md.
     Patched: Scene 1's "fades + slides/scales" entrance drops the fade — items slide/scale into
     their slot, opacity rides along at most as a helper. Rule-id citations replaced with
     self-contained build notes. -->

# grid-card-assemble

**roles**: Key_Feature, Benefits, Social_Proof
**duration**: 3.0-10.5s

**intent**: N items (tiles, cards, logos, list lines) self-assemble in a staggered cascade into a
grid or vertical list and hold — a "look how much/who/what it does" beat that enumerates breadth
at once; an optional camera zoom-out pulls back to reveal the assembled array inside a vaster
whole.

**shot structure**

- **Scene 1 (0.0-~1.0s) — open + first arrivals.** On a gradient/dark background, an empty
  grid/list region is established and items begin to ASSEMBLE in a quick staggered cascade
  (~0.04-0.08s gap; list pacing ~1 item/sec). Each item slides/scales a short distance directly
  into its slot — low drama, no scatter, no big bounce (overshoot is reserved for accent markers
  only). Camera static. An opening headline may fill in line-by-line above the array.
- **Scene 2 (~1.0s-~Xs) — array resolves + holds.** Remaining items finish arriving; layout
  resolves into its final grid/list. The completed array HOLDS, alive but resting — at most a
  gentle, finite parallax/float on the tiles and/or a slow camera push-in. An accent glow may
  travel across/behind the tiles once.
- **Scene 3 (~Xs-end) — settle / reveal / exit.** Everything settles and holds, OR a camera
  zoom-out reveal runs (below), OR the field clears to concise payoff copy (a price, a URL) via a
  wipe/slide, never a crossfade.

**variants**: a Key_Feature grid holds near-static with a slow push-in; a Social_Proof logo wall
builds then a continuous camera zoom-out shrinks it to reveal a vast ecosystem; a Benefits
vertical list either builds and stays lit, snaps up one slot per beat (slot-machine), or streams
continuously past a fixed focal slot and decelerates to a stop; a live-data variant populates
itself (skeleton pills fill left→right, cards spring in tethered to markers) and keeps flipping
state after assembly.

**build notes**:
- The stagger-assemble is a per-item slide/scale tween (`power3.out`, index-derived stagger delay)
  into each item's pre-computed slot position — never opacity alone; if opacity helps a fast
  arrival read cleanly, split it onto its own tween at the same position.
- The zoom-out reveal (Social_Proof / Key_Feature glass-card variant) is a single `cam.scale`
  tween on one `.world` wrapper around the whole array, matching SKILL.md §1's "no zoom-in, camera
  static outside the one move" discipline once it starts.
- A clear-to-payoff exit (price, URL) is a wipe (`clip-path`/`inset()` revealing left→right) or a
  slide, not a crossfade between the array and the payoff line.
- The slot-machine step (Benefits) is a masked column stepping to the next value on a discrete
  `tl.set`/short tween, not a continuous scroll.
