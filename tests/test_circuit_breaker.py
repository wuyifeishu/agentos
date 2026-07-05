"""Tests for agentos.tools.circuit_breaker."""

import time
import pytest
from agentos.tools.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
    CircuitRegistry,
    get_circuit_registry,
)


class TestCircuitBreaker:
    def test_normal_call(self):
        cb = CircuitBreaker()
        result = cb.call(lambda: 42)
        assert result == 42
        assert cb.state == CircuitState.CLOSED

    def test_call_with_args(self):
        cb = CircuitBreaker()
        result = cb.call(lambda x, y: x + y, 10, 20)
        assert result == 30

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker(failure_threshold=3)
        # Fail twice
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
            except RuntimeError:
                pass
        # Succeed
        cb.call(lambda: 1)
        assert cb._failure_count == 0

    def test_trip_on_failure_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        for i in range(3):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError(f"fail_{i}")))
            except RuntimeError:
                pass
        assert cb.state == CircuitState.OPEN

    def test_fast_fail_open(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=999)
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
            except RuntimeError:
                pass
        with pytest.raises(CircuitOpenError):
            cb.call(lambda: 42)

    def test_half_open_recovery(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.01, success_threshold=2)
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
            except RuntimeError:
                pass
        assert cb.state == CircuitState.OPEN
        time.sleep(0.02)  # wait for recovery
        # First call transitions to HALF_OPEN
        cb.call(lambda: "ok")
        cb.call(lambda: "ok")
        assert cb.state == CircuitState.CLOSED

    def test_half_open_fail_sends_back_to_open(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.01)
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
            except RuntimeError:
                pass
        time.sleep(0.02)
        # HALF_OPEN, then fail → back to OPEN
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass
        assert cb.state == CircuitState.OPEN

    def test_half_open_max_calls(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05, half_open_max_calls=2, success_threshold=10)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass
        time.sleep(0.1)
        cb.call(lambda: 1)
        cb.call(lambda: 2)
        with pytest.raises(CircuitOpenError):
            cb.call(lambda: 3)

    def test_reset(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=999)
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
            except RuntimeError:
                pass
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb._failure_count == 0

    def test_trip(self):
        cb = CircuitBreaker()
        cb.trip()
        assert cb.state == CircuitState.OPEN
        with pytest.raises(CircuitOpenError):
            cb.call(lambda: 42)

    def test_state_callback(self):
        states = []

        def on_change(cb, old, new):
            states.append((old, new))

        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=999, on_state_change=on_change)
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
            except RuntimeError:
                pass
        assert len(states) >= 1
        assert states[0] == (CircuitState.CLOSED, CircuitState.OPEN)

    def test_stats(self):
        cb = CircuitBreaker(failure_threshold=5)
        cb.call(lambda: 1)
        cb.call(lambda: 1)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass
        s = cb.stats
        assert s["total_calls"] == 3
        assert s["total_successes"] == 2
        assert s["total_failures"] == 1


class TestCircuitRegistry:
    def test_get_create(self):
        reg = CircuitRegistry()
        cb = reg.get("api", failure_threshold=3)
        assert cb.name == "api"
        assert cb.failure_threshold == 3

    def test_get_reuse(self):
        reg = CircuitRegistry()
        a = reg.get("x")
        b = reg.get("x")
        assert a is b

    def test_remove(self):
        reg = CircuitRegistry()
        reg.get("x")
        assert reg.remove("x") is True
        assert reg.remove("x") is False

    def test_list_breakers(self):
        reg = CircuitRegistry()
        reg.get("a")
        reg.get("b")
        lst = reg.list_breakers()
        assert "a" in lst
        assert "b" in lst

    def test_reset_all(self):
        reg = CircuitRegistry()
        cb = reg.get("a", failure_threshold=1)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass
        assert cb.state == CircuitState.OPEN
        reg.reset_all()
        assert cb.state == CircuitState.CLOSED


class TestGlobalRegistry:
    def test_singleton(self):
        r1 = get_circuit_registry()
        r2 = get_circuit_registry()
        assert r1 is r2
