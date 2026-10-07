---
id: motion-course-article
type: reference
created: "2026-10-03T00:00:00Z"
consequence: 7
locus: output
summary: Condensed 12-step playbook, image transcriptions, and lists from the Opus 5.5 motion-design course article by @0xMovez (2026-09-27).
scope: repo
status: active
---

# Motion-design course article — condensed

Source: "How to build motion design studio with Opus 5.5 (Full-course)", @0xMovez, 2026-09-27. Part of [[motion-course]]; the 16 verbatim code blocks are split to [[motion-course-code]] and [[motion-course-code-2]].

## Question

What does the article's 12-step playbook say, and what do its own diagrams and lists add?

## Method

Read the full article extract (`article-full.txt`, built from api.fxtwitter.com/status/2104216919033192746, since deleted; re-fetch from that URL) and its 14 diagrams plus cover; each image was viewed and transcribed. `Lnnn` cites an extract line; `Mnnnnnnnnnnnnnnnnnnn` an image id (URL under `.tweet.article.media_entities`). The article has 12 numbered steps in 4 parts; **article position** is where content sits, **true step** is the step it belongs to — several are misplaced (see Caveats).

## Findings

### Thesis and numbers

Prompt = 10% of the video, harness = 90% (L3). Sep 22 2026, Opus 5.5 ships; timeline fills with code-rendered showreels/launch/music videos/history films (L6-7). Range: 30-word prompts vs. a 9,500-char director's brief + skills + 2 API keys + 12h autonomous run (L9-11). Thariq (Claude Code team): a "one-shot" post really ran ~10k chars w/ skills, examples, keys (L12). Default effort = medium; every viral one-shot ran xhigh/max (L91). Effort ladder (M2104198466305974273, full table under 12 Ship/Thesis below): L1 one-liner ~150c/15-50min; L2 brand reel ~350c/30-45min; L3 state spec 1.5-3k c/~1-2h; L4 director brief 9.5-19k c/6-12h (Donald ≈9,500c, @pradeepXkapoor's "Pip" ≈19,000c, L419). @mablesjoseph: 163 model calls, ~7h, not one-shot (L498, L522).

### The 12 steps, condensed

**01 Pixels** — Claim: Opus writes `draw(t)`/`seek(t)`, not video (L28-29). Tech: headless browser calls it 900×/15s@60fps, ffmpeg stitches (L30-31). Ex: Tommy Rossi — one-shots default to route A: `index.html`, `eval(seek)`, Playwright, ffmpeg (L33).

**02 Setup** — Claim: only agent+shell renders/listens/looks at its own frames (L62-63). Rule: `CLAUDE.md` read every run (L65). Nums: medium=fixes/re-renders, xhigh=new films, max=launch-critical first 3s (L91-92).

**03 One-liner** — Claim: 4/9 posts used the same sentence (L97). Rules: "résumé showreel"=genre, "incredible designer"=subject=model, "15s"=6-8 shots, "go all out"=effort multiplier (L99-102). Caveats: "brief contagion" (L148); "tests the engine, never the idea" (L151).

**04 Brand** — Ex: Tony Dinh — TypingMind reel <30min vs $1,000+ agency; 3 lines: URL + real screenshot/logo/assets + "must have music" (L155-161). Rob Hallam — 2nd reel (ad) faster, pipeline reused; 1 session/brand (L157-158). achxvi — Pocketsflow+ElevenLabs mascot, now a paid service (L200-201). Rule: keys in `.env`, never in a screenshot-able prompt (L201).

**05 Reference** — Claim: no ref → centered/gradient/fade default (L205). Rule (Rexan Wong): naming a style > describing one (L206); 3 types — frame/video/library (L209-211); sources: whatships.com, Dribbble, competitors (L212); give look+constraints, let Opus pick the technique (L215-216). Ex: Pleometric — TikTok piece from 1 frame; PC-98-gallery piece (L207-208).

**06 Spec** — Claim: week's top prompt was an XML spec, not a one-liner (L253). Tech: one shape never cut — morphs across states, cursor drives change, last frame = first (loop) (L256). Ex: @twoclipping UI morph, 907K views/19K bookmarks (L254,287); @verbove MakerMap on real data (L290); NFT_Chen editor film (L293).

**07 Engine** — Claim: route A = 2 files — page paints on demand, renderer pipes to ffmpeg (L300). Tech: QA cmds — contact sheet, strip, phone test, loop check, md5 determinism (L303-318). Routes (table): A code-drawn (zero deps / weak: characters); B framework (reusable / weak: Remotion license>3 people); C mixed (physics+faces / weak: API cost, less determinism); D footage (real face/voice / weak: needs clean footage).

**08 Springs** — Claim: expensive motion has mass — accelerates, overshoots, settles (L326). Tech: closed-form = pure fn of time; multi-target = sum of springs, never restart (L327-329). Profiles: Snappy k320/d30, Default k170/d26, Heavy k90/d20, Playful k220/d14 (L391-394).

**09 Sound** — Claim: Rob Hallam assumed audio was post-added — wasn't (L400). Tech: supplied track→measure beats; none→synth on same timeline (L404). Ex: @oozn Steve Jobs film, Remotion+SVG, 23 transitions, 120 BPM (L408-409); Vox "small print", Python music, HyperFrames render (L412).

**10 Overnight** — Ex: Donald — 5min dictation→142s video, 2.1M views, ~9.5k-char brief (L418-419,445). Brief skeleton (9 parts, L420-428): logline / references / tools&keys / character bible / beat sheet / on-screen text / workflow gates / critique loop / deliverables. Tech: generate-then-trace — Seedance 2.5 base shots, Opus redraws in JS on top (L443-444). Ex: John Heibel's PDoom (1.1K★) — ANIMATION_GUIDE.md + STORYBOARD.md, 9 subagent chapters (L491).

**11 Critique** — Claim: Opus reads its own renders — separates viral from "mid" (L496). Ex: @mablesjoseph 163 calls/~7h, not one-shot (L498,522); Drew 1.7M views, visible cleanup (L498,519). "Iteration is the method" (L498).

**12 Ship** — Claim: 3 moves = business: multi-format export, package as skill, sell it (L564). Tech: `layout(w,h)`, render 9:16/1:1/16:9 parallel, reframe not crop (L566-567). Ex: achxvi offer (music/mascot/features/offer/language/3 edits, L603); 38s film in 45min, resold (L606); Tony Dinh's $1,000 anchors price (L604).

### The 16 code blocks

Verbatim in [[motion-course-code]] (CODE 1-8) and [[motion-course-code-2]] (CODE 9-16). Each is labeled with its article position and the step it truly belongs to:
CODE 1 one-shot showreel prompt (03) · CODE 2 brand reel template (04) · CODE 3 `lib/motion.js` springs (08) · CODE 4 setup commands (02) · CODE 5 `beats.py` (09) · CODE 6 `render.mjs` (07) · CODE 7 reference-extraction prompt (05) · CODE 8 four one-liner variants (03) · CODE 9 house-rules `CLAUDE.md` (02) · CODE 10 QA ffmpeg commands (07) · CODE 11 single-file `seek(t)` demo with `spring()`/`rng()` (08) · CODE 12 critique prompt (11) · CODE 13 director-brief template (10) · CODE 14 Remotion/HyperFrames commands (07) · CODE 15 XML UI-morph spec (06) · CODE 16 `motion-reel` SKILL.md (12).

### The 14 images + cover

All 14 are the article's own diagrams, not tweet screenshots; files were not kept. Tag = (article pos → true step).

- **cover.jpg** — orange blocky mascot holding a purple sine-wave icon; "Opus 5.5 /motion-graphic — FULL COURSE".
- **M2104203516134768640** (01→05) L58 — `ref.mp4→frames/→style_guide.md→shotlist.md→your OK then code`; "REJECT = REWRITE THE SHOT LIST, NOT THE CODE."
- **M2104212197295501312** (01→12) L59 — "Reframe type and UI per format, never crop": 1 timeline → 9:16 Reels/TikTok, 1:1 X feed, 16:9 YouTube/site mockups.
- **M2104211366902956032** (03→06) L150 — Loop: render stills→contact sheet→score 1-10 (7 axes)→fix worst 3→ship; "repeat until every score is 8+".
- **M2104201144847175682** (05→03) L213 — One-liner anatomy: Duration(6-8 shots)/Subject=model(no facts to get wrong)/Genre(fast cuts, best first)/Effort multiplier.
- **M2104206128368246784** (05→07) L230 — `index.html(seek)→render.mjs(t=i/fps×sub)→ffmpeg(tmix→60fps)→silent.mp4+score.wav→final`.
- **M2104199449727705088** (06→01/07) L255 — Brief→Opus writes code→4 routes→MP4: A code-drawn(Canvas/SVG/p5.brush+headless Chrome), B framework(Remotion|HyperFrames), C mixed(image+video models, composited), D footage edit(cuts/captions/b-roll/PiP).
- **M2104211017664249856** (06→10) L294 — Director→`STORYBOARD.md`/`ANIMATION_GUIDE.md`→9 subagents(`ch01.js`...`ch09.js`)→stitch+render(`timeline.js`).
- **M2104208284504694784** (06→09) L296 — 3 lanes @120BPM: Music/SFX/Picture; "downbeats carry scene changes, beats carry SFX, onset peaks place hits".
- **M2104210357908590592** (07→10) L322 — "Generate, then trace — the Donald pipeline": 5-min voice→Opus(director)→character sheets(fal)/base shots(Seedance 2.5, lip sync)/sound(ElevenLabs)→JS trace layer→142s video; "viewers only see the JS layer".
- **M2104199903425511425** (07→07, correct) L323 — Table Route/Best-for/Strength/Weakness: A code-drawn(showreels,loops/zero deps,editable/weak:characters+photoreal); B framework(explainers,series/reusable,skill-guided/weak:Remotion license>3); C mixed(music videos,character stories/physics+faces/weak:API spend,less determinism); D footage(talking heads,reels/real face+voice/weak:needs clean footage).
- **M2104204628308971521** (11→06) L520 — 120BPM/0.5s-per-beat timeline, 0-16s: logo→CTA(2s)→email(4s)→loader(6s)→check(8s)→card(10s)→chart(12s)→⌘K(14s)→logo(16s).
- **M2104207479068311552** (12→08) L568 — Spring step-response graph 0-1.2s: Snappy k320/d30(fastest,slight overshoot), Playful k220/d14(biggest overshoot ~1.25), Default k170/d26, Heavy k90/d20(slowest, none).
- **M2104198466305974273** (12→10) L605 — Bar chart, prompt size vs run time: L1 ~150c/15-50min(Stephan,Himanshu,Rob); L2 ~350c/30-45min(Tony Dinh,achxvi); L3 1.5-3k c/1-2h(twoclipping,verbove); L4 9.5-19k c/6-12h(Donald,Pradeep,Pleometric).
- **M2104204488177221632** (end→06) L617 — "One element, never cut" morph chain: button(Get started)→loader(spinner)→check→island/player→chart→palette(⌘K); "last state morphs back into button, seamless loop".

### Lists the article gives

Named sources and claims:

| Source | Claim / result |
|---|---|
| Thariq | one-shot post ≈10k chars w/ skills+keys (L12) |
| Tommy Rossi | one-shots default to route A, zero deps (L33) |
| Tony Dinh | TypingMind reel <30min vs $1,000+ agency; 3 extra lines (L155) |
| Rob Hallam | 2nd reel faster, reused pipeline; audio thought post-added—wasn't (L157) |
| Rexan Wong | naming a style beats describing one (L206) |
| Pleometric | TikTok piece from 1 frame; PC-98 gallery; re-ran Donald's brief (L207) |
| @kloss_xyz | 90s piano reel, sound-bar pattern (L234) |
| @1littlecoder | anti-slop guardrail prompt (L239) |
| @sonnylazuardi | story-mode prompt (L243) |
| @twoclipping | UI morph, 907K views/19K bookmarks, XML template (L254) |
| @verbove | MakerMap film, same XML spec, real data (L290) |
| NFT_Chen | editor film, UI-as-film-set (L293) |
| @oozn | Steve Jobs film: Remotion+SVG, 23 transitions, 120 BPM (L408) |
| Vox | "small print": Python music, HyperFrames render (L412) |
| Donald | 142s video, 2.1M views, ~9.5k-char brief (L418) |
| @pradeepXkapoor | "Pip" robot film, 19,000-char brief (L419) |
| John Heibel | PDoom repo, 1.1K★, subagent pattern (L491) |
| @mablesjoseph | watercolor short, 163 calls, ~7h (L522) |
| Drew | launch-day piece, 1.7M views, visible cleanup (L519) |
| achxvi | Pocketsflow+ElevenLabs mascot; now sells as a service (L200) |
| buildwithhanif | claude-animation-skill plugin (L118) |

Repos to clone (L609-616; full notes in [[motion-course-repos]]): music video JohnHeibel/PDoomVideo; starter JohnHeibel/ClaudeAnimationBase; node canvas buildwithhanif/claude-animation-skill; framework (html) heygen-com/hyperframes; framework (react) remotion.dev/docs/ai/skills; long form WinterArc21/Battle-of-Austerlitz-Film; prompt library guanmo-ai/awesome-ai-motion; dataset athemeroy/awesome-opus-5-5-videos.

Banned looks (CODE 9, 15, 16): centered title on gradient; everything fading in; corner labels/frame borders; glow on UI chrome; generic particle bursts; bouncy easing; gradients on UI chrome; dead time.

Critique criteria (CODE 9/12/13, union): hook in first 2s; readability at 360px; motion quality; variety (new thing every 2-4s); composition; depth; brand accuracy; sound sync; polish.

Workflow gates (CODE 13, L426): plan (style_guide.md+shotlist.md, wait ≤10min) → stills+contact sheet+critique → animatic 960x540 w/ placeholder audio → full animation+polish+sound+final render → subagents per chapter w/ ANIMATION_GUIDE.md first.

Effort guidance: "go all out" stacks as a multiplier on xhigh/max (L102); CODE 4 sets `/model` → Opus 5.5, xhigh for one-shots, max for flagship pieces (see Thesis and 02 Setup above for the ladder).

### Article's own caveats

- "Brief contagion": identical one-liners produce reels that rhyme (athemeroy's dataset, L148).
- "A one-liner tests the engine. It never tests the idea, because it doesn't contain one." (L151)
- One-shot output "skipped Remotion and HyperFrames even when available. If you want a framework, say so explicitly." (L57)
- Donald's brief re-run (PC-98 gallery) = "a mixed flow with bugs left in to keep it one-pass" (L488).
- Rob Hallam assumed his audio was post-added; it was synthesized in the same run (L400).
- @mablesjoseph/Drew counter "one prompt" claims: 163 calls/~7h, visible cleanup — "iteration is the method, not a failure" (L498, L519, L522).
- Route weaknesses (M2104199903425511425): code-drawn weak on characters/photoreal; framework needs a license above 3 people; mixed costs API spend + loses determinism; footage needs clean raw footage.
- Layout mismatch: most code blocks/images sit under the wrong step heading; lists above tag each (article pos → true step).

## Sources

- https://x.com/0xMovez/status/2104216919033192746 (article, deleted; re-fetch via api.fxtwitter.com/status/2104216919033192746).
- [[motion-course]], [[motion-course-code]], [[motion-course-code-2]], [[motion-course-prompts]], [[motion-course-showcase]].

## Date

Gathered 2026-10-03; condensed 2026-10-06 for the format 4 wiki.
