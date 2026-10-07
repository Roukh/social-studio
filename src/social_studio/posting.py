"""Posts out through Buffer, the only posting route, approved in one of two places.

In Buffer (the default once Buffer is connected): each finished video goes to Buffer as a draft on every
connected channel. Drafts publish nothing; the operator approves, edits or deletes them in Buffer, and
`post sync` (run by the timer) follows them to their post URL. Rejecting, revising or superseding the
video here takes its drafts back out.

At the terminal: the operator picks a signed-approved post, the channels and the time. Code checks the
signed approval (file and post text), uploads the file to public storage, creates one Buffer post per
channel and records each one; Buffer publishes at that time and `post sync` reads back what happened.

Code calls Buffer, never an agent: no agent-facing command reaches any of this.
"""
from __future__ import annotations

import fcntl
import os
import sqlite3
import textwrap
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from . import approval, db, platforms
from .core import (ConfigError, Ctx, DataError, Denied, StudioError, Unavailable, UsageError, iso, load_preset,
                   now_utc, parse_iso, require_human)
from .platforms import buffer, media

SCHEDULABLE = ("approved", "failed")  # failed: Buffer or the network refused it; the operator may try again
MIN_LEAD = timedelta(minutes=2)
DRAFTS = "drafts"  # posts.created_by for a video sent to Buffer as drafts, to be approved there


# --- time, locking, settling --------------------------------------------------------------------------

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


def local_str(ctx: Ctx, at: str) -> str:
    return parse_iso(at).astimezone(tz(ctx)).strftime("%Y-%m-%d %H:%M %Z")


@contextmanager
def post_lock(ctx: Ctx, wait: bool = False, held: bool = False):
    """One posting process at a time: sync, scheduling and cancelling share post.lock."""
    if held:
        yield
        return
    ctx.studio_dir.mkdir(parents=True, exist_ok=True)
    with open(ctx.studio_dir / "post.lock", "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | (0 if wait else fcntl.LOCK_NB))
        except BlockingIOError:
            raise Unavailable("another posting command is in progress; try again in a minute") from None
        yield


def settle_post(con, post_id: int) -> None:
    """Once no target is pending or a draft: the post becomes posted, partial or failed, and its video follows.

    A drafts post whose drafts were all deleted in Buffer was turned down there: it is cancelled and its
    video rejected. A drafts post moves its video only while that video still waits in review."""
    states = [r[0] for r in con.execute("SELECT status FROM post_targets WHERE post_id = ? AND status <> 'cancelled'",
                                        (post_id,))]
    if "pending" in states or "draft" in states:
        return
    vid, by = con.execute("SELECT video_id, created_by FROM posts WHERE id = ?", (post_id,)).fetchone()
    current = db.get_video(con, vid)["status"] if vid else None
    movable = bool(vid) and (by != DRAFTS or current == "review")
    if not states:
        con.execute("UPDATE posts SET status = 'cancelled', video_id = NULL WHERE id = ?", (post_id,))
        if movable and by == DRAFTS:
            db.set_status(con, vid, "rejected", f"post {post_id}: every draft was deleted in Buffer")
        return
    done = sum(s == "posted" for s in states)
    status = "posted" if done == len(states) else ("partial" if done else "failed")
    con.execute("UPDATE posts SET status = ? WHERE id = ?", (status, post_id))
    if movable:
        db.set_status(con, vid, "posted" if done else "failed", f"post {post_id} {status}")


def preset_publish(ctx: Ctx, name: str) -> dict:
    """The preset's [publish] table (caption link, bio note); empty when the preset is gone."""
    try:
        return load_preset(ctx, name).get("publish", {}) or {}
    except StudioError:
        return {}


# --- the Buffer route ---------------------------------------------------------------------------------


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
    pub = preset_publish(ctx, video["preset"])
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


# --- approval in Buffer: drafts -----------------------------------------------------------------------

def drafts_on(ctx: Ctx) -> bool:
    """Approval happens in Buffer unless publish.buffer.drafts = false; it needs Buffer connected."""
    return bool(ctx.env(buffer.KEY)) and ctx.cfg("publish.buffer.drafts", True) is not False


def drafts_post(con, video_id: int) -> int | None:
    """The video's drafts post while any of it can still change in Buffer."""
    r = con.execute(f"SELECT id FROM posts WHERE video_id = ? AND created_by = '{DRAFTS}' "
                    "AND status IN ('open', 'scheduled', 'partial')", (video_id,)).fetchone()
    return r[0] if r else None


def draft(ctx: Ctx, video_id: int) -> dict:
    """Put a video that waits for review into Buffer as a draft on every connected channel.

    Called by code after a make, or by `post draft`. One channel per network for now: a second account on
    the same network is skipped (several accounts is a later feature). Nothing reached Buffer -> undone."""
    with post_lock(ctx, wait=True):
        con = db.connect(ctx, actor=DRAFTS)
        try:
            v = db.get_video(con, video_id)
            if v["status"] != "review":
                raise DataError(f"video {video_id} is {v['status']}; only a video waiting for review goes to Buffer "
                                "as drafts")
            live = con.execute("SELECT id FROM posts WHERE video_id = ?", (video_id,)).fetchone()
            if live:
                raise DataError(f"video {video_id} is already on post {live[0]}", "see `social-studio post list`")
        finally:
            con.close()
        chans = select_channels(ctx, buffer.channels(ctx), None)
        if not chans:
            raise ConfigError("no Instagram, Facebook or X channel is connected in Buffer", "connect them at buffer.com")
        pub = preset_publish(ctx, v["preset"])
        targets, out, seen = [], [], set()
        for c in chans:
            text = platforms.caption_for(c["platform"], v, pub)
            n, cap = buffer.text_length(c["platform"], text), buffer.limit(ctx, c["platform"])
            why = (f"a second {c['platform']} channel; one per network for now" if c["platform"] in seen else
                   f"post text {n}/{cap} is over the limit" if n > cap else "")
            seen.add(c["platform"])
            if why:
                out.append({"platform": c["platform"], "channel": c["label"], "status": "skipped", "error": why})
            else:
                targets.append({"channel": c, "text": text})
        if not targets:
            raise DataError(f"video {video_id} fits no connected channel: " + "; ".join(e["error"] for e in out))
        url = media.ensure_hosted(ctx, v)
        con = db.connect(ctx, actor=DRAFTS)
        try:
            at = iso()
            with db.tx(con):
                pid = con.execute("INSERT INTO posts (at, video_id, status, created_by, created_at) "
                                  "VALUES (?, ?, 'open', ?, ?)", (at, v["id"], DRAFTS, at)).lastrowid
                rows = [(con.execute("INSERT INTO post_targets (post_id, platform, at, status, via, channel_id, text) "
                                     "VALUES (?, ?, ?, 'draft', 'buffer', ?, ?)",
                                     (pid, t["channel"]["platform"], at, t["channel"]["id"], t["text"])).lastrowid, t)
                        for t in targets]
            for tid, t in rows:
                entry = {"platform": t["channel"]["platform"], "channel": t["channel"]["label"]}
                try:
                    created = buffer.create_post(ctx, buffer.post_input(
                        t["channel"], t["text"], url, v, None, bool(ctx.cfg("publish.buffer.ai_label", False)),
                        draft=True))
                    con.execute("UPDATE post_targets SET platform_post_id = ?, attempts = 1 WHERE id = ?",
                                (created["id"], tid))
                    entry.update(status="draft", buffer_id=created["id"])
                except (StudioError, OSError) as e:
                    msg = str(e) if isinstance(e, StudioError) else (
                        f"{e}; the request may have reached Buffer, so check its drafts before trying again")
                    con.execute("UPDATE post_targets SET status = 'failed', attempts = 1, error = ? WHERE id = ?",
                                (msg[:1000], tid))
                    entry.update(status="failed", error=msg)
                out.append(entry)
            if not any(e["status"] == "draft" for e in out):
                with db.tx(con):
                    con.execute("UPDATE posts SET status = 'cancelled', video_id = NULL WHERE id = ?", (pid,))
        finally:
            con.close()
    return {"post_id": pid, "video_id": v["id"], "media_url": url, "targets": out}


def withdraw(ctx: Ctx, video_id: int, why: str) -> dict | None:
    """Take a video's drafts, and anything approved in Buffer but not yet sent, back out of Buffer.

    Runs before the video is rejected, revised or superseded here. A channel that already posted stays."""
    with post_lock(ctx, wait=True):
        con = db.connect(ctx, actor=DRAFTS)
        try:
            pid = drafts_post(con, video_id)
            if pid is None:
                return None
            targets = db.rows(con.execute("SELECT * FROM post_targets WHERE post_id = ? AND status IN "
                                          "('draft', 'pending')", (pid,)))
            for t in targets:
                remote = buffer.get_post(ctx, t["platform_post_id"]) if t["platform_post_id"] else None
                if remote and remote["status"] == "sent":  # it went out first: keep the record, not the withdrawal
                    with db.tx(con):
                        _apply(con, t, remote, {})
                    continue
                if remote:
                    buffer.delete_post(ctx, t["platform_post_id"])
                with db.tx(con):
                    con.execute("UPDATE post_targets SET status = 'cancelled', error = ? WHERE id = ?", (why, t["id"]))
            with db.tx(con):
                posted = con.execute("SELECT count(*) FROM post_targets WHERE post_id = ? AND status = 'posted'",
                                     (pid,)).fetchone()[0]
                if posted:
                    settle_post(con, pid)
                else:
                    con.execute("UPDATE posts SET status = 'cancelled', video_id = NULL WHERE id = ?", (pid,))
        finally:
            con.close()
    return {"post_id": pid, "video_id": video_id, "posted": posted}


def _apply(con, t: dict, remote: dict | None, entry: dict) -> None:
    """Record what Buffer says about one target. `remote` was read before the write transaction opened."""
    if not t["platform_post_id"]:
        con.execute("UPDATE post_targets SET status = 'failed', error = ? WHERE id = ?",
                    ("createPost never returned an id; check Buffer's queue for this post before trying again",
                     t["id"]))
        entry.update(status="failed", error="no Buffer id recorded")
    elif remote is None and t["status"] == "draft":  # the operator deleted the draft: turned down for that channel
        con.execute("UPDATE post_targets SET status = 'cancelled', error = 'draft deleted in Buffer' WHERE id = ?",
                    (t["id"],))
        entry.update(status="turned down", error="draft deleted in Buffer")
    elif remote is None:
        con.execute("UPDATE post_targets SET status = 'failed', error = 'deleted in Buffer' WHERE id = ?", (t["id"],))
        entry.update(status="failed", error="deleted in Buffer")
    elif remote["status"] in buffer.WAITING:
        entry.update(status="draft")
    elif t["status"] == "draft" and remote["status"] in ("scheduled", "sending"):  # approved in Buffer
        due = parse_iso(remote["dueAt"]) if remote.get("dueAt") else parse_iso(t["at"])
        for shift in range(60):  # a post here already holds that second on that network; Buffer keeps its own time
            try:
                con.execute("UPDATE post_targets SET status = 'pending', at = ? WHERE id = ?",
                            (iso(due + timedelta(seconds=shift)), t["id"]))
                break
            except sqlite3.IntegrityError:
                continue
        else:
            entry.update(status="draft", error="no free second to record its time; the next sync tries again")
            return
        con.execute("UPDATE posts SET status = 'scheduled' WHERE id = ? AND status = 'open'", (t["post_id"],))
        entry.update(status="approved", due=remote.get("dueAt"))
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
    """Read back every due Buffer target and every draft; settle posts whose targets all finished. Reads only."""
    con = db.connect(ctx, actor="post")
    out: list[dict] = []
    try:
        with post_lock(ctx, wait=False, held=locked):  # taken first: a schedule in flight has targets without ids yet
            due = db.rows(con.execute(
                "SELECT t.* FROM post_targets t JOIN posts p ON p.id = t.post_id WHERE t.via = 'buffer' AND ("
                "(t.status = 'pending' AND p.status IN ('scheduled', 'posting', 'partial') AND t.at <= ?) OR "
                "(t.status = 'draft' AND p.status IN ('open', 'scheduled', 'partial'))) "
                "ORDER BY t.at, t.id", (iso(),)))
            for t in due:
                entry = {"post_id": t["post_id"], "target_id": t["id"], "platform": t["platform"]}
                try:
                    remote = buffer.get_post(ctx, t["platform_post_id"]) if t["platform_post_id"] else None
                    with db.tx(con):
                        _apply(con, t, remote, entry)
                        settle_post(con, t["post_id"])
                except (StudioError, OSError) as e:
                    entry.update(status="error", error=str(e)[:300])
                out.append(entry)
        return out
    finally:
        con.close()


def cancel(ctx: Ctx, post_id: int) -> dict:
    require_human("cancelling a post")
    con = db.connect(ctx)
    try:
        post = con.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    finally:
        con.close()
    if post is not None and post["created_by"] == DRAFTS:  # drafts: withdrawn from Buffer, the video waits in review
        if not post["video_id"] or post["status"] not in ("open", "scheduled", "partial"):
            raise DataError(f"post {post_id} is {post['status']}; nothing of it is left to take out of Buffer")
        withdraw(ctx, post["video_id"], "cancelled at the terminal")
        return {"post_id": post_id, "status": "cancelled"}
    with post_lock(ctx, wait=True):
        con = db.connect(ctx, actor="human")
        try:
            post = con.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
            if post is None:
                raise DataError(f"no post {post_id}")
            targets = db.rows(con.execute("SELECT * FROM post_targets WHERE post_id = ?", (post_id,)))
            if not any(t["via"] == "buffer" for t in targets):
                raise UsageError(f"post {post_id} was not made through Buffer", "only Buffer posts can be cancelled")
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
