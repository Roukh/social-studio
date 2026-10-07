---
id: engine
type: reference
created: "2026-10-06T23:59:00Z"
consequence: 8
locus: output
summary: Box engine - pinned HyperFrames, Chrome and skills, the bubblewrap argv, the opaque master render, the H.264 delivery encode, loudness, poster and sheet.
scope: repo
status: active
---

# Box: engine

Part of [[index]]. Everything that touches the renderer, ffmpeg and the sandbox binary.

| Field | Value |
|---|---|
| Purpose | Install and pin the render engine, build the bubblewrap command, render the master, encode the delivery file |
| Owned paths | `src/social_studio/engine.py` (276 lines); `<project>/.studio/engine/hyperframes-<version>/` (engine, libraries, skills), `<project>/.studio/cache/` (Chrome, npm cache; HOME redirected there) |
| In | `render.version`, `render.libraries` (for example `gsap@3.14.2`), `render.vendor`, `render.esm`, `encode.*` from the preset, merged with the kit's defaults (`KIT_LIBRARIES` gsap and three, `KIT_VENDOR`, `KIT_ESM`; a preset's own pin wins), so every composition has GSAP, three.js and the motion kit (operator 2026-10-07); paths from [[runner]] |
| Out | `bwrap_argv`, `master.mp4`, the delivery `video.mp4` with `probe` info and sha256, `poster.jpg`, `contact.jpg` |

## Contracts

- Why HyperFrames: Apache-2.0, HTML plus GSAP with a deterministic seek(t); Remotion was rejected because companies of 4+ pay for automated renders.
- Engine: `hyperframes@X` installed once per version under `.studio/engine`, its skills fetched from the matching git tag; `require_version` accepts only an exact version. Today every built-in preset pins 0.8.106.
- Master: `hyperframes render COMP --format mp4 --crf 10 --fps N --no-browser-gpu --strict` inside the jail, timeout 1800 s.
- Delivery: libx264, yuv420p, preset slow, CRF 20, tune animation, GOP 2 s (`-g`, `-keyint_min`, `-sc_threshold 0`), maxrate 8M, bufsize 16M, faststart; audio AAC 192k 48 kHz with two-pass loudnorm to -14 LUFS, -1.5 dBTP, LRA 11; no audio stream -> `-an`. Every value is overridable through `encode.*`.
- Poster: one frame at `poster_at` (else mid-video). Contact sheet: 12 frames, 270 px wide, `tile=6x2`.
- `bwrap_argv(workdir, home, rw, ro, env, network=True)`: `--share-net` while `network` is true (open today; allowlist is feature F3).

## Invariants

- The master is an opaque MP4, never MOV or ProRes (issue I5).
- Never pass `--quiet` to render: it hides the lint findings that abort it (issue I6).
- Fonts are files under names the preset owns; aliased families get swapped for Inter (issue I4).
- `safe_root` never exposes a folder that is, or contains, home or the project; it falls back to the binary's own folder, then refuses.
- The jail starts from a cleared environment (`base_env`); only declared variables enter. An engine install run from inside an agent's own sandbox once hung because Node ignored that sandbox's proxy.
- Every frame is a pure function of time and there are no remote URLs; Three.js and other ES modules are vendored and loaded through an import map (`render.esm`).
- Software GL (llvmpipe) renders Three.js under `--no-browser-gpu`; capture runs about 34 ms per frame at 1920x1080.

## Rules, gotchas, open work

- Rules: R2 (sandbox), R8 (loudness target).
- Issues: I3 (Chrome cleanup kills commands carrying "chrome"), I4, I5, I6.
- Ledger: J4 (HyperFrames 0.8.114), J8 (network allowlist).
- Research: [[render-and-encoding]], [[motion-course-repos]] (the version gap).
