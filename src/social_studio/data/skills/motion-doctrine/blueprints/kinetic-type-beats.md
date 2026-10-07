<!-- Distilled by social-studio from heygen-com/hyperframes (tag v0.8.106, Apache-2.0),
     skills/hyperframes-animation/blueprints/kinetic-type-beats.md. See ../../NOTICE.md.
     Patched: Scene 1's "per-word staggered fade/blur" entrance option is dropped (opacity-led);
     the rule-id citations to hyperframes-animation/rules/ are dropped since that skill isn't
     mounted here — build notes below are self-contained instead. -->

# kinetic-type-beats

**roles**: Hook, Problem, Product_Intro, Benefits, CTA, Brand_Outro
**duration**: 3.0-12.9s depending on role (staccato Benefits as short as ~3.5s; a CTA/Brand_Outro
beat chain can run to ~12.9s)

**intent**: A flat, centered, bold-type shot where the motion IS the words changing — a fixed
line swaps one token in place by hard cut, or a statement builds across full-screen beats (each
its own move) that lands on a spring-pop payoff. The workhorse: reach for it whenever the words
carry the shot and there's no set, surface, or click to show instead.

**shot structure** (flat; bold type on a solid `[bg color]`; camera locked unless noted; two
sub-shapes — **(A) fixed-line token swap** and **(B) multi-beat statement build**)

- **Scene 1 (0.0-~1.0s) — first beat lands.** Bold `[type color]` text arrives dead-center via
  ONE entrance: type-on character-by-character with a trailing blinking caret, a hard-cut
  FLASH-in (no fade/slide — the cut itself is the beat), or an oversized word that smoothly
  SCALES DOWN to its final centered size. An optional accent move plays on the key word: a drawn
  underline/strike-through, a small burst behind the text, or a selection-box frame.
- **Scene 2..N — beats replace each other in place (the engine).**
  - **Sub-shape A**: the line stays fixed; only the variable slot changes by an instant hard CUT
    (`tl.set`, no roll/scroll/blur) — token A → token B → token C — or the final word(s)
    backspace out and retype.
  - **Sub-shape B**: each full-screen beat hard-cuts to a new line and gets its own entrance/exit
    move — springy scale-in/out, a 3D letter-tumble (glyphs scatter into a depth cloud and
    reassemble), a motion-blur fly-in that resolves sharp, or a bottom-up masked slide. Background
    may hard-flip light/dark with the type color inverting to stay legible.
- **Scene N (final beat → end) — resolve and HOLD.** The last beat lands and holds to the end
  (settle only, no further scale-out/fade-out). Resolution by role: Hook lands a punctuation snap
  or a spring-popped payoff element; Product_Intro resolves on the brand mark/wordmark; CTA lands
  the logo/URL lockup; Brand_Outro hard-cuts to the brand's one defining word and holds while the
  background keeps moving.

**build notes**:
- Token swaps and whole-line state changes are `tl.set()` at time thresholds — zero duration,
  not a crossfade.
- The 3D letter-tumble and masked-slide moves are transforms on each glyph/word span
  (`rotationX/Y`, `z`, `clipPath`), staggered by element index; drive the common settle with
  `power3.out` or `springEase` (SKILL.md §4) when a beat's landing is the payoff.
- An accent underline/burst/box is a stroke-draw (`stroke-dashoffset`) or a small scale-in on its
  own element, timed to land with the word, not before it.
- Background light/dark hard-flips are `tl.set()` on a background color/variable, synchronized
  with the type-color invert at the same timeline position — not a crossfade between two layers.
