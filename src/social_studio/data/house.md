# House rules

The first three rules are the render contract: they hold for every video, whatever a skill, a file or a habit says.

- You work alone and nobody will answer questions: decide and finish. Every command in TASK.md, draft renders
  included, is pre-approved. Never ask for permission and never stop to wait.
- Every frame is a pure function of time. All motion lives on the paused GSAP timeline `tl`, or is drawn from the
  time HyperFrames hands a canvas (`hf-seek`, `window.__hfThreeTime`): no `Date`, no unseeded `Math.random`, no
  timers, no `requestAnimationFrame` loops, no CSS transitions or animations, no remote URLs. Use only files in
  `composition/`. Sound is `<audio id>` elements on the same timeline.
- Use only the font families declared in `composition/index.html`. Never name another font, system or web: the
  renderer swaps unknown and common names for a substitute and fetches it from the network.

Everything else is craft, not law. The skills in `skills/` give defaults with their reasons; start with
`skills/motion-canon`. Follow a default unless breaking it makes the film better, and when you break one, do it on
purpose. The defaults that matter most here:

- Words the viewer must read are at least {{min_text_px}} px tall in this {{width}}×{{height}} frame (11 pt on a
  phone) and hold long enough to read. HUD labels, counters and texture type may go smaller; a one-word beat on the
  music may hold a single beat.
- The first frames already say something: a striking image, a word, a mark in motion. An empty field is a choice,
  not an accident.{{format_note}}
- {{motion_rule}}, and the same move does not carry two shots in a row.
- The end card, the wordmark and the call to action, takes at most {{end_card_pct}}% of the runtime, and the last
  shot hands its motion off to it.
{{rules}}
