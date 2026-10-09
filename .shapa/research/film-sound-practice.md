---
id: film-sound-practice
type: reference
created: "2026-10-09T17:50:00Z"
consequence: 8
locus: output
summary: How the 2026-10-09 sources make and sync film sound - measured grid, a sound per move, early peaks, sections, mix numbers - and what each changes in our code.
scope: repo
status: active
---

# Film sound practice in the sources (2026-10-09)

## Question

Video 8's music was the same tune as every film and did not fit the motion ([[kinetic-type-sound-and-pace]]).
Operator decision, 2026-10-09: ElevenLabs for voice-over, music and effects. How do the five sources the operator
sent make a film's sound and tie it to the picture? Which numbers do they give, and what does each change in our code?

## Method

- One helper session per source, run in parallel:
  - the fevr article, fetched twice (WebFetch and the raw HTML);
  - charliehills' Substack (the free part), plus the repos it links, cloned: `charlie947/motion-graphics-skills`
    @4cd156a and upstream `heygen-com/hyperframes` @cea48a5;
  - `Barty-Bart/motion-graphics` @83355bb;
  - `whaleyxbt/claude-motion` @b2a30af;
  - shneural's thread through api.fxtwitter.com, with the prompt-motion film downloaded and measured.
- Clones live in session scratch, `.local/tmp/fd3c0320-1d2d-4320-b6e6-ede96e9e7839/src/`.
- Read against our code and our pinned engine's skills (HyperFrames 0.8.106: `music-to-video`, `hyperframes-audio`,
  `media-use`), and against [[motion-course-prompts]] for claude-animation-skill's `sound.md`.
- Everything below is paraphrased (rule R43). The pipelines themselves are in [[claude-motion-pipelines]]; the
  ElevenLabs contract and prices are in [[elevenlabs-api-cost]].

## Findings

### 1. The sound and the picture run on one clock, and the grid is measured, not declared

- whaleyxbt: one `timeline.json` feeds both the scene code and the Python cue sheet, so no sound time is ever typed
  by hand (`.claude/skills/sound-design/SKILL.md:10,44`; `sfx/cues/effort.py:22-92`).
- shneural: the setup reply the operator pasted fits the making-of post (status 2103472385563459833). A Python script
  sequenced and mixed 909/808 and free-pack samples to the beat grid, in the same Claude Code session that drew
  the picture. The session made the music and rendered 900 frames in 1 h 32 min, for $81 at API prices.
- twoclipping ([[kinetic-type-sound-and-pace]]): a real song is measured for tempo, beat grid, energy per bar and
  its drop. The grid is calibrated to the real kick hits and every cut lands on a downbeat.
- The pinned engine's `music-to-video` skill (0.8.106, `scripts/analyze-beatgrid.py`):
  - the track is the spine of the film;
  - an analyser writes `audiomap.json`: the beat grid and downbeat, drum events, risers, impacts and silences,
    energy phases, phrases, and a density budget per section;
  - the film is cut at real musical changes: `beat_cut` on rhythmic tracks and `phrase_flow` on calm ones. A
    metronome grid is never forced onto music that does not have one;
  - it needs librosa, numpy and soundfile, which our stdlib-only package does not ship.
- whaleyxbt `sims/beats.py` (MIT) does the same core job in pure stdlib Python (210 lines). It finds the tempo from
  the autocorrelation of the onset envelope, weighted towards about 126 BPM over 70-190. It then finds the grid
  phase, the downbeats (the phase with the most low-band attack), the kicks, the energy per bar and the drop.
- **Applies**: today the designer declares `bpm` in brief.json and synthesizes a bed to that number
  (`runner.SOUND_STEP`, `data/tools/sound.mjs`), and nothing is measured. J49 composes the music first, measures
  its grid with a stdlib port of `beats.py`, and has the designer cut to the measured beats.

### 2. A sound per move, chosen by the kind of move; continuous motion stays silent

- whaleyxbt maps each kind of move to a sound (`SKILL.md:52-66`):

  | On screen | Sound |
  |---|---|
  | Typing | a keystroke per character, with jitter |
  | A word or line arrives | an airy whoosh, plus a blip on the landing |
  | A pop-in | a pop, its pitch rising across a sequence |
  | A snap to a step | a click and a blip in key |
  | A draw-on | a scratch |
  | A build-up | one riser per film, ending exactly on the hit |
  | Success | a chime chord in key |
  | The hero transition | a whoosh in and one impact per film |
  | Under everything | a bed, ducked under the hero |

- The same file says "accent, don't narrate": drift, grain and rotation stay silent (`SKILL.md:66`).
  claude-animation-skill built a continuous pencil scratch and dropped it for the same reason.
- fevr says the same in prose only. Each effect matches a visible movement and supports the picture rather than
  overpowering it. Balance the levels to avoid fatigue, and test on several devices. The article has no numbers,
  tools or timing rules at all.
- Video 8's brief already had 39 cues in 22 s (1.8 a second). The cue density was there. What failed was the
  sound: one synthesized family of effects in every film (the `CUES` table in `sound.mjs`) under a bed whose
  grid dominated.
- **Applies**:
  - every cue in brief.json (`data/session_prompt.md`) gets a description of the sound and a length matched to
    its move, and code generates it with ElevenLabs (J50);
  - the mapping table goes into the shipped sound skill (new job J53 in the plan).

### 3. Land the effect's peak on the event, slightly early

- claude-animation-skill (MIT): place the cue about 0.03 s before the contact frame. A late sound reads as broken;
  a slightly early one reads as synced.
- twoclipping: each effect is placed so that its measured peak, not the start of its file, lands on the event.
- whaleyxbt: a riser ends exactly on its hit.
- **Applies**: J50 measures each generated effect's peak and places it 0.02-0.03 s before the cue time. Risers and
  swells end at the cue; whooshes peak at the fastest point of the move.

### 4. Sections, a drop and silence, over a sustained bed

- Baseline spectrograms: the references run a sparse open, a full middle, a drop to near-silence and a slam back.
  Ours ran one metronome grid from end to end.
- ik-builds: the drums drop out on the dark switch and while the ball is in the air, and slam back on the type and
  the logo.
- whaleyxbt: a mix made of short hits with silence between them cannot reach -14 LUFS without crushing. The fix is
  sustained sound (a pad, longer tails), not more drive (`SKILL.md:47`, `sfx/mix.py:53-95`). That is our loudness
  range problem: our LRA is 4-4.7 LU against the references' 1.7, because our mix has thin low-mids between hits.
- claude-animation-skill can start the bed late (`--bed-at 2.0`) so the hook plays on effects alone. It places
  sections on absolute times and holds one chord under serious beats.
- Upstream HyperFrames `media-use/audio/references/bgm.md` (Apache-2.0): 90-110 BPM for calm films and 110-130 for
  energetic ones. Genre presets: creative 115, SaaS 108, crypto 100, fintech 92. The arc reshapes the tempo: +10 BPM
  for a feature cascade, -8 BPM for a demo loop. Eight of our ten measured references sit at 115-127 BPM.
- **Applies**: the storyteller writes the music in sections over its beats (J49). ElevenLabs' music_v2 and v2_5
  composition plans always keep each section's duration ([[elevenlabs-api-cost]]).

### 5. Levels and mastering numbers

| Source | Number |
|---|---|
| whaleyxbt `SKILL.md:70` | hero hits at gain 0.25-0.35; supporting sounds 0.08-0.2; the bed at about 0.03, ducked about 65% under the hero |
| whaleyxbt `sfx/mix.py:53-60` | master to -14 LUFS with the true peak at or below -2 dBFS before AAC, so the MP4 stays at or below -1 dBTP; soft-clip drive steps 1.2 to 4.0 |
| whaleyxbt `sims/capture.mjs:146` | the sims' quieter house level: loudnorm -21 LUFS, true peak -3 |
| upstream hyperframes `bgm.md:34` | the bed under narration at 0.12 linear (about -18 dB); a film with no voice at 0.9 |
| upstream hyperframes `tts.md:16-21` | its ElevenLabs reference voice speaks at 145-155 wpm, with music under it at about -31 LUFS |
| upstream hyperframes `sfx.md` | effects at a default volume of about 0.35, under the voice and the bed |
| pinned `hyperframes-audio/SKILL.md` | the voiceover carve: strength 0.8 makes six peaking cuts from 250 Hz to 2.5 kHz, about 7 dB each (15 dB at 1.6 kHz), with a slow release |
| claude-animation-skill `sound.md` | the bed about 22 dB under narration; with no narration, the bed at about 0.5 and effects at 0.3-0.6; final -16 LUFS, at or below -1 dBTP |
| ik-builds (baseline) | -14 LUFS, -2 dBTP, measured again after the AAC encode |
| 0xmovez brief ([[ref-x-0xmovez-2107515767986217026]]) | about -16 LUFS, at or below -1.5 dBTP; checked muted, then audio-only |
| shneural's film, baseline method | -14.3 LUFS, LRA 3.2 LU, 140 BPM, 3.29 onsets/s, 85% of cuts on an onset |
| the references (baseline) | -13.6 LUFS median; LRA 1.7 LU median, 0.8 LU at the top decile |
| ours, `engine._loudnorm_args` | two-pass linear loudnorm at I=-14, TP=-1.5, LRA=11: gain only, no compression. Measured LRA 4.0-4.7 |

- **Applies**: a linear loudnorm cannot bring the loudness range from 4.7 LU down to 1.7 LU. J50 adds a bus
  compressor and a limiter before the loudnorm, and measures the range after the encode.

### 6. Variety from film to film

- Ours has one composition, so every film gets the same tune (baseline). Upstream HyperFrames picks the genre and
  tempo from the brand's register and the film's arc (finding 4).
- **Applies**:
  - history.json carries each film's music fingerprint (genre, tempo, key, lead instrument);
  - the storyteller picks a different fingerprint from the last three films, and code checks it (J49).

### 7. A model cannot hear its own draft

- whaleyxbt's review loop draws a waveform image with beat markers, its LUFS and its true peak, and the agent
  checks that image, because it has no ears (`scripts/wave.mjs`, review-loop `SKILL.md:10-46`). The 0xmovez brief
  checks every cut muted, then audio-only.
- Our designer only checks that its draft has an audio stream (`session_prompt.md`, step 6).
- **Applies**: the sound's quality comes from contracts and measurements, not from the designer's ear.
  `tools/measure.py` (new job J51) prints onsets, cuts on onsets and the loudness range, and draws a strip of the
  waveform with the cut markers on it.

### 8. What does not apply

- Barty-Bart/motion-graphics generates no sound. It passes the source talking-head's audio through
  (`scripts/composite.py`, `-c:a copy`) and tells the user to mix in their own editor (`SKILL.md:130`).
- charlie947's skills write the score in code (`vox-explainer/SKILL.md:23,27`), the path we are leaving.
- Sample libraries (shneural's 909/808 packs, Surge XT) are out: the operator ruled ElevenLabs for everything. The
  ElevenLabs equivalent is one-shots generated once and sequenced to the grid (the conditional job Q1 in the plan).
- fevr gives framing only, with no numbers.

## Sources

- https://wearefevr.com/sound-design-for-motion-graphics (FEVR studio blog, all rights reserved; paraphrased).
- https://github.com/whaleyxbt/claude-motion @b2a30af, MIT: `.claude/skills/sound-design/SKILL.md`, `sfx/mix.py`,
  `sfx/loudness.py`, `sims/beats.py`, `sims/capture.mjs`, `scripts/wave.mjs`.
- https://github.com/heygen-com/hyperframes @cea48a5, Apache-2.0: `skills/media-use/audio/references/{bgm,tts,sfx}.md`.
  The pinned 0.8.106 copy is `.studio/engine/hyperframes-0.8.106/skills/{music-to-video,hyperframes-audio}`.
- https://github.com/charlie947/motion-graphics-skills @4cd156a, MIT.
- https://github.com/Barty-Bart/motion-graphics @83355bb, MIT.
- https://x.com/shneural/status/2103472490324648049, plus 2103151003272962130 (the film) and 2103472385563459833
  (the making-of), read through api.fxtwitter.com. The setup reply is the operator's paste and was not re-fetched.
- [[kinetic-type-sound-and-pace]] for the baseline numbers; [[motion-course-prompts]] for claude-animation-skill.
