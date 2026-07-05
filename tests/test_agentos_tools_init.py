"""Tests for agentos.tools.__init__ — public API surface."""

import pytest


def test_tools_init_imports():
    """Verify all exports from tools.__init__ are importable."""
    from agentos.tools import (
        FusionToolkit,
        FusionResult,
        ToolSpec,
        ToolRiskLevel,
        ToolRiskRating,
        get_risk_preset,
        infer_risk_level,
        BaseTool,
        PermissionLevel,
        BaseToolCall,
        BaseToolResult,
        ToolRegistry,
        ToolSchema,
        FCToolCall,
        FCToolResult,
        FCToolRegistry,
        OpenAPIToolGenerator,
        GeneratedTool,
        GrepTool,
        FileSearchTool,
        CodeSearchTool,
        JsonTool,
        CsvTool,
        HttpRequestTool,
        DownloadTool,
        ValidationSeverity,
        ValidationRule,
        ValidationIssue,
        ValidationResult,
        ToolOutputValidator,
        ToolErrorClassifier,
        validate_tool_output,
        classify_tool_error,
        base_tool_to_llm_tool,
        make_handler,
        bridge_registry_to_executor,
    )
    # Spot checks
    assert PermissionLevel.SAFE is not None
    assert ToolRiskLevel is not None
    assert BaseTool is not None


def test_tools___all___consistency():
    """Verify __all__ matches actual exports."""
    from agentos import tools as mod
    assert isinstance(mod.__all__, list)
    for name in mod.__all__:
        assert hasattr(mod, name), f"__all__ includes {name} but not importable"


def test_fusion_toolkit_import():
    from agentos.tools import FusionToolkit, FusionResult, ToolSpec
    assert FusionToolkit is not None
    assert FusionResult is not None
    assert ToolSpec is not None
