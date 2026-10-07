"""social-studio command line. Nouns first, `--json` everywhere, sysexits exit codes.

Humans and agents share one binary. Human-only actions (approve, reject, revise, schedule or cancel
posts, reveal scheduled videos, connect accounts, anything that writes outside the repo) need an
interactive terminal; agents in a harness never have one.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import textwrap
from datetime import timedelta
from pathlib import Path

from . import __version__, approval, db, engine, platforms, posting, review
from .core import (EFFORTS, FORMATS, GUARDED_CONFIG, PKG_DIR, PROJECT_FILE, SOUNDS, ConfigError, Ctx, DataError,
                   StudioError, UsageError, dget, dset, emit, format_sets, guarded, is_tty, iso, list_presets, load_preset,
                   load_toml, log, make_ctx, now_utc, parse_sets, parse_value, require_human, save_env,
                   validate_preset)

DEFAULT_CONFIG = {
    "default_preset": "",
    "preset_paths": [],
    "timezone": "",
    "paths": {"library": "library"},
    "backend": {"default": "claude",
                "claude": {"model": "opus", "auth": "user"},
                "opencode": {"model": ""},
                "codex": {"model": "", "auth": ""}},
    "sandbox": {"enabled": True},
    "publish": {"buffer": {"organization": "", "channels": [], "ai_label": False},
                "media": {"endpoint": "", "bucket": "", "region": "auto", "public_url": "", "prefix": "social-studio/"}},
}


# --- formatting --------------------------------------------------------------------------------------

def table(rows: list[dict], cols: list[str]) -> str:
    if not rows:
        return "(none)"
    cells = [[str(r.get(c, "") if r.get(c) is not None else "") for c in cols] for r in rows]
    widths = [min(60, max(len(c), *(len(row[i]) for row in cells))) for i, c in enumerate(cols)]
    line = lambda vals: "  ".join(v[:w].ljust(w) for v, w in zip(vals, widths))  # noqa: E731
    return "\n".join([line(cols), line(["-" * w for w in widths]), *map(line, cells)])


def pick_preset(ctx: Ctx, given: str | None) -> str:
    """The boot picker: flag, then config default, then a menu when a human is at the terminal."""
    if given:
        return given
    if ctx.cfg("default_preset"):
        return ctx.cfg("default_preset")
    found = list_presets(ctx)
    if not found:
        raise ConfigError("no presets found", "run `social-studio preset new <name>`")
    if not is_tty():
        raise UsageError("no preset given", f"pass --preset, or set default_preset in {PROJECT_FILE}")
    for i, p in enumerate(found):
        log(f"  [{i}] {p['name']}  {p['description']}")
    choice = input("preset number: ").strip() or "0"
    return found[int(choice)]["name"]


# --- commands ----------------------------------------------------------------------------------------

def cmd_init(ctx: Ctx, a) -> int:
    """Create or finish a project: one folder holding config, .env, presets, library and internal state."""
    root = Path(a.dir).expanduser().resolve() if a.dir else (ctx.project or Path.cwd().resolve())
    root.mkdir(parents=True, exist_ok=True)
    ctx.project = root
    notes = []
    if ctx.config_path.exists():
        ctx.config = load_toml(ctx.config_path)
    else:
        ctx.config = copy.deepcopy(DEFAULT_CONFIG)
        ctx.save_config()
        notes.append(f"wrote {ctx.config_path}")
    for d in (root / "presets", ctx.library_dir, ctx.studio_dir):
        d.mkdir(parents=True, exist_ok=True)
    if not ctx.env_path.exists():
        fd = os.open(ctx.env_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write((PKG_DIR / "data" / "env.template").read_text())
        notes.append(f"wrote {ctx.env_path} (0600)")
    if not (root / ".gitignore").exists():
        shutil.copyfile(PKG_DIR / "data" / "project.gitignore", root / ".gitignore")
        notes.append("wrote .gitignore (.env, .studio/, library/)")
    db.connect(ctx).close()
    notes.append(f"project {root} (writes stay inside {ctx.boundary})")
    if approval.is_ready(ctx):
        notes.append("approval key present")
    elif is_tty():
        log("Create the approval key. Choose a passphrase only you know: it is what lets you, and only you, approve videos.")
        notes.append(f"approval key {approval.init_key(ctx)}")
    else:
        notes.append("approval key NOT created (needs a terminal): run `social-studio init` yourself")
    if is_tty() and not ctx.cfg("default_preset") and list_presets(ctx):
        name = pick_preset(ctx, None)
        dset(ctx.config, "default_preset", name)
        ctx.save_config()
        notes.append(f"default preset {name}")
    if not a.no_engine and ctx.cfg("default_preset"):
        p = load_preset(ctx, ctx.cfg("default_preset"))
        v = engine.require_version(p.get("render.version"))
        engine.ensure_engine(ctx, v, p.get("render.libraries", []))
        engine.ensure_skills(ctx, v)
        notes.append(f"engine hyperframes {v} ready in {ctx.engine_dir}")
    emit(ctx, {"init": notes}, "\n".join(notes))
    return 0


def _checks(ctx: Ctx) -> list[dict]:
    out = []

    def add(name, ok, detail="", hint="", required=True):
        out.append({"check": name, "ok": bool(ok), "detail": detail, "hint": hint, "required": required})

    add("python >= 3.11", sys.version_info >= (3, 11), sys.version.split()[0])
    node = shutil.which("node")
    nv = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip() if node else ""
    add("node >= 22", nv and int(nv.lstrip("v").split(".")[0]) >= 22, nv or "missing", "install Node.js 22+")
    for b in ("npm", "ffmpeg", "ffprobe", "ssh-keygen"):
        add(b, shutil.which(b), shutil.which(b) or "missing", f"install {b}")
    add("bwrap (sandbox)", engine.sandbox_available() or not ctx.cfg("sandbox.enabled", True),
        shutil.which("bwrap") or "missing", "install bubblewrap, or set sandbox.enabled = false")
    for b in ("claude", "opencode", "codex"):
        add(f"backend {b}", shutil.which(b), shutil.which(b) or "not installed", "", required=(b == ctx.cfg("backend.default", "claude")))
    add("project", ctx.project is not None, str(ctx.project or "none found"),
        "run `social-studio init <dir>`, pass --project, or cd into the project")
    if ctx.project is None:
        return out
    add(PROJECT_FILE, ctx.config_path.exists(), str(ctx.config_path), "run `social-studio init`")
    if ctx.env_path.exists():
        mode = oct(ctx.env_path.stat().st_mode & 0o777)
        add(".env is 0600", mode == "0o600", mode, f"chmod 600 {ctx.env_path}")
    else:
        add(".env", False, "missing", "run `social-studio init`")
    try:
        con = db.connect(ctx)
        add("database", True, f"{ctx.db_path} (schema v{con.execute('PRAGMA user_version').fetchone()[0]})")
        con.close()
    except Exception as e:  # noqa: BLE001
        add("database", False, str(e))
    key, _, _ = approval.key_paths(ctx)
    if key.exists():
        probe = subprocess.run(["ssh-keygen", "-y", "-P", "", "-f", str(key)], capture_output=True)
        add("approval key has a passphrase", probe.returncode != 0, str(key), "recreate it with a passphrase")
    else:
        add("approval key", False, "missing", "run `social-studio init` yourself, in a terminal")
    name = ctx.cfg("default_preset")
    if name:
        try:
            p = load_preset(ctx, name)
            problems = validate_preset(p, ctx)
            add(f"preset {name}", not problems, "; ".join(problems) or str(p.dir))
            v = p.get("render.version", "?")
            add(f"engine hyperframes {v}", engine.hf_bin(ctx, v).exists() and engine.skills_root(ctx, v).is_dir(),
                str(engine.engine_root(ctx, v)), "run `social-studio engine install`")
        except StudioError as e:
            add(f"preset {name}", False, str(e), e.hint)
    else:
        add("default preset", False, "not set", "social-studio config set default_preset <name>", required=False)
    from . import platforms
    for pname, ad in platforms.registry().items():
        add(f"account {pname}", ad.connected(ctx), "connected" if ad.connected(ctx) else "not connected",
            f"social-studio channel connect {pname}", required=False)
    return out


def cmd_doctor(ctx: Ctx, a) -> int:
    checks = _checks(ctx)
    bad = [c for c in checks if c["required"] and not c["ok"]]
    human = "\n".join(f"{'ok ' if c['ok'] else ('-- ' if not c['required'] else 'XX ')} {c['check']}: {c['detail']}"
                      + (f"   -> {c['hint']}" if not c["ok"] and c["hint"] else "") for c in checks)
    emit(ctx, {"ok": not bad, "checks": checks}, human)
    return 1 if bad else 0


def cmd_config(ctx: Ctx, a) -> int:
    if a.action == "path":
        paths = {"project": ctx.need(), "config": ctx.config_path, "env": ctx.env_path, "library": ctx.library_dir,
                 "state": ctx.studio_dir, "boundary": ctx.boundary}
        emit(ctx, {k: str(v) for k, v in paths.items()}, "\n".join(f"{k:<9}{v}" for k, v in paths.items()))
    elif a.action == "list":
        emit(ctx, ctx.config, ctx.config_path.read_text() if ctx.config_path.exists() else f"(no {PROJECT_FILE})")
    elif a.action == "get":
        if not a.key:
            raise UsageError("config get needs a key")
        val = dget(ctx.config, a.key)
        emit(ctx, {a.key: val}, json.dumps(val) if not isinstance(val, str) else val)
    else:
        if not a.key or a.value is None:
            raise UsageError("config set needs a key and a value")
        if a.key == "paths.library":
            raise UsageError("move the library with `social-studio library dir <folder>`",
                             "it moves the videos and keeps the database pointing at them")
        if guarded(a.key, GUARDED_CONFIG):  # harness binary and credentials, sandbox, preset folders, post routes
            require_human(f"setting {a.key}")
        dset(ctx.config, a.key, parse_value(a.value))
        ctx.save_config()
        emit(ctx, {a.key: dget(ctx.config, a.key)}, f"{a.key} = {json.dumps(dget(ctx.config, a.key))}")
    return 0


def cmd_model(ctx: Ctx, a) -> int:
    if a.action == "key":
        require_human("storing an API key")
        name = (a.backend or "").upper()
        if not name.endswith(("_API_KEY", "_TOKEN")):
            raise UsageError("model key needs the variable name", "e.g. social-studio model key XAI_API_KEY")
        import getpass
        value = getpass.getpass(f"{name}: ").strip()
        if not value:
            raise UsageError("empty value")
        save_env(ctx.env_path, {name: value})
        emit(ctx, {"saved": name}, f"saved {name} to {ctx.env_path}")
        return 0
    if a.action == "set":
        if a.backend not in ("claude", "opencode", "codex"):
            raise UsageError("model set needs a backend: claude, opencode or codex")
        dset(ctx.config, "backend.default", a.backend)
        if a.model:
            dset(ctx.config, f"backend.{a.backend}.model", a.model)
        ctx.save_config()
    rows = [{"backend": b, "default": "*" if b == ctx.cfg("backend.default", "claude") else "",
             "model": ctx.cfg(f"backend.{b}.model") or "(harness default)",
             "installed": shutil.which(b) or "no"} for b in ("claude", "opencode", "codex")]
    emit(ctx, rows, table(rows, ["backend", "default", "model", "installed"]) +
         "\n\nopencode models use provider/model, e.g. xai/grok-4, deepseek/deepseek-chat, openrouter/<id>.")
    return 0


def cmd_preset(ctx: Ctx, a) -> int:
    if a.action == "list":
        rows = list_presets(ctx)
        emit(ctx, rows, table(rows, ["name", "description", "path"]))
        return 0
    if a.action == "new":
        if not a.name:
            raise UsageError("preset new needs a name")
        dest = ctx.need() / "presets" / a.name
        if dest.exists():
            raise DataError(f"{dest} already exists")
        shutil.copytree(PKG_DIR / "presets" / "example", dest)
        emit(ctx, {"created": str(dest)}, f"created {dest}/preset.toml; edit it, then `social-studio preset validate {a.name}`")
        return 0
    name = pick_preset(ctx, a.name)
    p = load_preset(ctx, name, parse_sets(a.set or []))
    if a.action == "validate":
        problems = validate_preset(p, ctx)
        emit(ctx, {"preset": p.name, "ok": not problems, "problems": problems, "hash": p.hash},
             "ok" if not problems else "\n".join(problems))
        return 0 if not problems else 65
    emit(ctx, {"name": p.name, "dir": str(p.dir), "hash": p.hash, "data": p.data}, json.dumps(p.data, indent=2))
    return 0


def cmd_engine(ctx: Ctx, a) -> int:
    p = load_preset(ctx, pick_preset(ctx, a.preset))
    v = engine.require_version(a.version or p.get("render.version"))
    if a.action == "install":
        engine.ensure_engine(ctx, v, p.get("render.libraries", []))
        engine.ensure_skills(ctx, v)
    info = {"version": v, "root": str(engine.engine_root(ctx, v)), "installed": engine.hf_bin(ctx, v).exists(),
            "skills": sorted(x.name for x in engine.skills_root(ctx, v).iterdir()) if engine.skills_root(ctx, v).is_dir() else []}
    if info["installed"]:
        info["chrome"] = str(engine.chrome_path(ctx, v))
    emit(ctx, info, "\n".join(f"{k}: {val}" for k, val in info.items()))
    return 0


def cmd_make(ctx: Ctx, a) -> int:
    from .runner import MakeOpts, make
    sets = parse_sets(a.set or [])
    for flag, key in (("title", "content.title"), ("subject", "content.subject"), ("topic", "content.topic"),
                      ("pillar", "content.pillar"), ("notes", "content.notes"), ("effort", "agent.effort"),
                      ("review_effort", "review.effort"), ("pacing", "video.pacing"), ("motion", "video.motion")):
        if getattr(a, flag):
            sets[key] = getattr(a, flag)
    sets.update(format_sets(a.aspect, a.fps, a.duration, a.sound, a.rounds))
    opts = MakeOpts(preset=pick_preset(ctx, a.preset), count=a.count, parallel=a.parallel, backend=a.backend,
                    model=a.model, sets=sets, sandbox=False if a.no_sandbox else None, revise=a.revise,
                    review=a.review)
    results = make(ctx, opts)
    ok = [r for r in results if r["ok"]]
    human = "\n".join(
        (f"video {r['video_id']}: {r['title']}  ({r['bytes'] / 1e6:.1f} MB, {r['duration']:.1f}s)  -> {r['file']}"
         if r["ok"] else f"FAILED session {r['session']}: {r['error']}") for r in results)
    if ok:
        human += ("\n\nNext: a human reviews them in a terminal with `social-studio review`, "
                  "then schedules approved ones with `social-studio post`.")
    emit(ctx, {"made": len(ok), "failed": len(results) - len(ok), "results": results}, human)
    return 0 if ok else 1


HIDDEN = ("scheduled", "posted", "failed")


def move_library(ctx: Ctx, new: Path) -> int:
    """Move every video folder into `new` and repoint the database. Both ends stay inside the repo."""
    old = ctx.library_dir
    new.mkdir(parents=True, exist_ok=True)
    moved = 0
    con = db.connect(ctx)
    try:
        with db.tx(con):
            for v in db.rows(con.execute("SELECT id, dir, file FROM videos WHERE dir <> ''")):
                src = ctx.abs(v["dir"])
                dst = new / src.name
                if src.exists() and src != dst:
                    shutil.move(str(src), str(dst))
                    moved += 1
                con.execute("UPDATE videos SET dir = ?, file = ? WHERE id = ?",
                            (ctx.rel(dst), ctx.rel(dst / Path(v["file"]).name), v["id"]))
    finally:
        con.close()
    d, project = old, ctx.need().resolve()
    while d != new and project in d.parents and d.is_dir() and not any(d.iterdir()):  # prune emptied folders
        d.rmdir()
        d = d.parent
    if project not in new.parents:
        log(f"note: {new} is outside the project, so the project's .gitignore does not cover it")
    return moved


def cmd_library(ctx: Ctx, a) -> int:
    if a.action == "dir":
        if not a.target:
            emit(ctx, {"library": str(ctx.library_dir)}, str(ctx.library_dir))
            return 0
        new = ctx.inside(ctx.abs(a.target), "the library")
        moved = move_library(ctx, new)
        dset(ctx.config, "paths.library", ctx.rel(new))
        ctx.save_config()
        emit(ctx, {"library": str(new), "moved": moved}, f"library is now {new} ({moved} video folders moved)")
        return 0
    con = db.connect(ctx)
    try:
        if a.action == "list":
            if a.all:
                require_human("listing scheduled and posted videos")
            statuses = a.status or []
            if any(s in HIDDEN for s in statuses):
                require_human("listing scheduled and posted videos")
            hide = (*HIDDEN, "superseded")  # superseded versions have no files left
            where, args = ("", ()) if a.all else (f"WHERE status NOT IN ({','.join('?' * len(hide))})", hide)
            if statuses:
                where = f"WHERE status IN ({','.join('?' * len(statuses))})"
                args = tuple(statuses)
            rows = db.rows(con.execute(f"SELECT id, status, title, pillar, duration, bytes, created_at FROM videos "
                                       f"{where} ORDER BY id DESC LIMIT ?", (*args, a.limit)))
            for r in rows:
                r["mb"] = round(r.pop("bytes") / 1e6, 1)
            emit(ctx, rows, table(rows, ["id", "status", "title", "pillar", "duration", "mb", "created_at"]))
            return 0
        if not (a.target or "").isdigit():
            raise UsageError(f"library {a.action} needs a video id")
        v = db.get_video(con, int(a.target))
        if v["status"] in HIDDEN:
            require_human(f"viewing a {v['status']} video")
        if a.action == "path":
            f = str(ctx.abs(v["file"])) if v["file"] else ""
            emit(ctx, {"file": f, "dir": str(ctx.abs(v["dir"])) if v["dir"] else ""}, f or "(files deleted)")
        elif a.action == "open":
            opener = shutil.which("xdg-open") or shutil.which("open")
            if not opener:
                raise DataError("no xdg-open/open available", str(ctx.abs(v["file"])))
            if not v["file"]:
                raise DataError(f"video {v['id']} has no files (a revision replaced it)")
            subprocess.Popen([opener, str(ctx.abs(v["file"]))], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            emit(ctx, {"opened": str(ctx.abs(v["file"]))}, str(ctx.abs(v["file"])))
        else:
            v["meta"] = json.loads(v["meta"])
            v["events"] = db.rows(con.execute("SELECT old_status, new_status, actor, at FROM video_events "
                                              "WHERE video_id = ? ORDER BY id", (v["id"],)))
            emit(ctx, v, json.dumps(v, indent=2, default=str))
    finally:
        con.close()
    return 0


def _review_rows(con) -> list[dict]:
    return db.rows(con.execute("SELECT id, status, title, description, dir, file, meta, sha256, slug, pillar, preset "
                               "FROM videos WHERE status IN ('review', 'revision') ORDER BY id"))


def _approve(ctx: Ctx, ids: list[int]) -> dict:
    con = db.connect(ctx, actor="human")
    try:
        videos = [db.get_video(con, i) for i in ids]
        for v in videos:
            if v["status"] not in ("review", "revision", "failed"):
                raise DataError(f"video {v['id']} is {v['status']}; only review or revision videos can be approved")
        signed = approval.sign(ctx, videos)
        with db.tx(con):
            for v, payload, sig in signed:
                con.execute("INSERT OR REPLACE INTO approvals (video_id, sha256, approved_at, payload, signature) "
                            "VALUES (?, ?, ?, ?, ?)", (v["id"], v["sha256"], payload.split("approved_at:")[1].strip(),
                                                        payload, sig))
                db.set_status(con, v["id"], "approved", "approved by a human")
    finally:
        con.close()
    return {"approved": ids}


def _decide(ctx: Ctx, vid: int, status: str, notes: str) -> None:
    con = db.connect(ctx, actor="human")
    try:
        with db.tx(con):
            db.set_status(con, vid, status, notes)
    finally:
        con.close()


def cmd_review(ctx: Ctx, a) -> int:
    con = db.connect(ctx)
    try:
        rows = _review_rows(con)
        v = db.get_video(con, a.ids[0]) if a.action == "rescore" and len(a.ids) == 1 else None
    finally:
        con.close()
    if a.action == "rescore":
        if v is None:
            raise UsageError("review rescore needs one video id")
        if v["status"] in HIDDEN:
            require_human(f"re-scoring a {v['status']} video")
        res = review.rescore(ctx, v, a.times, {"review.effort": a.effort} if a.effort else None)
        emit(ctx, res, "\n".join(f"{c}: {[r['scores'][c] for r in res['runs'] if r['scores']]} spread {s}"
                                 for c, s in res["spread"].items()) or "no run produced a valid verdict")
        return 0
    if a.action == "list":
        out = []
        for r in rows:
            verdict = (json.loads(r["meta"]).get("verdict") or {})
            out.append({"id": r["id"], "status": r["status"], "title": r["title"], "reviewer_pass": verdict.get("pass"),
                        "file": str(ctx.abs(r["file"]))})
        emit(ctx, out, table(out, ["id", "status", "title", "reviewer_pass", "file"]))
        return 0
    if a.action == "approve":
        require_human("approving videos")
        if not a.ids:
            raise UsageError("review approve needs video ids")
        res = _approve(ctx, a.ids)
        emit(ctx, res, f"approved {res['approved']}; schedule them with `social-studio post`")
        return 0
    if a.action in ("reject", "revise"):
        require_human(f"marking videos for {a.action}")
        if not a.ids:
            raise UsageError(f"review {a.action} needs video ids")
        if a.action == "revise" and not a.notes:
            raise UsageError("review revise needs --notes saying what to change")
        for vid in a.ids:
            _decide(ctx, vid, "rejected" if a.action == "reject" else "revision", a.notes or "")
        emit(ctx, {a.action: a.ids}, f"{a.action}: {a.ids}" + (
            "\nThen: social-studio make --revise <id>" if a.action == "revise" else ""))
        return 0
    # interactive walk-through
    require_human("reviewing videos")
    if not rows:
        emit(ctx, {"pending": 0}, "nothing to review")
        return 0
    to_approve: list[int] = []
    for r in rows:
        meta = json.loads(r["meta"])
        verdict = meta.get("verdict") or {}
        print(f"\n#{r['id']}  {r['title']}  [{r['status']}]\n  {r['description']}\n  {r['file']}")
        if verdict:
            print(f"  reviewer ({verdict.get('model')}): pass={verdict.get('pass')}  {verdict.get('summary', '')}")
            for issue in verdict.get("issues", [])[:5]:
                print(f"    - {issue}")
        # Approving signs this text with the video: show it exactly as each network will get it.
        caps = meta.get("video", {}).get("captions") or {"default": ""}
        pub = posting.preset_publish(ctx, r["preset"])
        for k in [c for c in caps if c != "default"] or ["default"]:
            print(f"  post text [{k}]:\n" + textwrap.indent(platforms.caption_for(k, r, pub), "    "))
        while True:
            ans = input("  [a]pprove [r]eject re[v]ise [o]pen [s]kip [q]uit > ").strip().lower()
            if ans == "o":
                opener = shutil.which("xdg-open") or shutil.which("open")
                if opener:
                    subprocess.Popen([opener, str(ctx.abs(r["file"]))], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                continue
            break
        if ans == "q":
            break
        if ans == "a":
            to_approve.append(r["id"])
        elif ans == "r":
            _decide(ctx, r["id"], "rejected", input("  reason (optional): ").strip())
        elif ans == "v":
            _decide(ctx, r["id"], "revision", input("  what should change: ").strip())
    if to_approve:
        print(f"\nSigning {len(to_approve)} approval(s), each covering the video and its post text. "
              "Enter your approval passphrase.")
        res = _approve(ctx, to_approve)
        emit(ctx, res, f"approved {res['approved']}; schedule them with `social-studio post`")
    return 0


def cmd_agent(ctx: Ctx, a) -> int:
    """Everything an agent needs, nothing it should not see. Agents read; they never schedule or post."""
    con = db.connect(ctx, actor="agent")
    try:
        if a.action == "status":
            counts = dict(con.execute("SELECT status, count(*) FROM agent_videos GROUP BY status").fetchall())
            nxt = con.execute("SELECT at FROM agent_calendar WHERE status = 'scheduled' AND at > ? ORDER BY at LIMIT 1",
                              (iso(),)).fetchone()
            data = {"videos": counts,
                    "approval_needed": counts.get("review", 0) + counts.get("revision", 0),
                    "ready_to_post": counts.get("approved", 0),  # approved and not on a live post
                    "next_post": posting.local_str(ctx, nxt[0]) if nxt else None}
            emit(ctx, data, json.dumps(data, indent=2))
        elif a.action == "videos":
            rows = db.rows(con.execute("SELECT id, status, title, pillar, topic, created_at FROM agent_videos "
                                       "ORDER BY id DESC LIMIT ?", (a.limit,)))
            emit(ctx, rows, table(rows, ["id", "status", "title", "pillar", "topic", "created_at"]))
        elif a.action == "topics":
            rows = db.rows(con.execute("SELECT day, pillar, topic, angle FROM agent_topics ORDER BY day DESC LIMIT ?",
                                       (a.limit,)))
            emit(ctx, rows, table(rows, ["day", "pillar", "topic", "angle"]))
        else:  # calendar: when posts go out and where, never which video
            rows = db.rows(con.execute("SELECT id AS post_id, at, status, platforms FROM agent_calendar "
                                       "WHERE at >= ? ORDER BY at LIMIT ?",
                                       (iso(now_utc() - timedelta(days=1)), a.limit)))
            for r in rows:
                r["local"] = posting.local_str(ctx, r["at"])
            emit(ctx, rows, table(rows, ["post_id", "local", "status", "platforms"]))
    finally:
        con.close()
    return 0


def _scheduled(ctx: Ctx, res: dict | None) -> int:
    if res is None:
        return 0
    if res.get("dry_run"):
        emit(ctx, res, "(dry run: nothing uploaded or scheduled)")
        return 0
    human = (f"post {res['post_id']}  {res['local']}  video {res['video_id']}\n" +
             table(res["targets"], ["platform", "channel", "status", "buffer_id", "error"]))
    emit(ctx, res, human)
    return 0 if any(t["status"] == "scheduled" for t in res["targets"]) else 1


def cmd_post(ctx: Ctx, a) -> int:
    if a.action == "sync":
        res = posting.sync(ctx)
        emit(ctx, res, table(res, ["post_id", "platform", "status", "url", "error"]) if res else "nothing due")
        return 1 if any(r.get("status") == "error" for r in res) else 0
    if a.action == "list":
        rows = posting.listing(ctx, include_past=a.past, limit=a.limit)
        emit(ctx, rows, table(rows, ["post_id", "local", "status", "video_id", "title", "targets", "urls"]))
        return 0
    if a.action == "cancel":
        if a.target is None:
            raise UsageError("post cancel needs a post id", "see `social-studio post list`")
        emit(ctx, posting.cancel(ctx, a.target), f"post {a.target} cancelled and removed from Buffer")
        return 0
    if a.action == "schedule":
        if a.target is None or not a.at:
            raise UsageError("post schedule needs a video id and --at",
                             "e.g. social-studio post schedule 12 --at '2026-10-08 09:00' -c instagram -c x")
        p = posting.plan(ctx, a.target, a.channel, a.at)
        log(posting.describe(p) + "\n")
        if a.dry_run:
            return _scheduled(ctx, {"dry_run": True, "video_id": a.target, "local": p["local"]})
        if not a.yes and input("schedule it? [y/N] ").strip().lower() != "y":
            log("nothing scheduled")
            return 0
        return _scheduled(ctx, posting.execute(ctx, p))
    return _scheduled(ctx, posting.pick(ctx, dry_run=a.dry_run))


def cmd_channel(ctx: Ctx, a) -> int:
    if a.action == "list":
        rows = [{"account": n, "connected": ad.connected(ctx)} for n, ad in platforms.registry().items()]
        emit(ctx, rows, table(rows, ["account", "connected"]))
        return 0
    if not a.platform:
        raise UsageError(f"channel {a.action} needs an account: buffer or media")
    ad = platforms.get(a.platform)
    if a.action == "connect":
        ad.connect(ctx)
        emit(ctx, {"platform": a.platform, "connected": True, "as": ad.whoami(ctx)}, f"connected: {ad.whoami(ctx)}")
    elif a.action == "test":
        who = ad.whoami(ctx)
        emit(ctx, {"platform": a.platform, "ok": True, "as": who}, f"ok: {who}")
    else:
        require_human("disconnecting an account")
        save_env(ctx.env_path, {k: None for k in ad.keys})
        emit(ctx, {"platform": a.platform, "disconnected": True}, f"removed {a.platform} keys from .env")
    return 0


def cmd_timer(ctx: Ctx, a) -> int:
    unit_dir = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "systemd" / "user"
    name = "social-studio-post"
    if a.action in ("install", "remove"):
        require_human(f"{a.action} the systemd timer (it writes to {unit_dir}, outside the repo)")
    if a.action == "install":
        exe = shutil.which("social-studio") or f"{sys.executable} -m social_studio"
        unit_dir.mkdir(parents=True, exist_ok=True)
        (unit_dir / f"{name}.service").write_text(
            f"[Unit]\nDescription=social-studio: record what Buffer did with due posts\n\n[Service]\nType=oneshot\n"
            f"ExecStart={exe} --project {ctx.need()} post sync\n")
        (unit_dir / f"{name}.timer").write_text(
            f"[Unit]\nDescription=social-studio: sync Buffer posts every {a.every} minutes\n\n[Timer]\n"
            f"OnCalendar=*:0/{a.every}\nPersistent=true\n\n[Install]\nWantedBy=timers.target\n")
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "--user", "enable", "--now", f"{name}.timer"], check=True)
    elif a.action == "remove":
        subprocess.run(["systemctl", "--user", "disable", "--now", f"{name}.timer"], check=False)
        for ext in ("service", "timer"):
            (unit_dir / f"{name}.{ext}").unlink(missing_ok=True)
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    out = subprocess.run(["systemctl", "--user", "list-timers", f"{name}.timer", "--no-pager"], capture_output=True, text=True)
    emit(ctx, {"timer": name, "status": out.stdout.strip()}, out.stdout.strip() or "no timer")
    return 0


def cmd_skill(ctx: Ctx, a) -> int:
    src = PKG_DIR / "data" / "SKILL.md"
    if a.action == "show":
        print(src.read_text())
        return 0
    targets = {"claude": Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "skills",
               "opencode": Path.home() / ".config" / "opencode" / "skills",
               "codex": Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "skills"}
    base = targets.get(a.target) or ctx.abs(a.target)
    dest = base / "social-studio"
    try:
        ctx.inside(dest, "the skill")
    except StudioError:
        require_human(f"installing the skill into {base}, outside the repo")
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest / "SKILL.md")
    emit(ctx, {"installed": str(dest / "SKILL.md")}, f"installed {dest / 'SKILL.md'}")
    return 0


def cmd_completion(ctx: Ctx, a) -> int:
    """Shell completion generated from the parser itself, so it never drifts from the commands."""
    ap = build_parser()
    sub = next(x for x in ap._actions if isinstance(x, argparse._SubParsersAction))
    top = sorted(sub.choices) + [o for x in ap._actions for o in x.option_strings if o.startswith("--")]
    cases = []
    for name, p in sub.choices.items():
        words = set()
        for act in p._actions:
            words.update(o for o in act.option_strings if o.startswith("--"))
            if act.choices and not act.option_strings:
                words.update(str(c) for c in act.choices)
        cases.append(f'    {name}) COMPREPLY=( $(compgen -W "{" ".join(sorted(words))}" -- "$cur") ) ;;')
    script = "\n".join([
        "_social_studio() {",
        '  local cur="${COMP_WORDS[COMP_CWORD]}" cmd="" w',
        '  for w in "${COMP_WORDS[@]:1:COMP_CWORD-1}"; do case "$w" in -*) ;; *) cmd="$w"; break ;; esac; done',
        '  if [ -z "$cmd" ]; then COMPREPLY=( $(compgen -W "' + " ".join(top) + '" -- "$cur") ); return; fi',
        '  case "$cmd" in', *cases, "  esac", "}", "complete -F _social_studio social-studio"])
    if a.shell == "zsh":
        script = "autoload -U +X bashcompinit && bashcompinit\n" + script
    print(script)
    return 0


def cmd_version(ctx: Ctx, a) -> int:
    emit(ctx, {"version": __version__}, __version__)
    return 0


# --- parser ------------------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="social-studio",
        description="Make motion-graphics videos in isolated LLM sessions, keep them in a library, post approved ones.",
        epilog="Typical day: social-studio make -n 3  ->  social-studio review  ->  social-studio post",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="machine-readable output on stdout")
    ap.add_argument("--project", help=f"project folder (default: found from the current folder: {PROJECT_FILE}, or social/{PROJECT_FILE})")
    ap.add_argument("--version", action="version", version=f"social-studio {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="command")

    def cmd(name, fn, help_, aliases=()):
        p = sub.add_parser(name, help=help_, description=help_, aliases=list(aliases))
        p.set_defaults(fn=fn)
        return p

    p = cmd("init", cmd_init, "create or finish a project: config, .env, folders, database, approval key, engine",
            aliases=["setup"])
    p.add_argument("dir", nargs="?", help="project folder (default: the current project, or this folder)")
    p.add_argument("--no-engine", action="store_true", help="skip installing the render engine")
    cmd("doctor", cmd_doctor, "check everything a run needs; exit 1 if a required check fails")
    cmd("version", cmd_version, "print the version")

    p = cmd("config", cmd_config, f"read or change {PROJECT_FILE} (comments are not kept on write)")
    p.add_argument("action", choices=["get", "set", "list", "path"])
    p.add_argument("key", nargs="?")
    p.add_argument("value", nargs="?")

    p = cmd("model", cmd_model, "list LLM backends, or pick the default backend and model")
    p.add_argument("action", nargs="?", choices=["list", "set", "key"], default="list")
    p.add_argument("backend", nargs="?", help="set: claude, opencode or codex. key: the .env name, e.g. XAI_API_KEY")
    p.add_argument("model", nargs="?", help="e.g. opus, sonnet, xai/grok-4, deepseek/deepseek-chat")

    p = cmd("preset", cmd_preset, "list, show, validate or create presets")
    p.add_argument("action", choices=["list", "show", "validate", "new"])
    p.add_argument("name", nargs="?")
    p.add_argument("--set", action="append", metavar="KEY=VALUE", help="override a preset value")

    p = cmd("engine", cmd_engine, "install or inspect the pinned render engine")
    p.add_argument("action", nargs="?", choices=["install", "status"], default="status")
    p.add_argument("--preset")
    p.add_argument("--version", dest="version")

    p = cmd("make", cmd_make, "generate videos: one isolated agent session per video")
    p.add_argument("-n", "--count", type=int, default=1, help="how many videos (default 1)")
    p.add_argument("--parallel", type=int, default=1, help="sessions at once (default 1)")
    p.add_argument("--preset", help="preset name or path (default: config default_preset, or a picker)")
    p.add_argument("--backend", choices=["claude", "opencode", "codex"])
    p.add_argument("--model")
    p.add_argument("--set", action="append", metavar="KEY=VALUE",
                   help="override a preset value, e.g. video.duration=[10,15]; MCP, skills, plugins, assets, fonts "
                        "and render keys are human-only")
    p.add_argument("--title")
    p.add_argument("--subject")
    p.add_argument("--topic")
    p.add_argument("--pillar")
    p.add_argument("--notes", help="extra direction for this batch")
    p.add_argument("--effort", choices=EFFORTS, help="the maker's effort (agent.effort); unset: the harness default")
    p.add_argument("--review-effort", choices=EFFORTS, help="the reviewer's effort (review.effort)")
    p.add_argument("--pacing", help="pacing for this batch, given to the maker as written (video.pacing)")
    p.add_argument("--motion", help="the motion signature, e.g. 'per-word ink and blur-up'; wins over the doctrine")
    p.add_argument("--aspect", choices=list(FORMATS), help="frame shape for this batch (video.width/height); "
                   "9:16 keeps the preset's safe zone, the others use 5%% title-safe")
    p.add_argument("--fps", type=int, choices=[24, 25, 30, 50, 60], help="frame rate (video.fps)")
    p.add_argument("--duration", metavar="S|MIN-MAX", help="length in seconds, e.g. 15 or 10-18 (video.duration)")
    p.add_argument("--sound", choices=SOUNDS, help="what the soundtrack carries (video.sound)")
    p.add_argument("--rounds", type=int, choices=range(1, 6), metavar="1-5", help="draft-look-fix rounds (agent.rounds)")
    p.add_argument("--revise", type=int, metavar="ID", help="make a new version of a video marked for revision")
    p.add_argument("--no-sandbox", action="store_true", help="run without bubblewrap (human only)")
    p.add_argument("--review", dest="review", action="store_true", default=None, help="force the independent reviewer")
    p.add_argument("--no-review", dest="review", action="store_false", help="skip the independent reviewer")

    p = cmd("library", cmd_library, "browse the library, or move it with `library dir <folder>` (inside the repo)")
    p.add_argument("action", choices=["list", "show", "path", "open", "dir"])
    p.add_argument("target", nargs="?", help="a video id; for `dir`, the new folder")
    p.add_argument("--status", action="append")
    p.add_argument("--all", action="store_true", help="include scheduled and posted (human only)")
    p.add_argument("--limit", type=int, default=25)

    p = cmd("review", cmd_review, "human review: walk the queue, or approve / reject / revise by id; "
            "rescore ID re-runs the independent reviewer to measure its noise")
    p.add_argument("action", nargs="?", choices=["walk", "list", "approve", "reject", "revise", "rescore"],
                   default="walk")
    p.add_argument("ids", nargs="*", type=int)
    p.add_argument("--notes")
    p.add_argument("--times", type=int, default=2, help="rescore: reviewer runs on the same video (default 2)")
    p.add_argument("--effort", choices=EFFORTS, help="rescore: the reviewer's effort (review.effort)")

    p = cmd("agent", cmd_agent, "the agent surface (read-only): status, unassigned videos, topics, calendar")
    p.add_argument("action", choices=["status", "videos", "topics", "calendar"])
    p.add_argument("--limit", type=int, default=50)

    p = cmd("post", cmd_post, "post approved videos through Buffer: with no action, pick one, its channels and a "
            "time at a terminal; schedule does the same from flags; list and cancel follow them; "
            "sync records what Buffer did (the timer runs it)")
    p.add_argument("action", nargs="?", choices=["pick", "schedule", "list", "sync", "cancel"], default="pick")
    p.add_argument("target", nargs="?", type=int, help="schedule: a video id; cancel: a post id")
    p.add_argument("--at", metavar="'YYYY-MM-DD HH:MM'|now", help="schedule: local time, or now")
    p.add_argument("-c", "--channel", action="append",
                   help="schedule: instagram, facebook, x, or a Buffer channel id (repeatable; default all)")
    p.add_argument("--yes", action="store_true", help="schedule: skip the confirmation question")
    p.add_argument("--dry-run", action="store_true", help="show what would happen; upload and schedule nothing")
    p.add_argument("--past", action="store_true", help="list: include posts older than a day")
    p.add_argument("--limit", type=int, default=50)

    p = cmd("channel", cmd_channel, "connect and test the accounts posting uses: buffer (posts) and media (video hosting)")
    p.add_argument("action", choices=["list", "connect", "test", "disconnect"])
    p.add_argument("platform", nargs="?", metavar="account", help="buffer or media")

    p = cmd("timer", cmd_timer, "systemd user timer that runs `post sync`")
    p.add_argument("action", choices=["install", "remove", "status"])
    p.add_argument("--every", type=int, default=10, help="minutes (default 10)")

    p = cmd("completion", cmd_completion, "print shell completion: eval \"$(social-studio completion bash)\"")
    p.add_argument("shell", choices=["bash", "zsh"])

    p = cmd("skill", cmd_skill, "install the agent skill into a harness (claude, opencode, codex, or a folder)")
    p.add_argument("action", choices=["install", "show"])
    p.add_argument("--target", default="claude")
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    a = ap.parse_args(argv)
    ctx = make_ctx(a.project, a.json)
    try:
        return a.fn(ctx, a) or 0
    except StudioError as e:
        if ctx.json:
            print(json.dumps({"error": {"code": e.code, "message": str(e), "hint": e.hint}}))
        else:
            log(f"error: {e}" + (f"\nhint: {e.hint}" if e.hint else ""))
        return e.exit_code
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
