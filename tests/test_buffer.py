"""Posting through Buffer: the GraphQL client, public media hosting, the signed post text, and the
operator-only schedule flow with its sync, cancel and timer behaviour. The network is a fake."""
from __future__ import annotations

import json
import sqlite3
import subprocess
from datetime import datetime, timedelta, timezone

import pytest

from social_studio import approval, cli, db, posting
from social_studio.core import (PROJECT_FILE, ConfigError, DataError, Denied, UsageError, dump_toml, make_ctx,
                                sha256_file)
from social_studio.platforms import HttpError, buffer, media

PUBLIC = "https://pub.example.dev"
ENDPOINT = "https://acct.r2.cloudflarestorage.com"
CHANNELS = [
    {"id": "ig1", "name": "ghobz", "displayName": "Ghobz", "service": "instagram"},
    {"id": "fb1", "name": "ghobz", "displayName": "Ghobz Page", "service": "facebook"},
    {"id": "tw1", "name": "ghobz", "displayName": "@ghobz", "service": "twitter"},
    {"id": "li1", "name": "ghobz", "displayName": "Ghobz", "service": "linkedin"},
    {"id": "ig2", "name": "old", "displayName": "Old", "service": "instagram", "isDisconnected": True},
]


class FakeNet:
    """Buffer's GraphQL endpoint and an S3-compatible bucket with a public URL, in memory."""

    def __init__(self):
        self.calls: list[tuple] = []
        self.hosted: dict[str, bytes] = {}
        self.remote: dict[str, dict] = {}
        self.refuse: set[str] = set()
        self.issued: list[str] = []

    def ops(self, word: str) -> list[dict]:
        return [c[3] for c in self.calls if c[1] == buffer.API and word in c[3]["query"]]

    def __call__(self, method, url, *, params=None, headers=None, json_body=None, form=None, data=None, timeout=120):
        self.calls.append((method, url, headers or {}, json_body, data))
        if url == buffer.API:
            q, v = json_body["query"], json_body["variables"]
            if "organizations" in q:
                return 200, {}, {"data": {"account": {"organizations": [{"id": "org1", "name": "Ghobz"}]}}}
            if "channels(" in q:
                chans = [{"isDisconnected": False, "isLocked": False, "isQueuePaused": False, "timezone": "UTC", **c}
                         for c in CHANNELS]
                return 200, {}, {"data": {"channels": chans}}
            if "createPost" in q:
                inp = v["input"]
                if inp["channelId"] in self.refuse:
                    return 200, {}, {"data": {"createPost": {"__typename": "InvalidInputError", "message": "nope"}}}
                pid = f"b-{inp['channelId']}"
                self.issued.append(pid)
                if self.issued.count(pid) > 1:  # Buffer never reuses a post id
                    pid = f"{pid}-{self.issued.count(pid)}"
                self.remote[pid] = {"id": pid, "status": "draft" if inp.get("saveToDraft") else "scheduled",
                                    "dueAt": inp.get("dueAt"), "sentAt": None, "externalLink": None, "error": None}
                return 200, {}, {"data": {"createPost": {"__typename": "PostActionSuccess", "post": self.remote[pid]}}}
            if "deletePost" in q:
                self.remote.pop(v["input"]["id"], None)
                return 200, {}, {"data": {"deletePost": {"__typename": "DeletePostSuccess", "id": v["input"]["id"]}}}
            if "post(input" in q:
                if v["input"]["id"] not in self.remote:
                    return 200, {}, {"data": None, "errors": [{"message": "gone", "extensions": {"code": "NOT_FOUND"}}]}
                return 200, {}, {"data": {"post": self.remote[v["input"]["id"]]}}
            raise AssertionError(q)
        if method == "HEAD":
            if url in self.hosted:
                return 200, {"Content-Length": str(len(self.hosted[url]))}, {}
            raise HttpError(404, url, "")
        if method == "PUT":
            assert url.startswith(f"{ENDPOINT}/bkt/") and headers["authorization"].startswith("AWS4-HMAC-SHA256 ")
            self.hosted[f"{PUBLIC}/{url.split('/bkt/', 1)[1]}"] = data
            return 200, {}, {}
        raise AssertionError(f"{method} {url}")


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    (tmp_path / "repo" / ".git").mkdir(parents=True)
    proj = tmp_path / "repo" / "social"
    proj.mkdir()
    (proj / PROJECT_FILE).write_text(dump_toml({
        "timezone": "UTC", "paths": {"library": "library"},
        "publish": {"media": {"endpoint": ENDPOINT, "bucket": "bkt", "public_url": PUBLIC, "prefix": "ss/",
                              "addressing": "path"}}}))
    monkeypatch.setenv("SOCIAL_STUDIO_PROJECT", str(proj))
    monkeypatch.setenv("TZ", "UTC")
    monkeypatch.setenv("BUFFER_API_KEY", "buf-test")
    monkeypatch.setenv("MEDIA_ACCESS_KEY_ID", "AKID")
    monkeypatch.setenv("MEDIA_SECRET_ACCESS_KEY", "SECRET")
    monkeypatch.delenv("SOCIAL_STUDIO_ROLE", raising=False)
    return make_ctx()


@pytest.fixture
def net(monkeypatch):
    fake = FakeNet()
    monkeypatch.setattr(buffer, "http", fake)
    monkeypatch.setattr(media, "http", fake)
    monkeypatch.setattr(buffer.time, "sleep", lambda s: None)
    monkeypatch.setattr(media.time, "sleep", lambda s: None)
    return fake


@pytest.fixture
def human(ctx, monkeypatch):
    """A passphrase-less test key and a human at the terminal."""
    key, pub, allowed = approval.key_paths(ctx)
    key.parent.mkdir(parents=True)
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "t", "-f", str(key)], check=True)
    allowed.write_text(f'{approval.IDENTITY} namespaces="{approval.NAMESPACE}" {pub.read_text().strip()}\n')
    for mod in (approval, posting):
        monkeypatch.setattr(mod, "require_human", lambda action: None)


def add_video(ctx, captions=None, width=1080, height=1920, title="A video") -> int:
    d = ctx.library_dir / title.replace(" ", "-")
    d.mkdir(parents=True, exist_ok=True)
    f = d / "video.mp4"
    f.write_bytes(title.encode() * 100)
    meta = {"video": {"captions": captions or {"instagram": "IG words", "facebook": "FB words", "x": "X words"},
                      "hashtags": ["motion"], "poster_at": 1.5}}
    con = db.connect(ctx, actor="test")
    now = "2026-10-01T00:00:00Z"
    vid = con.execute(
        "INSERT INTO videos (slug, title, description, preset, dir, file, sha256, bytes, duration, width, height,"
        " created_at, updated_at, pillar, meta) VALUES (?, ?, 'what it shows', 'example', ?, ?, ?, ?, 12.0, ?, ?, ?, ?,"
        " 'principle', ?)",
        (title.lower().replace(" ", "-"), title, ctx.rel(d), ctx.rel(f), sha256_file(f), f.stat().st_size,
         width, height, now, now, json.dumps(meta))).lastrowid
    con.close()
    return vid


def later(hours=24) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")


def schedule(ctx, vid, keys=None, when=None) -> dict:
    return posting.execute(ctx, posting.plan(ctx, vid, keys, when or later()))


def row(ctx, sql, *args):
    con = db.connect(ctx)
    try:
        return [dict(r) for r in con.execute(sql, args)]
    finally:
        con.close()


# --- client -------------------------------------------------------------------------------------------

def test_client_sends_bearer_key_and_reads_channels(ctx, net):
    found = buffer.channels(ctx)
    assert [c["platform"] for c in found] == ["facebook", "instagram", "x"]  # linkedin and disconnected dropped
    method, url, headers, body, _ = net.calls[-1]
    assert (method, url, headers["Authorization"]) == ("POST", buffer.API, "Bearer buf-test")
    assert body["variables"] == {"input": {"organizationId": "org1"}}


def test_client_missing_key_is_a_config_error(ctx, net, monkeypatch):
    monkeypatch.delenv("BUFFER_API_KEY")
    with pytest.raises(ConfigError):
        buffer.channels(ctx)


def test_client_retries_a_read_once_but_never_a_mutation(ctx, monkeypatch):
    calls = []

    def flaky(method, url, **kw):
        calls.append(kw["json_body"]["query"])
        return 200, {}, {"data": None, "errors": [{"message": "boom", "extensions": {"code": "UNEXPECTED"}}]}
    monkeypatch.setattr(buffer, "http", flaky)
    monkeypatch.setattr(buffer.time, "sleep", lambda s: None)
    with pytest.raises(buffer.BufferError):
        buffer.get_post(ctx, "p1")
    assert len(calls) == 2
    calls.clear()
    with pytest.raises(buffer.BufferError):
        buffer.create_post(ctx, {"channelId": "ig1"})
    assert len(calls) == 1


def test_client_mutation_error_becomes_a_data_error(ctx, net):
    net.refuse.add("ig1")
    with pytest.raises(DataError, match="nope"):
        buffer.create_post(ctx, {"channelId": "ig1"})


def test_client_builds_video_posts_per_network():
    vertical = {"meta": json.dumps({"video": {"poster_at": 1.5}}), "width": 1080, "height": 1920, "duration": 12.0}
    wide = {**vertical, "width": 1920, "height": 1080}
    ig = buffer.post_input({"id": "ig1", "service": "instagram"}, "t", "https://u/v.mp4", vertical, "2026-10-08T13:00:00Z")
    assert ig["mode"] == "customScheduled" and ig["dueAt"] == "2026-10-08T13:00:00Z"
    assert ig["assets"] == [{"video": {"url": "https://u/v.mp4", "metadata": {"thumbnailOffset": 1500}}}]
    assert ig["metadata"]["instagram"] == {"type": "reel", "shouldShareToFeed": True, "isAiGenerated": False}
    assert buffer.post_input({"id": "f", "service": "facebook"}, "t", "u", vertical, None)["metadata"] == {
        "facebook": {"type": "reel"}}
    fb_wide = buffer.post_input({"id": "f", "service": "facebook"}, "t", "u", wide, None)
    assert fb_wide["metadata"] == {"facebook": {"type": "post"}} and fb_wide["mode"] == "shareNow"
    x = buffer.post_input({"id": "t", "service": "twitter"}, "t", "u", wide, None)
    assert "metadata" not in x and x["assets"] == [{"video": {"url": "u"}}]
    draft = buffer.post_input({"id": "t", "service": "twitter"}, "t", "u", wide, "2026-10-08T13:00:00Z", draft=True)
    assert draft["saveToDraft"] is True and draft["mode"] == "addToQueue" and "dueAt" not in draft


def test_client_counts_text_like_buffer():
    assert buffer.text_length("x", "see https://example.com/a/very/long/path/indeed ok") == len("see  ok") + 23
    assert buffer.text_length("instagram", "hi 🎬") == 5  # the emoji is two UTF-16 units


# --- media --------------------------------------------------------------------------------------------

def test_media_sigv4_matches_the_aws_test_vector():
    """aws-c-auth signing test suite, v4/get-vanilla."""
    out = media.sign("GET", "https://example.amazonaws.com/", {}, media.EMPTY_SHA256, access="AKIDEXAMPLE",
                     secret="wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY", region="us-east-1", service="service",
                     amz_date="20150830T123600Z")
    assert out["authorization"] == (
        "AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/20150830/us-east-1/service/aws4_request, "
        "SignedHeaders=host;x-amz-date, Signature=5fa00fa31553b73ebf1942676e86291e8372ff2a2260956d9b8aae1d763fbf31")


def test_media_uploads_once_under_the_sha256_and_checks_the_public_url(ctx, net):
    vid = add_video(ctx)
    video = db.get_video(db.connect(ctx), vid)
    url = media.ensure_hosted(ctx, video)
    assert url == f"{PUBLIC}/ss/{video['sha256']}.mp4" and net.hosted[url] == ctx.abs(video["file"]).read_bytes()
    put = [c for c in net.calls if c[0] == "PUT"]
    assert len(put) == 1 and put[0][2]["x-amz-content-sha256"] == video["sha256"]
    assert media.ensure_hosted(ctx, video) == url and len([c for c in net.calls if c[0] == "PUT"]) == 1


def test_media_needs_https_settings(ctx, net):
    ctx.config["publish"]["media"]["public_url"] = "http://pub.example.dev"
    with pytest.raises(ConfigError):
        media.settings(ctx)
    del ctx.config["publish"]["media"]
    with pytest.raises(ConfigError, match="not set up"):
        media.settings(ctx)


# --- approval -----------------------------------------------------------------------------------------

def test_approval_covers_the_post_text(ctx, human):
    vid = add_video(ctx)
    cli._approve(ctx, [vid])
    con = db.connect(ctx)
    assert approval.check_video(ctx, con, db.get_video(con, vid), post=True) is None
    meta = {"video": {"captions": {"instagram": "something an agent wrote later"}, "hashtags": ["motion"],
                      "poster_at": 1.5}}
    con.execute("UPDATE videos SET meta = ? WHERE id = ?", (json.dumps(meta), vid))
    video = db.get_video(con, vid)
    assert approval.check_video(ctx, con, video, post=True) == "post text changed after approval"
    assert approval.check_video(ctx, con, video) is None  # the file itself is still the approved one


def test_approval_without_signed_text_must_be_approved_again(ctx, human, monkeypatch):
    vid = add_video(ctx)
    monkeypatch.setattr(approval, "payload", lambda v, at: (
        f"social-studio approval v1\nvideo:{v['id']}\nsha256:{v['sha256']}\napproved_at:{at}\n"))
    cli._approve(ctx, [vid])
    con = db.connect(ctx)
    assert approval.check_video(ctx, con, db.get_video(con, vid), post=True) == (
        "approved before post text was signed; approve it again")


# --- post ---------------------------------------------------------------------------------------------

def test_post_is_human_only(ctx, net):
    vid = add_video(ctx)
    assert cli.main(["--json", "post", "schedule", str(vid), "--at", "now"]) == 77
    assert cli.main(["--json", "post", "list"]) == 77
    assert cli.main(["--json", "post", "cancel", "1"]) == 77
    assert cli.main(["--json", "post"]) == 77
    assert not net.ops("createPost")


def test_post_schedules_an_approved_video_on_each_channel(ctx, net, human):
    vid = add_video(ctx)
    cli._approve(ctx, [vid])
    res = schedule(ctx, vid)
    assert [t["status"] for t in res["targets"]] == ["scheduled"] * 3
    created = {c["variables"]["input"]["channelId"]: c["variables"]["input"] for c in net.ops("createPost")}
    assert set(created) == {"ig1", "fb1", "tw1"}
    assert created["ig1"]["text"] == "IG words\n\n#motion" and created["tw1"]["text"] == "X words\n\n#motion"
    assert created["ig1"]["assets"][0]["video"]["url"] == res["media_url"] in net.hosted
    targets = row(ctx, "SELECT platform, via, status, platform_post_id, text FROM post_targets ORDER BY platform")
    assert [(t["platform"], t["via"], t["status"], t["platform_post_id"]) for t in targets] == [
        ("facebook", "buffer", "pending", "b-fb1"), ("instagram", "buffer", "pending", "b-ig1"),
        ("x", "buffer", "pending", "b-tw1")]
    assert db.get_video(db.connect(ctx), vid)["status"] == "scheduled"
    with pytest.raises(DataError, match="is scheduled"):
        posting.plan(ctx, vid, None, later())


def test_post_picks_channels_by_name(ctx, net, human):
    vid = add_video(ctx)
    cli._approve(ctx, [vid])
    res = schedule(ctx, vid, ["instagram", "x"])
    assert sorted(t["platform"] for t in res["targets"]) == ["instagram", "x"]
    other = add_video(ctx, title="Other")
    cli._approve(ctx, [other])
    with pytest.raises(UsageError, match="tiktok"):
        posting.plan(ctx, other, ["tiktok"], later())


def test_post_refuses_unapproved_or_rewritten_posts(ctx, net, human):
    vid = add_video(ctx)
    with pytest.raises(DataError, match="only approved"):
        posting.plan(ctx, vid, None, later())
    cli._approve(ctx, [vid])
    con = db.connect(ctx)
    con.execute("UPDATE videos SET description = 'changed' WHERE id = ?", (vid,))
    with pytest.raises(Denied, match="post text changed"):
        posting.plan(ctx, vid, None, later())
    assert not net.ops("createPost") and not net.hosted


def test_post_text_changed_while_confirming_is_refused(ctx, net, human):
    vid = add_video(ctx)
    cli._approve(ctx, [vid])
    planned = posting.plan(ctx, vid, None, later())
    db.connect(ctx).execute("UPDATE videos SET title = 'swapped' WHERE id = ?", (vid,))
    with pytest.raises(DataError, match="changed while you were confirming"):
        posting.execute(ctx, planned)
    assert not net.ops("createPost") and not net.hosted


def test_post_text_over_the_limit_is_refused_before_upload(ctx, net, human):
    vid = add_video(ctx, captions={"x": "w" * 300})
    cli._approve(ctx, [vid])
    with pytest.raises(DataError, match="too long"):
        posting.plan(ctx, vid, ["x"], later())
    assert not net.hosted


def test_post_in_the_past_is_refused(ctx, net, human):
    vid = add_video(ctx)
    cli._approve(ctx, [vid])
    with pytest.raises(UsageError):
        posting.plan(ctx, vid, None, later(hours=-1))


def test_post_refused_everywhere_is_undone(ctx, net, human):
    vid = add_video(ctx)
    cli._approve(ctx, [vid])
    net.refuse.update({"ig1", "fb1", "tw1"})
    res = schedule(ctx, vid)
    assert {t["status"] for t in res["targets"]} == {"failed"}
    assert db.get_video(db.connect(ctx), vid)["status"] == "approved"
    assert row(ctx, "SELECT status, video_id FROM posts")[0] == {"status": "cancelled", "video_id": None}
    net.refuse.clear()
    assert {t["status"] for t in schedule(ctx, vid)["targets"]} == {"scheduled"}


def test_post_sync_records_what_buffer_did(ctx, net, human):
    vid = add_video(ctx)
    cli._approve(ctx, [vid])
    pid = schedule(ctx, vid, ["instagram", "x"])["post_id"]
    assert posting.sync(ctx) == []  # nothing is due yet, so Buffer is not asked
    con = db.connect(ctx)
    con.execute("UPDATE post_targets SET at = '2000-01-01T00:00:00Z'")
    net.remote["b-ig1"].update(status="sent", sentAt="2026-10-08T13:00:04.000Z",
                               externalLink="https://instagram.com/reel/abc")
    net.remote["b-tw1"].update(status="error", error={"message": "video too long for X"})
    res = {r["platform"]: r for r in posting.sync(ctx)}
    assert res["instagram"]["status"] == "posted" and res["x"]["error"] == "video too long for X"
    assert con.execute("SELECT status FROM posts WHERE id = ?", (pid,)).fetchone()[0] == "partial"
    assert db.get_video(con, vid)["status"] == "posted"
    assert row(ctx, "SELECT url FROM post_targets WHERE platform = 'instagram'")[0]["url"] == "https://instagram.com/reel/abc"


def test_post_sync_from_the_timer_only_reads(ctx, net, human, capsys):
    """The timer runs `post sync`: no terminal needed, it only reads Buffer, and it never creates a post."""
    vid = add_video(ctx)
    cli._approve(ctx, [vid])
    schedule(ctx, vid, ["instagram"])
    db.connect(ctx).execute("UPDATE post_targets SET at = '2000-01-01T00:00:00Z'")
    assert cli.main(["--json", "post", "sync"]) == 0
    res = json.loads(capsys.readouterr().out)
    assert [(r["platform"], r["status"]) for r in res] == [("instagram", "scheduled")]
    assert len(net.ops("createPost")) == 1 and len(net.ops("post(input")) == 1
    with pytest.raises(SystemExit):  # the direct publisher it used to run is gone
        cli.main(["post", "run"])


def test_post_cancel_removes_it_from_buffer(ctx, net, human):
    vid = add_video(ctx)
    cli._approve(ctx, [vid])
    pid = schedule(ctx, vid)["post_id"]
    posting.cancel(ctx, pid)
    assert len(net.ops("deletePost")) == 3 and not net.remote
    assert db.get_video(db.connect(ctx), vid)["status"] == "approved"
    assert {r["status"] for r in row(ctx, "SELECT status FROM post_targets")} == {"cancelled"}


def test_post_pick_dry_run_sends_nothing(ctx, net, human, monkeypatch):
    vid = add_video(ctx)
    cli._approve(ctx, [vid])
    answers = iter(["1", "1, x", "now"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    res = posting.pick(ctx, dry_run=True)
    assert res == {"dry_run": True, "video_id": vid, "local": "now"}
    assert not net.ops("createPost") and not net.hosted


def test_post_schema_v2_upgrades_a_v1_library(tmp_path):
    path = tmp_path / "library.db"
    con = sqlite3.connect(path, isolation_level=None)
    con.create_function("ss_actor", 0, lambda: "t")
    con.executescript(f"BEGIN; {db.SCHEMA[0]} PRAGMA user_version = 1; COMMIT;")
    con.execute("INSERT INTO posts (at, created_by, created_at) VALUES ('2026-10-08T13:00:00Z', 't', 'x')")
    con.execute("INSERT INTO post_targets (post_id, platform, at) VALUES (1, 'bluesky', '2026-10-08T13:00:00Z')")
    con.close()

    class Ctx:
        studio_dir, db_path = tmp_path, path
    con = db.connect(Ctx())
    assert con.execute("PRAGMA user_version").fetchone()[0] == len(db.SCHEMA) == 3
    assert dict(con.execute("SELECT via, channel_id, text FROM post_targets").fetchone()) == {
        "via": "direct", "channel_id": None, "text": None}


# --- approval in Buffer: drafts ------------------------------------------------------------------------

def drafts(ctx, net, **kw) -> tuple[int, dict]:
    vid = add_video(ctx, **kw)
    return vid, posting.draft(ctx, vid)


def test_draft_puts_a_new_video_in_buffer_on_every_channel(ctx, net):
    """No terminal and no signature: drafts publish nothing, the operator approves them in Buffer."""
    vid, res = drafts(ctx, net)
    sent = [c["variables"]["input"] for c in net.ops("createPost")]
    assert sorted(i["channelId"] for i in sent) == ["fb1", "ig1", "tw1"]
    assert all(i["saveToDraft"] is True and i["mode"] == "addToQueue" and "dueAt" not in i for i in sent)
    assert {t["platform"]: t["status"] for t in res["targets"]} == {"facebook": "draft", "instagram": "draft",
                                                                   "x": "draft"}
    assert res["media_url"] in net.hosted
    assert row(ctx, "SELECT status, created_by, video_id FROM posts")[0] == {
        "status": "open", "created_by": "drafts", "video_id": vid}
    assert {r["status"] for r in row(ctx, "SELECT status FROM post_targets")} == {"draft"}
    assert db.get_video(db.connect(ctx), vid)["status"] == "review"


def test_draft_needs_a_video_waiting_for_review_and_not_in_buffer_yet(ctx, net, human):
    vid, _ = drafts(ctx, net)
    with pytest.raises(DataError, match="already on post"):
        posting.draft(ctx, vid)
    other = add_video(ctx, title="Other")
    cli._approve(ctx, [other])
    with pytest.raises(DataError, match="only a video waiting for review"):
        posting.draft(ctx, other)


def test_draft_skips_text_over_the_limit_and_undoes_a_draft_buffer_refused(ctx, net):
    vid, res = drafts(ctx, net, captions={"instagram": "ig", "facebook": "fb", "x": "x" * 300})
    assert {t["platform"]: t["status"] for t in res["targets"]}["x"] == "skipped"
    other = add_video(ctx, title="Other")
    net.refuse.update({"ig1", "fb1", "tw1"})
    assert {t["status"] for t in posting.draft(ctx, other)["targets"]} == {"failed"}
    assert row(ctx, "SELECT status, video_id FROM posts WHERE id = 2")[0] == {"status": "cancelled", "video_id": None}
    net.refuse.clear()
    assert {t["status"] for t in posting.draft(ctx, other)["targets"]} == {"draft"}


def test_draft_blocks_a_local_approval_and_a_bare_review_to_posted(ctx, net, human):
    vid, _ = drafts(ctx, net)
    with pytest.raises(DataError, match="approve it there"):
        cli._approve(ctx, [vid])
    loose = add_video(ctx, title="Loose")
    con = db.connect(ctx)
    with pytest.raises(DataError, match="refused"):
        db.set_status(con, loose, "posted")  # review -> posted needs a drafts post


def test_make_sends_each_new_video_to_buffer_as_drafts(ctx, net, monkeypatch, capsys):
    from social_studio import runner
    vid = add_video(ctx)
    made = {"ok": True, "video_id": vid, "title": "A video", "bytes": 1000, "duration": 12.0, "file": "v.mp4"}
    monkeypatch.setattr(runner, "make", lambda ctx, opts: [made])
    assert cli.main(["make", "--preset", "example"]) == 0
    out = capsys.readouterr().out
    assert f"video {vid} in Buffer as drafts" in out and "approve, edit or delete the drafts in Buffer" in out
    assert len(net.ops("createPost")) == 3
    ctx.config.setdefault("publish", {}).setdefault("buffer", {})["drafts"] = False
    ctx.save_config()
    assert not posting.drafts_on(make_ctx())


def test_sync_follows_drafts_approved_in_buffer_to_their_posts(ctx, net):
    vid, res = drafts(ctx, net)
    assert {r["status"] for r in posting.sync(ctx)} == {"draft"}  # still waiting in Buffer
    past = "2026-10-01T09:00:00.000Z"
    for pid in ("b-ig1", "b-tw1"):
        net.remote[pid].update(status="scheduled", dueAt=past)
    net.remote.pop("b-fb1")  # the operator deleted the Facebook draft
    got = {r["platform"]: r["status"] for r in posting.sync(ctx)}
    assert got == {"instagram": "approved", "x": "approved", "facebook": "turned down"}
    assert row(ctx, "SELECT status FROM posts")[0]["status"] == "scheduled"
    net.remote["b-ig1"].update(status="sent", sentAt=past, externalLink="https://instagram.com/reel/abc")
    net.remote["b-tw1"].update(status="sent", sentAt=past, externalLink="https://x.com/g/status/1")
    assert {r["status"] for r in posting.sync(ctx)} == {"posted"}
    con = db.connect(ctx)
    assert db.get_video(con, vid)["status"] == "posted"
    assert row(ctx, "SELECT status FROM posts")[0]["status"] == "posted"
    assert posting.sync(ctx) == []


def test_sync_rejects_a_video_whose_drafts_were_all_deleted_in_buffer(ctx, net):
    vid, _ = drafts(ctx, net)
    net.remote.clear()
    assert {r["status"] for r in posting.sync(ctx)} == {"turned down"}
    assert db.get_video(db.connect(ctx), vid)["status"] == "rejected"
    assert row(ctx, "SELECT status, video_id FROM posts")[0] == {"status": "cancelled", "video_id": None}


def test_withdraw_takes_drafts_out_of_buffer_when_rejected_or_revised_here(ctx, net, human):
    vid, _ = drafts(ctx, net)
    cli._decide(ctx, vid, "revision", "warmer colours")
    assert not net.remote and len(net.ops("deletePost")) == 3
    assert db.get_video(db.connect(ctx), vid)["status"] == "revision"
    assert row(ctx, "SELECT status, video_id FROM posts")[0] == {"status": "cancelled", "video_id": None}
    other, res = drafts(ctx, net, title="Other")
    ig = next(t["buffer_id"] for t in res["targets"] if t["platform"] == "instagram")
    net.remote[ig].update(status="sent", sentAt="2026-10-01T09:00:00Z", externalLink="https://instagram.com/r/1")
    posting.withdraw(ctx, other, "superseded by a revision")  # Instagram went out first: that record stays
    assert db.get_video(db.connect(ctx), other)["status"] == "posted"
    assert {r["platform"]: r["status"] for r in row(ctx, "SELECT platform, status FROM post_targets WHERE post_id = 2")
            } == {"instagram": "posted", "facebook": "cancelled", "x": "cancelled"}


def test_withdraw_by_post_cancel_leaves_the_video_waiting_for_review(ctx, net, human):
    vid, res = drafts(ctx, net)
    assert posting.cancel(ctx, res["post_id"]) == {"post_id": res["post_id"], "status": "cancelled"}
    assert not net.remote and db.get_video(db.connect(ctx), vid)["status"] == "review"
    assert {t["status"] for t in posting.draft(ctx, vid)["targets"]} == {"draft"}  # it can go back
