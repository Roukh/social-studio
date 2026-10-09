"""Iteration 1 of the reference look (reference-look-plan; rulings 15, 16, 18, 19): per-run format flags, the reel
preset with vendored Three.js, variable fonts and an import map, vendored third-party skills pinned in a lock file,
sound in the brief, the loudness gate, and the session's synthesizer."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from social_studio import cli, core, engine, qa, runner
from social_studio.core import PKG_DIR, PROJECT_FILE, UsageError, dump_toml, format_sets, load_preset, make_ctx

SOUND = PKG_DIR / "data" / "tools" / "sound.mjs"


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    (tmp_path / "repo" / ".git").mkdir(parents=True)
    proj = tmp_path / "repo" / "social"
    proj.mkdir()
    (proj / PROJECT_FILE).write_text(dump_toml({"paths": {"library": "library"},
                                                "backend": {"claude": {"auth": "api-key"}}}))
    monkeypatch.setenv("SOCIAL_STUDIO_PROJECT", str(proj))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("SOCIAL_STUDIO_ROLE", raising=False)
    return make_ctx()


@pytest.fixture
def engine_stub(tmp_path, monkeypatch):
    """The engine files the reel preset needs: its engine skills, GSAP and the two Three.js module files."""
    root = tmp_path / "engine"
    for name in {*load_preset(make_ctx(), "reel").get("agent.engine_skills"), *runner.KIT_ENGINE_SKILLS}:
        (root / "skills" / name).mkdir(parents=True)
        (root / "skills" / name / "SKILL.md").write_text(f"# {name}\n")
    for rel, text in (("gsap/dist/gsap.min.js", "/* gsap */"),
                      *((rel, f"/* {rel} */") for rel in engine.KIT_GSAP_PLUGINS.values()),
                      ("three/build/three.module.min.js", 'import{a}from"./three.core.min.js";'),
                      ("three/build/three.core.min.js", "export const a=1;")):
        (root / "node_modules" / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / "node_modules" / rel).write_text(text)
    monkeypatch.setattr(engine, "skills_root", lambda ctx, version: root / "skills")
    return root


def prepared(ctx, engine_stub, overrides=None):
    p = load_preset(ctx, "reel", overrides or {})
    s = runner.Session("20261006-120000-abcd", ctx.sessions_dir / "20261006-120000-abcd")
    runner.prepare(ctx, p, s, "0.8.106", engine_stub, "showreel", [], None)
    return p, s


# --- per-run format (ruling 15) ------------------------------------------------------------------------------

def test_format_sets_map_the_flags_to_preset_keys():
    assert format_sets("16:9", 60, "15", "bed+sfx", 3) == {
        "video.width": 1920, "video.height": 1080, "video.safe_zone": core.TITLE_SAFE, "video.fps": 60,
        "video.duration": [15, 15], "video.sound": "bed+sfx", "agent.rounds": 3}
    assert format_sets("9:16") == {"video.width": 1080, "video.height": 1920}  # keeps the preset's platform zone
    assert format_sets(duration="10-18") == {"video.duration": [10, 18]}
    assert format_sets(duration="12.5") == {"video.duration": [12.5, 12.5]}
    for bad in ({"duration": "18-10"}, {"duration": "soon"}, {"aspect": "2:1"}, {"sound": "music"}):
        with pytest.raises(UsageError):
            format_sets(**bad)


def test_make_flags_reach_the_preset(ctx, monkeypatch):
    seen = {}
    monkeypatch.setattr(runner, "make", lambda c, opts: seen.update(opts=opts) or [])
    cli.main(["--json", "make", "--preset", "example", "--aspect", "1:1", "--fps", "60", "--duration", "10-12",
              "--sound", "sfx", "--rounds", "4"])
    assert seen["opts"].sets == {"video.width": 1080, "video.height": 1080, "video.safe_zone": core.TITLE_SAFE,
                                 "video.fps": 60, "video.duration": [10, 12], "video.sound": "sfx", "agent.rounds": 4}


# --- the reel preset ------------------------------------------------------------------------------------------

def test_reel_preset_is_valid_from_any_project(ctx):
    p = load_preset(ctx, "reel")
    assert runner.validate_preset(p, ctx) == []     # its fonts and kit live in the package, outside the project repo
    assert (p.get("video.width"), p.get("video.height"), p.get("video.fps")) == (1920, 1080, 60)


def test_shipped_preset_files_pass_the_boundary_but_secrets_never_do(ctx):
    font = PKG_DIR / "presets" / "reel" / "assets" / "fonts" / "Inter-Variable.ttf"
    assert core.path_problem(ctx, font) is None
    assert core.path_problem(ctx, PKG_DIR / "presets" / "reel" / ".env") is not None
    assert core.path_problem(ctx, PKG_DIR / "data") is not None          # only the presets folder is exempt


def test_reel_composition_has_three_by_import_map_and_variable_fonts(ctx, engine_stub):
    _, s = prepared(ctx, engine_stub)
    html = (s.comp / "index.html").read_text()
    imports = json.loads(re.search(r'<script type="importmap">(.*?)</script>', html).group(1))
    assert imports == {"imports": {"three": "./vendor/three.module.min.js"}}
    assert (s.comp / "vendor" / "three.core.min.js").is_file()           # the entry's relative import resolves
    assert 'font-family: "Reel Sans"' in html and "font-weight: 100 900" in html and "font-style: italic" in html
    assert '<script src="assets/reel-kit.js"></script>' in html and 'data-fps="60"' in html
    assert html.index("vendor/gsap.min.js") < html.index("assets/reel-kit.js")


def test_reel_house_rules_and_task_follow_its_format_and_sound(ctx, engine_stub):
    _, s = prepared(ctx, engine_stub)
    house, task = (s.home / runner.HOUSE_FILE).read_text(), (s.work / "TASK.md").read_text()
    assert not re.search(r"\{\{\w+\}\}", house + task), re.findall(r"\{\{\w+\}\}", house + task)
    assert "at least 30 px" in house and "Reels, TikTok" not in house          # landscape: no platform overlay note
    assert "1920×1080 (16:9), 60 fps" in task and "--fps 30" in task              # drafts render at 30
    assert "Sound: a music bed" in task and "node tools/sound.mjs --help" in task
    assert (s.work / "tools" / "sound.mjs").read_bytes() == SOUND.read_bytes()
    _, s = prepared(ctx, engine_stub, {"video.width": 1080, "video.height": 1920, "video.sound": "none"})
    house, task = (s.home / runner.HOUSE_FILE).read_text(), (s.work / "TASK.md").read_text()
    assert "Reels, TikTok and Shorts" in house and "none for this video" in task


def test_reel_mounts_its_skills_with_their_licences(ctx, engine_stub):
    p, s = prepared(ctx, engine_stub)
    mounted = {x.name for x in (s.work / "skills").iterdir()}
    want = {*runner.PACKAGE_SKILLS, *p.get("agent.engine_skills"), *p.get("agent.package_skills"), "reel-look",
            *runner.KIT_ENGINE_SKILLS, *runner.KIT_VENDOR_SKILLS}
    assert mounted == want
    for name in p.get("agent.package_skills"):
        files = {f.name for f in (s.work / "skills" / name).iterdir()}
        assert "SKILL.md" in files and files & set(runner.LICENSE_FILES), name
    bad = load_preset(ctx, "reel", {"agent.package_skills": ["no-such-skill"]})
    assert any("no-such-skill" in e for e in runner.validate_preset(bad, ctx))


# --- vendored skills (ruling 19) ------------------------------------------------------------------------------

def test_vendored_skills_match_their_lock():
    lock = json.loads((runner.VENDOR_DIR / "skills.lock.json").read_text())
    for pack in lock["packs"]:
        root = runner.VENDOR_DIR / pack["name"]
        h = hashlib.sha256()
        for f in sorted(p for p in root.rglob("*") if p.is_file()
                        and not any(part.startswith(".") for part in p.relative_to(root).parts)):
            h.update(str(f.relative_to(root)).encode() + b"\0" + hashlib.sha256(f.read_bytes()).digest())
        assert h.hexdigest() == pack["tree_sha256"], pack["name"]
        assert re.fullmatch(r"[0-9a-f]{40}", pack["sha"]) and pack["licence"] in ("MIT", "Apache-2.0"), pack["name"]
        assert any((root / n).is_file() for n in runner.LICENSE_FILES), pack["name"]
    assert not (runner.VENDOR_DIR / "impeccable" / "scripts").exists()        # its launcher downloads a binary


def test_vendored_skill_names_do_not_shadow_shipped_or_engine_skills():
    names = runner.vendored_skills()
    assert not set(names) & {*runner.PACKAGE_SKILLS, *runner.DEFAULT_SKILLS, "reel-look"}
    assert {"gsap-core", "threejs-webgl", "kinetic-typography", "algorithmic-art", "ui-sound-design"} <= set(names)


# --- sound: the brief's cues, the loudness gate, the synthesizer ----------------------------------------------

def test_audio_gate_reads_cues_at_the_top_of_the_brief():
    brief = {"shots": [{"start": 0, "end": 2}], "cues": [{"t": 1.5, "kind": "hit"}]}
    assert qa.check_audio(brief, has_audio=False)[0]["gate"] == "audio"
    assert qa.check_audio(brief, has_audio=True) == []
    assert qa.check_audio({"shots": [], "cues": []}, has_audio=False) == []


def test_loudness_gate_allows_one_lu_either_side():
    assert qa.check_loudness(None) == [] and qa.check_loudness(-14.6) == []
    assert qa.check_loudness(-16.2)[0]["gate"] == "loudness"
    assert qa.check_loudness(-12.4, target=-14)[0]["detail"].startswith("-12.4 LUFS")


@pytest.mark.skipif(not shutil.which("node"), reason="needs node")
def test_sound_tool_is_deterministic_and_exact_length(tmp_path):
    score = {"duration": 2.0, "bpm": 120, "seed": 3, "bed": {"style": "pulse", "start": 0.0, "fade_out": 0.5},
             "cues": [{"t": 0.5, "kind": "hit"}, {"t": 1.0, "kind": "whoosh"}, {"t": 1.5, "kind": "riser", "dur": 0.5}]}
    (tmp_path / "s.json").write_text(json.dumps(score))
    outs = []
    for name in ("a.wav", "b.wav"):
        subprocess.run(["node", str(SOUND), str(tmp_path / "s.json"), str(tmp_path / name)], check=True,
                       capture_output=True)
        outs.append((tmp_path / name).read_bytes())
    assert outs[0] == outs[1]
    assert outs[0][:4] == b"RIFF" and len(outs[0]) == 44 + 2 * 48000 * 4     # 48 kHz, 16-bit stereo, 2 s
    grid = json.loads(subprocess.run(["node", str(SOUND), "--grid", "120", "2"], check=True, capture_output=True,
                                     text=True).stdout)
    assert grid["beats"] == [0, 0.5, 1, 1.5, 2] and grid["downbeats"] == [0, 2]
