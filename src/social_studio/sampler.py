"""Frames a model can judge a video by, picked from the video's own motion. Standard library and ffmpeg only, with no
package imports: the runner copies this file into each maker session (tools/sampler.py) so the maker can look at its
own draft render, and the reviewer and the quality checks use the same picks.

  settled-NN.png  every hold where nothing on screen changes for HOLD_S or longer, at full size: text and contrast
  strip-N.jpg     the STRIPS biggest moves, STRIP_FRAMES frames each from just before the move to its settle: motion
  frame-0.png     the first frame: the hook
  poster.png      the poster frame, when a time is given

  python3 sampler.py VIDEO OUTDIR [--fps 30] [--safe TOP,BOTTOM,LEFT,RIGHT] [--poster SECONDS]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

STILL = 2.0          # a step is still when no 10x10 block of the 180x320 grey difference averages above this (0-255)
HOLD_S = 0.3         # a settled hold shows the same picture for at least this long
MAX_SETTLED = 10
MIN_SAMPLES = 3      # with fewer holds than this, the calmest frames are added and marked as such
STRIPS = 3
STRIP_FRAMES = 6
PEAK_GAP_S = 1.0
HALF_MOVE_S = 0.75   # a strip reaches at most this far either side of its peak
PAGE_PX = 2000       # the most a page shown to a model may measure on either side
PAD = 8


def probe(video: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(video)],
                         capture_output=True, text=True, check=True)
    info = json.loads(out.stdout)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    return {"width": int(v["width"]), "height": int(v["height"]),
            "duration": float(info["format"].get("duration") or v.get("duration") or 0),
            "audio": any(s["codec_type"] == "audio" for s in info["streams"])}


def motion_curve(video: Path) -> list[tuple[float, float, float]]:
    """(time, mean change, largest 10x10-block change) for every frame after the first, against the frame before it,
    on a 180x320 grey copy. The block maximum sees one word inking that the frame-wide mean would miss."""
    vf = "scale=180:320,format=gray,tblend=all_mode=difference,scale=18:32:flags=area,signalstats,metadata=print:file=-"
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-loglevel", "error", "-i", str(video), "-an",
                          "-vf", vf, "-f", "null", "-"], capture_output=True, text=True, check=True).stdout
    frames: list[dict] = []
    for line in out.splitlines():
        if m := re.search(r"pts_time:([\d.]+)", line):
            frames.append({"t": float(m.group(1))})
        elif frames and (m := re.match(r"lavfi\.signalstats\.(YAVG|YMAX)=([\d.]+)", line.strip())):
            frames[-1][m.group(1)] = float(m.group(2))
    return [(f["t"], f.get("YAVG", 0.0), f.get("YMAX", 0.0)) for f in frames]


def pick_samples(curve: list[tuple[float, float, float]], fps: int) -> dict:
    """Frame numbers to show: the middle of every settled hold, strips over the biggest moves, frame 0."""
    mean = {round(t * fps): m for t, m, _ in curve}
    block = {round(t * fps): b for t, _, b in curve}
    last = max(block, default=0)
    holds, run = [], []
    for n in range(1, last + 2):
        if n <= last and block.get(n, STILL + 1) <= STILL:
            run.append(n)
        elif run:
            if (len(run) + 1) / fps >= HOLD_S:
                holds.append((run[0] - 1, run[-1]))
            run = []
    holds = sorted(sorted(holds, key=lambda h: h[0] - h[1])[:MAX_SETTLED])
    settled = [{"n": (a + b) // 2, "from": a, "to": b, "kind": "settled"} for a, b in holds]
    calm = sorted(range(1, last), key=lambda n: max(block.get(n, 0), block.get(n + 1, 0)))
    for n in calm if len(settled) < MIN_SAMPLES else ():
        if all(abs(n - x["n"]) >= fps for x in settled):
            settled.append({"n": n, "from": n, "to": n, "kind": "calmest"})
        if len(settled) >= MIN_SAMPLES:
            break
    smooth = {n: sum(mean.get(k, 0) for k in range(n - 2, n + 3)) / 5 for n in block}
    strips, half = [], round(HALF_MOVE_S * fps)
    for p in sorted(smooth, key=lambda n: -smooth[n]):
        if len(strips) == STRIPS:
            break
        if block[p] <= STILL or any(abs(p - s["peak"]) < PEAK_GAP_S * fps for s in strips):
            continue
        a, b = p, p
        while a - 1 >= 1 and block.get(a - 1, 0) > STILL and p - (a - 1) <= half:
            a -= 1
        while b + 1 <= last and block.get(b + 1, 0) > STILL and (b + 1) - p <= half:
            b += 1
        span = b - (a - 1)
        strips.append({"peak": p, "frames": sorted({round(a - 1 + k * span / (STRIP_FRAMES - 1))
                                                     for k in range(STRIP_FRAMES)})})
    return {"fps": fps, "frames": last + 1, "settled": sorted(settled, key=lambda x: x["n"]),
            "strips": sorted(strips, key=lambda s: s["peak"])}


def _grab(video: Path, frames: list[int], out: Path, vf: str) -> None:
    pick = "select=" + "+".join(f"eq(n\\,{n})" for n in sorted(set(frames)))
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video), "-an", "-vf", f"{pick},{vf}",
                    "-fps_mode", "passthrough", "-q:v", "3", str(out)], check=True)


def _safe_box(w: int, h: int, safe: dict) -> str:
    """A red outline of the safe zone: text belongs inside it."""
    x0, y0 = round(w * safe.get("left", 0.06)), round(h * safe.get("top", 0.12))
    x1, y1 = round(w * (1 - safe.get("right", 0.10))), round(h * (1 - safe.get("bottom", 0.25)))
    return f"drawbox=x={x0}:y={y0}:w={x1 - x0}:h={y1 - y0}:color=red@0.8:t=3,"


def write_samples(video: Path, plan: dict, work: Path, info: dict, safe: dict | None = None,
                  poster_at: float | None = None) -> dict:
    """Render the plan into work/samples/ and describe it in work/samples.json. No page exceeds PAGE_PX. With `safe`,
    the full-size frames carry the safe-zone outline."""
    out = work / "samples"
    out.mkdir(parents=True, exist_ok=True)
    fps, w, h = plan["fps"], info["width"], info["height"]
    fit = min(1.0, PAGE_PX / max(w, h))
    box = _safe_box(w, h, safe) if safe is not None else ""
    full = f"{box}scale={int(w * fit) // 2 * 2}:{int(h * fit) // 2 * 2}"
    cell = min(w, (PAGE_PX - PAD * (STRIP_FRAMES + 1)) // STRIP_FRAMES) // 2 * 2
    sec = lambda n: round(n / fps, 2)  # noqa: E731
    _grab(video, [0], out / "frame-0.png", full)
    if plan["settled"]:
        _grab(video, [x["n"] for x in plan["settled"]], out / "settled-%02d.png", full)
    for i, s in enumerate(plan["strips"], 1):
        _grab(video, s["frames"], out / f"strip-{i}.jpg",
              f"scale={cell}:-2,tile={STRIP_FRAMES}x1:padding={PAD}:margin={PAD}:color=white")
    manifest = {
        "fps": fps, "duration_s": round(info["duration"], 2), "size": [int(w * fit) // 2 * 2, int(h * fit) // 2 * 2],
        "first": {"file": "samples/frame-0.png", "t": 0.0},
        "settled": [{"file": f"samples/settled-{i:02d}.png", "t": sec(x["n"]), "kind": x["kind"],
                     "still_from": sec(x["from"]), "still_to": sec(x["to"])} for i, x in enumerate(plan["settled"], 1)],
        "strips": [{"file": f"samples/strip-{i}.jpg", "peak": sec(s["peak"]), "frames_at": [sec(n) for n in s["frames"]]}
                   for i, s in enumerate(plan["strips"], 1)],
    }
    if poster_at is not None:
        _grab(video, [min(round(poster_at * fps), plan["frames"] - 1)], out / "poster.png", full)
        manifest["poster"] = {"file": "samples/poster.png", "t": poster_at}
    (work / "samples.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Pick the frames worth judging from a rendered video.")
    ap.add_argument("video", type=Path)
    ap.add_argument("outdir", type=Path, help="gets samples/ and samples.json")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--safe", help="safe zone as top,bottom,left,right fractions, drawn on the full-size frames")
    ap.add_argument("--poster", type=float, help="also grab the poster frame at this time, in seconds")
    a = ap.parse_args(argv)
    safe = dict(zip(("top", "bottom", "left", "right"), map(float, a.safe.split(",")))) if a.safe else None
    manifest = write_samples(a.video, pick_samples(motion_curve(a.video), a.fps), a.outdir, probe(a.video), safe, a.poster)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
