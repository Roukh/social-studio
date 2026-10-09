# node-graph-build

**Family:** data, structure. **Wants:** 3-6 s. **Source:** prompt-motion.com's gallery (techyoutbe-945b56),
studied 2026-10-09.

## Looks

Small labelled boxes connect one at a time: a line draws from an existing node out to a new one, the new
node's box fades and scales in the instant the line lands, and the next connection starts right away, so a
system or flow diagram builds itself edge by edge until the whole graph sits connected and legible at once.

## Build

- Nodes sit at fixed layout coordinates from a precomputed tree or graph layout (do not force-direct it live;
  the shot needs a stable, readable result).
- Each edge is an SVG or canvas path stroked on with `strokeDashoffset`, `power2.out`.
- The target node's box fades/scales in (`0.9 -> 1`) the instant its incoming edge's dashoffset reaches 0.
- Animate one edge at a time in a seeded order, not all branches at once, so the eye can follow the build.

## Sound

A soft tick per edge connecting, a slightly brighter tick when a node lands.

## Adapting

Use it for a system architecture diagram, a user flow, an org chart, or any process map, anything that reads
as boxes and the lines between them. Keep the finished graph on screen at least 0.8 s before cutting away.

## Variants

The same move, as other reference films staged it:

- **node map reveal** (prompt-motion.com's gallery (prasad-pilla-2c0cba), studied 2026-10-09.): A small schematic of a system draws in at once: a handful of labelled nodes (words in boxes, no icons) arranged around a centre (a hub-and-spoke) or around a ring (a cycle), thin lines connecting them to the middle or to each other. It reads as "here is the whole system" in one glance, often alongside a plainer companion panel (a list, a before/after row) that builds in step with it.
- **hub spoke integrations** (prompt-motion.com's gallery (melvynx-6cde6c), studied 2026-10-09.): A single product icon sits at the centre of the frame; curved lines reach out to a ring of partner or tool icons arriving one at a time around it, each line drawing on as its icon lands. A small capability tagline (tool count, protocol names) settles beneath once the ring completes, naming the scale the diagram just showed.
