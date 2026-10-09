"""The storyteller session (F15, J43 and J44): it runs first in the same sandbox, its story.json is checked in
Python, each beat gets the store's top techniques, and the designer's TASK.md carries the resulting brief."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from social_studio import engine, runner, store, story
from social_studio.core import PROJECT_FILE, DataError, dump_toml, load_preset, make_ctx


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
    root = tmp_path / "engine"
    for name in [*runner.DEFAULT_SKILLS, *runner.KIT_ENGINE_SKILLS]:
        (root / "skills" / name).mkdir(parents=True)
        (root / "skills" / name / "SKILL.md").write_text(f"# {name}\n")
    for rel in ("gsap/dist/gsap.min.js", *engine.KIT_GSAP_PLUGINS.values(), "three/build/three.module.min.js",
                "three/build/three.core.min.js"):
        (root / "node_modules" / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / "node_modules" / rel).write_text(f"/* {rel} */")
    (root / "registry").mkdir()
    (root / "registry" / "registry.json").write_text("{}")
    monkeypatch.setattr(engine, "skills_root", lambda ctx, version: root / "skills")
    monkeypatch.setattr(engine, "registry_root", lambda ctx, version: root / "registry")
    return root


def backend(name: str = "claude") -> runner.Backend:
    return runner.Backend(name, "sonnet", Path(shutil.which("true") or "/bin/true"), True)


def prepared(ctx, engine_stub, overrides=None):
    p = load_preset(ctx, "example", {"video.duration": [20, 25], **(overrides or {})})
    s = runner.Session("20261009-120000-abcd", ctx.sessions_dir / "20261009-120000-abcd")
    skills = runner.prepare(ctx, p, s, "0.8.106", engine_stub, None, [], None)
    return p, s, skills


def a_story(**over) -> dict:
    beats = [
        {"role": "hook", "seconds": 3, "job": "the claim lands", "emotion": "curiosity", "shows": "one big word",
         "copy": ["Ship it today."], "purpose": ["tease"], "content": ["type"], "energy": "punch"},
        {"role": "problem", "seconds": 5, "job": "launches take weeks", "copy": ["Weeks of back and forth"],
         "purpose": ["build-tension"], "content": ["product-ui"], "energy": "build"},
        {"role": "solution", "seconds": 9, "job": "the product builds the page", "copy": ["One prompt. One page."],
         "purpose": ["reveal-product", "made-up-purpose"], "content": ["product-ui"], "energy": "build"},
        {"role": "cta", "seconds": 4, "job": "where to start", "copy": ["Try it free for 14 days."],
         "purpose": ["land-cta"], "content": ["logo"], "energy": "loud"},
    ]
    return {"idea": "This video tells founders that a launch page takes one prompt.", "title": "One prompt",
            "references": [], "structure": "intro-problem-solution-cta", "beats": beats,
            "cta": "Try it free for 14 days.", "banned": ["stock gradient blobs"], **over}


def test_a_story_is_checked_and_its_stray_tags_dropped(ctx):
    p = load_preset(ctx, "example", {"video.duration": [20, 25]})
    told = story.check(a_story(), p, set())
    assert told["seconds"] == 21 and told["beats"][2]["purpose"] == ["reveal-product"]
    assert told["beats"][3]["energy"] == "" and "beat 3 purpose 'made-up-purpose'" in told["dropped"]
    assert told["banned"][0] == "stock gradient blobs" and set(story.ALWAYS_BANNED) <= set(told["banned"])


def test_a_bad_story_fails_with_every_problem(ctx):
    p = load_preset(ctx, "example", {"video.duration": [20, 25]})
    bad = a_story(idea="", references=[{"id": "nobody", "took": "x"}])
    bad["beats"][0]["role"] = "drama"
    bad["beats"][1]["seconds"] = 30
    with pytest.raises(DataError) as e:
        story.check(bad, p, {"acme-launch"})
    msg = str(e.value)
    for part in ("idea is missing", "beat 1 role 'drama'", "the beats run 46 s; the film runs 20 to 25 s",
                 "reference 'nobody' is not in story-references.json"):
        assert part in msg, part
    with pytest.raises(DataError, match="references must name"):
        story.check(a_story(), p, {"acme-launch"})                    # posts were offered: the story learns from them


def test_the_storyteller_gets_its_own_task_references_and_skill(ctx, engine_stub):
    p, s, _ = prepared(ctx, engine_stub, {"video.sound": "bed+sfx+voice"})
    refs = story.prepare(p, s, None, store.open_store())
    task = (s.work / story.TASK).read_text()
    assert not re.search(r"\{\{\w+\}\}", task), re.findall(r"\{\{\w+\}\}", task)
    assert "voice sets the timing" in task and '"Try it free for 14 days."' in task and "crossfades" in task
    assert json.loads((s.work / story.REFERENCES).read_text()) == refs
    assert (s.work / "skills" / runner.STORY_SKILL / "SKILL.md").is_file()


def test_the_storyteller_session_has_its_own_limits_and_no_designer_extras(ctx, engine_stub):
    p, s, skills = prepared(ctx, engine_stub, {"story.effort": "high", "agent.effort": "max"})
    story.prepare(p, s, None, store.open_store())
    argv, _, _, _ = runner.backend_command(ctx, p, backend(), s, "go", story.STORY_SKILLS, role="story")
    assert argv[argv.index("--effort") + 1] == "high" and argv[argv.index("--max-turns") + 1] == "30"
    assert "--append-system-prompt-file" not in argv and "--mcp-config" not in argv
    cfg = s.home / ".claude-config" / "skills"
    assert sorted(x.name for x in cfg.iterdir()) == sorted(story.STORY_SKILLS)
    runner.backend_command(ctx, p, backend(), s, "go", skills)            # the designer next, in the same home
    assert runner.STORY_SKILL not in {x.name for x in cfg.iterdir()}


def test_tell_runs_the_storyteller_then_briefs_the_designer(ctx, engine_stub, monkeypatch):
    p, s, skills = prepared(ctx, engine_stub)
    calls = []

    def fake_storyteller(ctx_, s_, argv, env, ro, rw, sandbox, version, log_name, timeout, workdir=None):
        calls.append((log_name, timeout))
        refs = json.loads((s_.work / story.REFERENCES).read_text())
        cited = [{"id": r["id"], "took": "its pace"} for r in refs[:2]]
        (s_.work / story.STORY).write_text(json.dumps(a_story(references=cited)))
        return 0
    monkeypatch.setattr(story, "run_jailed", fake_storyteller)
    history = [{"techniques": ["kinetic-word-run"]}]
    told = story.tell(ctx, p, s, backend(), "0.8.106", history, None)
    assert calls == [("story", 15 * 60)]
    plan = json.loads((s.work / story.TECHNIQUES).read_text())
    assert [b["role"] for b in plan["beats"]] == ["hook", "problem", "solution", "cta"]
    assert all(b["candidates"] for b in plan["beats"])
    ids = [c["id"] for b in plan["beats"] for c in b["candidates"]]
    assert len(ids) == len(set(ids))                                      # each item serves one beat
    assert set(story.ALWAYS_BANNED) <= set(json.loads((s.work / story.STORY).read_text())["banned"])
    brief = told["brief"]
    assert "**This video tells founders that a launch page takes one prompt.**" in brief
    assert "1. **hook**, 0-3 s." in brief and "4. **cta**, 17-21 s." in brief and "Banned for this film" in brief
    assert told["meta"]["beats"] == ["hook", "problem", "solution", "cta"]
    runner.write_task(p, s, skills, None, None, designer_brief=brief)
    task = (s.work / "TASK.md").read_text()
    assert not re.search(r"\{\{\w+\}\}", task)
    assert "`story.json`: the story of this film" in task and brief in task and "inside its seconds" in task


def test_without_a_story_the_task_keeps_the_presets_brief(ctx, engine_stub):
    p, s, _ = prepared(ctx, engine_stub)
    task = (s.work / "TASK.md").read_text()
    assert "`story.json`" not in task and "Choose the pillar, topic and angle yourself" in task
    assert (s.work / "registry").is_symlink() and (s.work / runner.STORE_DB).is_file()


def test_a_build_tells_its_story_first_unless_it_is_a_revision_or_turned_off(ctx, monkeypatch):
    seen = []
    monkeypatch.setattr(engine, "require_version", lambda v: v)
    monkeypatch.setattr(engine, "ensure_engine", lambda *a: None)
    monkeypatch.setattr(engine, "ensure_skills", lambda *a: None)
    monkeypatch.setattr(runner, "resolve_backend", lambda ctx, p, name, model, sandbox, role="agent":
                        runner.Backend(name or "claude", model or role, Path("/bin/true"), True))
    monkeypatch.setattr(runner, "run_one", lambda *a: seen.append(a[-1]) or {"ok": True})
    runner.make(ctx, runner.MakeOpts(preset="example"))
    assert seen[-1].model == "agent"                                      # the designer's backend and model
    runner.make(ctx, runner.MakeOpts(preset="example", sets={"story.model": "opus"}))
    assert seen[-1].model == "opus"
    runner.make(ctx, runner.MakeOpts(preset="example", sets={"story.enabled": False}))
    assert seen[-1] is None


def test_the_kit_gives_gsap_its_plugins_only_where_gsap_has_them():
    class P:
        def __init__(self, data):
            self.data = data

        def get(self, key, default=None):
            from social_studio.core import dget
            return dget(self.data, key, default)
    assert set(engine.KIT_GSAP_PLUGINS) <= set(engine.vendor(P({})))
    assert set(engine.KIT_GSAP_PLUGINS) <= set(engine.vendor(P({"render": {"libraries": ["gsap@3.14.2"],
                                                                         "vendor": {"gsap.min.js": "gsap/dist/gsap.min.js"}}})))
    assert not set(engine.KIT_GSAP_PLUGINS) & set(engine.vendor(P({"render": {"libraries": ["gsap@3.12.5"]}})))


def test_the_engine_pins_its_skills_and_registry_from_one_tag(ctx, monkeypatch):
    import io
    import tarfile
    import urllib.request

    def tarball() -> bytes:
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            for name, text in (("hyperframes-0.8.106/skills/hyperframes-core/SKILL.md", "# core"),
                               ("hyperframes-0.8.106/registry/registry.json", "{}"),
                               ("hyperframes-0.8.106/registry/blocks/chart/chart.html", "<div></div>"),
                               ("hyperframes-0.8.106/packages/cli/x.js", "nope")):
                data = text.encode()
                info = tarfile.TarInfo(name)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
        return buf.getvalue()
    fetched = []

    def fake_urlopen(url, timeout=None):
        fetched.append(url)
        return io.BytesIO(tarball())
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    root = engine.engine_root(ctx, "0.8.106")
    assert engine.ensure_skills(ctx, "0.8.106") == root / "skills"
    assert (root / "registry" / "blocks" / "chart" / "chart.html").is_file() and not (root / "packages").exists()
    assert fetched == ["https://codeload.github.com/heygen-com/hyperframes/tar.gz/refs/tags/v0.8.106"]
    engine.ensure_skills(ctx, "0.8.106")
    assert len(fetched) == 1                                              # pinned once, reused after
    shutil.rmtree(root / "registry")
    engine.ensure_skills(ctx, "0.8.106")                                  # an install from before the registry
    assert len(fetched) == 2 and engine.registry_root(ctx, "0.8.106").is_dir()
