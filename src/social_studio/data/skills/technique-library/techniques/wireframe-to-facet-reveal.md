# wireframe-to-facet-reveal

**Family:** identity, 3d. **Wants:** 5-15 s. **Source:** prompt-motion.com's gallery (tdinh-me-815acb),
studied 2026-10-09.

## Looks

A skeletal wireframe, dots joined by thin lines, grows node by node in the dark until it traces the full
silhouette of the mark, a low-poly mesh. Its triangular faces then fill in one by one with flat colour panels,
in an uneven order, turning the skeleton solid and faceted, like cut glass, until every face is lit and the
mark reads whole.

## Build

- Precompute the mark's low-poly mesh (vertices and triangular faces) once, offline or on load.
- Edges draw with `strokeDashoffset`, in a seeded order, each with a small delay so the mesh grows as a
  network rather than all at once.
- Each face is a separate filled path that fades/scales in from 0 opacity the instant its three vertices are
  connected, with a seeded per-face stagger so the fill reads organic, not row by row.
- Hold on the completed, fully-faceted mark for at least 0.5 s before the next beat.

## Sound

A faint high shimmer per node connecting, a soft glassy tick per face landing, building to a held chord on
completion.

## Adapting

Use it for a tech or AI brand's mark opening a film. Take the facet colours from the brand's palette, not a
generic rainbow. Works for any mark with a recognisable silhouette; a text-only wordmark suits
`wordmark-assemble.md` or `noise-dissolve-logomark.md` better.
