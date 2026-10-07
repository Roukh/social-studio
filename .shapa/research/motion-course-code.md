---
id: motion-course-code
type: reference
created: "2026-10-03T01:00:00Z"
consequence: 7
locus: output
summary: Motion-course article's code blocks, part 1 of 2 (CODE 1-8) - one-shot prompt, brand reel, springs, setup, beats.py, render.mjs, ref prompt, one-liners.
scope: repo
status: active
---

# Motion-course code blocks, verbatim (part 1 of 2: CODE 1-8)

These are the builder's copy of the first 8 of 16 code and prompt templates in the motion-course article, split from [[motion-course-article]], which holds the steps they belong to. The other 8 (CODE 9-16) are in [[motion-course-code-2]]. The entry note is [[motion-course]]. They are the article author's own templates, published in the article. Line refs such as `L91` point into the article extract described in [[motion-course-article]].

## Question

What is the exact, verbatim text of the motion-course article's code and prompt templates CODE 1 through CODE 8?

## Method

Extracted verbatim from the article's full text extract (`article-full.txt`); no paraphrasing inside any code fence. Each block is labeled with its article position and the step it truly belongs to.

## Findings

Each heading: `CODE n — label (article position → true step)`.

### CODE 1 — original one-shot showreel prompt (pos: intro → true: 03)
```text
make a dynamic 15-second motion graphics video that shows what an 
incredible motion designer you are, like it's your showreel for a résumé. 
go all out.
```

### CODE 2 — brand/product reel prompt template (pos: 01 → true: 04)
```text
Make a dynamic 20-second motion graphics video for [PRODUCT] ([URL]), with the energy
of a motion designer's showreel. Go all out.

Assets
- Visit the site. Use real screenshots (Playwright), the real logo, real colors and fonts.
  Save everything to ./assets and list what you found before you animate.
- Never redraw the product UI from imagination. Crop and animate the real thing.

Story (one beat each, 2 to 4 seconds)
1. Hook: the problem in 5 words of huge kinetic type.
2. The product appears, the UI assembles itself piece by piece.
3. Three features, each as a UI moment with a cursor doing a real action.
4. One number that proves it works: [METRIC].
5. Logo lockup + [CTA].

Sound
- Original music, 120 BPM, synthesized in code. UI clicks and whooshes on the beat.

Format: 1080x1920 (9:16) first, then 1:1 and 16:9 from the same timeline.
Before the full render, show me a contact sheet of one frame per beat.
```

### CODE 3 — lib/motion.js spring helpers: track/indicator/swapAlpha/loopT (pos: 02 → true: 08)
```javascript
// keys: [[time, value], ...] sorted by time. Returns the value at t.
export function track(t, keys, k = 170, d = 26) {
  let v = keys[0][1];
  for (let i = 1; i < keys.length; i++)
    v += (keys[i][1] - keys[i - 1][1]) * spring(t - keys[i][0], k, d);
  return v;
}

// A tab indicator that stretches: leading edge is stiffer than trailing edge
export function indicator(t, stops) {             // stops: [[time, x], ...]
  const lead  = track(t, stops, 320, 30);
  const trail = track(t, stops, 140, 22);
  return { left: Math.min(lead, trail), right: Math.max(lead, trail) + 120 };
}

// Text inside a morphing box: in after the morph starts, out before the next one
export function swapAlpha(t, tIn, tOut) {
  return Math.min(clamp((t - tIn - 0.08) / 0.12), clamp((tOut - 0.1 - t) / 0.1));
}

// Seamless loop: pin the last frame to the first
export const loopT = (t, dur) => ((t % dur) + dur) % dur;
```

### CODE 4 — studio setup commands (pos: 03 → true: 02)
```bash
# 1. Runtime: Node 22+, ffmpeg, Python for audio analysis
brew install node ffmpeg python          # macOS; apt install on Linux
pip install numpy librosa soundfile

# 2. A clean project and a headless browser
mkdir motion-studio && cd motion-studio && npm init -y
npm i -D playwright && npx playwright install chromium

# 3. Framework skills (optional, route B)
npx skills add remotion-dev/skills       # /remotion-create, /remotion-render ...
npx skills add heygen-com/hyperframes    # /hyperframes router + GSAP skills

# 4. Hand-drawn look (optional): Node canvas rigs, pens, synthesized sound
claude plugin marketplace add buildwithhanif/claude-animation-skill
claude plugin install claude-animation@claude-animation-skill

# 5. Start Claude Code on Opus 5.5 at high effort
claude --model claude-opus-5-5
> /model   # pick Opus 5.5, then set effort to xhigh for one-shots, max for flagship pieces
```

### CODE 5 — beats.py, librosa beat/onset analysis (pos: 03 → true: 09)
```python
# python beats.py song.wav > beats.json   (the animation reads this file)
import sys, json, numpy as np, librosa

y, sr = librosa.load(sys.argv[1], sr=None, mono=True)
tempo, frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
beats = librosa.frames_to_time(frames, sr=sr).round(3).tolist()

onset = librosa.onset.onset_strength(y=y, sr=sr)
peaks = librosa.util.peak_pick(onset, pre_max=3, post_max=3, pre_avg=3,
                               post_avg=5, delta=0.5, wait=10)
json.dump({
    "bpm": float(np.atleast_1d(tempo)[0]),
    "beats": beats,                                   # state changes go here
    "downbeats": beats[::4],                          # big moments go here
    "hits": librosa.frames_to_time(peaks, sr=sr).round(3).tolist(),  # SFX go here
}, sys.stdout, indent=1)
```

### CODE 6 — render.mjs, Playwright seek(t) capture → ffmpeg pipeline (pos: 04 → true: 07)
```javascript
// node render.mjs --fps 60 --dur 15 --sub 4
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdirSync } from 'node:fs';

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? Number(process.argv[i + 1]) : d; };
const FPS = arg('fps', 60), DUR = arg('dur', 15), SUB = arg('sub', 4);
mkdirSync('out', { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
await page.goto('file://' + process.cwd() + '/index.html');
await page.evaluate(() => document.fonts.ready);       // canvas text needs loaded fonts

// tmix averages SUB consecutive subframes; select keeps the last of each group
const vf = `tmix=frames=${SUB},select='eq(mod(n\\,${SUB})\\,${SUB - 1})',setpts=N/${FPS}/TB`;
const ff = spawn('ffmpeg', ['-y', '-f', 'image2pipe', '-framerate', String(FPS * SUB), '-i', '-',
  '-vf', vf, '-r', String(FPS), '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', 'out/silent.mp4'],
  { stdio: ['pipe', 'inherit', 'inherit'] });

const total = Math.round(DUR * FPS * SUB);
for (let i = 0; i < total; i++) {
  await page.evaluate((t) => window.seek(t), i / (FPS * SUB));
  const png = await page.locator('#c').screenshot({ type: 'png' });
  if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once('drain', r));
  if (i % (FPS * SUB) === 0) console.log(`rendered ${i / (FPS * SUB)}s / ${DUR}s`);
}
ff.stdin.end();
await new Promise((r) => ff.on('close', r));
await browser.close();
```

### CODE 7 — reference-extraction prompt (pos: 05 = true, correct)
```text
Reference: ./refs/launch.mp4 (and ./refs/frames/*.png)

1. Extract one frame every 0.5s with ffmpeg. Study them.
2. Write ./docs/style_guide.md: palette (hex), type (family, weight, tracking),
   shot lengths, transition types, camera moves, texture/grain, how text enters and exits.
3. Write ./docs/shotlist.md for a [DURATION]s video about [SUBJECT] in THAT style.
   Take the grammar of the reference, never its content, logos or characters.
4. Show me both files. Wait for my OK before any code.
```

### CODE 8 — four one-liner variants: sound bar, anti-slop, story, agency persona (pos: 05 → true: 03)
```text
# Longer, with a sound bar (pattern from @kloss_xyz's 90-second piano reel)
make a dynamic 16:9, 60-second motion graphics showreel that shows your real creative limits.
S-tier sound design, no generic synth pads. Compose an original piano score and sync every
cut to it. Export 1080p MP4.

# Anti-slop guardrail (pattern from @1littlecoder)
make a dynamic 10-second motion graphics video that introduces who you are as Opus 5.5.
Avoid frames and text in the corners, the usual giveaways of AI-made video.

# Story instead of techniques (pattern from @sonnylazuardi)
use your showreel energy, but tell a story: the history of [TOPIC] from [START] to today,
surprise me with the storyboard. 45 seconds, vertical 9:16.

# Agency persona
make a 30-second showreel as if you were a niche branding studio for startup founders.
Create every graphic from scratch. One accent color. Every shot is a different technique.
```

## Sources

- https://x.com/0xMovez/status/2104216919033192746 (article, deleted; re-fetch via api.fxtwitter.com/status/2104216919033192746).
- [[motion-course]], [[motion-course-article]], [[motion-course-code-2]].

## Date

Gathered 2026-10-03; condensed 2026-10-06 for the format 4 wiki.
