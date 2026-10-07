---
id: motion-course-code-2
type: reference
created: "2026-10-03T01:00:00Z"
consequence: 7
locus: output
summary: Motion-course article's code blocks, part 2 of 2 (CODE 9-16) - house rules, QA ffmpeg, seek(t) spring demo, critique prompt, director brief, XML spec, SKILL.md.
scope: repo
status: active
---

# Motion-course code blocks, verbatim (part 2 of 2: CODE 9-16)

These are the builder's copy of the second 8 of 16 code and prompt templates in the motion-course article, split from [[motion-course-article]], which holds the steps they belong to. The first 8 (CODE 1-8) are in [[motion-course-code]]. The entry note is [[motion-course]]. They are the article author's own templates, published in the article. Line refs such as `L91` point into the article extract described in [[motion-course-article]].

## Question

What is the exact, verbatim text of the motion-course article's code and prompt templates CODE 9 through CODE 16?

## Method

Extracted verbatim from the article's full text extract (`article-full.txt`); no paraphrasing inside any code fence. Each block is labeled with its article position and the step it truly belongs to.

## Findings

Each heading: `CODE n — label (article position → true step)`.

### CODE 9 — house-rules CLAUDE.md: render contract, look, sound, critique loop (pos: 06 → true: 02)
```markdown
# Motion studio rules

## Render contract
- Every film is a pure function of time: `window.seek(t)` paints frame t.
- No CSS transitions, no setTimeout, no requestAnimationFrame in render mode,
  no state carried between frames. Seeded noise only (mulberry32), never Math.random.
- Render with `node render.mjs`, encode H.264 yuv420p, CRF 16.

## Look
- Banned defaults: centered title on gradient, everything fading in,
  corner labels and frame borders, glow on UI chrome, generic particle bursts.
- One display face, one UI face. One accent color unless the brief says otherwise.
- Every 2 to 4 seconds something new must happen on screen.

## Sound
- Score and SFX are synthesized in code unless a track is supplied.
- Place hits on the measured beat grid (beats.json). Loudness -14 LUFS.

## Loop before you show me anything
1. Render one frame per beat as a contact sheet and LOOK at it.
2. Score it 1-10 on: hook in first 2s, readability at phone size,
   motion quality, variety, brand accuracy, sound sync.
3. Fix the 3 worst problems. Repeat until every score is 8+.
4. Only then do the full render.
```

### CODE 10 — contact-sheet / QA ffmpeg commands (pos: 07 = true, correct)
```bash
# Contact sheet: 2 frames per second, 6 across
ffmpeg -i out/final.mp4 -vf "fps=2,scale=270:-1,tile=6x5" -frames:v 1 out/contact.png

# Strip: 12 consecutive frames around a fast action at 4.2s (catch pops and overlaps)
ffmpeg -ss 4.1 -i out/final.mp4 -vf "scale=320:-1,tile=12x1" -frames:v 1 out/strip.png

# Phone test: how it reads at 360 px wide
ffmpeg -i out/final.mp4 -vf "fps=1,scale=360:-1,tile=5x3" -frames:v 1 out/phone.png

# Loop check: play it twice back to back and watch the seam
ffmpeg -stream_loop 1 -i out/final.mp4 -c copy out/loop_check.mp4

# Determinism check: frame 300 rendered twice must hash the same
node render.mjs --dur 5 --fps 60 --sub 1 && md5 out/silent.mp4   # run twice, compare
```

### CODE 11 — single-file HTML/JS seek(t) demo: closed-form spring() + seeded rng() (pos: 08 = true, correct; also demos 07's engine)
```html
<style>html,body{margin:0;background:#141413}canvas{display:block}</style>
<canvas id="c" width="1080" height="1920"></canvas>
<script>
const W = 1080, H = 1920, DUR = 15;
const g = document.getElementById('c').getContext('2d');
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));

// Closed-form damped spring, 0 → 1. Pure function of time (step 08 explains it).
function spring(t, k = 170, d = 26) {
  if (t <= 0) return 0;
  const w0 = Math.sqrt(k), z = d / (2 * w0);
  if (z < 1) {
    const wd = w0 * Math.sqrt(1 - z * z);
    return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + (z * w0 / wd) * Math.sin(wd * t));
  }
  return 1 - Math.exp(-w0 * t) * (1 + w0 * t);      // z >= 1 treated as critical
}

// Seeded noise, never Math.random: the render must be identical every run
function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0;
  let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
  t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

const SCENES = [
  { from: 0, to: 3, draw(t) {                        // kinetic title
      const s = spring(t - 0.1, 220, 22);
      g.save(); g.translate(W / 2, H / 2); g.scale(0.6 + 0.4 * s, 0.6 + 0.4 * s);
      g.globalAlpha = clamp(t * 4);
      g.fillStyle = '#F0EEE6'; g.font = '700 190px "Source Serif 4", serif';
      g.textAlign = 'center'; g.fillText('MOTION', 0, 0);
      g.fillStyle = '#D97757'; g.fillRect(-320 * s, 50, 640 * s, 18);
      g.restore();
  }},
  { from: 3, to: 6, draw(t) {                        // grid of squares on a stagger
      const r = rng(7);
      for (let i = 0; i < 48; i++) {
        const x = (i % 6) * 170 + 115, y = Math.floor(i / 6) * 170 + 360;
        const s = spring(t - i * 0.03 - r() * 0.1, 260, 20);
        g.fillStyle = i % 7 ? '#F0EEE6' : '#D97757';
        g.fillRect(x - 60 * s, y - 60 * s, 120 * s, 120 * s);
      }
  }},
  // ... more scenes: Opus appends here, one object per shot
];

function draw(t) {
  g.fillStyle = '#141413'; g.fillRect(0, 0, W, H);
  for (const s of SCENES) if (t >= s.from && t < s.to) s.draw(t - s.from);
}
window.seek = (t) => { draw(t); return true; };

// Live preview in a normal browser, off during headless render
if (!navigator.webdriver) {
  const t0 = performance.now();
  (function loop() { draw(((performance.now() - t0) / 1000) % DUR); requestAnimationFrame(loop); })();
}
</script>
```

### CODE 12 — critique prompt: score contact sheet, list 3 problems, fix (pos: 10 → true: 11)
```text
Open out/contact.png, out/strip.png and out/phone.png and look at them properly.
Be a harsh motion director, not a proud author.

Score 1-10: hook in first 2s · readability at phone size · motion quality (springs,
no dead frames) · variety (new thing every 2-4s) · composition · brand accuracy · sound sync.

List the 3 biggest problems with timestamps. Hunt specifically for: text overlapping during
swaps, anything sliding instead of easing, corner labels and frame borders, centered-on-gradient
shots, blurry scaled text, a dead beat with nothing happening, a stutter at the loop seam.

Fix them, re-render only the affected seconds, show me the new contact sheet and new scores.
```

### CODE 13 — director-brief template, the ~9,500/19,000-char skeleton (pos: 10 = true, correct)
```markdown
You are the director, animator, sound designer and render engineer for a [DURATION] film
made in code. Treat this as a multi-session production. Don't rush to a final render.

## The film in one line
[LOGLINE. What the viewer should feel at the end.]

## References and inputs
- ./refs/ : [video / frames / image library]. Take the grammar, never the content.
- ./audio/track.wav : use it unchanged. Measure beats with beats.py first.
- Skills available: [/remotion-best-practices | /hyperframes | /claude-animation].
- APIs in .env: [ELEVENLABS_API_KEY, FAL_KEY]. Budget: [$X]. Be economical.

## Look
[3-5 lines: palette, type, texture, camera language. Banned looks.]

## Beat sheet
0:00-0:02  hook: [the single most striking image]
0:02-0:10  [act 1]
...        a new visual payoff every 3-5 seconds
[END]      the last frame sets up the first frame (loop)

## Workflow, with gates
1. Write docs/style_guide.md and docs/shotlist.md (every shot: frames, camera, text, SFX).
   Show me the shot list. Then continue without waiting if I don't answer in 10 minutes.
2. Build stills for every shot. Contact sheet. Critique.
3. Animatic at 960x540 with placeholder audio. Fix pacing before polish.
4. Full animation, polish pass, sound pass, final render.
5. Split work across subagents per chapter. Write docs/ANIMATION_GUIDE.md first
   so every subagent codes in the same style.

## Critique loop (every shot, at least 3 rounds)
Render 3-5 stills, score 1-10 on: hook, readability at 360px wide, motion, composition,
depth, sound sync, polish. Log scores + 3 biggest problems in docs/review_log.md. Fix. Repeat
until all are 8+.

## Deliverables
out/final.mp4 · out/loop_check.mp4 · out/poster.png · out/contact.png · README.md
```

### CODE 14 — Remotion / HyperFrames setup + invocation commands, route B (pos: 11 → true: 07)
```bash
# Remotion (React): best for series, templates, data-driven videos
npx create-video@latest launch-film && cd launch-film
npx skills add remotion-dev/skills
claude
> /remotion-create a 20s 9:16 launch film for [PRODUCT], springs only, one accent color
npx remotion studio                 # live timeline preview
npx remotion render Main out/launch.mp4

# HyperFrames (HTML + GSAP): best when you think in web pages
npx hyperframes init my-video && cd my-video
npx hyperframes skills update
claude
> Using /hyperframes, turn ./notes.md into a 45-second pitch video with kinetic captions
npx hyperframes preview && npx hyperframes render
```

### CODE 15 — XML spec for a UI-morph product film (pos: 11 → true: 06)
```xml
<inputs>
Ask me for: my product + URL, 8 to 12 UI states that tell its story, the real data shown in
each state, brand colors + fonts + one accent, a royalty-free track near 120 BPM, formats.
</inputs>

<direction>
Product-film UI motion. One container never cuts: every state is the same element changing
size, radius and fill while its content swaps behind a short blur. A cursor drives every change.
Warm neutral canvas, one accent. Springs with at most a tiny overshoot.
Banned: bouncy easing, glows, gradients on UI chrome, particle bursts, dead time.
</direction>

<structure>
120 BPM, 8 bars, something happens on every beat.
logo → CTA button → email field (typed) → loader → success check → dashboard card
→ chart draws itself → tooltip on hover → ⌘K palette → toast → logo.
</structure>

<build>
1. One HTML file, one canvas, window.seek(t). No CSS transitions, no timers, no carried state.
2. Closed-form springs. A value with many targets = sum of one spring per change.
3. Text inside a morphing container enters after the morph starts, leaves before the next one.
4. Tab indicators: leading and trailing edges on different springs so they stretch.
5. Beat grid from the track (numpy/librosa). Start on a downbeat. UI sounds on measured peaks.
6. Render in headless Chrome at 60 fps, 4 subframes per frame, blended for motion blur.
</build>

<gotchas>
Never use will-change on anything the camera scales (blurry text).
The last frame must equal the first, cursor position and velocity included.
</gotchas>

<start>
Ask for the inputs, then show me the state list on the beat grid before writing code.
</start>
```

### CODE 16 — motion-reel SKILL.md package (pos: 12 = true, correct)
```markdown
---
name: motion-reel
description: Make a product or showreel motion video rendered from code. Use when the
  user asks for a launch video, showreel, product reel, animated explainer or motion ad.
---

# Motion reel

## Inputs to collect first
Product + URL, duration, formats (9:16 / 1:1 / 16:9), brand colors + fonts,
a reference (frame, video or image folder), music (file or "synthesize").

## Pipeline
1. Gather assets from the URL with Playwright into ./assets. List them.
2. If a reference exists, write docs/style_guide.md from it.
3. Measure or synthesize music. beats.py → beats.json.
4. Write docs/shotlist.md on the beat grid. Show it and wait for OK.
5. Build index.html with window.seek(t) using lib/motion.js springs. Follow CLAUDE.md.
6. Contact sheet → critique-pass (see prompts/critique-pass.txt) → fix. 3 rounds minimum.
7. node render.mjs → sfx.mjs → mix to -14 LUFS → out/final.mp4, all formats.
8. Deliver final.mp4, contact.png, poster.png. Say what you'd improve next.

## Hard rules
- Real product UI only. Never invent screens.
- No Math.random, no timers, no CSS transitions in render mode.
- Banned: corner labels, centered title on gradient, everything fading in.
```

## Sources

- https://x.com/0xMovez/status/2104216919033192746 (article, deleted; re-fetch via api.fxtwitter.com/status/2104216919033192746).
- [[motion-course]], [[motion-course-article]], [[motion-course-code]].

## Date

Gathered 2026-10-03; condensed 2026-10-06 for the format 4 wiki.
