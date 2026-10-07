"""The posting calendar. People and agents choose WHEN; the code alone chooses WHICH video.

`add` creates a post slot (date, time, platforms) and immediately fills it with the oldest
approved video whose approval signature verifies. A slot with no approved video waits open and is
filled when the next video is approved. Once filled, the video leaves every agent-facing view.
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from . import approval, db
from .core import Ctx, DataError, UsageError, iso, now_utc, parse_iso

PLATFORMS = ("instagram", "facebook", "youtube", "x", "bluesky", "linkedin", "tiktok")


def tz(ctx: Ctx):
    name = ctx.cfg("timezone") or os.environ.get("TZ")
    if name:
        try:
            return ZoneInfo(name)
        except Exception as e:
            raise UsageError(f"unknown timezone {name!r}", "use an IANA name such as America/New_York") from e
    return datetime.now().astimezone().tzinfo


def parse_when(ctx: Ctx, date: str, time: str) -> datetime:
    try:
        local = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError as e:
        raise UsageError(f"bad date/time {date} {time}", "use YYYY-MM-DD and HH:MM (24h), local time") from e
    return local.replace(tzinfo=tz(ctx)).astimezone(timezone.utc)


def parse_every(text: str) -> timedelta:
    m = re.fullmatch(r"(\d+)\s*([mhdw])", text.strip())
    if not m:
        raise UsageError(f"bad interval {text!r}", "use forms like 90m, 6h, 2d, 1w")
    n, unit = int(m.group(1)), m.group(2)
    return {"m": timedelta(minutes=n), "h": timedelta(hours=n), "d": timedelta(days=n), "w": timedelta(weeks=n)}[unit]


def local_str(ctx: Ctx, at: str) -> str:
    return parse_iso(at).astimezone(tz(ctx)).strftime("%Y-%m-%d %H:%M %Z")


def fill(ctx: Ctx, con, post_id: int) -> bool:
    """Assign the oldest cleared video to an open slot. Caller holds the write transaction."""
    candidates = db.rows(con.execute(
        "SELECT v.* FROM videos v JOIN approvals a ON a.video_id = v.id "
        "WHERE v.status = 'approved' AND v.id NOT IN (SELECT video_id FROM posts WHERE video_id IS NOT NULL) "
        "ORDER BY a.approved_at, v.id"))
    for v in candidates:
        if approval.check_video(ctx, con, v) is None:
            con.execute("UPDATE posts SET video_id = ?, status = 'scheduled' WHERE id = ? AND status = 'open'",
                        (v["id"], post_id))
            db.set_status(con, v["id"], "scheduled", f"assigned to post {post_id}")
            return True
    return False


def fill_open(ctx: Ctx, actor: str = "cli") -> int:
    con = db.connect(ctx, actor=actor)
    filled = 0
    try:
        with db.tx(con):
            for row in db.rows(con.execute("SELECT id FROM posts WHERE status = 'open' AND at > ? ORDER BY at",
                                           (iso(),))):
                if not fill(ctx, con, row["id"]):
                    break
                filled += 1
    finally:
        con.close()
    return filled


class _Rollback(Exception):
    """Raised inside the transaction to undo a dry run."""


def add(ctx: Ctx, date: str, time: str, platforms: list[str], every: str | None = None, count: int = 1,
        actor: str = "cli", dry_run: bool = False) -> list[dict]:
    platforms = [p.lower() for p in (platforms or ctx.cfg("publish.default_platforms", []))]
    if not platforms:
        raise UsageError("no platform given", "pass --platform, or set publish.default_platforms in config.toml")
    bad = [p for p in platforms if p not in PLATFORMS]
    if bad:
        raise UsageError(f"unknown platform(s): {', '.join(bad)}", f"use: {', '.join(PLATFORMS)}")
    if count < 1 or count > 100:
        raise UsageError("--count must be 1 to 100")
    step = parse_every(every) if every else None
    if count > 1 and step is None:
        raise UsageError("--count needs --every")
    first = parse_when(ctx, date, time)
    out = []
    con = db.connect(ctx, actor=actor)
    try:
        with db.tx(con):
            for i in range(count):
                at = first + (step * i if step else timedelta(0))
                if at <= now_utc():
                    raise UsageError(f"{local_str(ctx, iso(at))} is in the past")
                stamp = iso(at)
                clash = con.execute(
                    f"SELECT platform FROM post_targets WHERE at = ? AND status IN ('pending', 'posted', 'draft') "
                    f"AND platform IN ({','.join('?' * len(platforms))})", (stamp, *platforms)).fetchone()
                if clash:
                    raise DataError(f"{clash['platform']} already has a post at {local_str(ctx, stamp)}",
                                    "pick another time, or cancel that post first")
                pid = con.execute("INSERT INTO posts (at, created_by, created_at) VALUES (?, ?, ?)",
                                  (stamp, actor, iso())).lastrowid
                for pl in platforms:
                    con.execute("INSERT INTO post_targets (post_id, platform, at) VALUES (?, ?, ?)", (pid, pl, stamp))
                filled = fill(ctx, con, pid)
                out.append({"post_id": pid, "at": stamp, "local": local_str(ctx, stamp),
                            "platforms": platforms, "filled": filled})
            if dry_run:
                raise _Rollback
    except _Rollback:
        for r in out:
            r["dry_run"] = True
    finally:
        con.close()
    return out


def cancel(ctx: Ctx, post_id: int, actor: str = "cli") -> dict:
    con = db.connect(ctx, actor=actor)
    try:
        with db.tx(con):
            post = con.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
            if post is None:
                raise DataError(f"no post {post_id}")
            if post["status"] not in ("open", "scheduled"):
                raise DataError(f"post {post_id} is {post['status']}; only open or scheduled posts can be cancelled")
            con.execute("UPDATE post_targets SET status = 'cancelled' WHERE post_id = ? AND status = 'pending'", (post_id,))
            con.execute("UPDATE posts SET status = 'cancelled', video_id = NULL WHERE id = ?", (post_id,))
            if post["video_id"]:
                db.set_status(con, post["video_id"], "approved", f"post {post_id} cancelled")
    finally:
        con.close()
    return {"post_id": post_id, "status": "cancelled"}


def listing(ctx: Ctx, reveal: bool, include_past: bool = False, limit: int = 50) -> list[dict]:
    con = db.connect(ctx)
    try:
        cond = "" if include_past else "WHERE p.at >= ?"
        args: tuple = () if include_past else (iso(now_utc() - timedelta(days=1)),)
        if reveal:
            q = (f"SELECT p.id AS post_id, p.at, p.status, p.video_id, v.title, "
                 f"(SELECT group_concat(t.platform || ':' || t.status, ', ') FROM post_targets t WHERE t.post_id = p.id) AS targets "
                 f"FROM posts p LEFT JOIN videos v ON v.id = p.video_id {cond} "
                 f"ORDER BY p.at LIMIT ?")
        else:
            q = (f"SELECT id AS post_id, at, status, filled, platforms FROM agent_calendar p {cond} ORDER BY at LIMIT ?")
        out = db.rows(con.execute(q, (*args, limit)))
        for r in out:
            r["local"] = local_str(ctx, r["at"])
        return out
    finally:
        con.close()
