# slider-scrub-preview

**Family:** interface, data. **Wants:** 2-3 s. **Source:** prompt-motion.com's gallery (rossaxbt-3085b7),
studied 2026-10-09.

## Looks

A small floating control panel holds two or three labelled sliders. Each handle glides along its track and its
percentage ticks up in turn, and right beside the panel a live preview (a photo, a swatch, a UI sample)
visibly changes in sync with the value, a colour shift, a style intensity, a filter strength, so the parameter
and its visible result read as one cause and effect, not two separate things.

## Build

- Each slider is a DOM track and handle; the handle's `x` and the percentage text are driven off the same clock
  value, `power2.inOut`, same pattern as `responsive-breakpoint-scrub.md`'s ruler.
- The preview's look (a CSS filter stack, a crossfade between two graded copies of the same image, or a
  gradient-duotone overlay's opacity) keys off that identical value, so it never lags or leads the handle.
- Animate one slider at a time; let its result settle before the next slider starts.

## Sound

A soft tick per slider step and a light shimmer as the preview resolves on each stop.

## Adapting

Use it for any tunable parameter a product exposes: style strength, creativity, speed, quality. The preview
must be a real, legible change, not a generic cross-dissolve.
