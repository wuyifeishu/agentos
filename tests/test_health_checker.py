"""
Tests for agentos.core.health — async health check with component probes.
"""

import asyncio
import tempfile
import time

import pytest

from agentos.core.health import HealthChecker, HealthReport, ComponentHealth


class TestComponentHealth:
    def test_healthy(self):
        ch = ComponentHealth(name="db", status="healthy", latency_ms=1.23)
        assert ch.name == "db"
        assert ch.status == "healthy"
        assert ch.latency_ms == 1.23
        assert ch.error is None

    def test_unhealthy(self):
        ch = ComponentHealth(name="redis", status="unhealthy", latency_ms=3000, error="Timeout")
        assert ch.status == "unhealthy"
        assert ch.error == "Timeout"


class TestHealthReport:
    def test_report_creation(self):
        report = HealthReport(status="healthy", uptime_seconds=42.0)
        assert report.status == "healthy"
        assert report.uptime_seconds == 42.0
        assert report.components == {}
        assert isinstance(report.timestamp, float)


class TestHealthChecker:
    def test_disk_probe_healthy(self):
        checker = HealthChecker(start_time=time.time())
        report = asyncio.run(checker.check())
        assert report.status == "healthy"
        assert report.components["disk"].status == "healthy"
        assert report.components["disk"].latency_ms < 100

    def test_all_components_healthy(self):
        checker = HealthChecker(start_time=time.time())
        report = asyncio.run(checker.check())
        for name, comp in report.components.items():
            assert comp.status == "healthy", f"{name}: {comp.error}"

    def test_uptime_calculation(self):
        t0 = time.time() - 120  # 2 minutes ago
        checker = HealthChecker(start_time=t0)
        report = asyncio.run(checker.check())
        assert 115 < report.uptime_seconds < 130

    def test_no_db_no_redis(self):
        """No DB/Redis configured - should still pass with disk probe."""
        checker = HealthChecker(start_time=time.time())
        report = asyncio.run(checker.check())
        assert report.status == "healthy"
        assert "database" not in report.components
        assert "redis" not in report.components

    def test_probe_timeout_handling(self):
        """Probe with a function that times out should report unhealthy."""

        async def slow_fn():
            await asyncio.sleep(5)

        checker = HealthChecker(start_time=time.time())
        result = asyncio.run(
            checker._probe("slow", slow_fn, timeout=0.1)
        )
        assert result.status == "unhealthy"
        assert "Timeout" in result.error

    def test_probe_exception_handling(self):
        """Probe that raises should report unhealthy."""

        async def crash_fn():
            raise RuntimeError("connection refused")

        checker = HealthChecker(start_time=time.time())
        result = asyncio.run(
            checker._probe("crash", crash_fn, timeout=1.0)
        )
        assert result.status == "unhealthy"
        assert "connection refused" in result.error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
