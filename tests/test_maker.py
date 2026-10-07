"""The maker's harness (motion-quality-plan B2, C1, D1, F1): effort per role, house rules through each harness's own
system channel, a brief with no unfilled placeholders, revisions that never carry scores, and draft renders the
maker can look at but never a write into render/."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from social_studio import cli, core, engine, runner, sampler
from social_studio.core import PKG_DIR, PROJECT_FILE, dump_toml, load_preset, make_ctx, validate_preset


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    (tmp_path / "repo" / ".git").mkdir(parents=True)
    proj = tmp_path / "repo" / "social"
    proj.mkdir()
    (proj / PROJECT_FILE).write_text(dump_toml({"paths": {"library": "library"},
                                                "backend": {"claude": {"auth": "api-key"}}}))
    monkeypatch.setenv("SOCIAL_STUDIO_PROJECT", str(proj))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("SOCIAL_STUDIO_ROLE", raising=False)
    return make_ctx()


@pytest.fixture
def engine_stub(tmp_path, monkeypatch):
    """Just enough of an installed engine for prepare(): two engine skills and the vendored GSAP file."""
    root = tmp_path / "engine"
    for name in runner.DEFAULT_SKILLS:
        (root / "skills" / name).mkdir(parents=True)
        (root / "skills" / name / "SKILL.md").write_text(f"# {name}\n")
    (root / "node_modules" / "gsap" / "dist").mkdir(parents=True)
    (root / "node_modules" / "gsap" / "dist" / "gsap.min.js").write_text("/* gsap */")
    monkeypatch.setattr(engine, "skills_root", lambda ctx, version: root / "skills")
    return root


def session(ctx, name="20261002-120000-abcd") -> runner.Session:
    return runner.Session(name, ctx.sessions_dir / name)


def prepared(ctx, engine_stub, overrides=None, revise=None):
    p = load_preset(ctx, "example", overrides or {})
    s = session(ctx)
    runner.prepare(ctx, p, s, "0.8.106", engine_stub, None, [], revise)
    return p, s


def backend(name: str) -> runner.Backend:
    return runner.Backend(name, {"claude": "sonnet", "codex": "gpt-5", "opencode": "openai/gpt-5"}[name],
                          Path(shutil.which("true") or "/bin/true"), True)


def test_brief_and_house_rules_are_fully_filled(ctx, engine_stub):
    p, s = prepared(ctx, engine_stub, {"video.pacing": "calm, long holds"})
    task, house = (s.work / "TASK.md").read_text(), (s.home / runner.HOUSE_FILE).read_text()
    for text in (task, house):
        assert not re.search(r"\{\{\w+\}\}", text), re.findall(r"\{\{\w+\}\}", text)
    assert "at least 30 px" in house and "at most 20% of the runtime" in house and '"Try it free for 14 days."' in house
    assert "--safe 0.12,0.25,0.06,0.1" in task and "Pacing: calm, long holds." in task
    assert "2 times in total" in task and "min_score" not in task and str(p.get("review.min_score")) + " " not in task
    assert (s.work / "tools" / "sampler.py").read_bytes() == (PKG_DIR / "sampler.py").read_bytes()
    assert not (s.work / "CLAUDE.md").exists() and not (s.work / "AGENTS.md").exists()   # never in the work folder


def test_the_motion_doctrine_and_canon_mount_beside_the_engine_skills(ctx, engine_stub, monkeypatch):
    p, s = prepared(ctx, engine_stub)
    mounted = sorted(x.name for x in (s.work / "skills").iterdir())
    assert mounted == sorted([*runner.PACKAGE_SKILLS, *runner.DEFAULT_SKILLS])
    doctrine = s.work / "skills" / "motion-doctrine"
    assert (doctrine / "SKILL.md").is_file() and (doctrine / "LICENSE").is_file() and (doctrine / "NOTICE.md").is_file()
    assert (s.work / "skills" / "motion-canon" / "SKILL.md").is_file()
    task = (s.work / "TASK.md").read_text()                # ruling 16: no redirect away from the engine's adapters
    assert "use `skills/motion-doctrine` instead" not in task and "adapters/three.md" in task
    index = (doctrine / "blueprints.md").read_text()
    for f in (doctrine / "blueprints").glob("*.md"):                     # every blueprint a shot can name is indexed
        assert f.stem in index, f.stem
    monkeypatch.setattr(core, "is_tty", lambda: True)
    taken = load_preset(ctx, "example", {"agent.skills": {"motion-doctrine": "mine"}})
    with pytest.raises(runner.ConfigError, match="taken"):
        runner._skills(ctx, taken, session(ctx, "20261002-120000-ffff"), "0.8.106")


def test_house_rules_reach_each_harness_through_its_own_channel(ctx, engine_stub):
    p, s = prepared(ctx, engine_stub)
    house = s.home / runner.HOUSE_FILE
    argv, env, _, _ = runner.backend_command(ctx, p, backend("claude"), s, "go", [])
    assert argv[argv.index("--append-system-prompt-file") + 1] == str(house)
    assert int(env["BASH_DEFAULT_TIMEOUT_MS"]) >= 600_000
    runner.backend_command(ctx, p, backend("codex"), s, "go", [])
    assert (s.home / ".codex" / "AGENTS.md").read_text() == house.read_text()
    _, env, _, _ = runner.backend_command(ctx, p, backend("opencode"), s, "go", [])
    assert json.loads(env["OPENCODE_CONFIG_CONTENT"])["instructions"] == [str(house)]
    argv, _, _, _ = runner.backend_command(ctx, p, backend("claude"), s, "go", [], review=True)
    assert "--append-system-prompt-file" not in argv                       # the reviewer has its own task


def test_effort_and_limits_are_per_role(ctx, engine_stub):
    p, s = prepared(ctx, engine_stub, {"agent.effort": "max", "agent.allow_web": True, "agent.max_budget_usd": 3,
                                       "review.effort": "high"})
    maker, _, _, _ = runner.backend_command(ctx, p, backend("claude"), s, "go", [])
    assert maker[maker.index("--effort") + 1] == "max" and "--max-budget-usd" in maker and "WebFetch" not in maker
    rev, _, _, _ = runner.backend_command(ctx, p, backend("claude"), s, "go", [], review=True)
    assert rev[rev.index("--effort") + 1] == "high" and "--max-budget-usd" not in rev and "WebFetch" in rev
    codex, _, _, _ = runner.backend_command(ctx, p, backend("codex"), s, "go", [])
    assert 'model_reasoning_effort="xhigh"' in codex                       # codex has no max
    oc, _, _, _ = runner.backend_command(ctx, p, backend("opencode"), s, "go", [])
    assert oc[oc.index("-m") + 1] == "openai/gpt-5#max"
    plain = load_preset(ctx, "example")
    argv, _, _, _ = runner.backend_command(ctx, plain, backend("claude"), s, "go", [], review=True)
    assert "--effort" not in argv                                          # unset: the harness default, never agent's


def test_effort_pacing_and_motion_are_set_from_the_cli(ctx, monkeypatch):
    seen = {}
    monkeypatch.setattr(runner, "make", lambda c, opts: seen.update(opts=opts) or [])
    cli.main(["--json", "make", "--preset", "example", "--effort", "high", "--review-effort", "low",
              "--pacing", "reel, 2 to 4 s a beat", "--motion", "per-word ink and blur-up"])
    assert seen["opts"].sets == {"agent.effort": "high", "review.effort": "low", "video.pacing": "reel, 2 to 4 s a beat",
                                 "video.motion": "per-word ink and blur-up"}
    with pytest.raises(SystemExit):
        cli.main(["--json", "make", "--effort", "turbo"])


def test_a_motion_signature_wins_over_the_doctrine(ctx, engine_stub):
    _, s = prepared(ctx, engine_stub)
    assert "never a fade" in (s.home / runner.HOUSE_FILE).read_text()
    _, s = prepared(ctx, engine_stub, {"video.motion": "per-word ink and blur-up"})
    house, task = (s.home / runner.HOUSE_FILE).read_text(), (s.work / "TASK.md").read_text()
    assert "never a fade" not in house and "motion signature in TASK.md first" in house
    assert "Motion signature, set by the operator" in task and "per-word ink and blur-up." in task


def test_preset_rejects_bad_effort_rounds_and_end_card(ctx):
    bad = load_preset(ctx, "example", {"agent.effort": "turbo", "review.effort": 3, "agent.rounds": 0,
                                       "video.end_card_max": 1.5})
    errs = validate_preset(bad, ctx)
    for key in ("agent.effort", "review.effort", "agent.rounds", "video.end_card_max"):
        assert any(e.startswith(key) for e in errs), key


def test_revision_never_carries_scores(ctx, engine_stub):
    old = ctx.library_dir / "old"
    (old / "composition").mkdir(parents=True)
    (old / "composition" / "index.html").write_text("<html></html>")
    meta = {"video": {"title": "Old", "scores": {"hook": 8}, "rounds": 3, "poster_at": 1.0},
            "verdict": {"pass": False, "scores": {"hook": 5}, "issues": ["settled-02.png: empty"], "summary": "s"}}
    revise = {"id": 1, "title": "Old", "pillar": "principle", "topic": "t", "angle": "a", "notes": "bigger type",
              "dir": ctx.rel(old), "meta": json.dumps(meta)}
    _, s = prepared(ctx, engine_stub, revise=revise)
    rev = json.loads((s.work / "revision.json").read_text())
    assert rev == {"previous": {"title": "Old", "poster_at": 1.0}, "reviewer": {"issues": ["settled-02.png: empty"],
                   "summary": "s"}, "notes": "bigger type"}


def test_the_maker_cannot_write_into_render(ctx, engine_stub, tmp_path, monkeypatch):
    if not shutil.which("bwrap"):
        pytest.skip("needs bwrap")
    seen = {}
    monkeypatch.setattr(engine, "engine_root", lambda ctx, v: engine_stub)
    monkeypatch.setattr(engine, "chrome_path", lambda ctx, v: tmp_path / "chrome" / "linux-1" / "chrome")
    monkeypatch.setattr(engine, "node_dirs", lambda ctx: ([], []))
    monkeypatch.setattr(subprocess, "run", lambda cmd, **k: seen.update(cmd=cmd) or subprocess.CompletedProcess(cmd, 0))
    p, s = prepared(ctx, engine_stub)
    runner.run_jailed(ctx, s, ["harness"], {}, [], [], True, "0.8.106", "agent", 60)
    binds = {seen["cmd"][i + 1] for i, a in enumerate(seen["cmd"]) if a == "--bind"}
    assert str(s.work) in binds and str(s.render) not in binds


def test_no_project_brand_leaks_into_the_shipped_data():
    """The tool stays brand-neutral: no brand name from the presets of the project this checkout serves (found the
    usual way, SOCIAL_STUDIO_PROJECT or the folder above) appears in the data the tool ships."""
    real = make_ctx(os.environ.get("SOCIAL_STUDIO_PROJECT"))
    if real.project is None:
        pytest.skip("no project here to read brand names from")
    names = {str(core.dget(core.load_toml(f), "brand.name") or "").lower()
             for f in (real.project / "presets").glob("*/preset.toml")} - {""}
    names = {n for n in names if len(n) > 3}
    if not names:
        pytest.skip("the project's presets name no brand")
    for f in (PKG_DIR / "data").rglob("*"):
        if f.is_file() and f.suffix in (".md", ".json", ".mjs", ".txt", ".template", "") and "vendor" not in f.parts:
            text = f.read_text(errors="ignore").lower()
            assert not [n for n in names if n in text], f


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_sampler_runs_standalone_with_the_safe_zone_and_poster(tmp_path):
    video = tmp_path / "v.mp4"
    move = "x='if(lt(t,1),0,if(lt(t,1.5),(t-1)*800,400))':y=800:eval=frame:shortest=1"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-f", "lavfi", "-i", "color=c=white:s=1080x1920:d=3:r=30",
                    "-f", "lavfi", "-i", "color=c=black:s=200x200:d=3:r=30", "-filter_complex", f"[0][1]overlay={move}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)], check=True)
    tool = tmp_path / "tools" / "sampler.py"                            # a copy, as the session gets it
    tool.parent.mkdir()
    shutil.copy2(PKG_DIR / "sampler.py", tool)
    out = subprocess.run([sys.executable, str(tool), str(video), str(tmp_path / "evidence"), "--fps", "30",
                          "--safe", "0.12,0.25,0.06,0.10", "--poster", "2.5"], capture_output=True, text=True,
                         cwd=tmp_path, check=True)
    manifest = json.loads(out.stdout)
    assert manifest["poster"]["t"] == 2.5 and (tmp_path / "evidence" / "samples" / "poster.png").is_file()
    corner = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i",
                             str(tmp_path / "evidence" / "samples" / "frame-0.png"), "-vf",
                             f"crop=1:1:{round(1080 * 0.06) + 1}:{round(1920 * 0.5)},format=rgb24", "-f", "rawvideo", "-"],
                            capture_output=True, check=True).stdout
    assert corner[0] > 200 and corner[1] < 80                              # the red safe-zone edge is drawn
    plain = sampler.write_samples(video, sampler.pick_samples(sampler.motion_curve(video), 30), tmp_path / "plain",
                                  sampler.probe(video))
    assert "poster" not in plain
