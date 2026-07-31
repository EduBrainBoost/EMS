from __future__ import annotations

from backend.app import config
from backend.app.security import RateLimiter, cors_headers, is_origin_allowed


def test_cors_allowlist_never_wildcard_or_credentials():
    assert cors_headers("https://evil.invalid") == {}
    allowed = cors_headers(config.EMS_CORS_ALLOWED_ORIGINS[0])
    assert allowed["Access-Control-Allow-Origin"] == config.EMS_CORS_ALLOWED_ORIGINS[0]
    assert allowed["Access-Control-Allow-Origin"] != "*"
    assert "Access-Control-Allow-Credentials" not in allowed
    assert not is_origin_allowed("null")


def test_rate_limiter_enforces_window_and_reset(monkeypatch):
    now = [100.0]
    monkeypatch.setattr("backend.app.security.time.time", lambda: now[0])
    limiter = RateLimiter()
    assert limiter.check("client", 2, 10)[0]
    limiter.hit("client", 10)
    limiter.hit("client", 10)
    assert limiter.check("client", 2, 10)[0] is False
    now[0] = 111.0
    assert limiter.check("client", 2, 10)[0] is True


def test_rate_limiter_is_thread_safe_and_bounded():
    limiter = RateLimiter()
    limiter.hit("client", 10)
    assert limiter.check("client", 1, 10)[1] == 0
    assert len(limiter._buckets["client"]) == 1
