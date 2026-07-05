"""Tests for agentos.tools.audit_logger."""

import json
import os
import tempfile
import pytest
from agentos.tools.audit_logger import AuditLogger, AuditEvent, Severity


class TestAuditEvent:
    def test_defaults(self):
        e = AuditEvent()
        assert e.actor == ""
        assert e.severity == Severity.INFO

    def test_to_dict(self):
        e = AuditEvent(
            actor="admin",
            action="user.delete",
            resource="user:42",
            outcome="success",
            severity=Severity.WARNING,
            details={"reason": "test"},
        )
        d = e.to_dict()
        assert d["actor"] == "admin"
        assert d["action"] == "user.delete"
        assert d["outcome"] == "success"
        assert d["severity"] == "WARNING"
        assert d["details"]["reason"] == "test"

    def test_from_dict(self):
        d = {
            "actor": "system",
            "action": "config.reload",
            "resource": "/etc/app.yaml",
            "outcome": "success",
            "severity": "INFO",
            "details": {"keys": 5},
        }
        e = AuditEvent.from_dict(d)
        assert e.actor == "system"
        assert e.action == "config.reload"
        assert e.severity == Severity.INFO


class TestAuditLogger:
    def test_log_and_count(self):
        audit = AuditLogger(capacity=100)
        audit.log(actor="u1", action="login", outcome="success")
        audit.log(actor="u1", action="view", resource="doc:1")
        assert audit.count == 2

    def test_recent(self):
        audit = AuditLogger(capacity=100)
        for i in range(10):
            audit.log(actor=f"user{i}", action="click")
        recent = audit.recent(3)
        assert len(recent) == 3
        assert recent[-1].actor == "user9"

    def test_query_by_actor(self):
        audit = AuditLogger()
        audit.log(actor="alice", action="login")
        audit.log(actor="bob", action="login")
        audit.log(actor="alice", action="logout")
        results = audit.query(actor="alice")
        assert len(results) == 2

    def test_query_by_action(self):
        audit = AuditLogger()
        audit.log(actor="a", action="login")
        audit.log(actor="b", action="view")
        audit.log(actor="c", action="login")
        results = audit.query(action="login")
        assert len(results) == 2

    def test_query_by_outcome(self):
        audit = AuditLogger()
        audit.log(actor="a", action="x", outcome="success")
        audit.log(actor="b", action="y", outcome="failure")
        results = audit.query(outcome="failure")
        assert len(results) == 1

    def test_query_by_severity(self):
        audit = AuditLogger()
        audit.log(severity=Severity.INFO)
        audit.log(severity=Severity.WARNING)
        audit.log(severity=Severity.ERROR)
        audit.log(severity=Severity.CRITICAL)
        results = audit.query(min_severity=Severity.ERROR)
        assert len(results) == 2

    def test_query_time_range(self):
        audit = AuditLogger()
        import time
        t0 = time.time()
        audit.log(actor="first")
        time.sleep(0.1)
        t1 = time.time()
        time.sleep(0.1)
        audit.log(actor="last")
        results = audit.query(since=t0, until=t1)
        assert len(results) == 1
        assert results[0].actor == "first"

    def test_query_limit(self):
        audit = AuditLogger()
        for i in range(10):
            audit.log(actor=f"u{i}")
        results = audit.query(limit=3)
        assert len(results) == 3
        # limit returns the last N
        assert results[-1].actor == "u9"

    def test_ring_buffer_eviction(self):
        audit = AuditLogger(capacity=5)
        for i in range(10):
            audit.log(actor=f"u{i}")
        assert audit.count == 5
        assert audit.recent(1)[0].actor == "u9"

    def test_export_json_to_string(self):
        audit = AuditLogger()
        audit.log(actor="admin", action="delete", outcome="success")
        s = audit.export_json()
        data = json.loads(s)
        assert len(data) == 1
        assert data[0]["actor"] == "admin"

    def test_export_json_to_file(self):
        audit = AuditLogger()
        audit.log(actor="s1", action="a1")
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            audit.export_json(path)
            data = json.loads(open(path).read())
            assert len(data) == 1
        finally:
            os.unlink(path)

    def test_subscribe(self):
        audit = AuditLogger()
        events = []

        def handler(e):
            events.append(e)

        audit.subscribe(handler)
        audit.log(actor="x", action="y")
        assert len(events) == 1
        assert events[0].actor == "x"

    def test_unsubscribe(self):
        audit = AuditLogger()
        events = []

        def handler(e):
            events.append(e)

        audit.subscribe(handler)
        audit.log(actor="first")
        assert len(events) == 1
        audit.unsubscribe(handler)
        audit.log(actor="second")
        assert len(events) == 1

    def test_subscriber_exception_does_not_break(self):
        audit = AuditLogger()
        events = []

        def bad_handler(e):
            raise RuntimeError("boom")

        def good_handler(e):
            events.append(e)

        audit.subscribe(bad_handler)
        audit.subscribe(good_handler)
        audit.log(actor="test")
        assert len(events) == 1

    def test_invalid_capacity(self):
        with pytest.raises(ValueError):
            AuditLogger(capacity=0)

    def test_severity_from_str(self):
        assert Severity.from_str("ERROR") == Severity.ERROR
        assert Severity.from_str("info") == Severity.INFO
        assert Severity.from_str("unknown") == Severity.INFO
