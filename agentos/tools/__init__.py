"""Tools module - Fusion toolkit, Risk rating, Base tools, Registry, Function Calling, Generator, Search, Data, HTTP"""

from agentos.tools.fusion import (
    FusionToolkit,
    FusionResult,
    ToolSpec,
)
from agentos.tools.risk import (
    ToolRiskLevel,
    ToolRiskRating,
    get_risk_preset,
    infer_risk_level,
)
from agentos.tools.base import (
    BaseTool,
    PermissionLevel,
    ToolCall as BaseToolCall,
    ToolResult as BaseToolResult,
)
from agentos.tools.registry import (
    ToolRegistry,
)
from agentos.tools.function_calling import (
    ToolSchema,
    ToolCall as FCToolCall,
    ToolResult as FCToolResult,
    ToolRegistry as FCToolRegistry,
)
from agentos.tools.generator import (
    OpenAPIToolGenerator,
    GeneratedTool,
)

# v1.5.3 - Tool ecosystem expansion
from agentos.tools.search_tools import (
    GrepTool,
    FileSearchTool,
    CodeSearchTool,
)
from agentos.tools.data_tools import (
    JsonTool,
    CsvTool,
)
from agentos.tools.http_tools import (
    HttpRequestTool,
    DownloadTool,
)

# v1.15.1 - Async tool execution optimization
from agentos.tools.async_executor import (
    ExecutionStatus,
    CircuitBreakerState,
    ExecutionMetrics,
    CircuitBreaker,
    AsyncToolExecutor,
    SmartRetryExecutor,
    execute_tool_with_retry,
    execute_tools_concurrently,
)

# v1.16.0 - Bridge: ToolRegistry ↔ ToolExecutor
from agentos.tools.bridge import (
    base_tool_to_llm_tool,
    make_handler,
    bridge_registry_to_executor,
)

# v1.15.0 - Tool output validation layer
from agentos.tools.validation import (
    ValidationSeverity,
    ValidationRule,
    ValidationIssue,
    ValidationResult,
    ToolOutputValidator,
    ToolErrorClassifier,
    validate_tool_output,
    classify_tool_error,
)

__all__ = [
    "FusionToolkit",
    "FusionResult",
    "ToolSpec",
    "ToolRiskLevel",
    "ToolRiskRating",
    "get_risk_preset",
    "infer_risk_level",
    "BaseTool",
    "PermissionLevel",
    "BaseToolCall",
    "BaseToolResult",
    "ToolRegistry",
    "ToolSchema",
    "FCToolCall",
    "FCToolResult",
    "FCToolRegistry",
    "OpenAPIToolGenerator",
    "GeneratedTool",
    # v1.5.3
    "GrepTool",
    "FileSearchTool",
    "CodeSearchTool",
    "JsonTool",
    "CsvTool",
    "HttpRequestTool",
    "DownloadTool",
    # v1.15.0
    "ValidationSeverity",
    "ValidationRule",
    "ValidationIssue",
    "ValidationResult",
    "ToolOutputValidator",
    "ToolErrorClassifier",
    "validate_tool_output",
    "classify_tool_error",
    # v1.16.0 - Bridge
    "base_tool_to_llm_tool",
    "make_handler",
    "bridge_registry_to_executor",
]
