"""Keyframe boards (F15, J7; rule R6, ruling 7, option B2): an opt-in stop between the story and the motion.

`build --boards` runs the story stage as usual (pitch round, storyteller, retrieval), then the designer in boards
mode: it lays out each shot's key pose as static HTML at the final layout, with the real fonts and tokens and no
animation (data/board_prompt.md, the key-poses skill). Code snapshots every pose inside the jail with HyperFrames' own
`snapshot`, tiles them into one sheet no wider or taller than 2000 px with a label per tile and, at 9:16, the safe
zone, files a board row (never a video) with its files under the library, and stops. A human decides the board at a
terminal (`board approve|revise|drop`); `build --from-board ID` then animates an approved board in a new designer
session, and `build --boards --from-board ID` lays out again a board sent back for revision. A build without
--boards never stops (memory M42).
"""
from __future__ import annotations

import html
import json
import shutil
import sqlite3
import subprocess
from pathlib import Path

from . import db, engine, story
from .core import PKG_DIR, Ctx, DataError, Preset, UsageError, emit, iso, log, new_id, require_human, slugify
from .runner import (BOARD_SKILL, SESSION_LOGS, STORY_FILES, STORY_STEP, Backend, MakeOpts, Session, _brief_block,
                     _claude_cost, _fill, _maker_values, _read_json, _session_end, _session_row, backend_command,
                     prepare, remove_within, run_jailed, trim_session)

DONE = "board.json"                     # the board designer's last file: the board's title and a note
BRIEF_FILE = "designer-brief.md"        # the story's designer brief, kept so the board can be animated later
SHEET, POSES = "sheet.png", "poses"
KEPT = ("brief.json", "story.json", "techniques.json", "story-references.json", "pitches.json",
        "pitch-verdict.json", DONE, BRIEF_FILE)
MAX_SHOTS = 16
SHEET_MAX, MARGIN, GAP = 2000, 24, 16  # px: the sheet's limit on both sides, its margin, the gap between tiles
MIN_FONT, MAX_FONT = 15, 28            # px: the labels' type, from many small tiles to a few large ones
SNAPSHOT_TIMEOUT_S = 300
GSAP = "gsap/dist/gsap.min.js"
IN_PLAY = ("review", "approved", "revision")
FORMAT_KEYS = ("video.width", "video.height", "video.fps", "video.duration", "video.sound", "video.safe_zone")
# board ACTION -> (the status it sets, how require_human names it)
DECISIONS = {"approve": ("approved", "approving boards"), "revise": ("revision", "sending boards back"),
             "drop": ("dropped", "dropping boards")}


# --- checks and the sheet ----------------------------------------------------------------------------------

def _number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def check_shots(raw: dict, p: Preset) -> list[dict]:
    """brief.json's shots checked before code snapshots them: 1 to 16 in order with no overlap, each with a technique
    and its text as lines, together inside the film's runtime. Every problem is listed; any fails the board."""
    problems = []
    shots = raw.get("shots") if isinstance(raw.get("shots"), list) else []
    if not 1 <= len(shots) <= MAX_SHOTS:
        problems.append(f"brief.json must list 1 to {MAX_SHOTS} shots, not {len(shots)}")
    last = 0.0
    for i, sh in enumerate(shots, 1):
        if not isinstance(sh, dict) or not (_number(sh.get("start")) and _number(sh.get("end"))
                                            and 0 <= sh["start"] < sh["end"]):
            problems.append(f"shot {i} needs a start before its end, in seconds")
            continue
        if sh["start"] < last - 0.01:
            problems.append(f"shot {i} starts at {sh['start']:g} s, before the shot before it ends")
        last = max(last, float(sh["end"]))
        if not str(sh.get("technique") or "").strip():
            problems.append(f"shot {i} has no technique")
        text = sh.get("text", [])
        if not isinstance(text, list) or not all(isinstance(x, str) for x in text):
            problems.append(f"shot {i} text must be a list of lines")
    lo, hi = (float(x) for x in p.get("video.duration"))
    if shots and not lo - 0.5 <= last <= hi + 0.5:
        problems.append(f"the shots run {last:g} s; the film runs {lo:g} to {hi:g} s")
    if problems:
        raise DataError("brief.json failed the board's check: " + "; ".join(problems), "see the designer's log")
    return shots


def pose_times(shots: list[dict]) -> list[float]:
    """Each shot's key pose is static across its shot, so its midpoint shows it clear of any cut."""
    return [round((float(sh["start"]) + float(sh["end"])) / 2, 3) for sh in shots]


def labels(shots: list[dict], told: dict | None) -> list[dict]:
    """Each tile's label: the shot, the story beat its start falls in, its time, its technique, its on-screen text."""
    beats = told.get("beats", []) if isinstance(told, dict) else []
    spans = list(zip(story._span(beats), beats)) if beats else []
    out = []
    for i, sh in enumerate(shots, 1):
        beat = next((f"beat {n} {b.get('role', '')}".strip() for n, ((a, z), b) in enumerate(spans, 1)
                     if a - 0.01 <= float(sh["start"]) < z), "")
        out.append({"shot": f"Shot {i}", "beat": beat, "time": f"{float(sh['start']):g}-{float(sh['end']):g} s",
                    "technique": str(sh.get("technique", "")), "text": " / ".join(sh.get("text") or [])})
    return out


def _grid(n: int, w: int, h: int, font: int) -> dict:
    """The grid that shows `n` poses of w x h largest inside SHEET_MAX on both sides, with a header band and, under
    every tile, a label band of three lines in `font` px."""
    line = round(font * 1.35)
    label, header = 10 + 3 * line, round(font * 2) + line + 12
    best = None
    for cols in range(1, n + 1):
        rows = -(-n // cols)
        scale = min((SHEET_MAX - 2 * MARGIN - (cols - 1) * GAP) / (cols * w),
                    (SHEET_MAX - 2 * MARGIN - header - (rows - 1) * GAP - rows * label) / (rows * h))
        if best is None or scale > best[0]:
            best = (scale, cols, rows)
    scale, cols, rows = best
    tw, th = int(w * scale), int(h * scale)
    return {"cols": cols, "rows": rows, "tile_w": tw, "tile_h": th, "font": font, "line": line, "label": label,
            "header": header, "width": 2 * MARGIN + cols * tw + (cols - 1) * GAP,
            "height": 2 * MARGIN + header + rows * (th + label) + (rows - 1) * GAP}


def sheet_layout(n: int, w: int, h: int) -> dict:
    """The sheet's grid. The labels grow with the tiles so they stay readable once the sheet is scaled to a screen,
    and take room from the tiles as they grow: two passes settle it."""
    lay = _grid(n, w, h, MIN_FONT)
    return _grid(n, w, h, max(MIN_FONT, min(MAX_FONT, lay["tile_w"] // 30)))


def _safe_box(safe: dict | None) -> str:
    if not safe:
        return ""
    inset = " ".join(f"{100 * float(safe.get(k, d)):g}%" for k, d in
                     (("top", 0.12), ("right", 0.10), ("bottom", 0.25), ("left", 0.06)))
    return f'<div class="safe" style="inset:{inset}"></div>'


def sheet_html(title: str, idea: str, lay: dict, tiles: list[dict], safe: dict | None) -> str:
    """The board sheet as a one-frame HyperFrames composition: every pose under its label, the safe zone drawn over
    each pose when `safe` is given (9:16), the board's title and idea on top."""
    esc = html.escape
    cells = []
    for i, t in enumerate(tiles):
        r, c = divmod(i, lay["cols"])
        x, y = MARGIN + c * (lay["tile_w"] + GAP), MARGIN + lay["header"] + r * (lay["tile_h"] + lay["label"] + GAP)
        first = " · ".join(esc(v) for v in (t["shot"], t["beat"], t["time"]) if v)
        cells.append(f'<div class="tile" style="left:{x}px;top:{y}px;width:{lay["tile_w"]}px">'
                     f'<div class="pose" style="height:{lay["tile_h"]}px"><img src="{POSES}/{i + 1:02d}.png" alt="">'
                     f'{_safe_box(safe)}</div><p class="l1">{first}</p><p class="l2">{esc(t["technique"])}</p>'
                     f'<p class="l3">{esc(t["text"]) or "(no text)"}</p></div>')
    w, h, font, line = lay["width"], lay["height"], lay["font"], lay["line"]
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={w}, height={h}" />
    <script src="vendor/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {w}px; height: {h}px; overflow: hidden; background: #f2f1ed; }}
      #root {{ position: relative; width: 100%; height: 100%; font-family: sans-serif; color: #16161a; }}
      .head {{ position: absolute; left: {MARGIN}px; right: {MARGIN}px; top: {MARGIN}px; }}
      .head h1 {{ font-size: {round(font * 1.5)}px; line-height: {round(font * 2)}px; }}
      .head p, .tile p {{ font-size: {font}px; line-height: {line}px; white-space: nowrap; overflow: hidden;
                         text-overflow: ellipsis; }}
      .head p {{ color: #55555c; }}
      .tile {{ position: absolute; }}
      .pose {{ position: relative; overflow: hidden; background: #ffffff; outline: 1px solid #c9c8c2; }}
      .pose img {{ display: block; width: 100%; height: 100%; }}
      .safe {{ position: absolute; border: 2px dashed rgba(220, 38, 38, 0.9); }}
      .l1 {{ margin-top: 8px; font-weight: 700; }}
      .l2 {{ font-family: monospace; color: #3a3a40; }}
      .l3 {{ color: #55555c; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="1" data-width="{w}" data-height="{h}">
      <div class="head"><h1>{esc(title)}</h1><p>{esc(idea)}</p></div>
      {chr(10).join('      ' + c for c in cells).strip()}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def snapshot(ctx: Ctx, s: Session, project: Path, times: list[float], out: Path, version: str,
             sandbox: bool) -> list[Path]:
    """PNG stills of a HyperFrames project at `times`, one per time and in order, taken by the engine's own
    `snapshot` inside the jail with no network: it runs a page the designer wrote."""
    eng_root, chrome = engine.engine_root(ctx, version), engine.chrome_path(ctx, version)
    node_ro, node_path = engine.node_dirs(ctx)
    home = s.work / "board" / "home"
    home.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(out, ignore_errors=True)
    env = engine.base_env(home, [eng_root / "node_modules" / ".bin", *node_path])
    env["HYPERFRAMES_BROWSER_PATH"] = str(chrome)
    argv = [str(engine.hf_bin(ctx, version)), "snapshot", str(project), "--at", ",".join(f"{t:g}" for t in times),
            "--no-end", "-o", str(out), "--no-browser-gpu"]
    if sandbox:
        prefix = engine.bwrap_argv(s.work, home, rw=[s.work], ro=[eng_root, engine.chrome_root(chrome), *node_ro],
                                   env=env, network=False)
        cmd, run_env = prefix + argv, None
    else:
        cmd, run_env = argv, env
    res = subprocess.run(cmd, capture_output=True, text=True, env=run_env, cwd=s.work, timeout=SNAPSHOT_TIMEOUT_S)
    frames = sorted(out.glob("frame-*-at-*.png"))
    if res.returncode != 0 or len(frames) != len(times):
        raise DataError(f"snapshot gave {len(frames)} of {len(times)} stills: "
                        f"{(res.stdout + res.stderr).strip()[-1200:]}", f"inspect {project}")
    return frames


def make_sheet(ctx: Ctx, p: Preset, s: Session, version: str, sandbox: bool, shots: list[dict],
               told: dict | None, title: str, frames: list[Path]) -> Path:
    """Tile the pose stills into work/board/sheet.png: an HTML sheet the engine's Chrome snapshots once."""
    w, h = int(p.get("video.width")), int(p.get("video.height"))
    root = s.work / "board" / "sheet"
    (root / POSES).mkdir(parents=True, exist_ok=True)
    (root / "vendor").mkdir(exist_ok=True)
    for i, f in enumerate(frames, 1):
        shutil.copy2(f, root / POSES / f"{i:02d}.png")
    shutil.copy2(engine.engine_root(ctx, version) / "node_modules" / GSAP, root / "vendor" / "gsap.min.js")
    safe = p.get("video.safe_zone", {}) if h > w else None  # the platform overlays are a 9:16 thing
    idea = (told or {}).get("idea", "")
    (root / "index.html").write_text(sheet_html(title, idea, sheet_layout(len(frames), w, h), labels(shots, told),
                                                safe))
    (root / "hyperframes.json").write_text(json.dumps({"paths": {"assets": "assets"}, "media": {"autoProxy": False}}))
    shot = snapshot(ctx, s, root, [0], s.work / "board" / "sheet-out", version, sandbox)[0]
    sheet = s.work / "board" / SHEET
    shutil.move(str(shot), str(sheet))
    return sheet


# --- the board session ---------------------------------------------------------------------------------------

ANIMATE = ("- This film animates board {id}, which the operator approved (`board.png` is the sheet they saw). "
           "`composition/index.html` holds its key poses, static, at the final layout. It is binding: keep its "
           "layout, copy, fonts, colours and every element's id. Your job is the motion between the poses, layout "
           "first (it is already there), then motion: animation dresses the poses and never redraws them, and each "
           "shot still reaches its pose.\n- `brief.json` is the board's shot list: keep its shots, their times, text "
           "and techniques. Set the beat grid, the cues and the moves between the poses.\n")
AGAIN = ("- The operator sent board {id} back with these notes: \"{notes}\". `composition/index.html` and `brief.json` "
         "are that board (`board.png` is its sheet). Change what the notes ask for and keep the rest. The result is "
         "still a board: static poses, no animation.\n")


def stage(ctx: Ctx, s: Session, board: dict) -> str:
    """A board's files into a new session: its composition over the scaffold, its story, techniques and shot list,
    its sheet. Returns the TASK.md block saying what they are: an approved board to animate, or one sent back to lay
    out again with the operator's notes."""
    src = ctx.abs(board["dir"])
    shutil.copytree(src / "composition", s.comp, dirs_exist_ok=True)
    for name in ("brief.json", "story.json", "techniques.json", "story-references.json"):
        if (src / name).is_file():
            shutil.copy2(src / name, s.work / name)
    shutil.copy2(src / SHEET, s.work / "board.png")
    if board["status"] == "approved":
        return ANIMATE.format(id=board["id"])
    return AGAIN.format(id=board["id"], notes=board["notes"].strip() or "no notes given")


def designer_brief(ctx: Ctx, board: dict) -> str | None:
    """The story's designer brief the board was laid out from, if it had one."""
    f = ctx.abs(board["dir"]) / BRIEF_FILE
    return f.read_text() if f.is_file() else None


def write_task(p: Preset, s: Session, skills: list[str], pillar: str | None, brief: str | None, block: str) -> None:
    """The board designer's TASK.md (the house rules prepare() wrote stay: the same render contract)."""
    vals = {**_maker_values(p), "skill_list": ", ".join(skills), "revision_block": block, "max_shots": MAX_SHOTS,
            "brief_block": brief if brief is not None else _brief_block(p, pillar, None),
            "story_files": STORY_FILES if brief is not None else "",
            "story_step": STORY_STEP if brief is not None else ""}
    (s.work / "TASK.md").write_text(_fill((PKG_DIR / "data" / "board_prompt.md").read_text(), vals))


def _format(p: Preset) -> dict:
    """The run's frame, so `--from-board` animates at the size the board was laid out in."""
    return {k: p.get(k) for k in FORMAT_KEYS if p.get(k) is not None}


def _file(ctx: Ctx, p: Preset, s: Session, b: Backend, shots: list[dict], told: dict | None, done: dict,
          meta_story: dict | None, parent: dict | None, pillar: str | None) -> tuple[int, Path]:
    """Copy the board's files under the library and file its row; a board it replaces becomes superseded."""
    title = str(done["title"]).strip()
    dest = ctx.library_dir / f"{s.id[:8]}-board-{slugify(title)}-{s.id[-4:]}"
    (dest / POSES).mkdir(parents=True, exist_ok=True)
    shutil.copy2(s.work / "board" / SHEET, dest / SHEET)
    for i, f in enumerate(sorted((s.work / "board" / "sheet" / POSES).glob("*.png")), 1):
        shutil.copy2(f, dest / POSES / f"{i:02d}.png")
    for name in KEPT:
        if (s.work / name).is_file():
            shutil.copy2(s.work / name, dest / name)
    shutil.copytree(s.comp, dest / "composition", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("snapshots", "renders", ".hf*"))
    meta = {"story": meta_story, "format": _format(p), "note": str(done.get("note", "")), "session": s.id,
            "backend": f"{b.name}:{b.model or 'default'}", "preset_hash": p.hash,
            "techniques": [str(sh.get("technique")) for sh in shots]}
    con = db.connect(ctx, actor="make")
    try:
        with db.tx(con):
            bid = con.execute(
                "INSERT INTO boards (session_id, parent_id, title, idea, pillar, preset, dir, sheet, shots, width, "
                "height, meta, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (s.id, parent["id"] if parent else None, title, str((told or {}).get("idea", "")),
                 str((told or {}).get("pillar") or pillar or ""), p.name, ctx.rel(dest), ctx.rel(dest / SHEET), len(shots),
                 int(p.get("video.width")), int(p.get("video.height")), json.dumps(meta), iso(), iso())).lastrowid
            if parent:
                con.execute("UPDATE boards SET status = 'superseded', updated_at = ? WHERE id = ?", (iso(), parent["id"]))
    finally:
        con.close()
    return bid, dest


def purge(ctx: Ctx, board: dict) -> None:
    """A board laid out again replaces the one sent back: its files and session go, its row stays as history."""
    if board.get("dir"):
        remove_within(ctx.abs(board["dir"]), ctx.library_dir)
    if board.get("session_id") and (ctx.sessions_dir / board["session_id"]).exists():
        remove_within(ctx.sessions_dir / board["session_id"], ctx.sessions_dir)
    con = db.connect(ctx, actor="make")
    try:
        con.execute("UPDATE boards SET dir = '', sheet = '' WHERE id = ?", (board["id"],))
    finally:
        con.close()


def run_board(ctx: Ctx, p: Preset, opts: MakeOpts, b: Backend, version: str, pillar: str | None,
              history: list[dict], revise: dict | None, sb: Backend | None = None, board: dict | None = None) -> dict:
    """One board: the story stage (`sb`; none when `board`, a board sent back, is laid out again), the designer in
    boards mode in the same sandbox, the poses snapshotted and tiled, a board row filed. Never a video."""
    sid = new_id()
    s = Session(sid, ctx.sessions_dir / sid)
    _session_row(ctx, s, "make", p, b)
    try:
        skills = prepare(ctx, p, s, version, engine.engine_root(ctx, version), pillar, history, None)
        shutil.copytree(PKG_DIR / "data" / "skills" / BOARD_SKILL, s.work / "skills" / BOARD_SKILL,
                        dirs_exist_ok=True, ignore=shutil.ignore_patterns(".*"))
        skills.append(BOARD_SKILL)
        block = stage(ctx, s, board) if board else ""
        told = story.tell(ctx, p, s, sb, version, history, pillar) if sb else None
        brief = told["brief"] if told else (designer_brief(ctx, board) if board else None)
        if brief is not None:
            (s.work / BRIEF_FILE).write_text(brief)
        write_task(p, s, skills, pillar, brief, block)
        prompt = ("Read TASK.md in the current folder and complete it. Work autonomously; nobody will answer "
                  f"questions. Finish by writing {DONE}.")
        argv, env, ro, rw = backend_command(ctx, p, b, s, prompt, skills)
        log(f"[{s.id}] board: {b.name}{':' + b.model if b.model else ''} laying out the key poses")
        code = run_jailed(ctx, s, argv, env, ro, rw, b.sandbox, version, "agent",
                          int(p.get("agent.timeout_min", 45)) * 60)
        done = _read_json(s.work / DONE, DONE)
        if not str(done.get("title", "")).strip():
            raise DataError(f"{DONE} has no title (agent exit {code})")
        shots = check_shots(_read_json(s.work / "brief.json", "brief.json"), p)
        told_story = json.loads((s.work / "story.json").read_text()) if (s.work / "story.json").is_file() else None
        log(f"[{s.id}] board: snapshotting {len(shots)} key poses")
        frames = snapshot(ctx, s, s.comp, pose_times(shots), s.work / "board" / POSES, version, b.sandbox)
        make_sheet(ctx, p, s, version, b.sandbox, shots, told_story, str(done["title"]).strip(), frames)
        meta_story = told["meta"] if told else (json.loads(board["meta"]).get("story") if board else None)
        bid, dest = _file(ctx, p, s, b, shots, told_story, done, meta_story, board, pillar)
        costs = [c for c in (_claude_cost(s, n) for n in SESSION_LOGS) if c is not None]
        cost = round(sum(costs), 4) if costs else None
        _session_end(ctx, s, "ok", cost=cost)
        try:  # the board exists from here on; cleanup trouble is a warning, never a failed run
            trim_session(s)
            if board:
                purge(ctx, board)
        except Exception as e:
            log(f"[{s.id}] warning: cleanup incomplete: {e}")
        log(f"[{s.id}] board {bid}: {done['title']} ({len(shots)} shots) -> {dest / SHEET}")
        return {"ok": True, "session": s.id, "board_id": bid, "title": str(done["title"]).strip(),
                "shots": len(shots), "sheet": str(dest / SHEET), "cost_usd": cost}
    except Exception as e:  # one failed try must not sink the batch; the session folder keeps the evidence
        _session_end(ctx, s, "failed", f"{type(e).__name__}: {e}"[:2000])
        log(f"[{s.id}] failed: {e}")
        try:
            trim_session(s, keep_composition=True)
        except Exception:
            pass
        return {"ok": False, "session": s.id, "error": str(e)[:2000], "dir": str(s.dir)}


# --- the library side ------------------------------------------------------------------------------------------

def get(con: sqlite3.Connection, bid: int) -> dict:
    r = con.execute("SELECT * FROM boards WHERE id = ?", (bid,)).fetchone()
    if r is None:
        raise DataError(f"no board with id {bid}", "run `sclstdio board`")
    return dict(r)


def for_build(ctx: Ctx, bid: int, again: bool) -> dict:
    """The board a `--from-board` build starts from: approved to animate it, or sent back to lay it out again."""
    con = db.connect(ctx)
    try:
        board = get(con, bid)
    finally:
        con.close()
    want = "revision" if again else "approved"
    if board["status"] != want:
        raise DataError(f"board {bid} is {board['status']}; " + (
            "only a board sent back for revision is laid out again" if again else
            "only an approved board is animated"), "a human decides boards at a terminal: sclstdio board approve|revise ID")
    if not board["dir"] or not (ctx.abs(board["dir"]) / "composition" / "index.html").is_file():
        raise DataError(f"board {bid} has no files left", "see `sclstdio board show ID`")
    return board


def format_of(board: dict) -> dict:
    return json.loads(board["meta"] or "{}").get("format", {})


def preset_of(ctx: Ctx, bid: int) -> str:
    """The preset a board was laid out with: `--from-board` animates with it unless --preset says otherwise."""
    con = db.connect(ctx)
    try:
        return get(con, bid)["preset"]
    finally:
        con.close()


def decide(ctx: Ctx, bid: int, status: str, notes: str) -> dict:
    """approve, revise or drop: a human's decision on a board, on a connection whose actor is `human` (the schema
    refuses any other). It writes no approvals row, so it can never pass for a video approval."""
    con = db.connect(ctx, actor="human")
    try:
        old = get(con, bid)
        with db.tx(con):
            try:
                con.execute("UPDATE boards SET status = ?, notes = ?, updated_at = ? WHERE id = ?",
                            (status, notes or old["notes"], iso(), bid))
            except sqlite3.IntegrityError as e:
                raise DataError(f"board {bid}: {old['status']} -> {status} refused ({e})",
                                "see `sclstdio board show ID`") from e
        return get(con, bid)
    finally:
        con.close()


def _rows(ctx: Ctx, every: bool) -> list[dict]:
    con = db.connect(ctx)
    try:
        where = "" if every else f"WHERE status IN ({','.join('?' * len(IN_PLAY))})"
        rows = db.rows(con.execute(f"SELECT id, status, title, shots, created_at, sheet FROM boards {where} "
                                   "ORDER BY id DESC", () if every else IN_PLAY))
    finally:
        con.close()
    for r in rows:
        r["sheet"] = str(ctx.abs(r["sheet"])) if r["sheet"] else ""
    return rows


def _show(ctx: Ctx, bid: int) -> dict:
    con = db.connect(ctx)
    try:
        board = get(con, bid)
        board["videos"] = db.rows(con.execute(  # what an agent may see of the films made from it
            "SELECT id, status, title FROM videos WHERE board_id = ? AND status IN "
            "('review', 'approved', 'rejected', 'revision') ORDER BY id", (bid,)))
    finally:
        con.close()
    board["meta"] = json.loads(board["meta"] or "{}")
    board["sheet"] = str(ctx.abs(board["sheet"])) if board["sheet"] else ""
    return board


NEXT = {"approved": "animate it: sclstdio build --from-board {id}",
        "revision": "lay it out again: sclstdio build --boards --from-board {id}",
        "dropped": "it stays in the library as history"}


def cmd_board(ctx: Ctx, a) -> int:
    """`board`: bare (or `list`), the boards in play with their sheets; `show ID`; `approve`, `revise --notes` or
    `drop` ID, which only a human at a terminal can do."""
    from .cli import table
    if a.action in DECISIONS:
        status, doing = DECISIONS[a.action]
        require_human(doing)
        if a.id is None:
            raise UsageError(f"board {a.action} needs a board id", "see `sclstdio board`")
        if a.action == "revise" and not a.notes:
            raise UsageError("board revise needs --notes saying what to change")
        res = decide(ctx, a.id, status, a.notes or "")
        emit(ctx, {"board": a.id, "status": res["status"]},
             f"board {a.id} {res['status']}; {NEXT[res['status']].format(id=a.id)}")
        return 0
    if a.action == "show":
        if a.id is None:
            raise UsageError("board show needs a board id", "see `sclstdio board`")
        board = _show(ctx, a.id)
        emit(ctx, board, json.dumps(board, indent=2, default=str))
        return 0
    rows = _rows(ctx, a.all)
    emit(ctx, rows, table(rows, ["id", "status", "title", "shots", "created_at", "sheet"]) if rows else
         "no boards; `sclstdio build --boards` makes one")
    return 0
