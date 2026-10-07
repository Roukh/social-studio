"""SQLite library: videos, sessions, approvals, and the posts sent through Buffer.

Invariants the schema enforces (not just the code):
- status values are an enum, and only legal transitions pass (trigger);
- a video can only become `approved` when an approval row for its exact sha256 exists;
- every status change writes an append-only event row, attributed through ss_actor(), a function
  only this tool registers, so raw edits from the sqlite3 shell fail instead of slipping through;
- a video is used by at most one post, and a platform has at most one live post per minute;
- a platform post id (the Buffer post id) is stored once per platform, never twice.
Earlier schema entries are never edited; v1 still carries the removed calendar's statuses (open, missed,
draft), which nothing writes any more.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager

from .core import Ctx, DataError, iso

SCHEMA = [
    # v1
    """
    CREATE TABLE sessions (
      id TEXT PRIMARY KEY,
      kind TEXT NOT NULL CHECK (kind IN ('make', 'review')),
      preset TEXT NOT NULL,
      preset_hash TEXT NOT NULL,
      backend TEXT NOT NULL,
      model TEXT,
      sandbox INTEGER NOT NULL,
      dir TEXT NOT NULL,
      video_id INTEGER,
      status TEXT NOT NULL CHECK (status IN ('running', 'ok', 'failed')),
      error TEXT,
      cost_usd REAL,
      started_at TEXT NOT NULL,
      ended_at TEXT
    );

    CREATE TABLE videos (
      id INTEGER PRIMARY KEY,
      session_id TEXT REFERENCES sessions(id),
      parent_id INTEGER REFERENCES videos(id),
      slug TEXT NOT NULL,
      title TEXT NOT NULL,
      description TEXT NOT NULL DEFAULT '',
      topic TEXT NOT NULL DEFAULT '',
      angle TEXT NOT NULL DEFAULT '',
      pillar TEXT NOT NULL DEFAULT '',
      meta TEXT NOT NULL DEFAULT '{}',
      preset TEXT NOT NULL,
      dir TEXT NOT NULL,
      file TEXT NOT NULL,
      sha256 TEXT NOT NULL,
      bytes INTEGER NOT NULL,
      duration REAL NOT NULL,
      width INTEGER NOT NULL,
      height INTEGER NOT NULL,
      status TEXT NOT NULL DEFAULT 'review' CHECK (status IN
        ('review', 'approved', 'rejected', 'revision', 'superseded', 'scheduled', 'posted', 'failed')),
      notes TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );

    CREATE TABLE video_events (
      id INTEGER PRIMARY KEY,
      video_id INTEGER NOT NULL REFERENCES videos(id),
      old_status TEXT,
      new_status TEXT NOT NULL,
      actor TEXT NOT NULL,
      at TEXT NOT NULL
    );

    CREATE TABLE approvals (
      video_id INTEGER PRIMARY KEY REFERENCES videos(id),
      sha256 TEXT NOT NULL,
      approved_at TEXT NOT NULL,
      payload TEXT NOT NULL,
      signature TEXT NOT NULL
    );

    CREATE TABLE posts (
      id INTEGER PRIMARY KEY,
      at TEXT NOT NULL,
      video_id INTEGER UNIQUE REFERENCES videos(id),
      status TEXT NOT NULL DEFAULT 'open' CHECK (status IN
        ('open', 'scheduled', 'posting', 'posted', 'partial', 'failed', 'cancelled', 'missed')),
      created_by TEXT NOT NULL,
      created_at TEXT NOT NULL
    );

    CREATE TABLE post_targets (
      id INTEGER PRIMARY KEY,
      post_id INTEGER NOT NULL REFERENCES posts(id),
      platform TEXT NOT NULL,
      at TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN
        ('pending', 'posted', 'failed', 'draft', 'cancelled')),
      platform_post_id TEXT,
      url TEXT,
      error TEXT,
      attempts INTEGER NOT NULL DEFAULT 0,
      next_try_at TEXT,
      posted_at TEXT,
      UNIQUE (post_id, platform)
    );

    CREATE UNIQUE INDEX post_targets_slot ON post_targets(platform, at)
      WHERE status IN ('pending', 'posted', 'draft');
    CREATE UNIQUE INDEX post_targets_remote ON post_targets(platform, platform_post_id)
      WHERE platform_post_id IS NOT NULL;
    CREATE INDEX videos_status ON videos(status, created_at);

    CREATE TRIGGER videos_transition BEFORE UPDATE OF status ON videos
    WHEN NEW.status <> OLD.status AND NOT (
         (OLD.status = 'review'    AND NEW.status IN ('approved', 'rejected', 'revision', 'superseded'))
      OR (OLD.status = 'revision'  AND NEW.status IN ('approved', 'rejected', 'superseded', 'review'))
      OR (OLD.status = 'rejected'  AND NEW.status IN ('review'))
      OR (OLD.status = 'approved'  AND NEW.status IN ('scheduled', 'rejected', 'revision'))
      OR (OLD.status = 'scheduled' AND NEW.status IN ('posted', 'failed', 'approved'))
      OR (OLD.status = 'failed'    AND NEW.status IN ('approved', 'scheduled', 'rejected'))
    )
    BEGIN
      SELECT RAISE(ABORT, 'invalid status transition');
    END;

    CREATE TRIGGER videos_need_approval BEFORE UPDATE OF status ON videos
    WHEN NEW.status IN ('approved', 'scheduled') AND NOT EXISTS
      (SELECT 1 FROM approvals a WHERE a.video_id = NEW.id AND a.sha256 = NEW.sha256)
    BEGIN
      SELECT RAISE(ABORT, 'no approval for this exact file');
    END;

    CREATE TRIGGER videos_event AFTER UPDATE OF status ON videos
    WHEN NEW.status <> OLD.status
    BEGIN
      INSERT INTO video_events (video_id, old_status, new_status, actor, at)
      VALUES (NEW.id, OLD.status, NEW.status, ss_actor(), strftime('%Y-%m-%dT%H:%M:%SZ', 'now'));
    END;

    CREATE TRIGGER videos_born AFTER INSERT ON videos
    BEGIN
      INSERT INTO video_events (video_id, old_status, new_status, actor, at)
      VALUES (NEW.id, NULL, NEW.status, ss_actor(), strftime('%Y-%m-%dT%H:%M:%SZ', 'now'));
    END;

    CREATE TRIGGER events_append_only_u BEFORE UPDATE ON video_events
    BEGIN SELECT RAISE(ABORT, 'video_events is append-only'); END;
    CREATE TRIGGER events_append_only_d BEFORE DELETE ON video_events
    BEGIN SELECT RAISE(ABORT, 'video_events is append-only'); END;

    -- What the agent surface may read. Assigned and posted videos never appear here.
    CREATE VIEW agent_videos AS
      SELECT id, title, description, topic, angle, pillar, preset, status, duration, created_at
      FROM videos WHERE status IN ('review', 'approved', 'rejected', 'revision');

    CREATE VIEW agent_topics AS
      SELECT topic, angle, pillar, substr(created_at, 1, 10) AS day
      FROM videos WHERE status <> 'superseded';

    CREATE VIEW agent_calendar AS
      SELECT p.id, p.at, p.status, p.video_id IS NOT NULL AS filled,
        (SELECT group_concat(t.platform, ',') FROM post_targets t
          WHERE t.post_id = p.id AND t.status <> 'cancelled') AS platforms
      FROM posts p WHERE p.status <> 'cancelled';
    """,
    # v2: targets that go out through Buffer (`via`; `direct` was the adapter route removed on 2026-10-06),
    # `channel_id` is the Buffer channel and `text` is exactly what was sent.
    """
    ALTER TABLE post_targets ADD COLUMN via TEXT NOT NULL DEFAULT 'direct' CHECK (via IN ('direct', 'buffer'));
    ALTER TABLE post_targets ADD COLUMN channel_id TEXT;
    ALTER TABLE post_targets ADD COLUMN text TEXT;
    """,
]


def connect(ctx: Ctx, actor: str = "cli") -> sqlite3.Connection:
    ctx.studio_dir.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ctx.db_path, timeout=30, isolation_level=None)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA busy_timeout=30000")
    con.create_function("ss_actor", 0, lambda: actor)
    version = con.execute("PRAGMA user_version").fetchone()[0]
    for i, script in enumerate(SCHEMA[version:], start=version + 1):
        con.executescript(f"BEGIN; {script} PRAGMA user_version = {i}; COMMIT;")
    return con


@contextmanager
def tx(con: sqlite3.Connection):
    """BEGIN IMMEDIATE takes the write lock up front, so check-then-write sequences cannot race."""
    con.execute("BEGIN IMMEDIATE")
    try:
        yield con
        con.execute("COMMIT")
    except BaseException:
        con.execute("ROLLBACK")
        raise


def rows(cur) -> list[dict]:
    return [dict(r) for r in cur.fetchall()]


def get_video(con: sqlite3.Connection, vid: int) -> dict:
    r = con.execute("SELECT * FROM videos WHERE id = ?", (vid,)).fetchone()
    if r is None:
        raise DataError(f"no video with id {vid}", "run `social-studio library list`")
    return dict(r)


def set_status(con: sqlite3.Connection, vid: int, status: str, note: str = "") -> None:
    try:
        if note:
            con.execute("UPDATE videos SET status = ?, updated_at = ?, notes = trim(notes || char(10) || ?) WHERE id = ?",
                        (status, iso(), note, vid))
        else:
            con.execute("UPDATE videos SET status = ?, updated_at = ? WHERE id = ?", (status, iso(), vid))
    except sqlite3.IntegrityError as e:
        v = get_video(con, vid)
        raise DataError(f"video {vid}: {v['status']} -> {status} refused ({e})",
                        "check `social-studio library show <id>` for its current status") from e
