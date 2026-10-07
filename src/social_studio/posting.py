"""Approved posts out through Buffer.

The operator picks the post, the channels and the time at a terminal. Code then checks the signed
approval (file and post text), uploads the file to public storage, creates one Buffer post per channel
and records each one. Buffer publishes at that time; `post sync` (also run by every `post run`) reads
back what happened. No agent-facing command reaches any of this.
"""
from __future__ import annotations

import sqlite3
import textwrap
from datetime import timedelta

from . import approval, db, platforms
from .core import ConfigError, Ctx, DataError, Denied, StudioError, UsageError, iso, now_utc, parse_iso, require_human
from .platforms import buffer, media
from .publish import _preset_publish, _settle_post, post_lock
from .schedule import local_str, parse_when

SCHEDULABLE = ("approved", "failed")  # failed: Buffer or the network refused it; the operator may try again
MIN_LEAD = timedelta(minutes=2)


def approved_posts(ctx: Ctx) -> list[dict]:
    """Approved videos not on a live post, newest approval first."""
    con = db.connect(ctx)
    try:
        return db.rows(con.execute(
            "SELECT v.*, a.approved_at FROM videos v JOIN approvals a ON a.video_id = v.id "
            "WHERE v.status IN ('approved', 'failed') AND v.id NOT IN "
            "(SELECT video_id FROM posts WHERE video_id IS NOT NULL AND status <> 'failed') "
            "ORDER BY a.approved_at DESC, v.id DESC"))
    finally:
        con.close()


def select_channels(ctx: Ctx, found: list[dict], keys: list[str] | None) -> list[dict]:
    """Match numbers (1-based, as listed), platform names (instagram, facebook, x), or Buffer channel ids."""
    keys = [k.strip().lower() for k in (keys or ctx.cfg("publish.buffer.channels", []) or []) if k.strip()]
    if not keys or keys == ["all"]:
        return found
    out = []
    for k in keys:
        hits = ([found[int(k) - 1]] if k.isdigit() and 0 < int(k) <= len(found) else
                [c for c in found if k in (c["id"].lower(), c["platform"], c["service"], c["name"].lower())])
        if not hits:
            raise UsageError(f"no Buffer channel matches {k!r}",
                             "use instagram, facebook or x, a number from the list, or a channel id")
        out += [c for c in hits if c not in out]
    return out


def _when(ctx: Ctx, when: str) -> str | None:
    """'now' -> None (Buffer shares at once); 'YYYY-MM-DD HH:MM' local -> UTC ISO, at least 2 minutes out."""
    when = (when or "").strip()
    if when.lower() == "now":
        return None
    parts = when.split()
    if len(parts) != 2:
        raise UsageError(f"bad time {when!r}", "use 'YYYY-MM-DD HH:MM' (local time) or now")
    at = parse_when(ctx, *parts)
    if at < now_utc() + MIN_LEAD:
        raise UsageError(f"{local_str(ctx, iso(at))} is less than 2 minutes away", "pick a later time, or now")
    return iso(at)


def plan(ctx: Ctx, video_id: int, channel_keys: list[str] | None, when: str) -> dict:
    """Everything a schedule would send, checked, with no side effects (it reads Buffer's channel list)."""
    require_human("scheduling a post")
    con = db.connect(ctx)
    try:
        video = db.get_video(con, video_id)
        if video["status"] not in SCHEDULABLE:
            raise DataError(f"video {video_id} is {video['status']}; only approved videos can be scheduled",
                            "approve it first with `social-studio review`")
        live = con.execute("SELECT id FROM posts WHERE video_id = ? AND status <> 'failed'", (video_id,)).fetchone()
        if live:
            raise DataError(f"video {video_id} is already on post {live[0]}", "see `social-studio post list`")
        problem = approval.check_video(ctx, con, video, post=True)
        if problem:
            raise Denied(f"video {video_id} is not cleared to post: {problem}")
    finally:
        con.close()
    due = _when(ctx, when)
    chans = select_channels(ctx, buffer.channels(ctx), channel_keys)
    if not chans:
        raise ConfigError("no Instagram, Facebook or X channel is connected in Buffer", "connect them at buffer.com")
    pub = _preset_publish(ctx, video["preset"])
    targets = []
    for c in chans:
        text = platforms.caption_for(c["platform"], video, pub)
        targets.append({"channel": c, "text": text, "length": buffer.text_length(c["platform"], text),
                        "limit": buffer.limit(ctx, c["platform"])})
    over = [f"{t['channel']['label']} {t['length']}/{t['limit']}" for t in targets if t["length"] > t["limit"]]
    if over:
        raise DataError(f"post text too long for {', '.join(over)}",
                        "shorten that caption in video.json and approve again, or drop the channel with -c")
    return {"video": video, "due": due, "local": local_str(ctx, due) if due else "now", "targets": targets}


def describe(p: dict) -> str:
    v = p["video"]
    lines = [f"#{v['id']}  {v['title']}  ({v['duration']:.0f}s, {v['width']}x{v['height']})  ->  {p['local']}"]
    for t in p["targets"]:
        lines.append(f"\n  {t['channel']['label']}  ({t['length']}/{t['limit']})")
        lines.append(textwrap.indent(t["text"], "    "))
    return "\n".join(lines)


def execute(ctx: Ctx, p: dict) -> dict:
    """Upload, record, create one Buffer post per channel. Nothing reached Buffer -> the post is undone."""
    require_human("scheduling a post")
    v = p["video"]
    with post_lock(ctx, wait=True):
        con = db.connect(ctx, actor="human")
        try:  # the confirmation prompt took time: the video must still be exactly what was planned and approved
            now = db.get_video(con, v["id"])
            same = (now["status"], now["sha256"], approval.post_hash(now)) == (v["status"], v["sha256"],
                                                                               approval.post_hash(v))
            if not same:
                raise DataError(f"video {v['id']} changed while you were confirming; run `social-studio post` again")
            problem = approval.check_video(ctx, con, now, post=True)
            if problem:
                raise Denied(f"video {v['id']} is not cleared to post: {problem}")
        finally:
            con.close()
        url = media.ensure_hosted(ctx, v)
        con = db.connect(ctx, actor="human")
        try:
            at = p["due"] or iso()
            with db.tx(con):
                con.execute("UPDATE posts SET video_id = NULL WHERE video_id = ? AND status = 'failed'", (v["id"],))
                pid = con.execute("INSERT INTO posts (at, video_id, status, created_by, created_at) "
                                  "VALUES (?, ?, 'scheduled', 'human', ?)", (at, v["id"], iso())).lastrowid
                rows = []
                for t in p["targets"]:
                    try:
                        tid = con.execute(
                            "INSERT INTO post_targets (post_id, platform, at, via, channel_id, text) "
                            "VALUES (?, ?, ?, 'buffer', ?, ?)",
                            (pid, t["channel"]["platform"], at, t["channel"]["id"], t["text"])).lastrowid
                    except sqlite3.IntegrityError as e:
                        raise DataError(f"{t['channel']['platform']} already has a post at {p['local']}",
                                        "pick another minute") from e
                    rows.append((tid, t))
                db.set_status(con, v["id"], "scheduled", f"Buffer post {pid}")
            out = []
            for tid, t in rows:
                entry = {"platform": t["channel"]["platform"], "channel": t["channel"]["label"]}
                try:
                    created = buffer.create_post(ctx, buffer.post_input(
                        t["channel"], t["text"], url, v, p["due"], bool(ctx.cfg("publish.buffer.ai_label", False))))
                    con.execute("UPDATE post_targets SET platform_post_id = ?, attempts = 1 WHERE id = ?",
                                (created["id"], tid))
                    entry.update(status="scheduled", buffer_id=created["id"], due=created.get("dueAt"))
                except (StudioError, OSError) as e:
                    msg = str(e) if isinstance(e, StudioError) else (
                        f"{e}; the request may have reached Buffer, so check its queue before trying again")
                    con.execute("UPDATE post_targets SET status = 'failed', attempts = 1, error = ? WHERE id = ?",
                                (msg[:1000], tid))
                    entry.update(status="failed", error=msg)
                out.append(entry)
            if not any(e["status"] == "scheduled" for e in out):
                with db.tx(con):
                    con.execute("UPDATE posts SET status = 'cancelled', video_id = NULL WHERE id = ?", (pid,))
                    db.set_status(con, v["id"], "approved" if v["status"] == "approved" else "failed",
                                  f"Buffer post {pid} refused")
        finally:
            con.close()
    return {"post_id": pid, "video_id": v["id"], "local": p["local"], "media_url": url, "targets": out}


def pick(ctx: Ctx, dry_run: bool = False) -> dict | None:
    """The terminal flow: approved post -> channels -> time -> confirm."""
    require_human("scheduling a post")
    vids = approved_posts(ctx)
    if not vids:
        print("No approved post is waiting. Approve some with `social-studio review`.")
        return None
    for i, v in enumerate(vids, 1):
        again = "  (failed before)" if v["status"] == "failed" else ""
        print(f"  [{i}] #{v['id']}  {v['title']}  ({v['duration']:.0f}s, {v['width']}x{v['height']})  "
              f"approved {v['approved_at'][:10]}{again}")
    n = input("post number: ").strip()
    if not n.isdigit() or not 0 < int(n) <= len(vids):
        raise UsageError(f"no post {n!r} in the list")
    video = vids[int(n) - 1]
    found = buffer.channels(ctx)
    for i, c in enumerate(found, 1):
        print(f"  [{i}] {c['label']}" + ("  (queue paused in Buffer)" if c["isQueuePaused"] else ""))
    keys = input("channels, comma-separated numbers or names [all]: ").replace(",", " ").split()
    when = input("when: 'YYYY-MM-DD HH:MM' local time, or now: ").strip()
    p = plan(ctx, video["id"], keys, when)
    print("\n" + describe(p) + "\n")
    if dry_run:
        return {"dry_run": True, "video_id": video["id"], "local": p["local"]}
    if input("schedule it? [y/N] ").strip().lower() != "y":
        print("nothing scheduled")
        return None
    return execute(ctx, p)


def _apply(con, t: dict, remote: dict | None, entry: dict) -> None:
    """Record what Buffer says about one target. `remote` was read before the write transaction opened."""
    if not t["platform_post_id"]:
        con.execute("UPDATE post_targets SET status = 'failed', error = ? WHERE id = ?",
                    ("createPost never returned an id; check Buffer's queue for this post before trying again",
                     t["id"]))
        entry.update(status="failed", error="no Buffer id recorded")
    elif remote is None:
        con.execute("UPDATE post_targets SET status = 'failed', error = 'deleted in Buffer' WHERE id = ?", (t["id"],))
        entry.update(status="failed", error="deleted in Buffer")
    elif remote["status"] == "sent":
        sent = iso(parse_iso(remote["sentAt"])) if remote.get("sentAt") else iso()
        con.execute("UPDATE post_targets SET status = 'posted', url = ?, posted_at = ?, error = NULL WHERE id = ?",
                    (remote.get("externalLink"), sent, t["id"]))
        entry.update(status="posted", url=remote.get("externalLink"))
    elif remote["status"] == "error":
        msg = (remote.get("error") or {}).get("message") or "Buffer reported an error"
        con.execute("UPDATE post_targets SET status = 'failed', error = ? WHERE id = ?", (msg[:1000], t["id"]))
        entry.update(status="failed", error=msg)
    else:
        entry.update(status=remote["status"])


def sync(ctx: Ctx, locked: bool = False) -> list[dict]:
    """Read back every due Buffer target; settle posts whose targets all finished. Reads only."""
    con = db.connect(ctx, actor="post")
    out: list[dict] = []
    try:
        with post_lock(ctx, wait=False, held=locked):  # taken first: a schedule in flight has targets without ids yet
            due = db.rows(con.execute(
                "SELECT t.* FROM post_targets t JOIN posts p ON p.id = t.post_id WHERE t.via = 'buffer' "
                "AND t.status = 'pending' AND p.status IN ('scheduled', 'posting', 'partial') AND t.at <= ? "
                "ORDER BY t.at, t.id", (iso(),)))
            for t in due:
                entry = {"post_id": t["post_id"], "target_id": t["id"], "platform": t["platform"]}
                try:
                    remote = buffer.get_post(ctx, t["platform_post_id"]) if t["platform_post_id"] else None
                    with db.tx(con):
                        _apply(con, t, remote, entry)
                        _settle_post(con, t["post_id"])
                except (StudioError, OSError) as e:
                    entry.update(status="error", error=str(e)[:300])
                out.append(entry)
        return out
    finally:
        con.close()


def cancel(ctx: Ctx, post_id: int) -> dict:
    require_human("cancelling a post")
    with post_lock(ctx, wait=True):
        con = db.connect(ctx, actor="human")
        try:
            post = con.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
            if post is None:
                raise DataError(f"no post {post_id}")
            targets = db.rows(con.execute("SELECT * FROM post_targets WHERE post_id = ?", (post_id,)))
            if not any(t["via"] == "buffer" for t in targets):
                raise UsageError(f"post {post_id} does not go through Buffer", "use `social-studio schedule cancel`")
            if post["status"] not in ("scheduled", "partial") or any(t["status"] == "posted" for t in targets):
                raise DataError(f"post {post_id} is {post['status']}; a post that went out cannot be cancelled here")
            for t in targets:
                if t["status"] == "pending" and t["platform_post_id"]:
                    buffer.delete_post(ctx, t["platform_post_id"])
                with db.tx(con):
                    con.execute("UPDATE post_targets SET status = 'cancelled' WHERE id = ? AND status = 'pending'",
                                (t["id"],))
            with db.tx(con):
                con.execute("UPDATE posts SET status = 'cancelled', video_id = NULL WHERE id = ?", (post_id,))
                if post["video_id"]:
                    db.set_status(con, post["video_id"], "approved", f"Buffer post {post_id} cancelled")
        finally:
            con.close()
    return {"post_id": post_id, "status": "cancelled"}


def listing(ctx: Ctx, include_past: bool = False, limit: int = 50) -> list[dict]:
    require_human("seeing which video goes out when")
    con = db.connect(ctx)
    try:
        cond = "" if include_past else "AND p.at >= ?"
        args: tuple = () if include_past else (iso(now_utc() - timedelta(days=1)),)
        rows = db.rows(con.execute(
            f"SELECT p.id AS post_id, p.at, p.status, p.video_id, v.title, "
            f"(SELECT group_concat(t.platform || ':' || t.status, ', ') FROM post_targets t WHERE t.post_id = p.id) "
            f"AS targets, (SELECT group_concat(t.url, ' ') FROM post_targets t WHERE t.post_id = p.id) AS urls "
            f"FROM posts p LEFT JOIN videos v ON v.id = p.video_id "
            f"WHERE EXISTS (SELECT 1 FROM post_targets t WHERE t.post_id = p.id AND t.via = 'buffer') {cond} "
            f"ORDER BY p.at DESC LIMIT ?", (*args, limit)))
        for r in rows:
            r["local"] = local_str(ctx, r["at"])
        return rows
    finally:
        con.close()
