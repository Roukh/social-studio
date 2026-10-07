<!-- Distilled by social-studio from heygen-com/hyperframes (tag v0.8.106, Apache-2.0),
     skills/hyperframes-animation/blueprints/titlecard-reveal.md. See ../../NOTICE.md.
     Patched: led with the wipe-away-to-reveal mechanic (Social_Proof) rather than the source's
     "slide-up crossfade" (Benefits); the Benefits variant's fade-in entrance is changed to a
     scale-up-only settle, and its Scene-3 "slide-up crossfade" is changed to a slide-up swap
     (tl.set hand-off, no opacity cross-blend). "Subtle breathing" is kept but reframed as the
     doctrine's rare, bounded sanctioned-aliveness register, not a default. Rule-id citations
     replaced with self-contained build notes. -->

# titlecard-reveal

**roles**: Benefits, Social_Proof, CTA, Product_Intro
**duration**: 3-5s (card chains run 2-3s per card, ~5.5-9.5s total)

**intent**: The calm breather/landing beat — one clean title or single brand/proof card revealed
with exactly one restrained transform move, then a still hold. Low motion is the payload, not a
deficiency.

**shot structure**

- **Scene 1 (0.0-~0.4s)**: static camera on a neutral/dark background. Establish the opening
  state (Social_Proof: a busy intro frame of overlapping cards holds briefly).
- **Scene 2 (~0.4-~1.5s)**: the ONE move executes.
  - _Social_Proof (lead variant)_: a large rounded pill sweeps diagonally bottom-left → top-right
    and exits the corner, clip-path WIPING the busy collage away to reveal the brand logo lockup
    beneath as its icon strokes draw on.
  - _Benefits_: the line scales up into place (~95%→100%, smooth ease-out) and holds — a
    scale-only settle, not a fade.
- **Scene 3 (~1.5s-end)**: the revealed/settled card holds to the end. At most one subtle,
  bounded live element (a rare, low-amplitude jitter on the card, or a very slow camera drift) —
  use sparingly, never as a default. No second development phase.
  - _Benefits_: line 1 slides up and out as line 2 (a qualifier) slides up from below to take
    center — a slide-up hand-off (`tl.set`/short overlap on position only), not a cross-blend of
    opacity between the two.
  - _Social_Proof_: the lockup — icon centered, wordmark below, a social-proof tagline (its
    count may count up) — spring-settles small, then holds.

**card-chain variant** (CTA end-card stack / Product_Intro title prelude): the single-card
contract repeats 2-3 times. Each card is a complete Scene 1-3 in miniature — arrive (or simply be
there), at most one restrained move, hold — and the seams between cards are INSTANT hard cuts at
full opacity (never a crossfade or fade-through-black), or a blur-away → snap-into-focus handoff.
The final card is always the brand logo/lockup, held static to the last frame.

**build notes**:
- The diagonal pill-wipe is a `clip-path`/mask boundary swept across the frame on one tween
  (`power2.inOut`), revealing the lockup underneath — not two layers cross-fading.
- A slide-up hand-off between two lines is two position tweens (outgoing up-and-out, incoming
  up-and-in) timed back-to-back on the same axis; keep any opacity component as a fast helper at
  the very tail of each move, not spread across the whole transition.
- The card-chain's seam is a zero-duration `tl.set` cut at full opacity — deliberately no
  transition entry at all.
- The "subtle breathing" hold-element is this skill's sanctioned jitter (SKILL.md §1 rule 3):
  bounded, finite, low-amplitude, and optional — default to a fully static hold unless the beat
  would otherwise read as a dead freeze-frame.
