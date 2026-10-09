# chat-updates-preview

**Family:** interface. **Wants:** 4-8 s. **Source:** prompt-motion.com's gallery (justincooperman-e7bbc4),
studied 2026-10-09.

## Looks

A chat or prompt panel sits beside a live document preview (an email, a page, a card). Each exchange in the
chat lands a corresponding change in the preview, with no cursor and no click: an image slots into the layout,
a headline and body copy appear, a brand mark paints itself onto a product in the photo, a button labels
itself. The preview is always "live" and current, one beat behind the chat that's driving it.

## Build

- Two fixed panels, chat narrower than preview. Each chat reply triggers exactly one preview change, cued on
  that reply's landing time (no independent clock for the preview side).
- Preview changes are content swaps within fixed layout bounds (image cross-fade, text reveal by clip-path,
  logo overlay blending onto a photo via a soft multiply layer) so the document's layout never jumps.
- Hold the finished preview a beat longer than the chat's last line so the viewer reads the result, then let
  the frame pull back slightly (`scale 1.04 -> 1`) to show the whole composed document at once.

## Sound

A soft, low pad under the chat typing, a light chime on each preview change, nothing under the final hold.

## Adapting

Works for any "ask for it, see it built" product moment. In 9:16, stack the chat above the preview instead of
beside it, and let the preview take the bulk of the frame.

## Variants

The same move, as other reference films staged it:

- **chat drives ui** (prompt-motion.com's gallery (jhylee95-e1152f), studied 2026-10-09.): A chat transcript types on in one half of the frame: a user question, then an assistant reply with a short summary card. In the other half, synced to the exact line that names it, a live product screen highlights the element being talked about: a tooltip bubble lands on a button with a short instruction and a step counter ("1 of 4"), the cursor moves to it and clicks, and the panel updates. The two halves never fight for attention; only one is "speaking" at a time.
