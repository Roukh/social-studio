"""`post run`: publish every due direct-adapter target whose video carries a valid human approval
signature, then read back the due Buffer posts (Buffer publishes those itself).

Safe to run from a timer every few minutes: a lock stops overlapping runs, a stored platform post
id makes a retry a no-op, failures back off (5 min, 30 min, 2 h) and then stop.
"""
from __future__ import annotations

import fcntl
from contextlib import contextmanager
from datetime import timedelta

from . import approval, db, platforms
from .core import Ctx, StudioError, Unavailable, iso, load_preset, log, now_utc

BACKOFF = (timedelta(minutes=5), timedelta(minutes=30), timedelta(hours=2))


def _preset_publish(ctx: Ctx, name: str) -> dict:
    try:
        return load_preset(ctx, name).get("publish", {}) or {}
    except StudioError:
        return {}


@contextmanager
def post_lock(ctx: Ctx, wait: bool = False, held: bool = False):
    """One posting process at a time: `post run`, `post sync`, scheduling and cancelling share post.lock."""
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


def _settle_post(con, post_id: int) -> None:
    states = [r[0] for r in con.execute("SELECT status FROM post_targets WHERE post_id = ? AND status <> 'cancelled'",
                                        (post_id,))]
    if "pending" in states:
        return
    done = sum(s in ("posted", "draft") for s in states)
    status = "posted" if done == len(states) else ("partial" if done else "failed")
    con.execute("UPDATE posts SET status = ? WHERE id = ?", (status, post_id))
    vid = con.execute("SELECT video_id FROM posts WHERE id = ?", (post_id,)).fetchone()[0]
    if vid:
        db.set_status(con, vid, "posted" if done else "failed", f"post {post_id} {status}")


def run(ctx: Ctx, dry_run: bool = False, only: int | None = None) -> list[dict]:
    with post_lock(ctx):
        results = _run(ctx, dry_run, only)
        if not dry_run and only is None:
            from . import posting
            results += posting.sync(ctx, locked=True)
    return results


def _run(ctx: Ctx, dry_run: bool, only: int | None) -> list[dict]:
    from .schedule import fill_open
    fill_open(ctx, actor="post")
    con = db.connect(ctx, actor="post")
    now = iso()
    results = []
    try:
        with db.tx(con):
            missed = db.rows(con.execute("SELECT id FROM posts WHERE status = 'open' AND at <= ?", (now,)))
            for m in missed:
                con.execute("UPDATE posts SET status = 'missed' WHERE id = ?", (m["id"],))
                con.execute("UPDATE post_targets SET status = 'cancelled' WHERE post_id = ?", (m["id"],))
                results.append({"post_id": m["id"], "status": "missed", "reason": "no approved video was available"})
        q = ("SELECT t.*, p.video_id FROM post_targets t JOIN posts p ON p.id = t.post_id "
             "WHERE t.via = 'direct' AND t.status = 'pending' AND p.status IN ('scheduled', 'posting', 'partial') "
             "AND t.at <= ? "
             "AND (t.next_try_at IS NULL OR t.next_try_at <= ?)")
        args: tuple = (now, now)
        if only is not None:
            q, args = q + " AND t.post_id = ?", (*args, only)
        for t in db.rows(con.execute(q + " ORDER BY t.at, t.id", args)):
            video = db.get_video(con, t["video_id"])
            entry = {"post_id": t["post_id"], "target_id": t["id"], "platform": t["platform"], "video_id": video["id"]}
            if t["platform_post_id"]:
                entry.update(status="posted", note="already published")
                results.append(entry)
                continue
            problem = approval.check_video(ctx, con, video)
            if problem:
                with db.tx(con):
                    con.execute("UPDATE post_targets SET status = 'failed', error = ? WHERE id = ?",
                                (f"blocked: {problem}", t["id"]))
                    _settle_post(con, t["post_id"])
                entry.update(status="blocked", error=problem)
                results.append(entry)
                continue
            adapter = platforms.get(t["platform"])
            caption = platforms.caption_for(t["platform"], video, _preset_publish(ctx, video["preset"]))
            if dry_run:
                entry.update(status="dry-run", kind=adapter.kind, caption=caption)
                results.append(entry)
                continue
            con.execute("UPDATE posts SET status = 'posting' WHERE id = ? AND status = 'scheduled'", (t["post_id"],))
            try:
                remote_id, url = adapter.publish(ctx, video, caption, t["post_id"])
                with db.tx(con):
                    con.execute("UPDATE post_targets SET status = ?, platform_post_id = ?, url = ?, posted_at = ?, "
                                "attempts = attempts + 1, error = NULL WHERE id = ?",
                                ("draft" if adapter.kind == "draft" else "posted", remote_id, url, iso(), t["id"]))
                    _settle_post(con, t["post_id"])
                entry.update(status="draft" if adapter.kind == "draft" else "posted", url=url)
            except (StudioError, OSError, KeyError, ValueError) as e:
                attempts = t["attempts"] + 1
                with db.tx(con):
                    if attempts > len(BACKOFF):
                        con.execute("UPDATE post_targets SET status = 'failed', attempts = ?, error = ? WHERE id = ?",
                                    (attempts, str(e)[:1000], t["id"]))
                        _settle_post(con, t["post_id"])
                    else:
                        con.execute("UPDATE post_targets SET attempts = ?, error = ?, next_try_at = ? WHERE id = ?",
                                    (attempts, str(e)[:1000], iso(now_utc() + BACKOFF[attempts - 1]), t["id"]))
                entry.update(status="error", attempts=attempts, error=str(e)[:300])
                log(f"post {t['post_id']} {t['platform']}: {e}")
            results.append(entry)
    finally:
        con.close()
    return results
