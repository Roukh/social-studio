# terminal-type-on

**Family:** type, interface. **Wants:** 1.5-3 s. **Source:** a Lightspark social promo in
prompt-motion.com's gallery (prompt-motion.com/davidmarcus-a28a60), studied 2026-10-09.

## Looks

A dark, rounded code or command panel types on character by character at a steady rate, mono face, with a
blinking block cursor that advances with the text. The call (a function, a CLI command, an API request) completes,
and a final status line or result (a dot plus a word, a returned value) appears below a hairline rule as the
payoff.

## Build

- DOM text revealed per character at a steady rate with `kit.typeOn`, same mechanic as `dual-voice-type.md`, but
  monospace and in one voice.
- The cursor is a `::after` block that blinks on the beat, not on a CSS timer, and sits at the live character
  position.
- The panel itself can pop or scale in before typing starts (0.9 -> 1, `power3.out`).
- The status line reveals after a short pause once typing finishes: a coloured dot (`box-shadow` glow) plus a
  word, fading and sliding up 4-6 px.

## Sound

A soft mechanical key tick per character, lighter than `kinetic-word-run.md`'s hits, and a single confirm tone
on the status line.

## Adapting

Use it for any developer-facing product: an API call, a CLI, a config snippet. The command and its result should
be the real shape of what the product does, not generic placeholder code.

## Variants

The same move, as other reference films staged it:

- **terminal readout card** (prompt-motion.com's gallery (kloss-xyz-15182a), studied 2026-10-09.): A small monospace card, styled like a terminal window or a config file (a thin top chrome with traffic-light dots), lists a handful of `field: value` rows. The rows type or clip in one after another, top to bottom, each landing with the value in a brighter weight than its label, so the card reads as the subject introducing itself in its own technical voice.
- **agent tool call log** (prompt-motion.com's gallery (melvynx-6cde6c), studied 2026-10-09.): A terminal-style panel holds a plain-language query typed in by a person. Underneath, a sequence of structured tool-call lines streams in one at a time — a function-like name, its arguments, a short result count or status — reading like a visible trace of the agent's actual actions rather than a vague "thinking" spinner. It closes on one plain-English confirmation line and a small status badge.
