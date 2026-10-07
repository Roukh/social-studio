"""End to end through the real sandbox, renderer and encoder, with a stub harness (no LLM, no cost).

Skipped unless bubblewrap, ffmpeg and the pinned engine are installed in a project (`social-studio
engine install`) found from SOCIAL_STUDIO_PROJECT or the current folder; the test project borrows it.
"""
from __future__ import annotations

import json
import shutil
import stat
from pathlib import Path

import pytest

from social_studio import db, engine, runner
from social_studio.core import PROJECT_FILE, dump_toml, make_ctx

VERSION = "0.8.106"
REAL = make_ctx()
READY = (REAL.project is not None and shutil.which("bwrap") and shutil.which("ffmpeg")
         and engine.hf_bin(REAL, VERSION).exists() and engine.skills_root(REAL, VERSION).is_dir())

STUB = """#!/bin/sh
# Stands in for a harness: writes the agent's output contract and animates one word.
cat > video.json <<'JSON'
{"title": "Stub video", "description": "Integration test.", "pillar": "principle", "topic": "stub", "angle": "stub",
 "captions": {"default": "A stub."}, "poster_at": 1.0}
JSON
sed -i 's#<!-- Each visible element.*-->#<h1 id="t" class="clip" data-start="0" data-duration="3" data-track-index="0" style="font-size:120px;margin:400px 80px">Stub</h1>#' composition/index.html
sed -i 's#// Build every animation on `tl`.*#tl.fromTo("\\#t", {opacity: 0}, {opacity: 1, duration: 1}, 0);#' composition/index.html
# The maker's own look at its work, as TASK.md tells it: a draft render, then the sampler. render/ is not its own.
hyperframes render composition --format mp4 --quality draft --fps 30 --no-browser-gpu -o drafts/draft.mp4 >drafts/render.log 2>&1
python3 tools/sampler.py drafts/draft.mp4 evidence --fps 30 --safe 0.12,0.25,0.06,0.1 --poster 1.0 >evidence.json 2>&1
if touch ../render/agent-was-here 2>/dev/null; then echo '{"render_writable": true}'; else echo '{"render_writable": false}'; fi >render.json
"""


@pytest.mark.skipif(not READY, reason="needs bwrap, ffmpeg and `social-studio engine install`")
def test_parallel_batch_through_sandbox(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "stub-not-used")
    stub = tmp_path / "bin" / "claude"
    stub.parent.mkdir()
    stub.write_text(STUB)
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    (tmp_path / "repo" / ".git").mkdir(parents=True)
    proj = tmp_path / "repo" / "social"
    proj.mkdir()
    (proj / PROJECT_FILE).write_text(dump_toml({
        "backend": {"default": "claude", "claude": {"bin": str(stub), "auth": "api-key"}},
        "sandbox": {"enabled": True}, "paths": {"library": "library"}}))
    monkeypatch.setenv("SOCIAL_STUDIO_PROJECT", str(proj))
    ctx = make_ctx()
    # Borrow the installed engine and its pinned Chrome instead of downloading them again.
    ctx.engine_dir.mkdir(parents=True)
    (ctx.engine_dir / f"hyperframes-{VERSION}").symlink_to(engine.engine_root(REAL, VERSION))
    ctx.cache_dir.symlink_to(REAL.cache_dir)
    opts = runner.MakeOpts(preset="example", count=2, parallel=2, review=False, sets={"video.duration": [3, 3]})
    results = runner.make(ctx, opts)
    assert [r["ok"] for r in results] == [True, True], results
    con = db.connect(ctx)
    rows = db.rows(con.execute("SELECT id, status, width, height, duration, file FROM videos ORDER BY id"))
    assert [r["status"] for r in rows] == ["review", "review"]
    for r in rows:
        assert (r["width"], r["height"]) == (1080, 1920) and 2.5 <= r["duration"] <= 3.5
        qa = json.loads((ctx.abs(r["file"]).parent / "qa.json").read_text())   # the gates ran on the filed video
        assert "error" not in qa and qa["gates"]["min_px"] == "ok" and qa["gates"]["safe_zone"] == "ok", qa
        assert r["file"].startswith("library/") and ctx.abs(r["file"]).stat().st_size > 1000
    sessions = db.rows(con.execute("SELECT status, sandbox FROM sessions"))
    assert all(s["status"] == "ok" and s["sandbox"] == 1 for s in sessions)
    meta = json.loads(con.execute("SELECT meta FROM videos LIMIT 1").fetchone()[0])
    assert meta["video"]["title"] == "Stub video"
    for d in ctx.sessions_dir.iterdir():                     # finished sessions keep notes, not copies
        assert not (d / "home").exists() and not (d / "work" / "composition").exists()
        evidence = json.loads((d / "work" / "evidence.json").read_text())   # the maker saw its own draft in the jail
        assert evidence["settled"] and evidence["poster"]["t"] == 1.0, evidence
        assert json.loads((d / "work" / "render.json").read_text()) == {"render_writable": False}
    # A revision replaces its predecessor: the old files and sessions go, the row stays as history.
    first = db.get_video(con, rows[0]["id"])
    old_dir, old_session = ctx.abs(first["dir"]), ctx.sessions_dir / first["session_id"]
    revised = runner.make(ctx, runner.MakeOpts(preset="example", revise=first["id"], review=False,
                                               sets={"video.duration": [3, 3]}))
    assert revised[0]["ok"], revised
    first = db.get_video(con, first["id"])
    assert first["status"] == "superseded" and (first["dir"], first["file"]) == ("", "")
    assert not old_dir.exists() and not old_session.exists()
    assert db.get_video(con, revised[0]["video_id"])["parent_id"] == first["id"]
    assert len(list(ctx.library_dir.iterdir())) == 2
