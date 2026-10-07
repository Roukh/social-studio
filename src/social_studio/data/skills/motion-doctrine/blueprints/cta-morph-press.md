<!-- Distilled by social-studio from heygen-com/hyperframes (tag v0.8.106, Apache-2.0),
     skills/hyperframes-animation/blueprints/cta-morph-press.md. See ../../NOTICE.md.
     Patched: Scene 1's "faint rotational breath" is renamed and reframed explicitly as the
     doctrine's sanctioned bounded jitter (rotation-only, finite) rather than a scale-breathe
     loop, matching the source's own rule mapping ("subtle jitter, not a scale breath"). Rule-id
     citations replaced with self-contained build notes. -->

# cta-morph-press

**roles**: CTA, Hook
**duration**: 4-6s (Hook widget-morph opener 5-7.5s)

**intent**: A resting brand mark condenses at the same screen center into a smaller, brighter
CTA, then a cursor arrives from off-stage and lands a human-aimed click on it. The viewer's eye is
walked from "this is who we are" to "and this is what you do." The morph and the click are the
two headline beats. Reach for it for a focused "click here" sign-off — no spatial set, no
multi-step UI.

**shot structure** (a bg canvas; hero and CTA are flex-centered siblings sharing one
`transform-origin`)

- **Scene 1 (0.0-~1.4s) — presence.** The hero mark/brand lockup holds dead-center, resting —
  at most a bounded, low-amplitude ROTATION-ONLY jitter on the mark (the doctrine's sanctioned
  aliveness, never a scale breathe); any title text beneath it stays rock-stable. Camera static.
- **Scene 2 (~1.4-2.4s) — the morph (signature move).** The hero CONDENSES at the same screen
  center into a smaller, brighter CTA: the outgoing mark shrinks (with opacity riding along as a
  helper, not the lead) exactly as the CTA scales up in its place. Because they share one
  `transform-origin`, the eye reads it as one element transforming, not a swap.
- **Scene 3 (~2.4-3.4s) — approach.** A cursor arrives from off-stage on a decelerating path (it
  "arrives," it doesn't pass through) and lands a few px off the CTA's geometric center, so the
  aim reads human.
- **Scene 4 (~3.4-end) — press.** The cursor lands a physical click — cursor and CTA compress
  together in lockstep, then release with feedback (an optional ripple/glow bloom). Holds on the
  clicked state.

**variant — Hook (widget-morph opener)**: reorders the beats — a lone pill/chip sits centered on
a flat field; the cursor glides in and clicks it; the widget transforms IN PLACE (expands
downward into a menu, or spring-morphs outward into a card); the transformed state performs
(types a placeholder, flips a control's color); then it VANISHES and a typed closing title
resolves the frame.

**build notes**:
- The condense-morph is a shared-center scale tween: outgoing mark `scale 1→0.4` while incoming
  CTA `scale 0.4→1` at the identical `transform-origin`, same duration, so neither ever appears to
  "pop" independently; split a light opacity tween onto the outgoing element only if the shrink
  alone doesn't read clean at small sizes.
- The resting-mark jitter is rotation-only, bounded to a few degrees, finite over the hold
  (derived from a fixed-duration sine, not `repeat: -1`) — kept deliberately separate from the
  Scene-2 scale tween so the two never fight on the same property.
- The press is a single-target-array compression: cursor and CTA scale down together on contact,
  then both release on `power2.out` with an optional expanding-ring ripple at the contact point.
- The approach path is `power2.out` on position only — no overshoot on a cursor move, overshoot is
  reserved for the press release.
