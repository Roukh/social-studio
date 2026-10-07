---
id: motion-course-prompts
type: reference
created: "2026-10-03T01:00:00Z"
consequence: 5
locus: output
summary: Condensed appendix of motion-course prompts by level (L1-L4) plus PDoom's ANIMATION_GUIDE and claude-animation-skill sound.md rules.
scope: repo
status: active
---

# Motion-course prompts, condensed

Metadata and structural moves for the prompts behind [[motion-course-showcase]]'s posts, by size tier. Canonical templates (CODE 1, 2, 8, 13, 15, 16) are verbatim in [[motion-course-code]] / motion-course-code-2 and not repeated here.

## Question

What length, effort and structural moves did each tier (L1 one-liner to L4 director brief) use, and what do PDoom's build rules and claude-animation-skill's sound rules specify?

## Method

Post text via api.fxtwitter.com, 2026-10-03. Repo prompts from guanmo-ai/awesome-ai-motion@2ff3da3f `prompts/` (excludes THIRD_PARTY.md prompts); JohnHeibel/PDoomVideo (no licence, read only); buildwithhanif/claude-animation-skill (MIT, @4ddb8c80).

## Findings

### L4: director brief (9.5k-19k chars)
- @donaldjewkes 2102801469976248500 (~9,554 chars; 588K views, 5.0K bookmarks): brief behind the 141.5s/3.82M-view video (2102801274173587569, CODE 13). Moves: hands over a reference MP4+repo, full freedom but warns off Pixar/"GPT slop", K-pop as loose anchor, a fal character sheet before any video gen, Seedance 2.5 shots cut to song timing then a JS trace overlay ("shoot first, draw over" - only overlay shows), a lip-sync verification loop, Claude Max 100%-usage budget, ~$2k fal credits. Re-run by @pleometric with his own PC-98 gallery (2103082510607610023); @anjmaxx's later brief shares 87.0% of five-word sequences with it (athemeroy dataset).
- @pradeepXkapoor "Pip" robot film (~19,000 chars): not reproduced - guanmo-ai links the source reply without redistributing it, fxtwitter has no replies endpoint. Reported to cover rigging, 12 world styles, sound/delivery checks.

### L3: state specs, XML (1.5k-3k chars)
- @twoclipping, one-shape UI morph loop, 2103273003555402193 (1.03M views, 20K bookmarks, CODE 15). Tags `<inputs><direction><structure><build><gotchas><start>`. Moves: closed-form spring-sum per retarget (no carried state), tab/toggle edges on separate springs, numpy beat grid, Playwright at 4 subframes blended with ffmpeg `tmix` at 60fps, one-frame-per-beat contact sheet gate. Re-run verbatim by @__morse (2103485566570369333), "make the video more colorful"; output as gist remorses/3d467b50a0519ef7859823046dc9c427.
- @twoclipping, beat-synced "Hooklab" ad, real footage, 2102554209166000267. Adds: real clips to 30fps JPEG sequences via ffmpeg, SFX on measured peaks, `loudnorm` to -14 LUFS, 3 subframes at t±1/240s, a `preserve-3d`+opacity gotcha (fade the wrapper, not the face).
- @verbove, MakerMap product journey, 2103483957266268381 (17K views, 358 bookmarks). Same skeleton; real data only, contact sheet gate, 6-subframe blur at 60fps, H.264/yuv420p exported to all ratios in parallel.

### L2: brand reel (~350 chars)
- @achxvi, Pocketsflow talking-mascot ad, 2103918792845963545 (1.12M views, 8.0K bookmarks, CODE 2). Casual register ("go all out", "LFG"); a joke ElevenLabs key placeholder, not a credential; asks only for a character to talk about the product.
- Not reachable (prompt in an X reply, absent from both repos): @tdinh_me TypingMind reel, 2103703135902700699 - article says it adds 3 lines: product URL, "use actual product screenshot, logo, assets", "must have music". @achxvi 38s Pocketsflow explainer + service offer, 2104014659615392078.

### L1: one-liners (~150 chars)
- Shared one-liner (CODE 1), 3 handles, unrelated outputs: @stephanlivera 2103315922098470926 (Max, 2.24M views, 13.0K bookmarks), @robj3d3 2103875898349088830 (xhigh, 139K views, 1.1K bookmarks; output branded for his own product though the prompt names none), @himanshutwtxs 2103495232637882858 (Max, 286K views, 1.7K bookmarks).
- @kloss_xyz, 90s piano reel, 2103557735086428547 (CODE 8 variant): adds 16:9, 90s, "s-tier sound design, no synth", original viral piano score, 1080p mp4 export.
- Paraphrase only: @oozn Steve Jobs biography, 2103482545111232946 (19K views, 275 bookmarks) - Remotion+React+SVG, ~8.7k lines, procedural-walk rig, 23 transitions, Node-synthesized 120 BPM score, 3,570 frames, <5min render. @pleometric "3:07am TikTok feed" loop, 2102572941699354900.
- No prompt published: @NFT_Chen 2102681172367323300; @devteamdrew 2102436464323661880; @mablesjoseph 2103465246014746943 (163 calls, 62.7M tokens, ~$34, ~6¾h); @Voxyz_ai 2102531681450119426 (Python-synthesized music, no images).
- Not found anywhere: @1littlecoder's anti-slop prompt, @sonnylazuardi's story prompt - only paraphrases survive, in motion-course-article CODE 8.

### PDoomVideo ANIMATION_GUIDE.md (no licence - read only, condensed from 11,560 chars)
- Renders a 156.6s watercolor (p5.brush) music video offline in headless Chrome: quality over speed, within a budget.
- Canvas 1920x1080, y-down. Tempo 88 BPM (beat = 0.682s) via `bpOf(t)`.
- Performance budget: aim <=2.5s/frame, never exceed 4s; prefer fewer, bigger shapes.
- Each shot fn is a pure function of `(t, localTime, duration)`: no cross-frame state, no `Math.random()` - use `hash(i)` for stable randomness, `jit(a)` (reseeded 12x/s) for hand-drawn "boil".
- Agents edit only their own chapter file; shared files are report-only.
- Check: `node render.mjs --sheet=<times> --cols=3 --w=640 --out=...jpg` (contact sheet) or `--stills=<times>`; verify first/last frame of each shot, motion across times, transitions, nothing hidden under the karaoke band.

### claude-animation-skill references/sound.md (MIT, buildwithhanif@4ddb8c80)
- Cue time = contact frame minus ~0.03s; late reads broken, slightly early reads synced.
- `scripts/sound.mjs` synthesizes all effects (no sample library), mixes on cue times over an optional bed, two-pass loudnorm to -16 LUFS/-1.5 dBTP default.
- Per-cue: vol, dur, pan (-1..1), pitch multiplier 0.9-1.3 (repeats don't sound pasted); footsteps ~1 per 0.1s walking.
- `--bed-at 2.0` delays the bed so the hook plays on typing/clicks alone first.
- `scripts/chiptune.mjs` places sections on absolute times, e.g. `--sections "level:0-13.8,alarm:13.8-15.4,..."`.
- `scripts/music.mjs` makes a ukulele bed (C-G-Am-F); `--quiet a-b,c-d` holds a chord under serious beats.
- Continuous "pencil scratch" tied to ink laid per frame: built and rejected, it competes with everything - draw-on is silent, only contacts sound.
- Mix: bed under narration ~-22dB relative; no narration: bed ~0.5, SFX 0.3-0.6.
- Final check: `ffmpeg -i final.mp4 -af loudnorm=print_format=summary -f null -` - integrated near target, true peak <= -1 dBTP.

## Sources

- api.fxtwitter.com, 2026-10-03 (post ids above).
- guanmo-ai/awesome-ai-motion@2ff3da3f `prompts/`, `THIRD_PARTY.md`.
- JohnHeibel/PDoomVideo `ANIMATION_GUIDE.md`@fa546a38 (no licence).
- buildwithhanif/claude-animation-skill `references/sound.md`@4ddb8c80 (MIT).
- [[motion-course-showcase]], [[motion-course-code]], motion-course-code-2, [[motion-course-repos]].

## Date

Gathered 2026-10-03; condensed 2026-10-06 for the format 4 wiki.
