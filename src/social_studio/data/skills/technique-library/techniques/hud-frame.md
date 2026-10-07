# hud-frame

**Family:** frame. **Wants:** the whole film. **Source:** the 2026 Opus showreels; built in
`examples/reel-2026-10-06.html`, the HUD markup and `// ===== HUD`.

## Looks

The frame is dressed like a camera viewfinder or an editor's monitor:

- corner bracket marks (1-2 px), about 2 % in from each corner;
- top left: a small accent dot and a mono label (the name, what the film is, the year);
- top right: a scene counter, `SCENE 03 / 09`, with the current number bright and the rest dim;
- bottom left: the current scene's section name;
- bottom right: progress squares (the current one in the accent) and a running timecode, from
  `kit.timecode(t, fps)`.

The HUD switches colour with the field: light on dark, dark on light.

## Build

- A DOM layer above every scene for the whole runtime. Its text updates from the clock with no easing, since a
  readout that eases looks decorative, not live.
- The labels sit about 4 % from the edges. They are texture, and may be smaller than reading text.

## Adapting

In 9:16, keep the HUD out of the platform's interface zones (`video.safe_zone`): the top 14 % and the bottom
35 % hold the app's own controls. The HUD fits a showcase or a technical message; a quieter film may drop it.
