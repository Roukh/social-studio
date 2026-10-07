"""The media proxy that serves videos from a private Railway bucket, and the client's bucket URLs."""
from __future__ import annotations

import http.client
import importlib.util
import threading
from pathlib import Path

import pytest

from social_studio.platforms import media

spec = importlib.util.spec_from_file_location(
    "media_proxy", Path(__file__).resolve().parents[1] / "deploy" / "media-proxy" / "server.py")
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)

VIDEO = "social-studio/" + "ab" * 32 + ".mp4"
BODY = bytes(range(256)) * 40


class FakeResponse:
    def __init__(self, status: int, body: bytes = b"", headers: dict | None = None):
        self.status, self._body, self._headers = status, body, {k.lower(): v for k, v in (headers or {}).items()}

    def getheader(self, name):
        return self._headers.get(name.lower())

    def read(self, n):
        out, self._body = self._body[:n], self._body[n:]
        return out


class FakeBucket:
    """Stands in for the signed bucket request: records what the proxy asked for."""

    def __init__(self):
        self.asked: list[tuple] = []
        self.status = 200

    def __call__(self, env, method, key, byte_range):
        self.asked.append((method, key, byte_range))
        if self.status != 200:
            return self, FakeResponse(self.status)
        if byte_range == "bytes=0-9":
            return self, FakeResponse(206, BODY[:10], {"Content-Range": f"bytes 0-9/{len(BODY)}",
                                                       "Content-Length": "10", "Content-Type": "video/mp4"})
        return self, FakeResponse(200, BODY if method == "GET" else b"",
                                  {"Content-Length": str(len(BODY)), "Content-Type": "video/mp4", "ETag": '"e"'})

    def close(self):
        pass


@pytest.fixture
def served():
    bucket = FakeBucket()

    class Handler(proxy.Handler):
        env = {"ENDPOINT": "https://t3.storageapi.dev", "BUCKET": "videos-x1"}
        keys = proxy.key_pattern("social-studio/")
        upstream = staticmethod(bucket)

        def log_message(self, *a):
            pass

    server = proxy.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    def ask(method, path, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
        conn.request(method, path, headers=headers or {})
        resp = conn.getresponse()
        out = (resp.status, {k.lower(): v for k, v in resp.getheaders()}, resp.read())
        conn.close()
        return out
    yield ask, bucket
    server.shutdown()
    server.server_close()


def test_proxy_signer_matches_the_aws_test_vector():
    out = proxy.sign("GET", "https://example.amazonaws.com/", {}, proxy.EMPTY_SHA256, access="AKIDEXAMPLE",
                     secret="wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY", region="us-east-1", service="service",
                     amz_date="20150830T123600Z")
    assert out["authorization"].endswith("Signature=5fa00fa31553b73ebf1942676e86291e8372ff2a2260956d9b8aae1d763fbf31")


def test_proxy_and_client_sign_alike():
    args = ("PUT", "https://videos-x1.t3.storageapi.dev/social-studio/a.mp4",
            {"content-type": "video/mp4", "x-amz-content-sha256": "ab" * 32}, "ab" * 32)
    kw = {"access": "AK", "secret": "SK", "region": "auto", "amz_date": "20261007T010203Z"}
    assert proxy.sign(*args, **kw) == media.sign(*args, **kw)


def test_proxy_streams_a_video_with_its_headers(served):
    ask, bucket = served
    status, headers, body = ask("GET", "/" + VIDEO)
    assert (status, body, headers["content-type"], headers["content-length"]) == (200, BODY, "video/mp4", str(len(BODY)))
    assert headers["cache-control"] == "public, max-age=31536000, immutable"
    status, headers, body = ask("HEAD", "/" + VIDEO)
    assert status == 200 and body == b"" and headers["content-length"] == str(len(BODY))
    assert bucket.asked == [("GET", VIDEO, None), ("HEAD", VIDEO, None)]


def test_proxy_passes_ranges_through(served):
    ask, bucket = served
    status, headers, body = ask("GET", "/" + VIDEO, {"Range": "bytes=0-9"})
    assert (status, body, headers["content-range"]) == (206, BODY[:10], f"bytes 0-9/{len(BODY)}")


@pytest.mark.parametrize("path", ["/", "/social-studio/", "/social-studio/notes.txt", "/other/" + "ab" * 32 + ".mp4",
                                  "/social-studio/" + "AB" * 32 + ".mp4", "/social-studio/../secrets",
                                  "/social-studio/%2e%2e/x.mp4"])
def test_proxy_refuses_every_other_key(served, path):
    ask, bucket = served
    assert ask("GET", path)[0] == 404 and bucket.asked == []


def test_proxy_hides_bucket_errors(served):
    ask, bucket = served
    bucket.status = 403
    assert ask("GET", "/" + VIDEO)[0] == 404
    bucket.status = 500
    assert ask("GET", "/" + VIDEO)[0] == 502
    assert ask("GET", "/healthz")[:2][0] == 200


def test_proxy_without_bucket_variables_reports_unconfigured(served, monkeypatch):
    ask, bucket = served
    monkeypatch.setattr(proxy.Handler, "ready", False)
    assert ask("GET", "/healthz")[2] == b"unconfigured\n"
    assert ask("GET", "/" + VIDEO)[0] == 503 and bucket.asked == []


def test_proxy_builds_virtual_and_path_urls():
    env = {"ENDPOINT": "https://t3.storageapi.dev", "BUCKET": "videos-x1"}
    assert proxy.object_url(env, VIDEO) == f"https://videos-x1.t3.storageapi.dev/{VIDEO}"
    assert proxy.object_url({**env, "ADDRESSING": "path"}, VIDEO) == f"https://t3.storageapi.dev/videos-x1/{VIDEO}"


def test_media_connect_takes_settings_and_keys_from_the_environment(tmp_path, monkeypatch):
    from social_studio.core import PROJECT_FILE, load_env, load_toml, make_ctx
    (tmp_path / ".git").mkdir()
    (tmp_path / PROJECT_FILE).write_text("")
    for k, v in {"MEDIA_ENDPOINT": "https://t3.storageapi.dev", "MEDIA_BUCKET": "videos-x1",
                 "MEDIA_PUBLIC_URL": "https://media.example.app", "MEDIA_ACCESS_KEY_ID": "AK",
                 "MEDIA_SECRET_ACCESS_KEY": "SK", "MEDIA_ADDRESSING": "virtual-host"}.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(media, "require_human", lambda action: None)
    ctx = make_ctx(str(tmp_path))
    media.MediaAdapter().connect(ctx)
    saved = load_toml(tmp_path / PROJECT_FILE)["publish"]["media"]
    assert saved == {"endpoint": "https://t3.storageapi.dev", "bucket": "videos-x1", "region": "auto",
                     "addressing": "virtual", "public_url": "https://media.example.app", "prefix": "social-studio/"}
    assert {k: load_env(ctx.env_path)[k] for k in media.KEYS} == {"MEDIA_ACCESS_KEY_ID": "AK",
                                                                  "MEDIA_SECRET_ACCESS_KEY": "SK"}


@pytest.mark.parametrize("given,style", [("virtual-host", "virtual"), ("Virtual", "virtual"), ("", "virtual"),
                                         ("path-style", "path"), ("path", "path")])
def test_media_reads_each_providers_url_style(given, style):
    assert media.url_style(given) == style


def test_media_refuses_an_unknown_url_style():
    from social_studio.core import ConfigError
    with pytest.raises(ConfigError):
        media.url_style("dns")


def test_media_connect_is_human_only(tmp_path, monkeypatch):
    from social_studio.core import PROJECT_FILE, Denied, make_ctx
    (tmp_path / ".git").mkdir()
    (tmp_path / PROJECT_FILE).write_text("")
    with pytest.raises(Denied):
        media.MediaAdapter().connect(make_ctx(str(tmp_path)))


def test_media_client_defaults_to_virtual_hosted_urls():
    s = {"endpoint": "https://t3.storageapi.dev/", "bucket": "videos-x1", "addressing": "virtual"}
    assert media.object_url(s, VIDEO) == f"https://videos-x1.t3.storageapi.dev/{VIDEO}"
    assert media.object_url({**s, "addressing": "path"}, VIDEO) == f"https://t3.storageapi.dev/videos-x1/{VIDEO}"
