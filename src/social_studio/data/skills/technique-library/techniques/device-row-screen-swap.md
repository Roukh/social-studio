# device-row-screen-swap

**Family:** interface, collage. **Wants:** 2.5-4 s. **Source:** prompt-motion.com's gallery
(jesscaroline7-1ff7cb), studied 2026-10-09.

## Looks

A row of identical device mockups lines up across the frame, each displaying a different screen of the same
product. The devices themselves stay fixed as the camera drifts slowly past; only the screen content inside
each frame swaps to the next feature, each on its own offset timing, so the row reads as a continuous tour
through several capabilities without a single hard cut. The source swapped its screens with cross-fades; here
each swap is spatial (the house default), so the row keeps its motion language.

## Build

- Fixed device frame positions, evenly spaced; the screen content is a layer inside each frame's mask.
- Each swap pushes the old screen out and the new one in inside the mask: a vertical slide (`yPercent` -100 to 0,
  `expo.out`, 0.35-0.45 s) or a clip-path wipe in the direction of the camera drift. Never an opacity fade.
- Stagger the swap times across devices (no two change in the same instant) so the row always has at least one
  frame mid-swap.
- A slow camera dolly (`translateX`, 15-20 px/s, or a subtle parallax scale) supplies the sense of motion even
  though the devices don't move relative to each other.

## Sound

A soft whoosh under the camera drift, a light tick on each individual screen swap.

## Adapting

Three to five devices read best. In 9:16, stack two rows of two-three devices instead of one wide row.
