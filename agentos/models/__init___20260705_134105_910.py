"""AgentOS Models — centralized Pydantic response/request/error/pagination models.

Provides type-safe, OpenAPI-compatible data models shared across the API layer,
client SDK, and internal components. All models follow REST best practices with
RFC 9457 Problem Details for errors.

v1.0: Response envelope, pagination, error model, health model.
"""

from __future__ import annotations

from agentos.models.response import (
    APIResponse,
    APIResponseMeta,
    APIErrorDetail,
    PaginationMeta,
    PaginatedResponse,
    HealthResponse,
    HealthComponent,
    VersionResponse,
)
from agentos.models.error import (
    ErrorCode,
    AgentOSError,
    ValidationError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    InternalError,
    ServiceUnavailableError,
)
from agentos.models.agent import (
    AgentRunRequest,
    AgentRunResponse,
    AgentStatus,
    AgentInfo,
    AgentListResponse,
)

__all__ = [
    # Response
    "APIResponse",
    "APIResponseMeta",
    "APIErrorDetail",
    "PaginationMeta",
    "PaginatedResponse",
    "HealthResponse",
    "HealthComponent",
    "VersionResponse",
    # Error
    "ErrorCode",
    "AgentOSError",
    "ValidationError",
    "NotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "InternalError",
    "ServiceUnavailableError",
    # Agent
    "AgentRunRequest",
    "AgentRunResponse",
    "AgentStatus",
    "AgentInfo",
    "AgentListResponse",
]
