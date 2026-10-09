# text-diff-highlight

**Family:** annotation, data. **Wants:** 2-5 s. **Source:** prompt-motion.com's gallery (visheshbaghell-3aba37),
studied 2026-10-09.

## Looks

Two real documents (a note and an invoice, a message and a record) sit side by side or stacked. A phrase in
one gets underlined or highlighted in an accent colour, and the instant it lands, the matching phrase or value
in the other document highlights too, as if a thread were drawn between them. The pairs light up one at a
time, and a running total or result updates each time a pair confirms.

## Build

- Each document is real DOM text (not an image), so specific `span`s can be targeted.
- A highlight is a `background` or `text-decoration` tween on the targeted span, `power2.out`, 0.15-0.2 s.
- The two matched spans highlight within one beat of each other, not simultaneously, so the eye reads cause
  then effect.
- Any running total nearby updates its digits the instant the pair confirms, no separate clock.

## Sound

A soft highlighter-pen tick per phrase, a slightly different pitch for the second half of each matched pair.

## Adapting

Use it for any reconciliation, audit, or comparison claim: two records that should agree, a claim and its
evidence, a before and after. Keep the matched pairs few (3-5) and let each one fully land before the next.
