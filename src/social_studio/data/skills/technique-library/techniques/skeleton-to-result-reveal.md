# skeleton-to-result-reveal

**Family:** interface, reveal. **Wants:** 1.5-2.5 s. **Source:** prompt-motion.com's gallery
(justincooperman-e7bbc4), studied 2026-10-09.

## Looks

A chat input receives a typed request, then a soft, blank placeholder block appears in its exact place in the
layout where a result will land, with a small "working on it" spinner or pulse. The placeholder resolves in
place into the finished asset (an image, a chart, a block of text), cross-fading within the placeholder's own
bounds rather than popping in elsewhere, so the generation feels like it happens exactly where it will live.

## Build

- The placeholder is a flat rounded rect, a few percent lighter or darker than its ground, with a slow opacity
  pulse (`0.85 <-> 1`, ~1.2s cycle) standing in for "working."
  its final asset is pre-sized to the same bounding box so no layout shift happens on the swap.
- The result cross-fades in over the placeholder (`opacity 0 -> 1`, 300-500ms, power1.out) at the same bounds;
  the placeholder fades out in the same window rather than being replaced by a hard cut.
- Optionally hold a thin progress underline or spinner in a fixed corner of the placeholder until ~80% through
  the resolve, then let it fade a touch before the result fully settles.

## Sound

A soft, low pulse under the "working" hold, a brighter chime exactly as the result resolves in.

## Adapting

Use for any agent/AI flow where a request becomes a placed asset: an image, a generated email, a drafted reply.
Keep the placeholder's bounds identical to the result's bounds so nothing reflows.
