<!-- Distilled by social-studio from heygen-com/hyperframes (tag v0.8.106, Apache-2.0),
     skills/hyperframes-animation/blueprints/ticker-takeover.md. See ../../NOTICE.md.
     Patched: rule-id citations replaced with self-contained build notes. No fade content to
     patch — the source already states the text "does not fade, it gets displaced." Kept as the
     flagship doctrine example. -->

# ticker-takeover

**roles**: Hook, Brand_Outro
**duration**: 5-7s

**intent**: A context phrase types in, an accent word cycles through a few options to suggest
"this could be many things," then a hero CRASHES in from off-screen and physically shoves the text
aside — "actually, this is what it is." A collision, not a fade.

**shot structure**

- **Scene 1 (0.0-~1.4s) — context build.** A typewriter lays down a lead-in phrase
  character-by-character (smooth, no typos). Camera static.
- **Scene 2 (~1.4-3.0s) — the cycling beat.** An accent word inside the line ticks through 2-3
  options on a vertical spring-roll (each click a new word). More than ~3 reads as filler.
- **Scene 3 (~3.0-4.2s) — the collision (signature move).** A hero crashes in from off-screen
  with momentum and physically SHOVES the whole text group aside — the text reacts to the impact
  (it gets displaced), it does not fade. The hero lands heavy: a longer settle (`power2.out`), not
  a zip, so it reads as mass, not speed.
- **Scene 4 (~4.2-end) — the hero alone.** The hero settles dead-center and reads still. Holds.

**build notes**:
- The accent-word cycle is a masked column stepping through N options, each step a short vertical
  tween landing on a `power2.out`/`power3.out` settle — a slot-machine step, not a fade-swap.
- The crash-in hero travels fast with a directional motion-blur proxy that resolves sharp as it
  lands; use a hard `power3.in`/`power4.in` approach into the impact frame.
- The impact itself is a `tl.set` collision moment: the hero's arrival position is reached exactly
  as the displaced text group's push-tween starts — both driven off one shared time, so the hand-off
  reads instant, not staggered.
- The displaced text moves away from the hero's landing point (position tween, `power2`/`power3`
  settle) — it is never allowed to simply fade out while the hero fades in.
- The only sanctioned aliveness on the resting hero afterward is a low-amplitude, finite,
  dual-axis jitter (scale + rotation) — never a `yoyo` loop.
