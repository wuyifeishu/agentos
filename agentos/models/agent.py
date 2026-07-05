"""AgentOS Agent Models — request/response types for agent lifecycle."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent run status."""
    IDLE = "idle"
    RUNNING = "running"
    WAITING_TOOL = "waiting_tool"
    WAITING_HUMAN = "waiting_human"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class AgentRunRequest(BaseModel):
    """Request to run an agent."""
    agent_name: str = Field(description="Agent identifier")
    input: str = Field(description="User input/message to the agent")
    model: Optional[str] = Field(
        default=None, description="Override the default model"
    )
    max_tokens: Optional[int] = Field(
        default=None, ge=1, le=128000, description="Max tokens for the response"
    )
    temperature: Optional[float] = Field(
        default=None, ge=0.0, le=2.0, description="Sampling temperature"
    )
    stream: bool = Field(default=False, description="Enable SSE streaming")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary metadata for tracing"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context injected into agent"
    )
    timeout_seconds: Optional[int] = Field(
        default=None, ge=1, le=3600, description="Max execution time in seconds"
    )


class AgentRunResponse(BaseModel):
    """Response from an agent run."""
    run_id: str = Field(description="Unique run identifier")
    agent_name: str
    status: AgentStatus
    output: Optional[str] = Field(default=None)
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    usage: Optional[Dict[str, int]] = Field(default=None)
    duration_ms: float = Field(default=0.0)
    error: Optional[str] = Field(default=None)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentInfo(BaseModel):
    """Static agent information."""
    name: str
    description: str = ""
    model: str = ""
    version: str = "1.0.0"
    tools: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentListResponse(BaseModel):
    """List of registered agents."""
    agents: List[AgentInfo] = Field(default_factory=list)
    total: int = 0
