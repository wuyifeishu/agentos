"""Tests for api/rate_limiter module."""

import pytest
from agentos.api.rate_limiter import FixedWindowLimiter


class TestFixedWindowLimiter:
    def test_allows_within_limit(self):
        limiter = FixedWindowLimiter(max_requests=5, window_seconds=60)
        for i in range(5):
            allowed, info = limiter.is_allowed(f"user-{i}")
            assert allowed

    def test_blocks_after_limit(self):
        limiter = FixedWindowLimiter(max_requests=3, window_seconds=60)
        for i in range(3):
            allowed, _ = limiter.is_allowed("user-99")
            assert allowed
        allowed, info = limiter.is_allowed("user-99")
        assert not allowed
        assert info["remaining"] == 0

    def test_resets_after_window(self, monkeypatch):
        import time as _time
        limiter = FixedWindowLimiter(max_requests=2, window_seconds=1)
        limiter.is_allowed("key1")
        limiter.is_allowed("key1")
        allowed, _ = limiter.is_allowed("key1")
        assert not allowed
        limiter._windows["key1"] = (2, int(_time.time()) - 10)
        allowed, info = limiter.is_allowed("key1")
        assert allowed
        assert info["remaining"] == 1

    def test_independent_keys(self):
        limiter = FixedWindowLimiter(max_requests=1, window_seconds=60)
        assert limiter.is_allowed("a")[0]
        assert limiter.is_allowed("b")[0]
        assert not limiter.is_allowed("a")[0]
        assert not limiter.is_allowed("b")[0]
