<!-- Distilled by social-studio from heygen-com/hyperframes (tag v0.8.106, Apache-2.0),
     skills/hyperframes-animation/blueprints/logo-assemble-lockup.md. See ../../NOTICE.md.
     Patched hard: of the source's 9 role variants, only the three most transform-led are kept
     (CTA push-through, CTA button-build wipe, Brand_Outro stroke-draw assemble). Dropped: the
     Product_Intro ring-pulse variant (built on a background light/dark crossfade), the
     "text-clears-mark-blooms" CTA variant (its lead move is word-by-word staggered fade), and
     the "settled-lockup-reveal" Brand_Outro variant (satellites fade out) — all three would have
     needed the heaviest rewrites for the least doctrine-aligned payoff. Rule-id citations
     replaced with self-contained build notes. -->

# logo-assemble-lockup

**roles**: Product_Intro, CTA, Brand_Outro
**duration**: ~4.4-11.0s

**intent**: A brand mark/wordmark comes to exist on screen and resolves into a centered lockup —
built from parts, drawn on stroke-by-stroke, or arrived at through a camera push — optionally
extended into a final URL/CTA/end card.

**variant — CTA push-through (the signature)**: on a bg gradient, a 3D mark is settling in
object space (thin wireframe edge-guides, a faint bracket motif behind center) while a very slow
camera push-in creeps underneath. The wordmark CASCADES out from behind the mark (letters
left→right with a bounded overshoot) into the full lockup; the mark may assemble in beats (a
part hinges open and snaps shut). Then the signature move: a single fast CAMERA PUSH-THROUGH the
mark's negative space, heavy horizontal motion-blur, resolving on the final lockup on a saturated
bg — a URL/CTA line revealed by a left→right WIPE with an accent leading edge, solid shapes
parallax-sliding in behind. Settles to a dead-static hold.

**variant — CTA button-build (wipe)**: on a dark grid bg, a rounded CTA-button pill rises/scales
into center; its thin border DRAWS ON as an animated glowing outline stroke. A graphic WIPE flips
the frame — a thin diagonal line sweeps in, swells into a full-frame diagonal band, then collapses
to a small accent slash. The wordmark BUILDS letter-by-letter to the right of the slash, landing
on the final lockup. Slow settle to static.

**variant — Brand_Outro stroke-draw assemble**: a pre-arranged formation of feature pills/element
grid DISPERSES — elements slide outward from their laid-out positions and fly off all four frame
edges (an edge-clearing drift, not a center-origin burst), emptying the frame. On the now-clear
frame, the logo mark DRAWS ON via stroke (built arc-by-arc / segment-by-segment). The wordmark
reveals beside the drawn mark (a slide, not a fade) to complete the lockup; the lockup holds, then
the frame cuts to black/bg (its own final-frame exit, per SKILL.md §1 rule 2 — not a mid-shot
fade).

**build notes**:
- Letter cascades and part-assemblies are per-element stagger tweens (index-derived delay,
  `power3.out` or a bounded `back.out(≤2)`/`springEase`) into each glyph/part's pre-measured final
  position — never an opacity-only arrival.
- The stroke-draw is an SVG `stroke-dashoffset` tween, segment by segment, each segment's start
  keyed to the previous one's end.
- The diagonal-band wipe is a `clip-path polygon()` tween sweeping across the frame — swelling
  then collapsing to the slash is the same clip-path driven through a grow→shrink keyframe pair.
- The camera push-through is a single hard `cam.scale` push on one `.world` wrapper aimed via a
  pre-measured target point (the mark's negative-space center), with a proxy-tweened motion-blur
  that peaks at the push's peak velocity and resolves sharp on landing.
- The formation-disperse exit (Brand_Outro) is an in-scene clearing beat only when it is NOT the
  shot's final exit — if this is the last beat of the video, prefer letting the harness
  `transition_in` carry the clear instead of animating it yourself (SKILL.md §1 rule 2).
