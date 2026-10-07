<!-- Distilled by social-studio from heygen-com/hyperframes (tag v0.8.106, Apache-2.0),
     skills/hyperframes-animation/blueprints/fixed-anchor-cycle.md. See ../../NOTICE.md.
     Patched: Scene 1's anchor entrance drops the "fade/scale-in" option, keeping word-by-word
     build or already-present-at-frame-one. The sub-shape B whole-context crossfade is kept
     (it is a deliberate discrete state-swap between skins around a fixed anchor, not an
     opacity-led arrival — SKILL.md §1 rule 8 allows a crossfade for a genuine replacement).
     Rule-id citations replaced with self-contained build notes. -->

# fixed-anchor-cycle

**roles**: Hook, Benefits, Brand_Outro
**duration**: 6.6-11.1s (the cycle engine itself occupies ~3-5s regardless of role)

**intent**: One element is PINNED — a wordmark, a composer box, an anchor line — enters once and
never moves again, while the region around it (or the whole surrounding theme) cycles through
many discrete states, resolving on an emphasis beat into a completed lockup. The stillness of the
anchor IS the claim: everything changes, this stays.

**shot structure** (flat static frame, camera locked throughout; two sub-shapes — **(A)
adjacent-region cycle**: a neighboring slot swaps through N states; **(B) whole-context morph**:
everything around the anchor re-skins in place)

- **Scene 1 (0.0-~2.0s) — the anchor lands and PINS.** The anchor enters once — a scale-in
  settle, a word-by-word build, or is already present at frame one — at a fixed position it holds
  for the entire clip. Zero movement from here on: no drift, no breathe, no re-layout.
- **Scene 2 (~2.0s-~70% of runtime) — the cycle engine (signature move).**
  - **Sub-shape A**: a region beside/beneath the anchor steps through N discrete states — an
    instant hard-cut label replacement, a sequential per-word highlight step, or a fast vertical
    carousel — at a steady cadence or a slow→accelerating flurry. The cycling region never
    overlaps or displaces the anchor.
  - **Sub-shape B**: at ~1.3s intervals the entire theme (background, typography, radii, chrome,
    logos) morphs in place via a quick (~0.3s) crossfade through N skins, every property blending
    simultaneously — this is a genuine state replacement between fully different themes, not an
    entrance, so a crossfade is the correct tool here. The anchor's own content string is
    identical in every skin.
- **Scene 3 (~70-85%) — the emphasis beat.** The cycle resolves, it does not just stop: a
  highlight walk snaps the whole line solid bright at once, a flurry halts and holds on the
  longest/weightiest phrase, or (theme morph) the final beat mutes to a washed-out freeze.
- **Scene 4 (final beat → end) — lockup completion and HOLD.** A final element joins the
  still-unmoved anchor (a closing word drops in, a sign-off appears on a shared baseline) and the
  finished composition holds static to the end — give the lockup 20-30% of the runtime.

**build notes**:
- The anchor's one entrance is a scale/position settle (`power3.out`) or a word-by-word build —
  never a bare fade-in.
- Sub-shape A's swap mechanics are all `tl.set()` state changes at time thresholds (hard-cut
  label replacement) or short masked-column tweens (the carousel) — never a crossfade.
- Sub-shape B's theme crossfade is N pre-styled full-scene layers stacked at the same geometry,
  opacity-crossfaded between them, with the shared anchor string rendered once on top so it never
  itself fades.
- No camera move anywhere in this blueprint — the pinned anchor's stillness is load-bearing; a
  push-in "for energy" breaks the contract.
