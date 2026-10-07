<!-- Distilled by social-studio from heygen-com/hyperframes (tag v0.8.106, Apache-2.0),
     skills/hyperframes-animation/blueprints/typewriter-reveal.md. See ../../NOTICE.md.
     Patched: rule-id citations to hyperframes-animation/rules/ replaced with self-contained
     build notes (that skill isn't mounted here). Motion itself needed no fade patching. -->

# typewriter-reveal

**roles**: Hook, Brand_Outro
**duration**: 3.6-7s (Brand_Outro 3.6-6.0s, Hook 5.5-7s)

**intent**: A live text caret types (and edits) a line as a human would, then either collapses it
to a point and pops a brand payoff, or holds it under a persistent brand mark while a sub-line
types/swaps into the final CTA. "Someone is typing this" is the engine of the shot.

**shot structure**

- **Scene 1 (0.0-~2.0s)**: On a solid `[bg color]` field, a blinking caret sits at the line
  start, then the primary line TYPES on character-by-character with the caret trailing.
  - _Hook_: nothing else on screen; the typed line owns the frame.
  - _Brand_Outro_: a logo mark (+ optional wordmark) is already centered/upper and stays visible
    for the whole shot; an entry flourish plays on the mark itself (an icon stroke-draws on, or
    thin concentric rings ripple outward from it) while the typed tagline is a sub-line beneath.
- **Scene 2 (~2.0-4.5s)**: The typed line is MODIFIED in place, not re-shot.
  - _Hook_: the final word(s) backspace out and a new word retypes.
  - _Brand_Outro_: the sub-line is removed by a direct hard cut/replace (no backspace) or a
    moving mask-wipe, while the mark performs a small bounded idle move (a low-amplitude rotate
    or sparkle reposition — jitter, not a scale breathe).
- **Scene 3 — resolve**:
  - _Hook_: the caret vanishes; the whole typed assembly COLLAPSES to a point at center (an
    x-collapse or scale-to-0) and disappears onto a clean bg. A centered brand element then
    SPRING-POPS in — a mark pops and a wordmark slides out from behind it into a lockup, or a UI
    control pops and a cursor sweeps in to land a click with a state-flip + glow bloom.
  - _Brand_Outro_: the final CTA resolves in the sub-line slot — typed in with a caret, or shown
    as an accent-color button beside plain text — with an optional glow ring settling around the
    persistent mark. Holds to end.

**build notes**:
- The caret is a blinking rect/pipe on a finite, deterministic blink cadence (derive the on/off
  from `tl.time()`, never a CSS `animation`).
- Type-on is a per-character reveal (`clip-path` growing or a per-character `autoAlpha` stepped at
  tiny, even time increments) driven by the timeline, not `setInterval`.
- The collapse-then-pop in Scene 3 is a same-center morph: the typed line scales/clips toward the
  caret position while the incoming brand element scales up from that same point — one
  `transform-origin`, so it reads as one transformation, not two unrelated moves.
- The idle move on a persistent mark (Scene 2, Brand_Outro) must stay bounded and finite — a few
  degrees of rotation or a few px of reposition, never a loop.
