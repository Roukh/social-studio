"""Keyframe boards (F15, J7): `build --boards` stops at a board sheet filed as a board row, only a human at a terminal
decides it, approving one never approves a video, `build --from-board` animates an approved board, and the v5
schema that holds them applies twice cleanly (rule R49)."""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import pytest

from social_studio import boards, cli, core, db, engine, runner, store, story
from social_studio.core import PROJECT_FILE, DataError, Denied, UsageError, dump_toml, load_preset, make_ctx


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
    monkeypatch.setattr(engine, "engine_root", lambda ctx, version: root)
    return root


def as_human(monkeypatch):
    monkeypatch.setattr(core, "is_tty", lambda: True)


def a_board(ctx, status="review", **over) -> int:
    """A board row as a build files it (actor make, in review), then moved to `status` by a human."""
    d = ctx.library_dir / "20261009-board-x-abcd"
    (d / "composition").mkdir(parents=True, exist_ok=True)
    (d / "composition" / "index.html").write_text("<html><!-- the approved poses --></html>")
    (d / boards.SHEET).write_bytes(b"png")
    (d / boards.BRIEF_FILE).write_text("- The story, written by the storyteller before you: **an idea**")
    (d / "brief.json").write_text(json.dumps({"shots": [{"start": 0, "end": 21, "technique": "t", "text": []}]}))
    meta = {"story": {"idea": "an idea", "beats": ["hook", "cta"]},
            "format": {"video.width": 1920, "video.height": 1080, "video.duration": [20, 25]}, **over}
    con = db.connect(ctx, actor="make")
    bid = con.execute("INSERT INTO boards (title, idea, pillar, preset, dir, sheet, shots, width, height, meta, "
                      "created_at, updated_at) VALUES ('Board', 'an idea', 'offer', 'example', ?, ?, 1, 1920, 1080, ?, "
                      "'x', 'x')", (ctx.rel(d), ctx.rel(d / boards.SHEET), json.dumps(meta))).lastrowid
    con.close()
    if status != "review":
        boards.decide(ctx, bid, status, "make the CTA bigger" if status == "revision" else "")
    return bid


# --- the schema --------------------------------------------------------------------------------------------

def test_the_v5_migration_keeps_every_row_and_applies_twice(tmp_path):
    """Rule R49: the boards migration is run a second time against the same database, literally."""
    path = tmp_path / "library.db"
    con = sqlite3.connect(path, isolation_level=None)
    con.create_function("ss_actor", 0, lambda: "t")
    for i, script in enumerate(db.SCHEMA[:4], start=1):
        con.executescript(f"BEGIN; {script} PRAGMA user_version = {i}; COMMIT;")
    con.execute("INSERT INTO videos (slug, title, preset, dir, file, sha256, bytes, duration, width, height, "
                "created_at, updated_at) VALUES ('a', 'A', 'example', 'd', 'f', 'h', 1, 1.0, 1080, 1920, 'x', 'x')")
    con.close()

    class Ctx:
        studio_dir, db_path = tmp_path, path
    con = db.connect(Ctx())
    assert con.execute("PRAGMA user_version").fetchone()[0] == len(db.SCHEMA) == 5
    video = dict(con.execute("SELECT * FROM videos").fetchone())
    assert video["title"] == "A" and video["board_id"] is None and video["status"] == "review"
    schema = sorted(tuple(r) for r in con.execute("SELECT type, name, sql FROM sqlite_master"))
    con.executescript(f"BEGIN; {db.SCHEMA[4](con)} COMMIT;")              # the second apply, by hand
    con.execute("PRAGMA user_version = 4")
    con.close()
    con = db.connect(Ctx())                                               # and again through connect()
    assert con.execute("PRAGMA user_version").fetchone()[0] == 5
    assert sorted(tuple(r) for r in con.execute("SELECT type, name, sql FROM sqlite_master")) == schema
    assert dict(con.execute("SELECT * FROM videos").fetchone()) == video
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_board_statuses_are_enforced_by_the_schema(ctx):
    bid = a_board(ctx)
    agent = db.connect(ctx, actor="agent")
    with pytest.raises(sqlite3.IntegrityError, match="only a human"):
        agent.execute("UPDATE boards SET status = 'approved' WHERE id = ?", (bid,))
    human = db.connect(ctx, actor="human")
    with pytest.raises(sqlite3.IntegrityError, match="invalid board status"):
        human.execute("UPDATE boards SET status = 'superseded' WHERE id = ?", (bid,))
    human.execute("UPDATE boards SET status = 'approved' WHERE id = ?", (bid,))
    row = human.execute("SELECT status, decided_by FROM boards WHERE id = ?", (bid,)).fetchone()
    assert tuple(row) == ("approved", "human")
    with pytest.raises(sqlite3.IntegrityError, match="filed by a build"):  # never born approved
        db.connect(ctx, actor="make").execute(
            "INSERT INTO boards (title, preset, dir, sheet, shots, width, height, status, created_at, updated_at) "
            "VALUES ('x', 'p', 'd', 's', 1, 1, 1, 'approved', 'x', 'x')")
    raw = sqlite3.connect(ctx.db_path)
    with pytest.raises(sqlite3.OperationalError):                         # ss_actor() exists only inside the tool
        raw.execute("UPDATE boards SET status = 'dropped' WHERE id = ?", (bid,))


def test_the_agent_view_shows_boards_in_play_only(ctx, capsys):
    keep, gone = a_board(ctx), a_board(ctx, "dropped")
    assert cli.main(["--json", "agent", "boards"]) == 0
    assert [r["id"] for r in json.loads(capsys.readouterr().out)] == [keep]
    assert gone not in {r[0] for r in db.connect(ctx).execute("SELECT id FROM agent_boards")}


# --- the human gate ----------------------------------------------------------------------------------------

def test_board_decisions_need_a_terminal(ctx, capsys):
    bid = a_board(ctx)
    for action in ("approve", "revise", "drop"):
        assert cli.main(["--json", "board", action, str(bid), "--notes", "x"]) == 77, action
    assert '"code": "denied"' in capsys.readouterr().out
    with pytest.raises(Denied):
        boards.cmd_board(ctx, cli.build_parser().parse_args(["board", "approve", str(bid)]))
    assert db.connect(ctx).execute("SELECT status FROM boards").fetchone()[0] == "review"


def test_approving_a_board_never_approves_a_video(ctx, monkeypatch, capsys):
    bid = a_board(ctx)
    con = db.connect(ctx, actor="make")
    vid = con.execute("INSERT INTO videos (slug, title, preset, dir, file, sha256, bytes, duration, width, height, "
                      "created_at, updated_at, board_id) VALUES ('a', 'A', 'example', 'd', 'f', 'h', 1, 1.0, 1080, "
                      "1920, 'x', 'x', ?)", (bid,)).lastrowid
    as_human(monkeypatch)
    assert cli.main(["--json", "board", "revise", str(bid)]) == 64          # revise says what to change
    capsys.readouterr()
    assert cli.main(["--json", "board", "approve", str(bid)]) == 0
    assert json.loads(capsys.readouterr().out) == {"board": bid, "status": "approved"}
    assert con.execute("SELECT status FROM boards WHERE id = ?", (bid,)).fetchone()[0] == "approved"
    assert con.execute("SELECT status FROM videos WHERE id = ?", (vid,)).fetchone()[0] == "review"
    assert con.execute("SELECT count(*) FROM approvals").fetchone()[0] == 0
    with pytest.raises(DataError):                                        # the video still needs its own signature
        db.set_status(con, vid, "approved")
    assert cli.main(["--json", "board", "drop", str(bid)]) == 0
    assert cli.main(["--json", "board", "approve", str(bid)]) == 65         # a dropped board stays dropped


def test_the_cli_parses_boards(capsys):
    parse = cli.build_parser().parse_args
    a = parse(["build", "--boards"])
    assert a.boards and a.from_board is None and a.fn is cli.cmd_make
    a = parse(["build", "--from-board", "3"])
    assert a.from_board == 3 and not a.boards
    assert parse(["board"]).action == "list" and parse(["board", "approve", "3", "--notes", "ok"]).id == 3
    assert parse(["agent", "boards"]).action == "boards"
    with pytest.raises(SystemExit):
        parse(["board", "sign", "3"])
    assert cli.main(["help", "board"]) == 0 and "approving a board never approves a video" in capsys.readouterr().out


# --- the checks and the sheet --------------------------------------------------------------------------------

def test_a_boards_shots_are_checked_with_every_problem(ctx):
    p = load_preset(ctx, "example", {"video.duration": [20, 25]})
    good = {"shots": [{"start": 0, "end": 9, "technique": "a", "text": ["One"]},
                      {"start": 9, "end": 21, "technique": "b", "text": []}]}
    assert boards.pose_times(boards.check_shots(good, p)) == [4.5, 15.0]
    bad = {"shots": [{"start": 0, "end": 9, "technique": "", "text": "One"}, {"start": 5, "end": 4},
                     {"start": 6, "end": 30, "technique": "c", "text": []}]}
    with pytest.raises(DataError) as e:
        boards.check_shots(bad, p)
    for part in ("shot 1 has no technique", "shot 1 text must be a list", "shot 2 needs a start before its end",
                 "shot 3 starts at 6 s, before", "the shots run 30 s; the film runs 20 to 25 s"):
        assert part in str(e.value), part
    with pytest.raises(DataError, match="1 to 16 shots, not 17"):
        boards.check_shots({"shots": [{"start": i, "end": i + 1, "technique": "t", "text": []} for i in range(17)]}, p)


@pytest.mark.parametrize("size", [(1080, 1920), (1920, 1080), (1080, 1350), (1080, 1080)])
def test_the_sheet_stays_within_2000_px_for_any_board(size):
    w, h = size
    for n in range(1, boards.MAX_SHOTS + 1):
        lay = boards.sheet_layout(n, w, h)
        assert lay["width"] <= boards.SHEET_MAX and lay["height"] <= boards.SHEET_MAX, (n, lay)
        assert lay["cols"] * lay["rows"] >= n and abs(lay["tile_w"] / lay["tile_h"] - w / h) < 0.01
        assert boards.MIN_FONT <= lay["font"] <= boards.MAX_FONT


def test_the_sheet_labels_every_pose_and_draws_the_safe_zone_at_9_16():
    shots = [{"start": 0, "end": 2.5, "technique": "kinetic-word-run", "text": ["Ship <it>", "today"]},
             {"start": 2.5, "end": 21, "technique": "logo-lockup", "text": []}]
    told = {"idea": "This video tells founders that it ships.",
            "beats": [{"role": "hook", "seconds": 3}, {"role": "cta", "seconds": 18}]}
    tiles = boards.labels(shots, told)
    assert tiles[0] == {"shot": "Shot 1", "beat": "beat 1 hook", "time": "0-2.5 s", "technique": "kinetic-word-run",
                        "text": "Ship <it> / today"}
    assert tiles[1]["beat"] == "beat 1 hook"                                # 2.5 s is still inside the hook
    page = boards.sheet_html("Board", told["idea"], boards.sheet_layout(2, 1080, 1920), tiles,
                             {"top": 0.12, "bottom": 0.25, "left": 0.06, "right": 0.10})
    assert page.count('class="safe"') == 2 and "inset:12% 10% 25% 6%" in page
    assert "Ship &lt;it&gt; / today" in page and "(no text)" in page and 'src="poses/02.png"' in page
    assert 'data-composition-id="main"' in page and 'window.__timelines["main"] = tl' in page
    wide = boards.sheet_html("Board", "", boards.sheet_layout(2, 1920, 1080), tiles, None)
    assert 'class="safe"' not in wide


def test_poses_are_snapshotted_by_the_engine_in_the_jail_without_network(ctx, monkeypatch, tmp_path):
    s = runner.Session("20261009-140000-abcd", ctx.sessions_dir / "20261009-140000-abcd")
    s.work.mkdir(parents=True)
    seen = {}
    monkeypatch.setattr(engine, "engine_root", lambda c, v: tmp_path / "eng")
    monkeypatch.setattr(engine, "hf_bin", lambda c, v: tmp_path / "eng" / "hyperframes")
    monkeypatch.setattr(engine, "chrome_path", lambda c, v: tmp_path / "chrome" / "linux-1" / "chrome")
    monkeypatch.setattr(engine, "node_dirs", lambda c: ([], []))
    monkeypatch.setattr(engine, "bwrap_argv", lambda *a, **k: seen.update(jail=k) or ["bwrap", "--"])

    class Done:
        returncode, stdout, stderr = 0, "", ""

    def run(cmd, **kw):
        seen["cmd"] = cmd
        out = Path(cmd[cmd.index("-o") + 1])
        out.mkdir(parents=True)
        for i in range(2):
            (out / f"frame-{i:02d}-at-{i}s.png").write_bytes(b"png")
        return Done()
    monkeypatch.setattr(boards.subprocess, "run", run)
    frames = boards.snapshot(ctx, s, s.comp, [1.25, 3], s.work / "board" / "poses", "0.8.106", True)
    assert [f.name for f in frames] == ["frame-00-at-0s.png", "frame-01-at-1s.png"]
    assert seen["jail"]["network"] is False and seen["jail"]["rw"] == [s.work]
    cmd = seen["cmd"]
    assert cmd[:2] == ["bwrap", "--"] and cmd[3:5] == ["snapshot", str(s.comp)]
    assert cmd[cmd.index("--at") + 1] == "1.25,3" and "--no-end" in cmd
    with pytest.raises(DataError, match="snapshot gave 2 of 3 stills"):
        boards.snapshot(ctx, s, s.comp, [1, 2, 3], s.work / "board" / "poses2", "0.8.106", True)


def test_the_board_task_is_fully_filled(ctx, engine_stub):
    p = load_preset(ctx, "example")
    s = runner.Session("20261009-150000-abcd", ctx.sessions_dir / "20261009-150000-abcd")
    skills = runner.prepare(ctx, p, s, "0.8.106", engine_stub, None, [], None)
    for brief, block in ((None, ""), ("- The story: **an idea**", boards.AGAIN.format(id=3, notes="bigger CTA"))):
        boards.write_task(p, s, [*skills, runner.BOARD_SKILL], None, brief, block)
        task = (s.work / "TASK.md").read_text()
        assert not re.search(r"\{\{\w+\}\}", task), re.findall(r"\{\{\w+\}\}", task)
        assert "skills/key-poses/SKILL.md" in task and "No animation" in task and "at most 16 shots" in task
    assert "bigger CTA" in task and "**an idea**" in task and "`story.json`" in task


# --- the builds ----------------------------------------------------------------------------------------------

SHOTS = [{"start": 0, "end": 10, "start_state": "", "change": "", "end_state": "", "technique": "kinetic-word-run",
          "text": ["Ship it today."]},
         {"start": 10, "end": 21, "start_state": "", "change": "", "end_state": "", "technique": "logo-lockup",
          "text": ["Try it free for 14 days."]}]


def stubbed(monkeypatch, calls: list):
    """make() with every session, the engine's snapshot and its install stubbed; each stub writes what the real
    step would."""
    monkeypatch.setattr(engine, "require_version", lambda v: v)
    monkeypatch.setattr(engine, "ensure_engine", lambda *a: None)
    monkeypatch.setattr(engine, "ensure_skills", lambda *a: None)
    monkeypatch.setattr(runner, "resolve_backend", lambda ctx, p, name, model, sandbox, role="agent":
                        runner.Backend("claude", "sonnet", Path("/bin/true"), False))

    def storyteller(ctx_, s_, argv, env, ro, rw, sandbox, version, log_name, timeout, workdir=None):
        calls.append(("story", ""))
        refs = json.loads((s_.work / story.REFERENCES).read_text())
        beats = [{"role": "hook", "seconds": 10, "job": "the claim lands", "copy": ["Ship it today."]},
                 {"role": "cta", "seconds": 11, "job": "where to start", "copy": ["Try it free for 14 days."]}]
        (s_.work / story.STORY).write_text(json.dumps({"idea": "This video tells founders that a page ships today.",
                                                       "title": "Ship today", "pillar": "offer", "beats": beats,
                                                       "references": [{"id": r["id"], "took": "x"} for r in refs[:1]]}))
        return 0

    def board_designer(ctx_, s_, argv, env, ro, rw, sandbox, version, log_name, timeout, workdir=None):
        calls.append(("board", (s_.work / "TASK.md").read_text()))
        (s_.work / "brief.json").write_text(json.dumps({"film": "ship it", "shots": SHOTS}))
        (s_.work / boards.DONE).write_text(json.dumps({"title": "Ship today", "note": "look at the CTA"}))
        html = (s_.comp / "index.html").read_text()
        (s_.comp / "index.html").write_text(html.replace("</body>", f"<!-- poses {len(calls)} --></body>"))
        return 0

    def designer(ctx_, s_, argv, env, ro, rw, sandbox, version, log_name, timeout, workdir=None):
        calls.append(("agent", (s_.work / "TASK.md").read_text(), (s_.comp / "index.html").read_text()))
        (s_.work / "video.json").write_text(json.dumps({"title": "Ship today, animated", "techniques": []}))
        return 0

    def snapshot(ctx_, s_, project, times, out, version, sandbox):
        calls.append(("snapshot", project.name, times))
        out.mkdir(parents=True, exist_ok=True)
        for i, t in enumerate(times):
            (out / f"frame-{i:02d}-at-{t:g}s.png").write_bytes(b"png")
        return sorted(out.glob("*.png"))
    monkeypatch.setattr(story, "run_jailed", storyteller)
    monkeypatch.setattr(boards, "run_jailed", board_designer)
    monkeypatch.setattr(runner, "run_jailed", designer)
    monkeypatch.setattr(boards, "snapshot", snapshot)


BRIEFED = {"video.duration": [20, 25], "content.topic": "launch day"}  # a brief: no pitch round in these builds


def test_a_board_build_stops_at_a_sheet_and_files_no_video(ctx, engine_stub, monkeypatch):
    calls: list = []
    stubbed(monkeypatch, calls)
    res = runner.make(ctx, runner.MakeOpts(preset="example", boards=True, sets=dict(BRIEFED)))
    assert res[0]["ok"], res
    assert [c[0] for c in calls] == ["story", "board", "snapshot", "snapshot"]
    assert calls[2][1:] == ("composition", [5, 15.5]) and calls[3][1:] == ("sheet", [0])
    assert "skills/key-poses/SKILL.md" in calls[1][1] and "**This video tells founders" in calls[1][1]
    con = db.connect(ctx)
    assert con.execute("SELECT count(*) FROM videos").fetchone()[0] == 0
    board = boards.get(con, res[0]["board_id"])
    assert (board["status"], board["title"], board["shots"], board["width"]) == ("review", "Ship today", 2, 1080)
    folder = ctx.abs(board["dir"])
    for name in (boards.SHEET, "poses/01.png", "poses/02.png", "composition/index.html", "story.json", "brief.json",
                 "techniques.json", boards.BRIEF_FILE, boards.DONE):
        assert (folder / name).is_file(), name
    meta = json.loads(board["meta"])
    assert meta["format"]["video.width"] == 1080 and meta["story"]["idea"].startswith("This video tells founders")
    page = (ctx.sessions_dir / res[0]["session"] / "work" / "TASK.md").read_text()
    assert "lay out the key poses" in page                                # the session kept the board's task
    with pytest.raises(UsageError):
        runner.make(ctx, runner.MakeOpts(preset="example", boards=True, revise=1))


def test_an_approved_board_is_animated_and_the_video_records_it(ctx, engine_stub, render_stub, monkeypatch):
    calls: list = []
    stubbed(monkeypatch, calls)
    bid = runner.make(ctx, runner.MakeOpts(preset="example", boards=True, sets=dict(BRIEFED)))[0]["board_id"]
    with pytest.raises(DataError, match="only an approved board is animated"):
        runner.make(ctx, runner.MakeOpts(preset="example", from_board=bid))
    boards.decide(ctx, bid, "approved", "")
    calls.clear()
    res = runner.make(ctx, runner.MakeOpts(preset="example", from_board=bid, count=3))
    assert len(res) == 1 and res[0]["ok"], res                            # one board, one film
    assert [c[0] for c in calls] == ["agent"]                             # no story again, no board step
    task, comp = calls[0][1], calls[0][2]
    assert f"animates board {bid}, which the operator approved" in task and "**This video tells founders" in task
    assert "<!-- poses 2 -->" in comp                                      # the board's poses, not a blank scaffold
    con = db.connect(ctx)
    video = db.get_video(con, res[0]["video_id"])
    assert video["board_id"] == bid and video["status"] == "review"
    meta = json.loads(video["meta"])
    assert meta["board"] == bid and meta["story"]["idea"].startswith("This video tells founders")
    assert boards.get(con, bid)["status"] == "approved"                   # animating a board leaves it approved


def test_a_board_sent_back_is_laid_out_again_and_replaced(ctx, engine_stub, monkeypatch):
    calls: list = []
    stubbed(monkeypatch, calls)
    first = runner.make(ctx, runner.MakeOpts(preset="example", boards=True, sets=dict(BRIEFED)))[0]
    old = ctx.abs(boards.get(db.connect(ctx), first["board_id"])["dir"])
    boards.decide(ctx, first["board_id"], "revision", "make the CTA bigger")
    with pytest.raises(DataError, match="only an approved board"):
        runner.make(ctx, runner.MakeOpts(preset="example", from_board=first["board_id"]))
    calls.clear()
    again = runner.make(ctx, runner.MakeOpts(preset="example", boards=True, from_board=first["board_id"]))[0]
    assert again["ok"], again
    assert [c[0] for c in calls] == ["board", "snapshot", "snapshot"]     # the story is kept, not told again
    assert '"make the CTA bigger"' in calls[0][1] and "**This video tells founders" in calls[0][1]
    con = db.connect(ctx)
    parent, child = boards.get(con, first["board_id"]), boards.get(con, again["board_id"])
    assert (parent["status"], parent["dir"]) == ("superseded", "") and not old.exists()
    assert child["parent_id"] == first["board_id"] and child["status"] == "review"


def test_without_boards_a_build_runs_on_and_files_videos(ctx, monkeypatch):
    used = []
    monkeypatch.setattr(engine, "require_version", lambda v: v)
    monkeypatch.setattr(engine, "ensure_engine", lambda *a: None)
    monkeypatch.setattr(engine, "ensure_skills", lambda *a: None)
    monkeypatch.setattr(runner, "resolve_backend", lambda *a, **k: runner.Backend("claude", None, Path("/bin/true"), True))
    monkeypatch.setattr(runner, "run_one", lambda *a, **k: used.append(("video", k["board"])) or {"ok": True})
    monkeypatch.setattr(boards, "run_board", lambda *a, **k: used.append(("board", k["board"])) or {"ok": True})
    runner.make(ctx, runner.MakeOpts(preset="example", count=2))
    assert used == [("video", None), ("video", None)]


def test_boards_move_with_the_library(ctx, monkeypatch):
    bid = a_board(ctx)
    assert cli.main(["--json", "library", "dir", "media"]) == 0
    board = boards.get(db.connect(make_ctx()), bid)
    assert board["dir"].startswith("media/") and (ctx.project / board["sheet"]).is_file()
