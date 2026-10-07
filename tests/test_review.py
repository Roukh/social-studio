"""The measurement fix (motion-quality-plan A2): samples picked from the video's own motion, anchors filled into the
reviewer's task, the composition's CSS handed over, and the verdict checked in Python."""
from __future__ import annotations

import json
import re
import shutil
import subprocess

import pytest

from social_studio import engine, review
from social_studio.core import Preset, load_preset, make_ctx
from social_studio.runner import DEFAULT_CRITERIA

FPS = 30


def curve(steps: dict[int, tuple[float, float]], last: int) -> list[tuple[float, float, float]]:
    """A motion curve: every step still unless `steps` gives it (mean, block)."""
    return [(n / FPS, *steps.get(n, (0.0, 0.0))) for n in range(1, last + 1)]


def moves() -> tuple[dict, int]:
    """4 s: still, a big move at 1.0-1.5 s, still, a smaller move at 2.5-2.8 s, still with one word inking at 3.5 s."""
    steps = {n: (5.0 + (5 if n == 38 else 0), 50.0) for n in range(31, 46)}
    steps |= {n: (3.0, 30.0) for n in range(76, 85)}
    steps[105] = (0.02, 12.0)                       # one small word: the frame-wide mean barely moves, its block does
    return steps, 119


def test_sampler_lands_in_settled_windows():
    steps, last = moves()
    plan = review.pick_samples(curve(steps, last), FPS)
    moving = set(steps)
    assert plan["settled"] and all(x["kind"] == "settled" for x in plan["settled"])
    for x in plan["settled"]:
        assert not any(x["from"] < m <= x["to"] for m in moving), x    # no hold spans a change, the ink at 3.5 s too
        assert x["from"] <= x["n"] <= x["to"] and (x["to"] - x["from"] + 1) / FPS >= review.HOLD_S
    peaks = [s["peak"] for s in plan["strips"]]
    assert peaks[0] in range(31, 46) and peaks[1] in range(76, 85) and len(peaks) <= review.STRIPS
    first = plan["strips"][0]["frames"]
    assert first[0] == 30 and first[-1] == 45 and len(first) == review.STRIP_FRAMES   # from still to settled


def test_sampler_marks_calmest_frames_when_nothing_holds():
    steps = {n: (1.0, 10.0 + n % 7) for n in range(1, 120)}
    plan = review.pick_samples(curve(steps, 119), FPS)
    assert len(plan["settled"]) == review.MIN_SAMPLES and {x["kind"] for x in plan["settled"]} == {"calmest"}
    times = sorted(x["n"] for x in plan["settled"])
    assert all(b - a >= FPS for a, b in zip(times, times[1:]))


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_samples_from_a_real_encode_stay_within_the_display_limit(tmp_path):
    video = tmp_path / "v.mp4"
    # overlay, not drawbox: in a drawbox expression `t` is the box's thickness, so its box never moves
    move = "x='if(lt(t,1),0,if(lt(t,1.5),(t-1)*800,400))':y=800:eval=frame:shortest=1"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-f", "lavfi", "-i", f"color=c=white:s=1080x1920:d=3:r={FPS}",
                    "-f", "lavfi", "-i", f"color=c=black:s=200x200:d=3:r={FPS}", "-filter_complex", f"[0][1]overlay={move}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)], check=True)
    info = engine.probe(video)
    plan = review.pick_samples(review.motion_curve(video), FPS)
    manifest = review.write_samples(video, plan, tmp_path, info)
    assert all(x["t"] < 1.0 or x["t"] > 1.5 for x in manifest["settled"])            # never inside the move
    assert manifest["strips"] and 1.0 <= manifest["strips"][0]["peak"] <= 1.5
    files = [manifest["first"]["file"], *(x["file"] for x in manifest["settled"]), *(s["file"] for s in manifest["strips"])]
    for rel in files:
        dims = engine.probe(tmp_path / rel)
        assert max(dims["width"], dims["height"]) <= review.PAGE_PX, rel
    assert json.loads((tmp_path / "samples.json").read_text()) == manifest


def test_reviewer_task_has_anchors_and_no_unfilled_placeholders(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.setenv("SOCIAL_STUDIO_PROJECT", str(tmp_path))
    p = load_preset(make_ctx(), "example")
    text = review.task_text(p, [1080, 1920])
    assert not re.search(r"\{\{\w+\}\}", text)
    for c in p.get("review.criteria", DEFAULT_CRITERIA):
        assert f"**{c}**" in text
    assert "at least 30 px" in text and "y from 230 to 1440 px" in text             # example safe zone 0.12 / 0.25
    custom = Preset("x", tmp_path, {**p.data, "review": {**p.data["review"], "criteria": ["pacing"]}})
    assert "**pacing** (judge on the samples)" in review.task_text(custom, [1080, 1920])


def test_composition_css_reaches_the_reviewer(tmp_path):
    (tmp_path / "vendor").mkdir()
    (tmp_path / "vendor" / "lib.css").write_text(".lib { color: red; }")
    (tmp_path / "theme.css").write_text(".card { box-shadow: 0 40px 80px -40px rgba(40,0,110,.6); }")
    (tmp_path / "index.html").write_text('<style>.label { font-size: 26px; }</style>'
                                         '<div id="pill" style="font-size:18px">Sample</div>')
    css = review.composition_css(tmp_path)
    assert "font-size: 26px" in css and "box-shadow" in css and "pill { font-size:18px }" in css
    assert ".lib" not in css


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_rescore_measures_the_reviewer_and_leaves_the_video_alone(tmp_path, monkeypatch, capsys):
    from social_studio import cli, db, runner
    from social_studio.core import PROJECT_FILE, dump_toml
    (tmp_path / ".git").mkdir()
    (tmp_path / PROJECT_FILE).write_text(dump_toml({"paths": {"library": "library"}}))
    monkeypatch.setenv("SOCIAL_STUDIO_PROJECT", str(tmp_path))
    ctx = make_ctx()
    folder = ctx.library_dir / "v1"
    (folder / "composition").mkdir(parents=True)
    (folder / "composition" / "index.html").write_text("<style>.t { font-size: 96px; }</style>")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                    f"color=c=white:s=1080x1920:d=2:r={FPS}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    str(folder / "video.mp4")], check=True)
    shutil.copy2(folder / "video.mp4", folder / "contact.jpg")
    (folder / "video.json").write_text('{"title": "One"}')
    maker = ctx.sessions_dir / "20261001-000000-aaaa" / "work"
    maker.mkdir(parents=True)
    (maker / "history.json").write_text('[{"topic": "seen by the maker"}]')
    con = db.connect(ctx, actor="test")
    con.execute("INSERT INTO sessions (id, kind, preset, preset_hash, backend, sandbox, dir, status, started_at)"
                " VALUES ('20261001-000000-aaaa', 'make', 'example', 'h', 'claude', 1, 'x', 'ok', 'now')")
    vid = con.execute("INSERT INTO videos (session_id, slug, title, preset, dir, file, sha256, bytes, duration, width,"
                      " height, created_at, updated_at, meta) VALUES ('20261001-000000-aaaa', 'one', 'One', 'example',"
                      " ?, ?, 'x', 1, 2.0, 1080, 1920, 'now', 'now', '{\"verdict\": {\"pass\": true}}')",
                      (ctx.rel(folder), ctx.rel(folder / "video.mp4"))).lastrowid
    con.close()
    crit, seen, given = DEFAULT_CRITERIA, iter([7, 9]), []

    def fake_reviewer(ctx, s, *a, **k):                       # each run scores motion differently, all else 8
        given.append({f.name: f.read_text() for f in s.work.glob("*.json")})
        assert (s.work / "composition.css").read_text().count("96px") and (s.work / "samples.json").is_file()
        n = next(seen)
        (s.work / "verdict.json").write_text(json.dumps({"pass": n >= 8, "scores": {c: n if c == "motion quality"
                                                         else 8 for c in crit}, "repeat": {"found": False, "of": ""},
                                                         "issues": [], "summary": "s"}))
        return 0
    monkeypatch.setattr(review, "resolve_backend", lambda *a, **k: runner.Backend("claude", "sonnet", tmp_path, True))
    monkeypatch.setattr(review, "backend_command", lambda *a, **k: ([], {}, [], []))
    monkeypatch.setattr(review, "run_jailed", fake_reviewer)
    assert cli.main(["--json", "review", "rescore", str(vid)]) == 0
    res = json.loads(capsys.readouterr().out)
    assert [r["scores"]["motion quality"] for r in res["runs"]] == [7, 9]
    assert res["spread"]["motion quality"] == 2 and res["spread"]["composition"] == 0 and res["mean"]["motion quality"] == 8
    assert all(g["history.json"] == '[{"topic": "seen by the maker"}]' for g in given)   # what the maker saw
    assert all(json.loads(g["preset.json"])["video"]["width"] == 1080 for g in given)    # rebuilt from the preset
    con = db.connect(ctx)
    row = db.get_video(con, vid)
    kinds = [r[0] for r in con.execute("SELECT kind FROM sessions WHERE id LIKE '%-review'")]
    con.close()
    assert row["meta"] == '{"verdict": {"pass": true}}' and row["status"] == "review"    # the video is untouched
    assert kinds == ["review", "review"] and not list(ctx.sessions_dir.glob("rescore-*"))
    for r in res["runs"]:                                     # trimmed to its notes, the verdict kept
        work = ctx.sessions_dir / r["session"] / "work"
        assert (work / "verdict.json").is_file() and not (work / "samples").exists()
    con = db.connect(ctx, actor="test")
    con.executescript("DROP TRIGGER videos_transition; DROP TRIGGER videos_need_approval;")
    con.execute("UPDATE videos SET status = 'scheduled' WHERE id = ?", (vid,))
    con.close()
    assert cli.main(["--json", "review", "rescore", str(vid)]) == 77            # an agent never sees a scheduled video
    con = db.connect(ctx, actor="test")
    con.execute("UPDATE videos SET status = 'superseded', file = '' WHERE id = ?", (vid,))
    con.close()
    assert cli.main(["--json", "review", "rescore", str(vid)]) == 65            # nothing left on disk to review


def test_verdict_is_checked_in_python():
    crit = ["hook", "motion"]
    good = {"pass": True, "scores": {"hook": 9, "motion": 8}, "repeat": {"found": False, "of": ""},
            "issues": [], "summary": "fine"}
    assert review.check_verdict(good, crit, 8)["pass"] is True
    low = review.check_verdict({**good, "scores": {"hook": 9, "motion": 7}}, crit, 8)
    assert low["pass"] is False and low["checked"]["below_min"] == ["motion"]
    rep = review.check_verdict({**good, "repeat": {"found": True, "of": "2026-10-01 the-path"}}, crit, 8)
    assert rep["pass"] is False and rep["scores"] == good["scores"]                   # a repeat never moves a score
    for bad in ({"scores": {"hook": 9}}, {"scores": {"hook": 11, "motion": 8}}, {"scores": {"hook": "9", "motion": 8}},
                {"scores": {"hook": True, "motion": 8}}, {"scores": {"hook": 9, "motion": 8, "variety": 3}},
                {"pass": "yes"}, {"repeat": None}, {"issues": "none"}):
        out = review.check_verdict({**good, **bad}, crit, 8)
        assert out["pass"] is None and "failed its check" in out["error"], bad
