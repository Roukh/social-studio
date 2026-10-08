---
id: brand-site-design-kit
type: reference
created: "2026-10-06T23:59:00Z"
consequence: 7
locus: output
summary: How a brand's own website becomes a video's design system - the ghobz-ui kit (site CSS in phone layout, section markup, phone screens), proven in HyperFrames.
scope: repo
status: superseded
---

# Brand site as design kit (the ghobz-ui kit)

The operator asked for this on 2026-10-06: "Ui should match the theme of ghobz.com, same components, fonts, styles,
vivid cards, gradients, blurs, spacing, grids". The decision is logged in [[reference-look-decisions]].

**Method.** The site's production stylesheet (Tailwind v4 output, fetched from the live site) is rewritten for a
phone:

- Every media query is evaluated as for a 360 x 640 touch phone with reduced motion and no site script.
- vh and vw are converted to that phone's pixels.
- The fonts point at the preset's embedded faces. HyperFrames swaps out the names Helvetica and Arial, so the
  preset names its own.

The maker then builds each scene in three steps:

1. It lays out the interface on a 360 px stage, scaled x3 to fill 1080 x 1920.
2. It copies the site's own section markup. That markup was split from the site's server-rendered HTML into 20
   sections.
3. It checks each scene against 64 phone screens of the live site. The engine's pinned headless browser captured
   those screens.

**Proof.** Two checks passed:

- A puppeteer render of the site's HTML through the rewritten CSS matches the live phone screens.
- A two-scene composition built from the kit (the hero and a vivid card) renders correctly in HyperFrames
  0.8.106.

**Where it lives.** The kit is ghobz brand material, so it stays out of this public repo. It is staged in
`.local/ghobz-preset/` (gitignored), and `.local/install-ghobz-preset.sh` installs it into the ghobz project's
preset.

The tools are generic and are the starting point for fetching a brand when several accounts are connected:
`.local/ghobz-ui/capture.mjs`, `phone_css.py`, `kitbuild.mjs`, `refs_to_jpg.py` and `screens_md.py`.
