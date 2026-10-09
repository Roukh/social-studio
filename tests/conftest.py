"""Shared stand-ins for the steps of a build that need the installed engine, Chrome and ffmpeg, so a whole build can
run with stubbed sessions (a real `sclstdio build` cannot start from an agent session, issue I2)."""
from __future__ import annotations

import hashlib

import pytest

from social_studio import engine, runner


@pytest.fixture
def render_stub(monkeypatch):
    """render_master, encode, poster_and_sheet and the QA gates, each writing what the real step would."""
    def render_master(prefix, hf, comp, out, fps, crf=10, timeout=1800, env=None):
        out.write_bytes(b"master of " + (comp / "index.html").read_bytes()[:64])

    def encode(src, dst, enc, fps):
        dst.write_bytes(src.read_bytes())
        data = dst.read_bytes()
        return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "duration": 21.0, "width": 1080,
                "height": 1920, "audio": False}

    def poster_and_sheet(video, poster, sheet, duration, poster_at):
        poster.write_bytes(b"jpg")
        sheet.write_bytes(b"jpg")
    monkeypatch.setattr(engine, "render_master", render_master)
    monkeypatch.setattr(engine, "encode", encode)
    monkeypatch.setattr(engine, "poster_and_sheet", poster_and_sheet)
    monkeypatch.setattr(engine, "hf_bin", lambda ctx, version: ctx.engine_dir / "hyperframes")
    monkeypatch.setattr(engine, "chrome_path", lambda ctx, version: ctx.engine_dir / "chrome" / "chrome")
    monkeypatch.setattr(engine, "node_dirs", lambda ctx: ([], []))
    monkeypatch.setattr(runner, "_qa", lambda *a: {"version": 1, "gates": {}, "findings": []})
