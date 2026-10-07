# Critique checklist

Run this pass after every beat is first-drafted and again after the whole piece is assembled. Read the sampler's strips first. A strip is one move, frame by frame: slow motion on paper. Cheap motion shows most there, because every ease, timing and stagger choice (or the lack of one) is exposed.

## Frame-freeze test

Pause on 3 random frames per beat (not the designed key poses — genuinely random mid-motion frames). For each frozen frame, ask:

1. Does this frame, alone, still look intentional (readable composition, clear focal point) or does it look like an accident of interpolation?
2. Is there visible hierarchy — one clear primary element, with everything else clearly secondary — or does everything compete for attention equally?
3. If this is a hold-frame (not mid-motion), would it work as a still screenshot/thumbnail on its own?

## Per-element easing audit

List every animated element in the beat and its ease curve. If more than ~60% of elements in a single beat share the exact same ease string, that's a signal the ease was set once and copy-pasted rather than chosen per element. Cross-check against `references/easing-and-timing.md`'s intent table — does each element's ease match *why* it's moving?

## Timing-variation audit

List every element's duration. If most durations in a beat are identical, check whether that's motivated (e.g. a synchronized grid reveal, which *should* share timing) or accidental (unrelated elements that happen to all be set to the same default duration).

## The 15 cheap-motion tells (hunt explicitly)

1. Uniform linear easing on everything, regardless of motion type.
2. Identical duration across unrelated elements.
3. "Fade" as the only transition verb anywhere in the piece.
4. Subject centered on a gradient background with no off-center staging or depth separation.
5. Particle system/glow present but not motivated by the content.
6. Grain/vignette/chromatic aberration applied uniformly and statically rather than at a motivated moment.
7. HUD/counter elements that ease instead of snapping on data-update frames.
8. Every kinetic-type word held for the same duration regardless of length/importance.
9. Cuts landing on literally every beat with zero variation in hold length.
10. No anticipation before any major action (everything just starts moving).
11. No follow-through/overlapping action (parent and children stop simultaneously, every time).
12. Camera or 3D elements with flat, shadowless lighting.
13. Sound cues consistently early/late relative to their visual frame (outside ±1-2 frame tolerance).
14. A riser that cuts off before its payoff hit instead of resolving into it.
15. Bloom/glow/blur applied globally rather than reserved for a climax moment.

## Sign-off questions

- If I described this beat's idea in one sentence to someone who can't see it, would the finished beat actually communicate that sentence, or just "look cool"?
- Is there exactly one thing this beat is teaching/showing the viewer, or has a second idea crept in?
- Would removing this beat's biggest visual flourish (the particle system, the glow, the overshoot) make it *less* clear, or just less decorated? If just less decorated, the flourish may be covering for a weak idea rather than serving a strong one.
