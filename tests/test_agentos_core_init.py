"""Tests for agentos.core.__init__ — public API surface."""

import pytest


def test_core_init_imports():
    """Verify all exports from core.__init__ are importable."""
    from agentos.core import (
        Agent,
        RunContext,
        Depends,
        inject_tool,
        requires_context,
        Handoff,
        HandoffResult,
        transfer_to,
        can_handle,
        CodeAgent,
        CodeResult,
        CodeStep,
        AgentContext,
        ContextManager,
        CoreMessage,
        CoreToolCall,
        CoreToolResult,
        AgentStateMachine,
        AgentState,
        StateTransition,
        TransitionError,
        StateTimeoutError,
        StreamChunk,
        StreamEmitter,
        StreamEvent,
        ResponseCollector,
        Session,
        SessionStore,
        AsyncAgentLoop,
        AsyncLoopConfig,
        AsyncInvocationResult,
        AsyncContextManager,
    )
    # Spot checks
    assert Agent is not None
    assert RunContext is not None
    assert Session is not None
    assert ContextManager is not None


def test_core___all___consistency():
    """Verify __all__ matches actual exports."""
    from agentos import core as mod
    assert isinstance(mod.__all__, list)
    for name in mod.__all__:
        assert hasattr(mod, name), f"__all__ includes {name} but not importable"


def test_streaming_in_core():
    """Streaming types are accessible via core."""
    from agentos.core import StreamChunk, StreamEmitter, StreamEvent, ResponseCollector
    assert StreamEvent.TEXT is not None
