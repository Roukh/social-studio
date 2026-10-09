"""The pitch round (F15, J6): with no operator brief, a pitcher writes five concepts, a judge in its own folder scores
them on one rubric, code checks both files and picks the winner, and the storyteller writes the story from it."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from social_studio import core, db, engine, pitch, runner, story
from social_studio.core import PROJECT_FILE, ConfigError, DataError, dump_toml, load_preset, make_ctx, validate_preset


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
    monkeypatch.setattr(engine, "skills_root", lambda ctx, version: root / "skills")
    monkeypatch.setattr(engine, "registry_root", lambda ctx, version: root / "registry")
    return root


def backend() -> runner.Backend:
    return runner.Backend("claude", "sonnet", Path(shutil.which("true") or "/bin/true"), True)


def prepared(ctx, engine_stub, overrides=None):
    p = load_preset(ctx, "example", {"video.duration": [20, 25], **(overrides or {})})
    s = runner.Session("20261009-130000-abcd", ctx.sessions_dir / "20261009-130000-abcd")
    skills = runner.prepare(ctx, p, s, "0.8.106", engine_stub, None, [], None)
    return p, s, skills


def some_pitches(**over) -> dict:
    concepts = [
        {"id": "c1", "path": "subject", "concept": "The page builds itself from one prompt.", "world": "the editor",
         "hook": "a blank page fills", "truth": "one prompt makes a launch page", "p": 0.3, "silhouette": "page centre"},
        {"id": "c2", "path": "emotion", "concept": "Relief: a cluttered desk empties.", "world": "tabs closing",
         "hook": "forty tabs", "truth": "one tool instead of five", "p": 0.2, "silhouette": "grid of tabs"},
        {"id": "c3", "path": "audience", "concept": "A founder's launch week in 20 s.", "world": "a calendar",
         "hook": "Monday 9:00", "truth": "a launch page in one prompt", "p": 0.12, "silhouette": "calendar strip"},
        {"id": "c4", "path": "anti-pattern", "concept": "No product shots: only the receipt.", "world": "a receipt",
         "hook": "a till prints", "truth": "free for 14 days", "p": 0.05, "silhouette": "tall narrow receipt"},
        {"id": "c5", "path": "format", "concept": "A recipe card for a launch.", "world": "a recipe card",
         "hook": "Ingredients: one prompt", "truth": "one prompt makes a launch page", "p": 0.04,
         "silhouette": "card with list"},
    ]
    return {"grounding": {"subject": "an editor", "emotion": "relief as empty space", "surface": "a vertical feed",
                          "everyone_else": "glass cards and gradient blobs"},
            "concepts": concepts, "dropped": [{"concept": "a second editor", "why": "same silhouette as c1"}],
            "left_behind": "a montage of UI cards over a gradient", **over}


def scores_for(ids, truth=7, base=6, best=None) -> dict:
    out = {i: {c: base for c in pitch.RUBRIC} for i in ids}
    for i in ids:
        out[i][pitch.TRUTH] = truth
    if best:
        out[best] = {c: 9 for c in pitch.RUBRIC}
    return out


# --- when it runs -------------------------------------------------------------------------------------

def test_the_pitch_round_runs_only_without_an_operator_brief(ctx):
    assert pitch.needed(load_preset(ctx, "example"))
    for key in pitch.BRIEF_KEYS:                                          # any of the four is a brief
        assert not pitch.needed(load_preset(ctx, "example", {key: "launch week"})), key
    assert not pitch.needed(load_preset(ctx, "example", {"story.pitch": False}))


def test_the_preset_checks_the_pitch_rounds_keys(ctx):
    bad = load_preset(ctx, "example", {"story.pitch": "yes", "pitch.max_turns": 0, "judge.timeout_min": "ten",
                                       "judge.effort": "huge"})
    errs = validate_preset(bad, ctx)
    for part in ("story.pitch must be true or false", "pitch.max_turns must be a whole number",
                 "judge.timeout_min must be a whole number", "judge.effort must be one of"):
        assert any(part in e for e in errs), part
    ok = load_preset(ctx, "example", {"story.pitch": False, "pitch.max_turns": 20, "judge.timeout_min": 5})
    assert validate_preset(ok, ctx) == []


def test_the_pitch_skill_name_is_reserved(ctx, monkeypatch):
    monkeypatch.setattr(core, "is_tty", lambda: True)
    p = load_preset(ctx, "example", {"agent.skills": {runner.PITCH_SKILL: "mine"}})
    with pytest.raises(ConfigError, match="taken"):
        runner._skills(ctx, p, runner.Session("x", ctx.sessions_dir / "x"), "0.8.106")


# --- the checks ---------------------------------------------------------------------------------------

def test_good_pitches_pass_their_check():
    assert pitch.check_pitches(some_pitches())["left_behind"].startswith("a montage")


def test_bad_pitches_fail_with_every_problem():
    bad = some_pitches(left_behind=" ")
    bad["grounding"]["everyone_else"] = ""
    bad["concepts"][1]["path"] = "subject"                                # two on one path
    bad["concepts"][2]["truth"] = ""
    bad["concepts"][3]["p"] = 0.5                                         # only one left below 0.10
    bad["concepts"][4]["silhouette"] = "Page   centre"                    # c1's silhouette again
    bad["concepts"][4]["id"] = "c1"
    with pytest.raises(DataError) as e:
        pitch.check_pitches(bad)
    msg = str(e.value)
    for part in ("grounding.everyone_else is not answered", "the five pitches must take the five paths",
                 "pitch 3 has no truth", "1 pitches sit below p = 0.10", "pitches 1 and 5 share a silhouette",
                 "pitch 5 needs an id of its own", "left_behind"):
        assert part in msg, part
    with pytest.raises(DataError, match="exactly 5 pitches, not 4"):
        pitch.check_pitches(some_pitches(concepts=some_pitches()["concepts"][:4]))


def test_the_judge_sees_only_each_pitchs_own_words_in_a_shuffled_order():
    concepts = some_pitches()["concepts"]
    shown, letters = pitch.for_judge(concepts, "seed-1")
    assert [x["id"] for x in shown] == list("ABCDE") and sorted(letters.values()) == ["c1", "c2", "c3", "c4", "c5"]
    assert all(set(x) == {"id", *pitch.SHOWN} for x in shown)            # no p, path or silhouette
    assert any(letters[x] != f"c{i}" for i, x in enumerate("ABCDE", 1))  # the pitcher's order is not the judge's
    assert pitch.for_judge(concepts, "seed-1") == (shown, letters)        # the same build shuffles the same way


def test_code_checks_the_verdict_and_picks_the_winner():
    ids = list("ABCDE")
    v = pitch.check_verdict({"scores": scores_for(ids, best="C"), "pick": "A", "why": "bold"}, ids)
    assert v["winner"] == "C" and v["checked"] == {"judge_said": "A", "by_scores": "C"}
    assert v["totals"]["C"] == 9 * len(pitch.RUBRIC)
    abstract = scores_for(ids, best="B")
    abstract["B"][pitch.TRUTH] = pitch.TRUTH_FLOOR - 1                   # the best total rests on a mood: out
    assert pitch.check_verdict({"scores": abstract, "pick": "B", "why": "x"}, ids)["winner"] != "B"
    tie = scores_for(ids)
    assert pitch.check_verdict({"scores": tie, "pick": "D", "why": "x"}, ids)["winner"] == "D"
    moods = scores_for(ids, truth=2)
    with pytest.raises(DataError, match="no pitch scored"):
        pitch.check_verdict({"scores": moods, "pick": "A", "why": "x"}, ids)


def test_a_malformed_verdict_fails_with_every_problem():
    ids = list("ABCDE")
    scores = scores_for(ids)
    scores["A"]["clarity"] = 11
    scores["B"]["hook"] = 7.5
    scores["C"]["vibes"] = 9
    del scores["D"]
    scores["F"] = scores["E"]
    with pytest.raises(DataError) as e:
        pitch.check_verdict({"scores": scores, "pick": "Z"}, ids)
    msg = str(e.value)
    for part in ("pitch A 'clarity' is scored 11", "pitch B 'hook' is scored 7.5", "pitch C: 'vibes' is not a",
                 "pitch D is not scored", "'F' is not a pitch", "pick 'Z' is not one of", "why is missing"):
        assert part in msg, part


# --- the sessions -------------------------------------------------------------------------------------

def test_the_pitch_and_judge_tasks_are_fully_filled(ctx):
    p = load_preset(ctx, "example", {"video.sound": "bed+sfx+voice"})
    for text in (pitch.task_text(p, "offer"), pitch.judge_text(p, "offer", list("ABCDE"))):
        assert not re.search(r"\{\{\w+\}\}", text), re.findall(r"\{\{\w+\}\}", text)
    task = pitch.task_text(p, "offer")
    assert "anti-pattern" in task and "below 0.10" in task and '"Try it free for 14 days."' in task
    judge = pitch.judge_text(p, "offer", list("ABCDE"))
    assert all(f"**{c}**" in judge for c in pitch.RUBRIC) and '"E": {' in judge and "Pillar for this video" in judge


def test_the_pitch_and_judge_sessions_have_their_own_limits(ctx, engine_stub):
    p, s, _ = prepared(ctx, engine_stub, {"judge.max_turns": 9, "pitch.effort": "high", "agent.effort": "max"})
    shutil.copytree(core.PKG_DIR / "data" / "skills" / runner.PITCH_SKILL, s.work / "skills" / runner.PITCH_SKILL)
    argv, _, _, _ = runner.backend_command(ctx, p, backend(), s, "go", [runner.PITCH_SKILL], role="pitch")
    assert argv[argv.index("--max-turns") + 1] == "30" and argv[argv.index("--effort") + 1] == "high"
    assert "--append-system-prompt-file" not in argv and "--mcp-config" not in argv
    assert [x.name for x in (s.home / ".claude-config" / "skills").iterdir()] == [runner.PITCH_SKILL]
    argv, _, _, _ = runner.backend_command(ctx, p, backend(), s, "go", [], role="judge")
    assert argv[argv.index("--max-turns") + 1] == "9" and "--effort" not in argv


def fake_sessions(calls: list, verdict=None, pitches=None):
    """Stand-ins for the pitcher, the judge and the storyteller: each writes what its real session would."""
    def run(ctx_, s_, argv, env, ro, rw, sandbox, version, log_name, timeout, workdir=None):
        calls.append((log_name, s_.dir.name, timeout))
        (s_.logs / f"{log_name}.out").write_text("{}\n")
        if log_name == "pitch":
            (s_.work / pitch.PITCHES).write_text(json.dumps(pitches or some_pitches()))
        elif log_name == "judge":
            shown = json.loads((s_.work / pitch.PITCHES).read_text())
            calls.append(("judge saw", sorted(x.name for x in s_.work.iterdir()), shown))
            ids = [x["id"] for x in shown]
            best = next(x["id"] for x in shown if x["concept"].startswith("A recipe card"))
            (s_.work / "verdict.json").write_text(json.dumps(
                verdict or {"scores": scores_for(ids, best=best), "pick": best, "why": "the recipe is unexpected"}))
        else:
            calls.append(("storyteller read", (s_.work / story.TASK).read_text()))
            refs = json.loads((s_.work / story.REFERENCES).read_text())
            beats = [{"role": role, "seconds": sec, "job": f"the {role} lands", "copy": ["One prompt."]}
                     for role, sec in (("hook", 4), ("solution", 12), ("cta", 5))]
            (s_.work / story.STORY).write_text(json.dumps(
                {"idea": "This video tells founders that a launch is a recipe.", "beats": beats,
                 "references": [{"id": r["id"], "took": "its pace"} for r in refs[:1]]}))
        return 0
    return run


def test_a_build_without_a_brief_pitches_judges_then_tells(ctx, engine_stub, monkeypatch):
    p, s, _ = prepared(ctx, engine_stub)
    calls: list = []
    fake = fake_sessions(calls)
    monkeypatch.setattr(pitch, "run_jailed", fake)
    monkeypatch.setattr(story, "run_jailed", fake)
    told = story.tell(ctx, p, s, backend(), "0.8.106", [], None)
    runs = [c for c in calls if c[0] in ("pitch", "judge", "story")]
    assert runs == [("pitch", s.id, 15 * 60), ("judge", "judge", 10 * 60), ("story", s.id, 15 * 60)]
    saw = next(c for c in calls if c[0] == "judge saw")
    assert saw[1] == [pitch.JUDGE_TASK, pitch.PITCHES, "preset.json"]     # the brief and the pitches, nothing else
    assert all(set(x) == {"id", *pitch.SHOWN} for x in saw[2])
    read = next(c for c in calls if c[0] == "storyteller read")[1]
    assert "Concept: A recipe card for a launch." in read and "Left behind on purpose" in read
    assert "a montage of UI cards over a gradient" in read
    verdict = json.loads((s.work / pitch.VERDICT).read_text())
    assert verdict["letters"][verdict["winner"]] == "c5" and (s.work / pitch.PITCHES).is_file()
    assert told["meta"]["pitch"] == {"winner": "c5", "path": "format", "concept": "A recipe card for a launch.",
                                     "truth": "one prompt makes a launch page",
                                     "left_behind": "a montage of UI cards over a gradient",
                                     "points": 9 * len(pitch.RUBRIC)}
    assert not (s.dir / "judge").exists() and (s.logs / "judge.out").is_file()   # the judge's folder goes, its log stays
    assert (s.work / "skills" / runner.PITCH_SKILL / "NOTICE.md").is_file()


def test_a_malformed_verdict_fails_the_build_before_the_storyteller(ctx, engine_stub, monkeypatch):
    p, s, _ = prepared(ctx, engine_stub)
    calls: list = []
    fake = fake_sessions(calls, verdict={"scores": {}, "pick": "nobody"})
    monkeypatch.setattr(pitch, "run_jailed", fake)
    monkeypatch.setattr(story, "run_jailed", fake)
    with pytest.raises(DataError) as e:
        story.tell(ctx, p, s, backend(), "0.8.106", [], None)
    assert "pitch A is not scored" in str(e.value) and "pick 'nobody'" in str(e.value) and "judge exit 0" in str(e.value)
    assert "story" not in [c[0] for c in calls] and not (s.dir / "judge").exists()


def test_with_an_operator_brief_there_is_no_pitch_round(ctx, engine_stub, monkeypatch):
    p, s, _ = prepared(ctx, engine_stub, {"content.topic": "launch week"})
    calls: list = []
    fake = fake_sessions(calls)
    monkeypatch.setattr(pitch, "run_jailed", fake)
    monkeypatch.setattr(story, "run_jailed", fake)
    told = story.tell(ctx, p, s, backend(), "0.8.106", [], None)
    assert [c[0] for c in calls if c[0] in ("pitch", "judge", "story")] == ["story"]
    assert "pitch" not in told["meta"] and not (s.work / pitch.PITCHES).exists()
    assert "Concept:" not in (s.work / story.TASK).read_text()


def test_a_built_video_keeps_its_pitch_round(ctx, engine_stub, render_stub, monkeypatch):
    """The whole build with stubbed sessions: the pitch files reach the library, the winner its meta."""
    monkeypatch.setattr(engine, "engine_root", lambda ctx_, version: engine_stub)
    calls: list = []
    fake = fake_sessions(calls)

    def designer(ctx_, s_, argv, env, ro, rw, sandbox, version, log_name, timeout, workdir=None):
        calls.append((log_name, s_.dir.name, timeout))
        (s_.work / "brief.json").write_text(json.dumps({"film": "a recipe", "shots": []}))
        (s_.work / "video.json").write_text(json.dumps({"title": "A recipe for a launch", "techniques": []}))
        return 0
    monkeypatch.setattr(pitch, "run_jailed", fake)
    monkeypatch.setattr(story, "run_jailed", fake)
    monkeypatch.setattr(runner, "run_jailed", designer)
    p = load_preset(ctx, "example", {"video.duration": [20, 25]})
    b = runner.Backend("claude", "sonnet", Path("/bin/true"), False)
    res = runner.run_one(ctx, p, runner.MakeOpts(preset="example"), b, "0.8.106", None, [], None, sb=b)
    assert res["ok"], res
    assert [c[0] for c in calls if c[0] in ("pitch", "judge", "story", "agent")] == ["pitch", "judge", "story", "agent"]
    dest = Path(res["file"]).parent
    assert json.loads((dest / pitch.PITCHES).read_text())["left_behind"] == "a montage of UI cards over a gradient"
    assert json.loads((dest / pitch.VERDICT).read_text())["why"] == "the recipe is unexpected"
    con = db.connect(ctx)
    meta = json.loads(con.execute("SELECT meta FROM videos WHERE id = ?", (res["video_id"],)).fetchone()[0])
    assert meta["story"]["pitch"]["winner"] == "c5"
    assert meta["story"]["pitch"]["left_behind"] == "a montage of UI cards over a gradient"
