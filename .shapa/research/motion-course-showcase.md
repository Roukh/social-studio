---
id: motion-course-showcase
type: reference
created: "2026-10-03T01:00:00Z"
consequence: 7
locus: output
summary: The motion-course article's 21 embedded posts, measured (duration, fps, LUFS, cuts, look, hook, audio, tooling), plus aggregates over 17 Opus videos.
scope: repo
status: active
---

# Motion-course showcase: the 21 embedded posts, measured

Each post in the [[motion-course]] article was fetched and its video measured on 2026-10-03.

## Question

What do the showcased videos actually contain (duration, fps, loudness, cuts, look, hook, audio, tooling), and how do they aggregate across the 17 made by Opus?

## Method

Posts fetched via api.fxtwitter.com. Each video measured with ffprobe (format), `ebur128` (loudness) and `select='gt(scene,0.3)'` (cuts); a 1fps contact sheet, 3s strip and spectrogram were each viewed. Audio type read from the spectrogram; nobody listened. Verbatim prompts: [[motion-course-prompts]].

## Findings

### Read this first: the captions do not match the embeds

Several article "Shows: ..." captions sit beside a different post than described: "TypingMind reel" beside @pleometric 2102572941699354900; "MakerMap" beside @achxvi 2103918792845963545; "UI morph 907K" beside @devteamdrew 2102436464323661880; "Steve Jobs" beside @mablesjoseph; "Small print" beside @stephanlivera; "163 calls watercolor" beside @__morse. This note keys everything on post id and actual content, not captions.

### Master table

Abbreviations: **R** route (A = code-drawn, B = framework, M = mixed with a video/image model, F = footage); **P** prompt status (V = verbatim, p = paraphrase only, - = none); **\*** not made by Opus, excluded from aggregates.

| # | Post | Handle | What | Views | Bkmk | Dur s | Res @fps | LUFS | Cuts | /10s | R | P |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2102801469976248500 | donaldjewkes | text: the 9.5k-char Claude Pop brief (no video; quotes a 156.6 s ref cartoon\*) | 588K | 5.0K | — | — | — | — | — | — | V |
| 2 | 2103875898349088830 | robj3d3 | 15 s SuperX ad from the one-liner, xhigh | 139K | 1.1K | 15.0 | 2160p@60 | -14.1 | 6 | 4.0 | A | V |
| 3 | 2102681172367323300 | NFT_Chen | fake editor app; mascot edits its own clip | 445K | 1.2K | 30.0 | 1080p@30 | -12.3 | 0 | 0 | A | – |
| 4 | 2102572941699354900 | pleometric | "3:07am TikTok feed" 9:16 loop | 410K | 1.3K | 47.0 | 9:16@30 | -14.4 | 3 | 0.6 | A | p |
| 5 | 2102801274173587569 | donaldjewkes | Claude Pop music video, 12 h run | **3.82M** | 11.1K | 141.5 | 1080p@30 | -15.6 | 98 | 6.9 | M | V (#1) |
| 6 | 2103482545111232946 | oozn | Steve Jobs life, rig plus walk cycle | 19K | 275 | 119.1 | 1080p@30 | -13.7 | 7 | 0.6 | B | p |
| 7 | 2102436464323661880 | devteamdrew | brick mascot bookends a science montage | 1.82M | 4.2K | 31.9 | 1080p@24 | -13.9 | 11 | 3.4 | A | – |
| 8 | 2103918792845963545 | achxvi | 15 s Pocketsflow ad, ElevenLabs talking mascot | 1.12M | 8.0K | 15.1 | 1080p@60 | -14.3 | 1 | 0.7 | A | V |
| 9 | 2103483957266268381 | verbove | MakerMap one-shape morph, real data, 1:1 | 17K | 358 | 20.1 | 1440²@60 | -14.6 | 0 | 0 | A | V |
| 10 | 2102435511222890900 | claudeai | official Opus 5.5 launch\*: macro-footage montage | 28.0M | 13.2K | 20.1 | 1080p@25 | -16.4 | 32 | 16.0 | F | – |
| 11 | 2103495232637882858 | himanshutwtxs | one-liner showreel, animation principles, Max | 286K | 1.7K | 15.1 | 1080p@30 | -11.7 | 7 | 4.7 | A | V |
| 12 | 2103707054108299437 | rexan_wong | screen recording of whatships.com\* plus a 6-step thread | 615K | **18.0K** | 11.0 | — | none | 2 | — | — | n/a |
| 13 | 2103465246014746943 | mablesjoseph | watercolor short; 163 calls, ~$34, ~6¾ h | 12K | 140 | 45.7 | 1080p@24 | -14.4 | 1 | 0.2 | A | – |
| 14 | 2103315922098470926 | stephanlivera | the one-liner showreel, Max | **2.24M** | 13.0K | 15.1 | 1080p@60 | -13.1 | 9 | 6.0 | A | V |
| 15 | 2102531681450119426 | Voxyz_ai | "Small print" HyperFrames short, Python music | 125K | 807 | 29.0 | 2160²@24 | -15.2 | 0 | 0 | B | – |
| 16 | 2103273003555402193 | twoclipping | one-shape UI morph loop plus XML template | 1.03M | **20.0K** | 14.0 | 1440²@60 | -14.1 | 0 | 0 | A | V |
| 17 | 2104014659615392078 | achxvi | 38 s Pocketsflow explainer, 45 min, sold as a service | 65K | 557 | 38.6 | 1080p@60 | -14.4 | 1 | 0.3 | A | – |
| 18 | 2103703135902740699 | tdinh_me | 15 s TypingMind reel; the "$1,000 agency" anchor | 193K | 986 | 15.0 | 1080p@60 | -12.2 | 0 | 0 | A | – |
| 19 | 2102870353781641416 | trq212 | text: "the prompt: 10k characters…" | 263K | 1.0K | — | — | — | — | — | — | — |
| 20 | 2103485566570369333 | __morse | twoclipping prompt re-run, "more colorful" | 27K | 304 | 15.4 | 1440²@60 | -20.7 | 0 | 0 | A | V (#16) |
| 21 | 2103082510607610023 | pleometric | P(Doom) PC-98 music video; re-run of Donald's brief | 733K | 4.0K | 156.7 | 1080p@30 | -15.5 | 168 | 10.7 | M | V (#1) |

### Aggregates over the 17 Opus-made videos

- **Audio: 17/17 have an audio track.** Loudness runs -11.7 to -20.7 LUFS; 15/17 sit between -12 and -16.
- **Duration:** median 29.0 s; range 14.0-156.7 s. Six are 15 s ±0.4. Three run 119-157 s: two music videos and one biography.
- **Two cut families:** continuous/morph, 0-0.7 cuts per 10s, 11 videos; montage, 3.4-10.7 cuts per 10s, 6 videos. Nothing sits between them.
- **fps:** 60 in 8 videos (every UI/product piece except NFT_Chen), 30 in 6, 24 in 3.
- **Route:** code-drawn (A/B) in 15/17; mixed (Seedance/fal base plus JS trace) in 2 (Donald, Pleometric). Matches the athemeroy dataset, where 152/168 curated cases are code-rendered and 8 used an external video model ([[motion-course-repos]]).
- **Top decile by views:** #5 Donald, 3.82M, 141.5s, 98 cuts (6.9/10s), mixed route, supplied song. #14 Stephan, 2.24M, a 15s one-liner at Max effort, 6.0 cuts/10s. Floor (median views of the 17): 286K.
- **Top decile by bookmarks:** #16 twoclipping, 20.0K - a template post, the XML spec ships in the post. #12 Rexan, 18.0K - a workflow thread with no film. The template and how-to posts are the ones saved.

### Per post: look, hook, audio, tooling (terse)

- **#2 robj3d3.** B&W glitch type ("Post. Hope. Refresh. Repeat."), redrawn UI, bar chart; hook "Post." slams in. Bare one-liner prompt, yet self-branded - context must have supplied the brand.
- **#3 NFT_Chen.** Beige code-drawn editor UI; mascot drags clips, "SNIP!", joke export filename. Hook: empty editor; UI clicks/whooshes ~1/s. No prompt published.
- **#4 pleometric.** Pastel kawaii bedroom; sun character scrolls mini-game parodies. Hook "3:07am / no new messages", loops to bedroom.
- **#5 donaldjewkes.** Manga/screentone panels, meme-dense AI-acceleration story. Hook: eye close-up + date. Tooling: 12h run, Seedance 2.5+fal bases, JS trace overlay, ElevenLabs sound design.
- **#6 oozn.** Flat silhouette rig, procedural walk, year-stamped scenes. Hook: tiny figure, "Adopted at birth."; Node-synth score, widest LRA (10.4). Tooling: Remotion+React+SVG, ~8.7k lines, 23 transitions, 3,570 frames, <5min render.
- **#7 devteamdrew.** Cream walk-cycle mascot bookends glossy science vignettes. Hook: mascot on empty field; score hit-synced to cuts. No prompt published.
- **#8 achxvi.** Halftone mascot narrates a storefront tour. Hook: slow "pss" speech bubble; syllable-rate pulses. Prompt: one-liner + ElevenLabs-key placeholder + "character talks about pocketsflow".
- **#9 verbove.** One pill morphs button→search→profile→dot-globe (3,393 makers)→stats→RSVP→logo, 0 cuts, cursor-driven, loops. UI-click SFX only. Tooling: canvas `draw(t)`, closed-form springs, 6-subframe blur@60fps, 3 ratios parallel.
- **#10 claudeai** (excluded). Macro-photography montage, 0.61s avg shot. Brand bar, not Opus.
- **#11 himanshutwtxs.** Flat diagrams, marker annotations, bouncing-ball squash/stretch, ease graphs, radial loader. Hook: ball drops onto a baseline; music aligns with title cuts.
- **#12 rexan_wong.** A 6-step thread, no film: name refs from whatships.com; install HyperFrames/Remotion; use real UI from 21st.dev; feed assets+braindump for storyboard variants; one still per scene; direct with camera notes.
- **#13 mablesjoseph.** Watercolor/gouache, warm-to-cool arc, slow pan; character+lantern desk→street→rooftop→sky. Hook: iris opens from a dot. 62.7M tokens (96% cache), 163 calls, ~$34.
- **#14 stephanlivera.** Black/red Swiss geometric: radial bursts, huge "CLAUDE", ranked-list UI, wireframe globe. Hook: pulsing dot bursts. Same prompt as #11, unrelated look - variance is high.
- **#15 Voxyz_ai.** Cream paper-collage desktop of notes; redacted fragment→jar; night constellation; dawn loop. Hook: notes flying, reads "AI inbox". Tooling: HyperFrames, one `index.html`, zero image assets.
- **#16 twoclipping.** Warm-gray canvas, B&W, Geist; one shape morphs 13 states; camera zooms to fill. Hook: a lone "Generate" pill (withhold); seamless loop; UI sounds on measured peaks. Tooling: `window.seek(t)`, Playwright 4 subframes + tmix.
- **#17 achxvi.** Halftone mascot hook, hard cut at 15.3s into a saturated UI tour. Loud bed, possibly VO. 45min; sold as a service.
- **#18 tdinh_me.** Dark navy; continuous push/pan over floating chat-UI windows; kinetic type; pricing/trust badges. Hook: chat input mid-typing; loud bed.
- **#20 __morse.** The #16 structure recoloured into saturated cards. Reuses the #16 track at -20.7 LUFS, quiet; code published as a gist.
- **#21 pleometric.** PC-9801 boot/CRT UI; twin-tail protagonist; neon lyric cards; Shoggoth/paperclip memes. Hook: "1MB OK" memory-check screen; mastered song follows its sections. Donald's brief + a different gallery produced a different film.

### Hook patterns seen (first 2s)

Text slam (#2); graphic burst (#14); in-product typing (#18); a withheld, calm UI element (#9, #16); mood/atmosphere (#4, #13); close-up plus date (#5); period boot screen (#21); a principle demo (#11); a world establishing itself (#15); a lone mascot (#7, #8, #17). None open on a centered title over a gradient.

## Sources

- api.fxtwitter.com, 2026-10-03 (post ids in the master table); per-video ffprobe/`ebur128`/scene-cut measurements, same date.
- [[motion-course]], [[motion-course-prompts]], [[motion-course-repos]].

## Date

Gathered 2026-10-03; condensed 2026-10-06 for the format 4 wiki.
