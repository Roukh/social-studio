---
id: render-and-encoding
type: reference
created: "2026-10-01T00:00:00Z"
consequence: 7
locus: output
summary: HyperFrames render stack, rejected alternatives, ffmpeg encode/loudness/poster recipe, sound-sourcing licence findings.
scope: repo
status: superseded
---

# Render and encoding

How social-studio renders (HyperFrames) and encodes output (ffmpeg); why alternatives were rejected; where sound effects can legally come from. Gathered 2026-10-01.

## Question

HyperFrames' capabilities/limits, how it compares to alternative renderers, correct ffmpeg encode parameters, and licence terms for sourcing sound effects by API.

## Method

Live WebSearch/WebFetch against GitHub repos/source/issues, npm/GitHub APIs, ffmpeg.org/trac.ffmpeg.org docs, vendor terms pages, 2026-10-01. Instagram/TikTok/LinkedIn/X upload-spec pages failed (403/404/CAPTCHA) — open gap, not guessed.

## Findings

### HyperFrames (pinned 0.8.106, Apache-2.0)

github.com/heygen-com/hyperframes (HeyGen), Apache-2.0, no per-render fee. Node >=22 + system `ffmpeg`; auto-downloads pinned `chrome-headless-shell` (152.0.7977.30, falls back 150.0.7871.124 on macOS 12).

- **CLI**: `init, preview, normalize-audio, render, publish, lint, compositions, benchmark, doctor, browser, info, docs, upgrade` (plus ~80 undocumented: auth, cloud, figma, lambda...). `render` flags: `--output`, `--resolution 4k`, `--format {mov,webm,gif,png-sequence,hls}`, `--fps`, `--quality high`, `--docker`, `--workers N`, `--variables '{json}'`.
- **Composition**: plain HTML, `data-start/data-duration/data-track-index` on clips, timed via GSAP on `window.__timelines`, paused and seeked, never played (adapters also exist for CSS/Lottie/Three.js/WAAPI).
- **Determinism**: frame clock `floor(frame)/fps`; `Date`/`performance.now`/rAF replaced by a virtual-time shim, optionally Mulberry32-seeded RNG. Capture via atomic `HeadlessExperimental.beginFrame`. Readiness gate waits on media `canplay`, image decode, `document.fonts.ready`. `--docker` pins Chromium/fonts/ffmpeg for byte-exact reproducibility.
- **Workers**: `--workers N|auto` (~256MB RAM each), `--batch-concurrency` (default 1), `--low-memory-mode` (1 worker). `@hyperframes/producer` orchestrates Lambda/Cloud Run/Kubernetes, limited to mp4(SDR)/mov(ProRes4444)/png-sequence. `--docker` builds locally.
- **Audio**: `<audio>` with `data-volume`, mixed via ffmpeg. `normalize-audio` matches LUFS, refuses boosts past "+12dB" or clipping. Codec: mp4/mov→AAC, webm→Opus, png-sequence→sidecar `audio.aac`.
- **Captions**: `transcribe` (Parakeet, fallback Whisper; imports .srt/.vtt), e.g. `hyperframes transcribe interview.mp4 --engine whisper --model medium.en`. `.caption-group` elements, overrides in `caption-overrides.json`; burned in, no subtitle track.
- **Fonts**: `doc.fonts.ready` gates render-readiness. **HyperFrames remaps Helvetica/Arial to Inter** — fonts must load as files under their own name or get silently substituted.
- **Output formats**: mp4 (H.264 yuv420p/H.265+HDR10, AAC, default); webm (VP9, true alpha, Opus); mov (ProRes 4444, 10-bit alpha, AAC); png-sequence (RGBA, sidecar `audio.aac`); hls (H.264, AAC, SDR); gif (previews). Alpha is real CDP transparency, not chroma key. Presets: 1080p/4k landscape/portrait, square/square-4k; default 30fps or `data-fps`.
- **Known limits**: frame-sampling rounding (#4763), BeginFrame timeout ≥6 workers/GPU (#4584), `z-index:-1` fails to render (#4366); no GSAP timeline → fixed 45s timeout unless `data-no-timeline` set; provenance tags unauthenticated/spoofable; Studio editor not stable.

### Alternatives (rejected / compared)

| Tool | Licence | Authoring | LLM fit | 2026 maintenance |
|---|---|---|---|---|
| HyperFrames | Apache-2.0 | HTML + data attrs | Strong | Very active |
| Remotion | Source-available, free ≤3 employees; 4+ need paid licence (see below) | React/TS | Strong | Active, **rejected** |
| Revideo | MIT | TS generators | Strong | Quiet since 2026-07, moved to commercial Midrender |
| Motion Canvas | MIT | TS generators | Moderate | Stalled since early 2025 |
| Manim (Community/3b1b) | MIT | Python `Scene` | Moderate | Community active, 3b1b dormant |
| Lottie/lottie-web | MIT | JSON, normally AE export | Weak | Unchanged since 2024-11 |
| rlottie | Mixed/NOASSERTION | C++, consumes Lottie JSON | n/a | Deprecated |
| timecut/timesnap | BSD-3-Clause | captures HTML/CSS/JS | Strong | Unmaintained since 2022 |
| Mediabunny | MPL-2.0 | WebCodecs mux/encode lib | Strong | Very active |
| Vello/rust-skia | MIT/Apache-2.0, MIT/BSD | Rust API only | Weak, backend only | Active |
| Typst | Apache-2.0 | Custom DSL | n/a, no video | Wrong tool |

Remotion's FAQ defines "automation" as any code calling `renderMedia()`/`npx remotion render`; a 4+-employee company running this CLI would, by inference, owe its own Automators licence ($0.01/render, $100/mo min) — why it was rejected.

### FFmpeg encoding parameters

| Parameter | Value | Reason |
|---|---|---|
| `-c:v libx264`, no `-profile:v` | — | x264 auto-selects profile (usually High) |
| `-pix_fmt yuv420p` | — | broad decoder/browser/QuickTime compat |
| `-preset` | `slow` | slowest with patience; `veryslow` = diminishing returns |
| `-crf` | `20` | ffmpeg's sane range 17-28; near-lossless for flat-color/text |
| `-tune animation` | — | "cartoons; higher deblocking, more ref frames," extended to motion graphics |
| `-g`/`-keyint_min` | `60`/`60` @30fps | 2s GOP per Apple HLS Authoring Spec 1.13; scale 2×fps elsewhere |
| `-sc_threshold 0` | — | fixed GOP spacing (x264, not ffmpeg wiki) |
| `-maxrate`/`-bufsize` | `8M`/`16M` | VBV cap 1:2; 8Mbps anchored to YouTube's 1080p figure |
| `-c:a aac -b:a` | `192k` | ffmpeg's floor is 128kbps stereo; 192k is a safe ceiling |
| `-ar` | `48000` | ffmpeg's AAC page gives no rate; from YouTube |
| `-af loudnorm` two-pass | `I=-14:TP=-1.5:LRA=11` | measure pass feeds `measured_*` to apply pass; -14 LUFS is convention, not mandate |
| `-movflags +faststart` | — | moov atom to file start; ffmpeg + YouTube recommend |
| CRF vs two-pass | CRF | "recommended for most uses"; two-pass wins only on exact size |
| `tmix` motion blur | `tmix=frames=5` | averages N frames (default 3); costs ~N× the render |
| Poster | `ffmpeg -ss T -i in.mov -frames:v 1 out.jpg` | `-ss` before `-i` = fast seek |
| Contact sheet | `select='not(mod(n,100))',scale=160:90,tile=6x5` | `tile` default 6x5, with frame selection |

### Platform upload specs

Only YouTube reachable; others failed.

| Spec | YouTube |
|---|---|
| Container/video | MP4, H.264 High Profile, progressive, 2 B-frames, closed GOP, moov-front |
| Audio | AAC-LC/Opus/Eclipsa, 48kHz, 384kbps stereo / 512kbps 5.1 / 128kbps mono |
| SDR bitrate (16:9) | 1080p 8Mbps, 720p 5Mbps, 480p 2.5Mbps, 360p 1Mbps |
| Accepted codecs | MOV, MPEG-1/2/4, MP4, MPG, AVI, WMV, MPEGPS, FLV, 3GPP, WebM, DNxHR, ProRes, CineForm, HEVC |
| Shorts | ≤3 min, max 1080p |

AV1/VP9 not accepted uploads. Platforms re-encode server-side regardless of input codec.

### Determinism checks

Pin the headless browser exactly (Playwright/Puppeteer pin Chromium/Chrome-for-Testing per release). Await `document.fonts.ready` before capture — cross-machine pixel diffs come from font rendering (Playwright #20097) and headless-vs-headful hinting (Puppeteer #2410, fix `--font-render-hinting=none`). Docker images ship no fonts by default — bundle and `fc-cache -fv`. Pin ffmpeg to a checksummed static build (johnvansickle.com, BtbN/FFmpeg-Builds): output isn't byte-identical unless `-bitexact` is passed (yt-dlp #2284). Verify by hashing (`ffmpeg -i INPUT -f framemd5 -`), render twice, diff; mismatched line = divergent frame; `psnr`/`ssim` with `stats_file=` add per-frame diffs. Browsers tie animation to wall clock, skipping frames under load; Remotion and HyperFrames both fix this with virtual time + seeded RNG.

### Sound effects sourcing (licence findings)

**Freesound — ruled out.** Licence values: `Creative Commons 0`, `Attribution`, `Attribution NonCommercial` (`Sampling+` retired). Key auth for search/preview; OAuth2 for full downloads. Its API Terms of Use say free access is non-commercial only, but its fuller legal terms only forbid breaching the content licence — conflicting, unresolved, hence ruled out.

**ElevenLabs — operator-ruled keyed source.** `POST https://api.elevenlabs.io/v1/sound-generation`, `xi-api-key` header, params `text, loop, duration_seconds (0.5-30), prompt_influence, model_id`. Higher-quality formats need higher tiers (192kbps MP3: Creator+; 44.1kHz PCM: Pro+); ≈$0.12/min. Commercial rights gated by **account plan tier**: Free-tier is non-commercial; Paid-tier is commercial and indefinite — unverifiable by the CLI itself, a documentation obligation. Outputs sublicense to other users by default unless disabled via dashboard toggle. Iteration 1 synthesizes sound in code instead of calling either API.

### Recommended ffmpeg baseline (1080x1920, 30fps master)

```bash
# measure
ffmpeg -i input.mov -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null -

# encode, using measured_* above
ffmpeg -y -i input.mov \
  -c:v libx264 -pix_fmt yuv420p \
  -preset slow -crf 20 -tune animation \
  -g 60 -keyint_min 60 -sc_threshold 0 \
  -maxrate 8M -bufsize 16M \
  -c:a aac -b:a 192k -ar 48000 \
  -af loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=<input_i>:measured_TP=<input_tp>:measured_LRA=<input_lra>:measured_thresh=<input_thresh>:offset=<target_offset>:linear=true \
  -movflags +faststart \
  master_1080x1920.mp4
```

Baseline, not platform-certified: scale `-g`/`-keyint_min` to 2×fps for other rates; treat `-maxrate`/`-bufsize` as provisional pending the other platforms' ceilings.

### Open verification gaps

1. Remotion automation-licence inference above — not Remotion's direct answer; highest-stakes item.
2. Official upload specs for Instagram/TikTok/LinkedIn/X — not retrievable; only YouTube confirmed.
3. Freesound's conflicting ToU clauses — moot now.
4. Whether an LLM can hand-author raw Lottie JSON, vs. it being only played-back.
5. Node.js's native WebCodecs maturity for a Mediabunny pipeline.
6. HyperFrames' `hyperframes lambda` CLI: README calls it future work; source tree suggests otherwise.

## Sources

github.com/heygen-com/hyperframes (README, packages/{cli,core,engine,producer,aws-lambda}, docs/); registry.npmjs.org/hyperframes; api.github.com/repos/heygen-com/hyperframes; remotion.dev, remotion.pro, github.com/remotion-dev/remotion; github.com/midrender/revideo; github.com/motion-canvas/motion-canvas; github.com/{3b1b,ManimCommunity}/manim; github.com/airbnb/lottie-web; github.com/Samsung/rlottie; github.com/thorvg/thorvg; github.com/tungs/{timecut,timesnap}; github.com/Vanilagy/{mediabunny,mp4-muxer}; github.com/linebender/vello; github.com/rust-skia/rust-skia; github.com/typst/typst; trac.ffmpeg.org/wiki/{Encode/H.264,Encode/AAC,Seeking}; ffmpeg.org/ffmpeg-{filters,formats,codecs}.html; support.google.com/youtube/answer/{1722171,55744,10059070}; k.ylo.ph/2016/04/04/loudnorm.html; playwright.dev/docs/{browsers,docker,release-notes}; pptr.dev/{supported-browsers,guides/headless-modes}; github.com/microsoft/playwright/issues/20097; github.com/puppeteer/puppeteer/issues/2410; johnvansickle.com/ffmpeg; github.com/BtbN/FFmpeg-Builds; github.com/yt-dlp/yt-dlp/issues/2284; freesound.org/docs/api/*, freesound.org/help/{faq,tos_api}; elevenlabs.io/docs/api-reference/text-to-sound-effects/convert, elevenlabs.io/terms-of-use, elevenlabs.io/sound-effects-terms.

## Date

Gathered 2026-10-01; condensed 2026-10-06 for the format 4 wiki.
