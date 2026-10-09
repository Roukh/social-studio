#!/usr/bin/env python3
"""Split a reference film into scenes for extraction into the reference store (src/social_studio/store.py).

    python3 scripts/split_scenes.py FILM.mp4 OUT_DIR [--threshold 0.3] [--min 0.5] [--every 2.5] [--start S --end S]

Writes into OUT_DIR:
  scenes.json      the film (duration, size, fps) and its scenes [{n, start, end}]
  sheet.jpg        one frame from the middle of every scene, in order, 4 per row
  scene-NN.jpg     each scene as 3 to 6 frames side by side (about one a second), from just after it starts to
                   just before it ends

A cut is a jump in ffmpeg's scene score above --threshold. Cuts closer than --min seconds merge. A film that cuts
less than once every 6 s (one long take, a continuous morph) is cut every --every seconds instead, so its moves
still get separate items. Frames stay local (.local/), never in the package.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def probe(film: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(film)],
                         capture_output=True, text=True, check=True)
    data = json.loads(out.stdout)
    s = data["streams"][0]
    num, den = (int(x) for x in s["r_frame_rate"].split("/"))
    return {"duration": float(data["format"]["duration"]), "width": s["width"], "height": s["height"],
            "fps": round(num / den, 3) if den else None}


def cuts(film: Path, threshold: float, start: float, end: float) -> list[float]:
    out = subprocess.run(["ffmpeg", "-hide_banner", "-ss", str(start), "-to", str(end), "-i", str(film),
                          "-filter:v", f"select='gt(scene,{threshold})',showinfo", "-an", "-f", "null", "-"],
                         capture_output=True, text=True)
    return [start + float(t) for t in re.findall(r"pts_time:([0-9.]+)", out.stderr)]


def scenes(times: list[float], start: float, end: float, min_len: float, every: float) -> list[dict]:
    bounds = [start]
    for t in sorted(times):
        if t - bounds[-1] >= min_len and end - t >= min_len:
            bounds.append(t)
    if (end - start) / len(bounds) > 6 and every > 0:  # a long take: cut it on a fixed step instead
        bounds = [start + i * every for i in range(int((end - start) / every) + 1) if end - (start + i * every) >= min_len]
    bounds.append(end)
    return [{"n": i + 1, "start": round(a, 3), "end": round(b, 3)} for i, (a, b) in enumerate(zip(bounds, bounds[1:]))]


def frame(film: Path, t: float, dst: Path, width: int) -> None:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.3f}", "-i", str(film),
                    "-frames:v", "1", "-vf", f"scale={width}:-2", "-q:v", "3", str(dst)], check=True)


def stack(images: list[Path], dst: Path, per_row: int) -> None:
    """Tile images in rows of per_row (the last row padded with black), as one JPEG."""
    rows = [images[i:i + per_row] for i in range(0, len(images), per_row)]
    inputs, chains, row_labels = [], [], []
    k = 0
    for r, row in enumerate(rows):
        labels = []
        for img in row:
            inputs += ["-i", str(img)]
            labels.append(f"[{k}:v]")
            k += 1
        pad = per_row - len(row)
        if pad:
            chains.append(f"{labels[-1]}split={pad + 1}" + "".join(f"[d{r}_{j}]" for j in range(pad + 1)))
            chains += [f"[d{r}_{j}]drawbox=c=black:t=fill[b{r}_{j}]" for j in range(1, pad + 1)]
            labels = labels[:-1] + [f"[d{r}_0]"] + [f"[b{r}_{j}]" for j in range(1, pad + 1)]
        if per_row == 1:
            chains.append(f"{labels[0]}null[r{r}]")
        else:
            chains.append("".join(labels) + f"hstack=inputs={per_row}[r{r}]")
        row_labels.append(f"[r{r}]")
    chains.append("".join(row_labels) + (f"vstack=inputs={len(rows)}[out]" if len(rows) > 1 else "null[out]"))
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs, "-filter_complex", ";".join(chains),
                    "-map", "[out]", "-q:v", "3", str(dst)], check=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("film", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--threshold", type=float, default=0.3)
    ap.add_argument("--min", type=float, default=0.5, help="shortest scene in seconds")
    ap.add_argument("--every", type=float, default=2.5, help="fixed step for a long take; 0 turns it off")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float)
    a = ap.parse_args(argv)
    info = probe(a.film)
    end = min(a.end or info["duration"], info["duration"])
    found = scenes(cuts(a.film, a.threshold, a.start, end), a.start, end, a.min, a.every)
    a.out.mkdir(parents=True, exist_ok=True)
    tmp = a.out / "frames"
    tmp.mkdir(exist_ok=True)
    thumb = 360 if info["height"] > info["width"] else 480
    mids = []
    for s in found:
        span = s["end"] - s["start"]
        edge = min(0.1, span / 4)
        n = max(3, min(6, round(span)))
        shots = []
        for j in range(n):
            f = tmp / f"s{s['n']:02d}-{j}.jpg"
            frame(a.film, s["start"] + edge + (span - 2 * edge) * j / (n - 1), f, thumb)
            shots.append(f)
        stack(shots, a.out / f"scene-{s['n']:02d}.jpg", n)
        mids.append(shots[n // 2])
    stack(mids, a.out / "sheet.jpg", 4 if info["height"] > info["width"] else 3)
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()
    (a.out / "scenes.json").write_text(json.dumps({"film": str(a.film), **info, "window": [a.start, end],
                                                   "scenes": found}, indent=2))
    print(f"{len(found)} scenes -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
