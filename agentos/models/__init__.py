"""AgentOS v1.2.8 — Models module: routing, resilience, and API contracts."""

from agentos.models.router import ModelRouter
from agentos.models.resilience import (
    CancellationSource,
    CancelledError,
    RetryConfig,
    CircuitBreaker,
    CircuitBreakerConfig,
    ResilienceConfig,
    ResilientCall,
    retry_with_backoff,
    with_timeout,
    with_fallback,
)
from agentos.models.routing_strategy import (
    RoutingStrategy,
    Complexity,
    Budget,
)

# v1.17.0: API contract models
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
    # Routing & Resilience
    "ModelRouter",
    "CancellationSource",
    "CancelledError",
    "RetryConfig",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "ResilienceConfig",
    "ResilientCall",
    "retry_with_backoff",
    "with_timeout",
    "with_fallback",
    "RoutingStrategy",
    "Complexity",
    "Budget",
    # API Contracts
    "APIResponse",
    "APIResponseMeta",
    "APIErrorDetail",
    "PaginationMeta",
    "PaginatedResponse",
    "HealthResponse",
    "HealthComponent",
    "VersionResponse",
    # Errors
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
