# physics-ray-diagram

**Family:** data, annotation. **Wants:** 3-8 s. **Source:** a shadow-play explainer studied from
x.com/LLMJunky/status/2106411941497389342, studied 2026-10-09.

## Looks

A silhouetted figure holds up a prop, a crystal, a lens, a prism, and a thin bright ray travels across the
frame to meet it, bending or splitting the instant it arrives. Small plain labels sit fixed in the corners
naming the two ideas in tension (for example "wave" and "particle"), and a tiny live graph or equation sits low
in the frame, drawing or updating in sync with the ray's behaviour.

## Build

- The ray is an SVG or canvas line with `strokeDashoffset` revealing it from source to prop, `power2.inOut`.
- The prop's effect on the ray (a bend, a split into two paths, a colour separation) triggers the instant the
  ray's reveal reaches it, not on a separate timer.
- The corner labels are static DOM text, low-contrast, present for the whole beat.
- The small graph (a sine curve, a bar, an equation) draws or fills in sync with the ray's own progress, same
  mechanic as `easing-graph-draw.md`, so the diagram and the demonstration are one timeline.

## Sound

A thin, rising tone as the ray travels, a soft chime the instant it meets the prop and bends or splits.

## Adapting

Use it for any explainer that needs to show a concept and its maths at once: a physics idea, a conversion
rate, a trade-off. Keep the labels to one or two words; the ray and the prop carry the demonstration.
