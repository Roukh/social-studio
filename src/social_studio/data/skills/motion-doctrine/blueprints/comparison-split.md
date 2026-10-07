<!-- Distilled by social-studio from heygen-com/hyperframes (tag v0.8.106, Apache-2.0),
     skills/hyperframes-animation/blueprints/comparison-split.md. See ../../NOTICE.md.
     Patched: rule-id citations replaced with self-contained build notes. No fade content to
     patch — the source already names its idle float "subtle jitter, NOT lazy breathing." -->

# comparison-split

**roles**: Key_Feature
**duration**: 4-6s

**intent**: Two paired items of equal weight, shown side-by-side with mirrored 3D "book-open"
tilts — the eye reads them as a balanced comparison — then a pill badge lands at each card's inner
edge to punctuate. The motion IS the symmetry: two cards arriving from opposite wings into a held
spread. Not for more than two items (use `grid-card-assemble`) and not for sequential steps.

**shot structure** (a bg carrying two faint ambient glow blooms, one per side, so each half owns a
color identity across the 50% symmetry axis)

- **Scene 1 (0.0-~0.8s) — title sets the concept.** A centered title line with an accent keyword
  slides DOWN into place from just above (a short smooth settle) — forming a T-shape against the
  cards, which arrive from the sides next.
- **Scene 2 (~0.4-1.9s) — the split-tilt entry (signature move).** Two equal-width cards arrive
  from opposite wings — left from the left, right from the right ~0.2s behind — each carrying a
  mirrored 3D `rotateY` tilt (left faces right, right faces left, opening like a book) and scaling
  ~0.85→1 as it lands. The entry overlaps the title's tail so the whole thing reads as ONE
  arrival. Box-shadows fall outward from the tilt.
- **Scene 3 (~1.9s-end) — badges punctuate, then hold.** A pill badge lands at each card's inner
  edge (left then right, ~0.3s apart), overlapping its card ~15% so it reads as attached. This is
  the lone overshoot in the shot — it earns the punctuation. Settles and holds.

**build notes**:
- The mirrored tilt is `rotationY: +tiltDeg` on the left card and `rotationY: -tiltDeg` on the
  right, both tweened from an off-stage x-position to 0 on the same duration/ease (`power3.out`)
  so they land in lockstep; shadows are a separate, lighter tween on the same position.
- The badge pop is the one place overshoot is earned — `back.out(≤2)` or `springEase` at
  `dampingFraction` 0.6-0.7 — because it is explicitly the punctuation beat, not the entrance.
- The post-settle idle is a phase-opposed, low-amplitude float: left card `sin(t)`, right card
  `sin(t + π)`, so the two never move in lockstep (which would read as a synchronized breathe) —
  bounded, finite over the hold, same register as SKILL.md §1 rule 3's sanctioned jitter.
