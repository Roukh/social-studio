#!/usr/bin/env node
// Synthesize a film's soundtrack in code: a music bed on the beat grid plus effects on cues. No dependencies, no
// network, and deterministic: the same score always gives the same samples. 48 kHz, 16-bit stereo WAV.
//
//   node tools/sound.mjs score.json composition/assets/soundtrack.wav
//   node tools/sound.mjs --grid 143 15          beat and downbeat times for planning cuts
//   node tools/sound.mjs --help
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";

const HELP = `sound.mjs: a soundtrack from a score, synthesized in code.

  node tools/sound.mjs SCORE.json OUT.wav
  node tools/sound.mjs --grid BPM SECONDS

SCORE.json:
  {"duration": 15.0, "bpm": 143, "seed": 7,
   "bed": {"style": "pulse", "root": "A", "scale": "minor", "start": 1.5, "end": 15.0, "fade_out": 1.6,
           "sections": [{"from": 1.5, "to": 5.0, "energy": 0.5}, {"from": 5.0, "to": 13.3, "energy": 0.9}]},
   "cues": [{"t": 1.5, "kind": "hit"}, {"t": 3.3, "kind": "whoosh", "dur": 0.3}, {"t": 1.5, "kind": "riser", "dur": 1.0}],
   "gain": {"bed": 0.55, "cues": 0.9}}

  bed.style   pulse (kick, hats, bass, plucks, pad), minimal (ticks and bass only), or none.
  energy 0-1  per section: 0.3 is hats and bass, 0.6 adds the kick and plucks, 0.85 and up adds the pad and drives.
  cue.t       the moment the sound lands: a cut, an impact, a click. Risers, swells and whooshes build up to t.
  cue.kind    hit, thump, sub, whoosh, swell, riser, tick, click, blip, pop, chime, glitch, type
  cue fields  dur (seconds, for whoosh/swell/riser/type/sub), pitch (Hz, for blip/pop/chime), gain (0-1), pan (-1..1)

Place the output as one <audio id="soundtrack" src="assets/soundtrack.wav" data-start="0" data-duration="DUR"
data-track-index="N"> spanning the film; the runner normalizes the final loudness to -14 LUFS.`;

const SR = 48000;
const TAU = Math.PI * 2;

function rng(seed) {                                   // mulberry32: seeded, never Math.random
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const NOTES = { C: 0, "C#": 1, Db: 1, D: 2, "D#": 3, Eb: 3, E: 4, F: 5, "F#": 6, Gb: 6, G: 7, "G#": 8, Ab: 8, A: 9,
  "A#": 10, Bb: 10, B: 11 };
const SCALES = { minor: [0, 2, 3, 5, 7, 8, 10], major: [0, 2, 4, 5, 7, 9, 11], dorian: [0, 2, 3, 5, 7, 9, 10] };
const hz = (midi) => 440 * 2 ** ((midi - 69) / 12);

class Track {
  constructor(seconds) {
    this.n = Math.ceil(seconds * SR);
    this.L = new Float32Array(this.n);
    this.R = new Float32Array(this.n);
  }
  add(i, v, pan = 0) {                                 // equal-power pan
    if (i < 0 || i >= this.n) return;
    const a = (pan + 1) * Math.PI / 4;
    this.L[i] += v * Math.cos(a);
    this.R[i] += v * Math.sin(a);
  }
}

// --- voices: each writes into a track from a start time; all envelopes are closed-form in time ---------------

function kick(tr, t0, g) {
  const n = Math.floor(0.32 * SR), i0 = Math.round(t0 * SR);
  let ph = 0;
  for (let k = 0; k < n; k++) {
    const t = k / SR, f = 45 + 120 * Math.exp(-t * 32);
    ph += TAU * f / SR;
    tr.add(i0 + k, Math.tanh(1.6 * Math.sin(ph)) * Math.exp(-t * 9) * g);
  }
}

function noiseBurst(tr, t0, dur, g, rand, { hp = 0.0, lp = 1.0, decay = 40, pan = 0 } = {}) {
  const n = Math.floor(dur * SR), i0 = Math.round(t0 * SR);
  let low = 0, prev = 0, high = 0;
  for (let k = 0; k < n; k++) {
    const x = rand() * 2 - 1;
    low += lp * (x - low);                             // one-pole low-pass
    high = hp > 0 ? hp * (high + low - prev) : low;    // one-pole high-pass
    prev = low;
    tr.add(i0 + k, high * Math.exp(-(k / SR) * decay) * g, pan);
  }
}

function tone(tr, t0, dur, f, g, { wave = "sine", decay = 8, attack = 0.004, pan = 0, glide = 0 } = {}) {
  const n = Math.floor(dur * SR), i0 = Math.round(t0 * SR);
  let ph = 0;
  for (let k = 0; k < n; k++) {
    const t = k / SR, fr = f * (1 + glide * Math.exp(-t * 30));
    ph += fr / SR;
    const p = ph % 1;
    const w = wave === "saw" ? 2 * p - 1 : wave === "tri" ? 1 - 4 * Math.abs(p - 0.5) : wave === "square"
      ? (p < 0.5 ? 1 : -1) : Math.sin(TAU * p);
    const env = Math.min(1, t / attack) * Math.exp(-t * decay);
    tr.add(i0 + k, w * env * g, pan);
  }
}

function sweep(tr, tEnd, dur, g, rand, { rise = true, pan = 0, pitch = false } = {}) {
  // Filtered noise (plus an optional rising saw) building to tEnd: risers, swells and the front of a whoosh.
  const n = Math.floor(dur * SR), i0 = Math.round((tEnd - dur) * SR);
  let low = 0, ph = 0;
  for (let k = 0; k < n; k++) {
    const u = k / n, shape = rise ? u ** 2.2 : 1 - u;
    const cutoff = 0.02 + 0.5 * shape;
    low += cutoff * (rand() * 2 - 1 - low);
    let v = low * shape;
    if (pitch) {
      ph += (180 + 900 * u ** 2) / SR;
      v += 0.35 * (2 * (ph % 1) - 1) * shape;
    }
    tr.add(i0 + k, v * g, pan);
  }
}

const CUES = {
  thump: (tr, c, g) => kick(tr, c.t, 1.1 * g),
  sub: (tr, c, g) => tone(tr, c.t, c.dur ?? 1.2, c.pitch ?? 48, 0.9 * g, { decay: 2.4, glide: 1.5 }),
  hit: (tr, c, g, r) => {
    kick(tr, c.t, 1.0 * g);
    noiseBurst(tr, c.t, 0.5, 0.55 * g, r, { lp: 0.6, decay: 9 });
    tone(tr, c.t, 0.9, c.pitch ?? 110, 0.25 * g, { wave: "saw", decay: 5 });
  },
  whoosh: (tr, c, g, r) => {
    const d = c.dur ?? 0.35;
    sweep(tr, c.t, d * 0.7, 0.8 * g, r, { pan: c.pan ?? -0.3 });
    sweep(tr, c.t + d * 0.3, d * 0.3, 0.6 * g, r, { rise: false, pan: -(c.pan ?? -0.3) });
  },
  swell: (tr, c, g, r) => sweep(tr, c.t, c.dur ?? 0.8, 0.7 * g, r, { pan: c.pan ?? 0 }),
  riser: (tr, c, g, r) => sweep(tr, c.t, c.dur ?? 1.0, 0.75 * g, r, { pitch: true, pan: c.pan ?? 0 }),
  tick: (tr, c, g, r) => noiseBurst(tr, c.t, 0.03, 0.45 * g, r, { hp: 0.6, decay: 180, pan: c.pan ?? 0.2 }),
  click: (tr, c, g, r) => {
    noiseBurst(tr, c.t, 0.02, 0.35 * g, r, { hp: 0.4, decay: 260, pan: c.pan ?? 0 });
    tone(tr, c.t, 0.05, 2200, 0.2 * g, { decay: 90, pan: c.pan ?? 0 });
  },
  blip: (tr, c, g) => tone(tr, c.t, 0.12, c.pitch ?? 1320, 0.32 * g, { wave: "tri", decay: 30, pan: c.pan ?? 0 }),
  pop: (tr, c, g) => tone(tr, c.t, 0.09, c.pitch ?? 420, 0.6 * g, { decay: 40, glide: 1.2, pan: c.pan ?? 0 }),
  chime: (tr, c, g) => {
    const f = c.pitch ?? 880;
    for (const [m, a] of [[1, 0.5], [2.76, 0.18], [5.4, 0.08]])
      tone(tr, c.t, 1.6, f * m, a * g, { decay: 2.2 + m, pan: c.pan ?? 0 });
  },
  glitch: (tr, c, g, r) => {
    for (let k = 0; k < 6; k++)
      noiseBurst(tr, c.t + k * 0.022, 0.015, (0.25 + 0.3 * r()) * g, r, { hp: 0.2, lp: 0.9, decay: 30, pan: r() - 0.5 });
  },
  type: (tr, c, g, r) => {
    const d = c.dur ?? 0.6;
    for (let t = 0; t < d; t += 0.055 + 0.03 * r()) CUES.tick(tr, { t: c.t + t, pan: r() * 0.4 - 0.2 }, 0.7 * g, r);
  },
};

// --- the bed ------------------------------------------------------------------------------------------------

function energyAt(bed, t) {
  for (const s of bed.sections ?? []) if (t >= s.from && t < s.to) return s.energy;
  return bed.sections?.length ? 0 : 0.7;
}

function renderBed(tr, score, bed, g, rand) {
  if (!bed || bed.style === "none") return;
  const beat = 60 / score.bpm, six = beat / 4;
  const start = bed.start ?? 0, end = bed.end ?? score.duration;
  const root = 45 + (NOTES[bed.root ?? "A"] ?? 9), scale = SCALES[bed.scale ?? "minor"] ?? SCALES.minor;
  const chords = [0, 5, 2, 6];                         // i - VI - III - VII in scale degrees
  const deg = (d) => root + 12 * Math.floor(d / 7) + scale[((d % 7) + 7) % 7];
  for (let k = 0; ; k++) {
    const t = start + k * six;
    if (t >= end) break;
    const e = energyAt(bed, t), step = k % 16, bar = Math.floor(k / 16), chord = chords[bar % 4];
    if (e <= 0) continue;
    if (bed.style === "minimal") {
      if (step % 2 === 0) CUES.tick(tr, { t, pan: step % 4 ? 0.3 : -0.3 }, 0.5 * g, rand);
      if (step % 8 === 0) tone(tr, t, beat * 1.8, hz(deg(chord) - 12), 0.4 * g, { wave: "tri", decay: 1.5 });
      continue;
    }
    if (e >= 0.6 && (step % 4 === 0) && (e >= 0.85 || step % 8 === 0)) kick(tr, t, 0.9 * g);
    if (e >= 0.3) noiseBurst(tr, t, 0.04, (step % 2 ? 0.16 : 0.09) * g, rand, { hp: 0.7, decay: 120, pan: 0.25 });
    if (e >= 0.3 && step % 2 === 0)
      tone(tr, t, six * 1.8, hz(deg(chord) - 12), 0.30 * g, { wave: "saw", decay: 7, attack: 0.008 });
    if (e >= 0.6 && step % 2 === 1) {
      const arp = [0, 2, 4, 7][(k >> 1) % 4];
      tone(tr, t, 0.22, hz(deg(chord + arp) + 12), 0.11 * g, { wave: "tri", decay: 14, pan: (k % 4) < 2 ? -0.4 : 0.4 });
    }
    if (e >= 0.85 && step === 0)
      for (const d of [0, 2, 4]) tone(tr, t, beat * 4, hz(deg(chord + d)), 0.05 * g, { wave: "saw", decay: 0.6,
        attack: 0.15, pan: d ? (d === 2 ? -0.5 : 0.5) : 0 });
  }
}

// --- mix and write ------------------------------------------------------------------------------------------

function sidechain(bed, kicks, beat) {                 // the bed ducks under every kick and hit, then breathes back
  for (const t0 of kicks) {
    const i0 = Math.round(t0 * SR), n = Math.floor(beat * 0.8 * SR);
    for (let k = 0; k < n && i0 + k < bed.n; k++) {
      if (i0 + k < 0) continue;
      const d = 1 - 0.55 * Math.exp(-(k / SR) * 9);
      bed.L[i0 + k] *= d; bed.R[i0 + k] *= d;
    }
  }
}

function wav(L, R) {
  const n = L.length, buf = Buffer.alloc(44 + n * 4);
  buf.write("RIFF", 0); buf.writeUInt32LE(36 + n * 4, 4); buf.write("WAVEfmt ", 8);
  buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22); buf.writeUInt32LE(SR, 24);
  buf.writeUInt32LE(SR * 4, 28); buf.writeUInt16LE(4, 32); buf.writeUInt16LE(16, 34);
  buf.write("data", 36); buf.writeUInt32LE(n * 4, 40);
  for (let i = 0; i < n; i++) {
    buf.writeInt16LE(Math.round(Math.max(-1, Math.min(1, L[i])) * 32767), 44 + i * 4);
    buf.writeInt16LE(Math.round(Math.max(-1, Math.min(1, R[i])) * 32767), 46 + i * 4);
  }
  return buf;
}

export function render(score) {
  const dur = score.duration, rand = rng(score.seed ?? 1), gains = { bed: 0.55, cues: 0.9, ...(score.gain ?? {}) };
  const bed = new Track(dur), fx = new Track(dur);
  renderBed(bed, score, score.bed, gains.bed, rand);
  const cues = (score.cues ?? []).filter((c) => CUES[c.kind]);
  for (const c of cues) CUES[c.kind](fx, c, gains.cues * (c.gain ?? 1), rand);
  sidechain(bed, cues.filter((c) => ["hit", "thump"].includes(c.kind)).map((c) => c.t), 60 / score.bpm);
  const L = new Float32Array(bed.n), R = new Float32Array(bed.n);
  const fade = score.bed?.fade_out ?? 0, fadeFrom = dur - fade;
  let peak = 1e-9;
  for (let i = 0; i < bed.n; i++) {
    const t = i / SR, f = fade > 0 && t > fadeFrom ? Math.max(0, 1 - (t - fadeFrom) / fade) : 1;
    L[i] = Math.tanh(1.2 * (bed.L[i] * f + fx.L[i]));   // soft clip glues the mix
    R[i] = Math.tanh(1.2 * (bed.R[i] * f + fx.R[i]));
    peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i]));
  }
  const norm = 0.89 / peak;                            // -1 dBFS peak; the runner sets the final loudness
  for (let i = 0; i < L.length; i++) { L[i] *= norm; R[i] *= norm; }
  return { L, R, unknown: (score.cues ?? []).filter((c) => !CUES[c.kind]).map((c) => c.kind) };
}

function grid(bpm, seconds) {
  const beat = 60 / bpm, beats = [];
  for (let t = 0; t <= seconds + 1e-9; t += beat) beats.push(+t.toFixed(3));
  return { bpm, beat: +beat.toFixed(4), sixteenth: +(beat / 4).toFixed(4), beats, downbeats: beats.filter((_, i) => i % 4 === 0) };
}

const args = process.argv.slice(2);
if (!args.length || args[0] === "--help" || args[0] === "-h") {
  console.log(HELP);
} else if (args[0] === "--grid") {
  console.log(JSON.stringify(grid(Number(args[1]), Number(args[2] ?? 15))));
} else {
  const score = JSON.parse(readFileSync(args[0], "utf8"));
  if (!(score.duration > 0) || !(score.bpm > 0)) throw new Error("score needs duration and bpm");
  const out = args[1] ?? "composition/assets/soundtrack.wav";
  const { L, R, unknown } = render(score);
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, wav(L, R));
  if (unknown.length) console.error(`skipped unknown cue kinds: ${[...new Set(unknown)].join(", ")}`);
  console.log(`${out}: ${score.duration}s, ${score.bpm} BPM, ${(score.cues ?? []).length} cues`);
}
