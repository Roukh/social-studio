---
id: mcp-skill-candidates
type: reference
created: "2026-10-06T23:45:00Z"
consequence: 6
locus: output
summary: 2026-10-06 sweep of 49 MCPs, APIs and skills (sound, voice, music, image, video, 3D, UI, fonts) - auth, licence, terms, price, flags.
scope: repo
status: superseded
---

# MCP/API/skill candidates for the jail

Sweep of servers/APIs/skills (sound, voice, music, image, video, 3D, UI, fonts, motion) for the engine's jail. Part of [[reference-look-decisions]]. Iteration 1 (2026-10-06) vendored 16 skill packs, synthesizes sound in code; nothing here is keyed yet — this is the menu.

## Question

Which MCPs/APIs/skills run in a headless jail (network out, no browser, no login) with commercially usable output?

## Method

Web research 2026-10-06; vendor pages preferred over aggregator blogs on conflict.

## Findings

"Fits the jail" = key in env var/header, or local. OAuth-only = cannot log in from the video session.

**Disputed:** Pixabay audio (row says non-commercial; `CREDITS.md` + [[reference-look-decisions]] say commercial-OK — unresolved). playwright-mcp/chrome-devtools-mcp: jail binds a pinned chrome-headless-shell read-only (`runner.py:556-565`) — whether either server can target it is unverified.

### 1. SFX generation / libraries

| Name | Gives | Auth | Licence/price | Flags | Source |
|---|---|---|---|---|---|
| ElevenLabs Sound Effects | text→SFX | key hdr | comm $5+/mo; $0.12/min | hosted MCP OAuth-only | [costbench](https://costbench.com/software/ai-music-apis/elevenlabs-sfx-api/) |
| Stable Audio 3 SFX (fal.ai) | text→SFX | `FAL_KEY` | Community/Enterprise lic; $0.028/gen | check-$1M/yr-cap | [fal.ai](https://fal.ai/models/fal-ai/stable-audio-3/small/sfx/text-to-audio/api) |
| Stable Audio (direct) | text→SFX | key | Community <$1M/yr free; $0.20/file | Enterprise ≥$1M | [stability.ai](https://stability.ai/membership) |
| Pixabay Audio API | SFX/music lib | key | disputed-above; free | unresolved | [pixabay.com](https://pixabay.com/) |
| Zapsplat | SFX lib | unverified | free w/attrib, Gold-removes | web-only, unverified | [forums](https://forums.unrealengine.com/t/the-complete-guide-to-free-commercially-usable-music-sfx-that-dont-suck/115450) |
| Freesound | SFX/music API | key | CC-BY-NC; free | excluded: non-comm | n/a |
| Meta AudioCraft/AudioGen | local SFX gen | none | code MIT; weights CC-BY-NC; free | non-comm-weights | [vantaige.io](https://vantaige.io/ai-tool/audiocraft) |
| Beatoven Maestro SFX | SFX+music | key | paid=comm; free=non-comm; ~$7/mo | verify-terms | [aiindigo.com](https://aiindigo.com/tool/beatoven-ai) |

### 2. Voice / TTS

| Name | Gives | Auth | Licence/price | Flags | Source |
|---|---|---|---|---|---|
| ElevenLabs TTS (REST) | text→speech | key hdr | comm $5+/mo; free→$990/mo | jail-safe | [elevenlabs.io](https://elevenlabs.io/docs/changelog/2026/8/22) |
| ElevenLabs hosted MCP | text→speech | **OAuth only** | same as plan | archived 2026-08-20; no headless | [creativeainews.com](https://www.creativeainews.com/blog/elevenlabs-hosted-mcp-server-migration-2026/) |
| OpenAI TTS | text→speech | Bearer key | $0.015/min–$30/1M chars | track model-lifecycle | [developers.openai.com](https://developers.openai.com/api/docs/models/gpt-4o-mini-tts.md) |
| Google Gemini TTS | text→speech | key | ~$0.91/narration hr | — | [ai.google.dev](https://ai.google.dev/gemini-api/docs/pricing) |
| Cartesia Sonic | text→speech | key | comm Pro $5/mo+; $5–$299/mo | free-tier-non-comm | [costbench](https://www.costbench.com/software/voice-apis/cartesia/) |
| Hume AI Octave TTS | text→speech | key | comm Creator+; $14–$200/mo | free/Starter-non-comm | [hume.ai](https://hume.ai/pricing) |
| MiniMax-MCP (official) | TTS/voice MCP | `MINIMAX_API_KEY` | MIT server; pay-per-use | key/region-mismatch→silent-fails | [dev.co](https://dev.co/ai/mcp/minimax-mcp) |
| PlayHT/Play.ai | — | — | — | **dead**: absorbed-by-Meta-2025 | [casrai.org](https://casrai.org/guides/murf-play-ht-wellsaid-labs-pricing-compared) |
| Azure AI Speech | text→speech | key hdr | free 0.5M chars/mo | — | [azure.microsoft.com](https://azure.microsoft.com/pricing/details/speech/) |
| Kokoro TTS (local) | local TTS | none | Apache-2.0; free | best jail-fit, no-network | [awesome.ecosyste.ms](https://awesome.ecosyste.ms/projects/github.com%2Fpguso%2Fkokoro) |
| Piper TTS (local) | local TTS | none | fork **GPL-3.0+** (was MIT) | orig.-archived | [promptquorum.com](https://www.promptquorum.com/power-local-llm/piper-tts-review) |

### 3. Music generation / licensed beds

| Name | Gives | Auth | Licence/price | Flags | Source |
|---|---|---|---|---|---|
| Stable Audio (music) | text→music | key | comm Pro $12/mo; free non-comm | — | [stability.ai](https://stability.ai/membership) |
| MiniMax Music 3.0 | text→music | key, existing users | Community Lic, attrib in UI | **closed to new users 2026-08-20** | [rits.shanghai.nyu.edu](https://rits.shanghai.nyu.edu/ai/minimax-opens-music-3-0-weights-no-territorial-carve-out-this-time/) |
| ElevenLabs Music v2 | text→music | key hdr | cleared via Merlin/Kobalt; $0.15/min | excl-film/TV-self-serve | [pulse2.com](https://pulse2.com/elevenlabs-introduces-music-v2-with-advanced-genre-switching-enhanced-editing-and-licensed-commercial-use/amp/) |
| Suno developer API | text→music | invite-only | unverified | **not GA**; no-public-docs | [digitalmusicnews.com](https://www.digitalmusicnews.com/2026/07/03/suno-is-opening-an-api-partner-program/) |
| Udio | text→music | N/A | UMG walled garden; $10–30/mo | no-API, blocks-download | [musicweek.com](https://www.musicweek.com/labels/read/umg-settles-lawsuit-and-signs-strategic-deal-with-udio-for-licensed-ai-music-platform/092966) |
| Mubert API v3 | text→music | key | covers YT/TikTok; free–$199/mo | not-streaming-release | [costbench](https://costbench.com/software/ai-music-generators/mubert/) |
| Beatoven Maestro Music | text→music | key | paid=full comm+stems; ~$7/mo | free-tier-personal-use | [aiindigo.com](https://aiindigo.com/tool/beatoven-ai) |
| Loudly Music API | text→music | key | "copyright-safe"; volume PAYG | price-unpublished | [loudly.com](https://www.loudly.com/) |
| Epidemic Sound Partner API | 55k+ tracks | key; partnership for catalog | cleared once partnered | non-generative | [help.epidemicsound.com](https://help.epidemicsound.com/hc/en-us/articles/35854988839570-Getting-Started-with-the-API) |
| Meta AudioCraft MusicGen | local music gen | none | code MIT; weights CC-BY-NC; free | non-comm-weights | [vantaige.io](https://vantaige.io/ai-tool/audiocraft) |

### 4. Image generation

| Name | Gives | Auth | Licence/price | Flags | Source |
|---|---|---|---|---|---|
| fal.ai (FLUX etc.) | image aggregator | `FAL_KEY` | per model; from $0.014/img | varies-per-model | [fal.ai](https://fal.ai/models/fal-ai/stable-audio-3/small/sfx/text-to-audio/api) |
| Replicate (+official MCP) | image/model gen | `REPLICATE_API_TOKEN` | per-model, pay-per-sec/run | Cloudflare-acquired-Dec-2025 | [jsdelivr](https://cdn.jsdelivr.net/npm/replicate-mcp@0.9.0/README.md) |
| OpenAI gpt-image | text→image | Bearer key | $0.006–$0.211/img | retires 2026-10-23 | [gate.ai](https://gate.ai/blog/gpt-image-latest-openai-specs-pricing-api-use-cases) |
| Google Imagen (Gemini API) | text→image | key | full comm rights; $0.02–$0.04/img | — | [pricepertoken.com](https://pricepertoken.com/imagen-pricing) |
| Black Forest Labs FLUX API | text→image | key | comm all tiers; $0.014–$0.07/img | self-host-9B/32B-needs-paid-lic | [developer.puter.com](https://developer.puter.com/tutorials/flux-api-pricing/) |
| Ideogram API | text→image | key, Stripe credit | comm paid tiers; $0.03–$0.10/img | auto-topup-risk | [eesel.ai](https://eesel.ai/blog/ideogram-pricing) |
| Recraft API (vector/SVG) | text→image (SVG) | key | full comm paid; $0.035–$0.30/img | fits-code-drawn-video | [invideo.io](https://invideo.io/blog/recraft-ai-image-generator/) |
| Stable Image Ultra/Core | text→image | key | Community <$1M/yr free; $0.03–$0.08/img | Enterprise-$1M-rev | [costbench](https://www.costbench.com/software/ai-media-apis/stability-ai-api/) |

### 5. Video generation (generate-then-trace base layers)

| Name | Gives | Auth | Licence/price | Flags | Source |
|---|---|---|---|---|---|
| Runway API + official MCP | text/image→video | key/account | **MIT** server; ≈12 credits/sec | best-fit-video-MCP | [aiweekly.co](https://aiweekly.co/alerts/runway-opens-mcp-server-for-chatgpt-claude-cursor-replit) |
| Luma Dream Machine API | text/image→video | key | ~11 credits/sec, no free tier | ~70%-above-list | [costbench](https://www.costbench.com/software/ai-media-apis/luma-dream-machine-api/hidden-costs/) |
| Kling API (direct/fal/Replicate) | text/image→video | key | $0.07–$0.14/sec, by host | pricing-fragmented | [costbench](https://www.costbench.com/compare/kling-api-vs-replicate/) |
| Google Veo 3.1 | text/image→video | key (Gemini/GCP) | $0.05–$0.60/sec | "success"≠usable | [wavespeed.ai](https://wavespeed.ai/blog/cost-and-billing/google-veo-3-pricing/) |
| MiniMax Hailuo/H3 | text/image→video | key | $0.18–$0.28/6s | H3:US/EU/UK/Korea-only | [wireflow.ai](https://www.wireflow.ai/blog/best-hailuo-api-tools-in-2026) |
| ByteDance Seedance 2.0 | text/image→video | key | $0.022–$0.09/sec | cheapest-via-resellers | [techsy.io](https://techsy.io/en/blog/best-ai-video-providers) |
| Pika API/Club | text/image→video | key | Club $10/mo, direct custom | watermark-removal+30-60% | [magichour.ai](https://magichour.ai/blog/pika-labs-pricing) |
| PiAPI/GoAPI (aggregator) | re-exposes Udio/DiffRhythm/MMAudio/AceStep | key | unverified, pay-per-call | **unofficial**; no-Suno | [apiframe.ai](https://apiframe.ai/blog/ai-music-api-pricing-2026) |

### 6. 3D / scene

| Name | Gives | Auth | Licence/price | Flags | Source |
|---|---|---|---|---|---|
| Blender MCP | drives local Blender | none | **MIT**; free | needs-local-Blender | [github.com/ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) |
| Poly Haven API | 3D assets/HDRIs | none (public) | **CC0**; bulk comm = 5% rev+fee | — | [polyhaven.com](https://polyhaven.com/corporate) |
| Sketchfab Download API | 3D models | account login | per-model CC, comm OK w/attrib | not headless-key-only | [sketchfab.com](https://sketchfab.com/developers/download-api/guidelines) |
| Meshy AI API | text→3D | key | paid=full comm; free=CC-BY-4.0; $20–$90+/mo | attrib-on-free-tier | [docs.meshy.ai](https://docs.meshy.ai/en/webapp/pricing) |
| Tripo3D API | text→3D | key | free CC-BY-4.0; paid=full comm; $1/100 credits | attrib-on-free-tier | [tripo3d.ai](https://www.tripo3d.ai/blog/commercial-use-ai-3d-models) |
| Spline | embeddable-runtime, no-gen-API | N/A | proprietary; freemium | no-programmatic-gen | [apis.io](https://apis.io/providers/spline/) |

### 7. Real UI components / assets / reference capture

| Name | Gives | Auth | Licence/price | Flags | Source |
|---|---|---|---|---|---|
| 21st.dev Magic MCP | React/Tailwind/shadcn code | key flag | **MIT**; usage-based | thin-client, hosted-gen | [docsearch.algolia.com](https://docsearch.algolia.com/mcp/docs/repo/21st-dev/magic-mcp) |
| shadcn MCP (community) | shadcn/ui code | unverified | code MIT; free | unofficial/unaudited | [glama.ai](https://glama.ai/mcp/servers/ymadd/shadcn-ui-mcp-server) |
| Firecrawl MCP Server | web scraping | `FIRECRAWL_API_KEY` | **MIT**; SaaS metered | — | [unpkg](https://unpkg.com/firecrawl-mcp@3.23.8/README.md) |
| Browserbase MCP+Stagehand | browser automation | 2 keys+model key | **Apache-2.0**; SaaS metered | needs-3rd-model-key | [github.com](https://github.com/browserbase/mcp-server-browserbase) |
| playwright-mcp | local browser automation | none | **Apache-2.0**; free | jail-bound chrome-headless-shell; unverified | [glama.ai](https://glama.ai/mcp/servers/@microsoft/playwright-mcp/blob/10c340c0b334c3e3c2653257d36fb45f6594583d/package.json) |
| chrome-devtools-mcp | local Chrome automation | none | **Apache-2.0**; free | same note (above) | [dev.co](https://dev.co/ai/mcp/chrome-devtools-mcp) |
| Mobbin API/MCP | UI screenshots | Bearer key/hosted MCP | research-use-only; REST-Team+/MCP-Pro+ | — | [everydev.ai](https://www.everydev.ai/tools/mobbin-mcp) |

### 8. Fonts

| Name | Gives | Auth | Licence/price | Flags | Source |
|---|---|---|---|---|---|
| Google Fonts API | font metadata/CSS | keyless CSS; key for metadata | **SIL OFL**; free | — | [developers.google.com](https://developers.google.com/fonts/terms) |
| Fontsource (npm) | self-hosted-variable-fonts | none | mostly **OFL**; free | no-network-at-render | [makandracards.com](https://makandracards.com/makandra/625274-self-hosted-fonts-via-npm-packages) |

### 9. Claude Code skills (motion/sound/3D/Three.js/GSAP/Remotion/Lottie/Rive)

| Name | Gives | Auth | Licence/price | Flags | Source |
|---|---|---|---|---|---|
| buildwithhanif/claude-animation-skill | local-sound/music/chiptune-synth | N/A | **MIT** (prior context) | unverified-this-session | n/a — unverified |
| DirectorSKILL | local skill | N/A | **MIT** (prior context) | unverified-this-session | n/a — unverified |
| motion-skills (iart-ai) | 50 skills, 14 packs (WebGL/Manim) | N/A, `npx skills add` | **MIT**; free | unaudited-bundle | [sourcepulse.org](https://www.sourcepulse.org/projects/32918651) |
| GSAP (npm) | animation lib (plugins) | none | **free, all plugins** since Webflow 2025 buy | no-key/paywall | [webflow.com](https://webflow.com/blog/webflow-acquires-gsap) |
| Remotion | React-video-render framework | none | **Remotion License**, not MIT; free ≤3-person | else $25/seat/mo+ | [remotion.dev/license](https://remotion.dev/license) |
| Lottie/LottieFiles | anim-runtime+marketplace | none; key-for-premium | runtime **MIT**; free assets "Simple License" | 2-licence-regimes | [lottiefiles.com](https://lottiefiles.com/blog/lottie-animations/lottiefiles-or-rive.md) |
| Rive | interactive-runtime+editor | N/A runtime; account-for-editor | **unverified** runtime terms | confirm rive.app/legal | [rive.app/docs](https://rive.app/docs/editor/assets/lottie) |

### Excluded / already known

- **Freesound** — CC-BY-NC, excluded per scope.
- **Higgsfield** — excluded by org policy.
- **HyperFrames' own skills** (media-use, music-to-video, hyperframes-audio) — internal, not re-researched.
- **Suno/Udio** — no public self-serve API as of 2026-10-06.

## Sources

One URL per row above; see the tables.

## Date

Gathered 2026-10-06; condensed 2026-10-06 for the format 4 wiki.
