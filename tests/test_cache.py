"""Tests for agentos.core.cache — Multi-backend Cache."""

import asyncio
import time

import pytest

from agentos.core.cache import (
    Cache,
    CacheConfig,
    CacheStats,
    JSONSerializer,
    MemoryCacheBackend,
    PickleSerializer,
    TieredCache,
    cached,
)


# ═════════════════════════════════════════════════════════════════════════
# MemoryCacheBackend
# ═════════════════════════════════════════════════════════════════════════

class TestMemoryCacheBackend:
    @pytest.fixture
    def backend(self):
        return MemoryCacheBackend(max_size=100, default_ttl=60.0)

    @pytest.mark.asyncio
    async def test_set_and_get(self, backend):
        await backend.set("k1", b"v1")
        assert await backend.get("k1") == b"v1"

    @pytest.mark.asyncio
    async def test_get_missing(self, backend):
        assert await backend.get("no-such") is None

    @pytest.mark.asyncio
    async def test_delete(self, backend):
        await backend.set("k1", b"v1")
        assert await backend.delete("k1") is True
        assert await backend.get("k1") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, backend):
        assert await backend.delete("no-such") is False

    @pytest.mark.asyncio
    async def test_exists(self, backend):
        await backend.set("k1", b"v1")
        assert await backend.exists("k1") is True
        assert await backend.exists("k2") is False

    @pytest.mark.asyncio
    async def test_ttl_expiry(self):
        backend = MemoryCacheBackend(default_ttl=0.01)
        await backend.set("k1", b"v1")
        await asyncio.sleep(0.02)
        assert await backend.get("k1") is None

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        backend = MemoryCacheBackend(max_size=3, default_ttl=None)
        await backend.set("a", b"1")
        await backend.set("b", b"2")
        await backend.set("c", b"3")
        await backend.set("d", b"4")  # should evict "a"
        assert await backend.get("a") is None
        assert await backend.get("b") == b"2"

    @pytest.mark.asyncio
    async def test_clear(self, backend):
        await backend.set("a", b"1")
        await backend.set("b", b"2")
        await backend.clear()
        assert await backend.get("a") is None
        assert await backend.get("b") is None

    @pytest.mark.asyncio
    async def test_get_many(self, backend):
        await backend.set("a", b"1")
        await backend.set("b", b"2")
        await backend.set("c", b"3")
        result = await backend.get_many(["a", "c", "z"])
        assert result["a"] == b"1"
        assert result["c"] == b"3"
        assert "z" not in result

    @pytest.mark.asyncio
    async def test_set_many(self, backend):
        await backend.set_many({"x": b"10", "y": b"20"})
        assert await backend.get("x") == b"10"
        assert await backend.get("y") == b"20"

    @pytest.mark.asyncio
    async def test_delete_many(self, backend):
        await backend.set("a", b"1")
        await backend.set("b", b"2")
        deleted = await backend.delete_many(["a", "b", "z"])
        assert deleted == 2


# ═════════════════════════════════════════════════════════════════════════
# Cache (high-level)
# ═════════════════════════════════════════════════════════════════════════

class TestCache:
    @pytest.fixture
    def cache(self):
        return Cache[str](MemoryCacheBackend(max_size=100))

    @pytest.mark.asyncio
    async def test_get_set_delete(self, cache):
        await cache.set("user:1", "Alice")
        assert await cache.get("user:1") == "Alice"
        await cache.delete("user:1")
        assert await cache.get("user:1") is None

    @pytest.mark.asyncio
    async def test_complex_types(self):
        cache = Cache[dict](MemoryCacheBackend())
        data = {"name": "Bob", "roles": ["admin", "user"]}
        await cache.set("user:2", data)
        result = await cache.get("user:2")
        assert result == data

    @pytest.mark.asyncio
    async def test_exists(self, cache):
        await cache.set("test", "ok")
        assert await cache.exists("test") is True
        assert await cache.exists("ghost") is False
        await cache.delete("test")
        assert await cache.exists("test") is False

    @pytest.mark.asyncio
    async def test_get_or_set_hit(self, cache):
        await cache.set("key", "cached")
        result = await cache.get_or_set("key", lambda: "fresh")
        assert result == "cached"

    @pytest.mark.asyncio
    async def test_get_or_set_miss(self, cache):
        calls = []
        result = await cache.get_or_set("key", lambda: calls.append(1) or "fresh")
        assert result == "fresh"
        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_get_or_set_force_refresh(self, cache):
        await cache.set("key", "old")
        result = await cache.get_or_set("key", lambda: "new", force_refresh=True)
        assert result == "new"

    @pytest.mark.asyncio
    async def test_get_or_default(self, cache):
        assert await cache.get_or_default("missing", "fallback") == "fallback"
        await cache.set("exists", "value")
        assert await cache.get_or_default("exists", "fallback") == "value"

    @pytest.mark.asyncio
    async def test_get_many(self, cache):
        await cache.set("a", "1")
        await cache.set("b", "2")
        result = await cache.get_many(["a", "b", "c"])
        assert result["a"] == "1"
        assert result["b"] == "2"
        assert result["c"] is None

    @pytest.mark.asyncio
    async def test_set_many(self, cache):
        await cache.set_many({"x": "10", "y": "20"})
        assert await cache.get("x") == "10"
        assert await cache.get("y") == "20"

    @pytest.mark.asyncio
    async def test_delete_many(self, cache):
        await cache.set("a", "1")
        await cache.set("b", "2")
        assert await cache.delete_many(["a", "b"]) == 2
        assert await cache.get("a") is None

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        await cache.set("a", "1")
        await cache.clear()
        assert await cache.get("a") is None

    @pytest.mark.asyncio
    async def test_stats_tracking(self, cache):
        await cache.get("miss1")
        await cache.get("miss2")
        await cache.set("hit", "data")
        await cache.get("hit")
        await cache.get("hit")
        await cache.delete("hit")
        s = cache.stats
        assert s.misses >= 2
        assert s.hits == 2
        assert s.sets == 1
        assert s.deletes == 1

    @pytest.mark.asyncio
    async def test_stat_snapshot(self, cache):
        s = cache.stats.snapshot()
        assert "hits" in s
        assert "misses" in s


# ═════════════════════════════════════════════════════════════════════════
# TieredCache
# ═════════════════════════════════════════════════════════════════════════

class TestTieredCache:
    @pytest.fixture
    def tcache(self):
        l1 = Cache[str](MemoryCacheBackend(max_size=100))
        l2 = Cache[str](MemoryCacheBackend(max_size=1000))
        return TieredCache[str](l1, l2)

    @pytest.mark.asyncio
    async def test_write_through(self, tcache):
        await tcache.set("k", "v")
        assert await tcache.l1.get("k") == "v"
        assert await tcache.l2.get("k") == "v"

    @pytest.mark.asyncio
    async def test_read_promote(self, tcache):
        await tcache.l2.set("k", "from_l2")
        result = await tcache.get("k")
        assert result == "from_l2"
        # L1 should now have it (promoted)
        assert await tcache.l1.get("k") == "from_l2"

    @pytest.mark.asyncio
    async def test_l1_hit_skips_l2(self, tcache):
        await tcache.l1.set("k", "l1_val")
        await tcache.l2.set("k", "l2_val")
        result = await tcache.get("k")
        assert result == "l1_val"

    @pytest.mark.asyncio
    async def test_delete_both(self, tcache):
        await tcache.set("k", "v")
        assert await tcache.delete("k") is True
        assert await tcache.l1.get("k") is None
        assert await tcache.l2.get("k") is None

    @pytest.mark.asyncio
    async def test_clear_both(self, tcache):
        await tcache.set("a", "1")
        await tcache.set("b", "2")
        await tcache.clear()
        assert await tcache.l1.get("a") is None
        assert await tcache.l2.get("b") is None


# ═════════════════════════════════════════════════════════════════════════
# @cached decorator
# ═════════════════════════════════════════════════════════════════════════

class TestCachedDecorator:
    @pytest.mark.asyncio
    async def test_caches_result(self):
        cache = Cache[int](MemoryCacheBackend())
        call_count = 0

        @cached(cache, key_prefix="test", ttl=60)
        async def expensive(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        r1 = await expensive(5)
        r2 = await expensive(5)
        assert r1 == 10
        assert r2 == 10
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_different_args_not_cached(self):
        cache = Cache[int](MemoryCacheBackend())
        call_count = 0

        @cached(cache)
        async def compute(x):
            nonlocal call_count
            call_count += 1
            return x + 1

        await compute(1)
        await compute(2)
        assert call_count == 2


# ═════════════════════════════════════════════════════════════════════════
# Serializer
# ═════════════════════════════════════════════════════════════════════════

class TestSerializers:
    def test_pickle_roundtrip(self):
        s = PickleSerializer()
        data = {"complex": [1, 2, 3], "nested": {"a": "b"}}
        assert s.loads(s.dumps(data)) == data

    def test_json_roundtrip(self):
        s = JSONSerializer()
        data = {"simple": "yes", "num": 42}
        result = s.loads(s.dumps(data))
        assert result["simple"] == "yes"
        assert result["num"] == 42


# ═════════════════════════════════════════════════════════════════════════
# Config
# ═════════════════════════════════════════════════════════════════════════

class TestCacheConfig:
    def test_defaults(self):
        cfg = CacheConfig()
        assert isinstance(cfg.serializer, PickleSerializer)
        assert cfg.key_prefix == ""
        assert cfg.hash_keys is False
        assert cfg.stampede_protection is True
