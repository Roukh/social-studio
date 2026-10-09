---
id: kinetic-type-sound-and-pace
type: reference
created: "2026-10-09T13:40:00Z"
consequence: 8
locus: output
summary: prompt-motion's 11 kinetic-type films vs our videos 4, 6, 8, measured - sound, pace, motion, colour; why ours read pale, one-screen and slow.
scope: repo
status: active
---

# Kinetic-type films vs ours: sound and pace (2026-10-09)

## Question

The operator, 2026-10-09, after video 8 ("Sized for a thumb, not a cursor", the first F15 build): the story and narrative are much better, but the music is the same tune in every film and does not fit the motion; the picture is better but "too pale, on one screen, not enough happening and a lil slow"; video 8 is much closer to video 6 than to prompt-motion. What do prompt-motion's kinetic-type films ([[ref-prompt-motion]]) do with sound, and how far are ours from them?

## Method

- The 11 films tagged kinetic-type in `.local/refs/prompt-motion/index.json`, downloaded to session scratch, and our videos 4 (the reel), 6 (48 hours) and 8 (thumb) from the ghobz library.
- One stdlib + ffmpeg script for every film: cuts (scene score > 0.3), mean frame-to-frame change and share of near-still frames (scene score at 15 fps), mean saturation and luma (signalstats), loudness and loudness range (ebur128), band RMS (low < 150 Hz, mid 300 Hz-3 kHz, high > 5 kHz), onsets (energy flux), tempo (onset autocorrelation), and the share of cuts that land within 70 ms of an audio onset.
- Spectrograms (log frequency) of six references and videos 6 and 8, read side by side.
- The published prompts, searched for sound instructions. The scores of our films, read from session folders and logs.

## Findings

### Pace and picture

| Measure | References: median (range) | Video 8 | Video 6 | Video 4 (reel) |
|---|---|---|---|---|
| Mean frame-to-frame change | 0.044 (0.002-0.129; top 0.129 zheke) | 0.0066 | 0.021 | 0.041 |
| Near-still frames | 28% (11-83%) | 58% | 48% | 28% |
| Hard cuts per second | 0.33 (0-1.73) | 0 (one 22 s take) | 0.04 | 0.26 |
| Mean saturation | 22.8 for the colour films (18-30); 2-3 for the three paper-style ones | 4.6 | 19.4 | 37.9 |
| Mean luma (0-255) | 89 (28-146) | 209 | 142 | 85 |

- Video 8 is the stillest film measured: a sixth of the median motion and twice the still frames. It is one continuous take on one near-white phone page (luma 209, saturation 4.6): the "pale, one screen" the operator saw. Video 6 sits between it and the references; the reel (video 4), the film the operator rated highest, sits at the reference median on every measure.
- The references change scene or field on almost every move. The colour films sit on dark or saturated grounds; the three low-saturation ones are paper-style by design (ik-builds, tdinh, twoclipping).

### Sound

| Measure | References: median (range) | Video 8 | Video 6 |
|---|---|---|---|
| Loudness range (LRA) | 1.7 LU (0.8-4.6) | 4.7 | 4.0 |
| Integrated loudness | -13.6 LUFS (-11.8 to -15.8) | -14.5 | -14.2 |
| Onsets per second | 3.7 (2.6-4.7) | 2.9 | 2.5 |
| Tempo | 115-127 BPM for 8 of 10 | 115 | 115 |
| Cuts landing on an audio onset | 92% (43-100%) | no cuts | 100% |

- Spectrograms: the references carry a continuous harmonic bed (the low-mid band filled the whole way), many distinct sound shapes (rising and falling sweeps whose length matches a move, pitch glides, impacts), and sections: a sparse open, a full middle, a drop to silence or near-silence, a slam back (itsuki, zheke, shneural, web3wesley). Ours show one metronomic grid of identical hi-hat and kick stripes from start to end, thin low-mids between the hits, and no section change, drop or silence.
- Ours are the same tune by construction: `data/tools/sound.mjs` has one composition. The progression is fixed at i-VI-III-VII (line 168), the arpeggio at [0, 2, 4, 7] (185), the drum pattern too (180-181); the seed only changes hi-hat noise. Videos 4, 6 and 8 all used style `pulse`, seed 11, D or A minor; only the tempo differed.
- The references are louder and flatter (LRA median 1.7 LU against ours 4-4.7): their beds are compressed; ours have soft passages between hits.
- How the references made their sound: 9 of 11 prompts are one line ("make a dynamic 15-second ... showreel ... go all out") and say nothing about sound; the pages carry no music credit ("Music" on the page is a category tag). Two say it:
  - twoclipping-6dd14e: a royalty-free song with a clear drop (Mixkit, free for commercial use), analysed in numpy for tempo, beat grid, energy per bar and the drop, the grid calibrated to the real kick hits; every cut on a downbeat, every UI hit on a beat; each effect placed so its measured peak (not its file start) lands on the event; effects kept under the music.
  - ik-builds-b8bdcf: music in sections (the drums drop on the dark switch and while the ball is airborne, and slam back on the type and the logo); SFX pops, pen scribbles, whooshes, a sub-hit on the logo; CC0 or generated only; master -14 LUFS, -2 dBTP, re-measured after the AAC encode.
  - Most references are HyperFrames films. The engine's media-use skill fetches background music from HeyGen's catalogue on its free sign-in path (`skills/media-use/references/setup-providers.md` line 30), and its music-to-video skill makes the track the spine that the cuts follow. Our sessions forbid network installs and use only the code synthesizer, so they never take that path. Whether these 9 films used it is not published.

### Skills in video 8's session

The designer opened the storyteller, pitch-round and launch-video skills, the explainer-video references, the technique library and the engine's animation blueprints. The log shows no reads of hyperframes-registry, motion-graphics, product-launch-video, short-form-video, product-demo-video or hyperframes-creative, all mounted since J45.

## Sources

- Films: `https://prompt-motion.com/<id>` for ik-builds-b8bdcf, itsuki-dev-10942d, m1n9-k7-ff9ab9, motiondsgnr-9dcfa6, shneural-2abdfa, souravbhar871-61f424, tdinh-me-815acb, topi-003-9ca6b5, twoclipping-6dd14e, web3wesley-7bb108, zheke-38deff (the creators' work, studied only: rule R43).
- Ours: ghobz library videos 4, 6 and 8; their scores in `.studio/sessions/*/work/score.json` and video 8's `logs/agent.out.gz`.
- Code: `src/social_studio/data/tools/sound.mjs`; the engine's `skills/media-use/references/setup-providers.md` and `skills/music-to-video/SKILL.md` (HyperFrames 0.8.106).
- Measurement scripts and spectrograms were in session scratch; the numbers above are the record.
