# glass-ui-flow

**Family:** interface. **Wants:** 1.7-2.5 s. **Source:** the 2026 Opus showreels; built in
`examples/reel-2026-10-06.html`, S7.

## Looks

A radial colour field with a fine dot grid behind it. Three frosted glass cards spring up into a stack, each
slightly rotated as it arrives and settling square. A cursor flies in, presses (it scales down on the click),
flips a toggle and picks an option. A button turns into a progress fill that counts to 100 % and becomes
"Done", and a toast slides in. The scene leaves on a soft-edged circle wipe from the centre.

## Build

- Cards are DOM with `backdrop-filter: blur()`, a translucent fill, a 1 px light border and a deep tinted
  shadow.
- Spring eases (response 0.36-0.42, damping 0.78-0.85) carry the cards, the toggle knob and the toast.
- The cursor uses `power3.inOut` paths, with a 0.045 s press (scale 0.82) and a 0.14 s release.
- The progress percentage is text set from the clock.
- Every interface is a fictional sample: invented product names, no real brand.

## Sound

Blips on each card landing, a click on the press, a toggle tick, a rising tone under the progress, and a
chime on Done.

## Adapting

Style the cards in the brand's colours and fonts. In 9:16, stack the cards vertically and let the cursor travel
the height.
