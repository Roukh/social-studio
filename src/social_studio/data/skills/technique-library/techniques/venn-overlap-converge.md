# venn-overlap-converge

**Family:** shape, morph. **Wants:** 2-3 s. **Source:** rneayan-474bcf (prompt-motion.com/rneayan-474bcf),
studied 2026-10-09.

## Looks

Two solid-coloured circles, each labelled with one half of a capability, slide together until they overlap.
The lens where they meet fills with a dense, noisy texture distinct from either parent colour, and a caption
names the overlap as the exact, deliberate fit — not an accident of two shapes crossing.

## Build

- Two DOM or SVG circles translate toward each other on `power2.inOut` until their overlap is a fixed fraction
  of their radius.
- The intersection is a clipped third layer (a `clip-path` intersection, or an SVG mask) filled with a seeded
  noise or stipple pattern instead of a flat alpha blend, so the meeting point reads as made, not just
  overlapped.
- The caption clips in under the pair once they settle.

## Sound

A soft converging whoosh as the circles close, a short grain-like rattle as the intersection texture resolves,
a tick on the caption.

## Adapting

Use for any "two things combine into one capability" claim: two skills, two technologies, two teams. The
parent colours should be the brand's own two accents.
