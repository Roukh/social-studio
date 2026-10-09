---
id: elevenlabs-api-cost
type: reference
created: "2026-10-09T17:50:00Z"
consequence: 7
locus: output
summary: ElevenLabs REST contract (speech timings, effects, sectioned music, stems) checked 2026-10-09, credit prices, and credits per film.
scope: repo
status: active
---

# ElevenLabs: API contract and cost per film (2026-10-09)

## Question

The operator decided on 2026-10-09: "elevenlabs for everything. Voice over videos, music, sound effects." Rule R8
already makes the ElevenLabs REST API, keyed by `ELEVENLABS_API_KEY`, the sound source, and commercial use needs a
paid plan. What exactly does the API take and return today, what does a film cost, and what is still unverified?
The draft at `.shapa/temp/F15/sound.md` describes only the music_v1 plan; this note corrects that.

## Method

On 2026-10-09 I read these pages through WebFetch:

- the API references for `/v1/text-to-speech/{voice_id}/with-timestamps`, `/v1/sound-generation`, `/v1/music` and
  `/v1/music/stem-separation`;
- the sound-effects and music capability pages and the models page;
- elevenlabs.io/pricing and /pricing/api.

The help-centre article on music cost returned 403, so its figure comes from a search snippet. No call was made to
the API.

## Findings

### Contract

- **Base and auth**: base URL `https://api.elevenlabs.io`, key in the `xi-api-key` header.
- **Speech with timings**: `POST /v1/text-to-speech/{voice_id}/with-timestamps`.
  - Query: `output_format`, default `mp3_44100_128`. `enable_logging=false` turns on zero retention.
  - Body: `text`; `model_id`, default `eleven_multilingual_v2`; `voice_settings` {`stability` 0.5, `similarity_boost`
    0.75, `style` 0, `speed` 1.0, `use_speaker_boost` true}; `seed` (0-4294967295); `previous_text` and
    `next_text`, which keep a line's prosody continuous with its neighbours; `language_code`;
    `apply_text_normalization`.
  - Response: JSON with `audio_base64`, plus `alignment` and `normalized_alignment`, each holding `characters`,
    `character_start_times_seconds` and `character_end_times_seconds`.
- **Speech models**: `eleven_v4` (10,000 characters), `eleven_v4_turbo`, `eleven_v3` (5,000),
  `eleven_multilingual_v2` (10,000), `eleven_flash_v2_5` (40,000).
  - The docs do not say which models return timings. Third-party pages say v3 does.
  - A forced-alignment endpoint exists as a fallback; its contract was not read.
- **Effects**: `POST /v1/sound-generation`.
  - Body: `text`; `duration_seconds` 0.5-30, which picks the length automatically when unset; `prompt_influence`
    0-1, default 0.3, where higher is more literal; `loop`, default false; `model_id`, only
    `eleven_text_to_sound_v2`.
  - The response is the audio itself. WAV at 48 kHz is offered for non-looping effects.
  - Prompt vocabulary from the capability page: impact, whoosh, braam (a big brassy hit), ambience, glitch. A
    sequence of sounds is described in order.
- **Music**: `POST /v1/music`.
  - `prompt` and `composition_plan` are exclusive. `music_length_ms` (3,000-600,000) and `force_instrumental` work
    with a prompt only; `seed` works with a plan only.
  - `model_id`: `music_v1` is the API default; `music_v2` and `music_v2_5` are newer.
  - Other fields: `store_for_inpainting`, `sign_with_c2pa`. Lengths run from 3 s to 5 min.
  - The response is the audio, with a `song-id` header.
  - **music_v1 plan**: {`positive_global_styles`, `negative_global_styles`, `sections` [{`section_name`,
    `positive_local_styles`, `negative_local_styles`, `duration_ms` 3,000-120,000, `lines` (at most 30 of 200
    characters)}]}. It keeps the section durations only while `respect_sections_durations` is true.
  - **music_v2 / v2_5 plan**: {`chunks` [{`text` (section name, lyrics or inline direction), `duration_ms`
    3,000-120,000, `positive_styles` (six or seven for the early chunks), `negative_styles`, `context_adherence`
    low|medium|high, `conditioning_ref`, `condition_strength`}]}. It **always** keeps the section durations.
  - Tempo and key are not separate fields: they go in the styles as text, so the delivered tempo must be measured.
  - Sibling endpoints exist (`detailed`, `stream`, `plan`, `upload`); not read.
- **Stems**: `POST /v1/music/stem-separation` takes a multipart `file` and an optional `stem_variation_id`, and
  returns a ZIP with one file per stem. It can be slow on long files; its variants and billing were not read.
- **Formats by plan**: `mp3_44100_192` needs Creator or above; `pcm_44100` needs Pro or above. `mp3_44100_128`
  works on every plan.

### Credits and prices

| Item | Subscription credits | Pay-as-you-go API price |
|---|---|---|
| Speech, multilingual v2 | 1 credit a character | $0.08 per 1,000 characters |
| Speech, v2.5 flash / turbo | 0.5-1 credit a character | $0.04 per 1,000 characters |
| Speech, v4 / v4 turbo | (not stated) | $0.022 / $0.011 per 1,000 characters (a 72% discount at the time) |
| Effects | 40 credits a second when `duration_seconds` is set; about 200 a generation when it is not | $0.12 a minute |
| Music | about 900 credits a minute | $0.15 a minute |

| Plan | $ a month | Credits a month | Commercial use |
|---|---|---|---|
| Free | 0 | 10,000 | no |
| Starter | 6 | 30,000 | yes, music included |
| Creator | 22 | 121,000 | yes |
| Pro | 99 | 600,000 | yes |
| Scale | 299 | 1,800,000 | yes |
| Business | 990 | 6,000,000 | yes |

- Credits are shared across products. Unused credits roll over for up to two months on paid plans.

### Credits per film (a 20-25 s ghobz film)

| Part | Assumption | Credits |
|---|---|---|
| Music | one 25 s composition; two candidates if the first one's measured grid is unsteady | 375-750 |
| Effects | a palette of 12-16 distinct effects at about 1 s each, `duration_seconds` always set; repeats reuse a file | 480-640 |
| Voice (only if voiced) | about 2.5 words a second, so about 55 words or 330 characters on multilingual v2, plus one retake of two lines | 330-450 |
| **No voice (`bed+sfx`)** | | **about 860-1,400** |
| **Voiced** | | **about 1,200-1,850** |

- A first revision that keeps the story re-uses the cache and pays only for new effects. One that changes the story
  pays again in full.
- **Films a month**: Starter about 20-35, Creator about 65-140, Pro about 320-700.
- **Dollars a film**: about $0.16-0.34 at Creator's credit price ($22 / 121,000 credits). At the pay-as-you-go
  prices: music $0.06-0.13, effects about $0.03, voice about $0.03, so about $0.12-0.19.
- For scale: a designer session costs dollars (shneural's one-shot cost $81 at API prices), so sound is a rounding
  error next to the model. The real limit is the monthly credits.
- **Effects without a duration**: an effect sent without `duration_seconds` costs about 200 credits, five times a
  1 s effect. The client must always send a duration.

### Not yet verified (check before relying on it)

- Which speech models return timings, and the forced-alignment contract.
- Current premade voice ids.
- Whether a music_v2 plan with no `text` lines stays instrumental (`force_instrumental` is prompt-only).
- The stem-separation variants and their cost.
- Whether the API reports remaining credits: `GET /v1/user/subscription` is assumed, not read.
- Whether `previous_text` and `next_text` are billed.

## Sources

- https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps
- https://elevenlabs.io/docs/api-reference/text-to-sound-effects/convert;
  https://elevenlabs.io/docs/overview/capabilities/sound-effects
- https://elevenlabs.io/docs/api-reference/music/compose; https://elevenlabs.io/docs/overview/capabilities/music;
  https://elevenlabs.io/docs/api-reference/music/separate-stems
- https://elevenlabs.io/docs/models
- https://elevenlabs.io/pricing; https://elevenlabs.io/pricing/api; help.elevenlabs.io article 37821528996497 (music
  at 900 credits a minute, read from a search snippet: the page returned 403).
- Rule R8 (ElevenLabs REST as the keyed sound source); [[film-sound-practice]] for how the sound is used.
