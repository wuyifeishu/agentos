"""Tests for agentos.tools.registry."""

import asyncio
import pytest
from agentos.tools.registry import ToolRegistry
from agentos.tools.base import BaseTool, ToolCall, ToolResult


class EchoTool(BaseTool):
    """A simple tool that echoes its input."""
    name = "echo"
    description = "Echo input"

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, arguments: dict, sandbox=None) -> ToolResult:
        return ToolResult(call_id=arguments.get("call_id", "x"), output=arguments)


class FailTool(BaseTool):
    """A tool that always fails."""
    name = "fail"
    description = "Always fails"

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, arguments: dict, sandbox=None) -> ToolResult:
        raise RuntimeError("I always fail")


class TestToolRegistry:
    def test_register_and_get(self):
        reg = ToolRegistry()
        tool = EchoTool()
        reg.register(tool)
        assert reg.get("echo") is tool

    def test_get_missing_returns_none(self):
        reg = ToolRegistry()
        assert reg.get("nope") is None

    def test_register_many(self):
        reg = ToolRegistry()
        reg.register_many([EchoTool(), FailTool()])
        assert set(reg.list_names()) == {"echo", "fail"}

    def test_list_names_empty(self):
        reg = ToolRegistry()
        assert reg.list_names() == []

    def test_list_names(self):
        reg = ToolRegistry()
        reg.register(EchoTool())
        assert reg.list_names() == ["echo"]

    def test_get_schemas_for_model_openai(self):
        reg = ToolRegistry()
        reg.register(EchoTool())
        schemas = reg.get_schemas_for_model("openai")
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "echo"

    def test_get_schemas_for_model_anthropic(self):
        reg = ToolRegistry()
        reg.register(EchoTool())
        schemas = reg.get_schemas_for_model("anthropic")
        assert len(schemas) == 1
        assert "name" in schemas[0]

    def test_get_schemas_unknown_falls_back(self):
        reg = ToolRegistry()
        reg.register(EchoTool())
        schemas = reg.get_schemas_for_model("unknown_model")
        assert len(schemas) == 1

    def test_make_call_id(self):
        cid = ToolRegistry.make_call_id()
        assert cid.startswith("call_")
        assert len(cid) > 6

    @pytest.mark.asyncio
    async def test_execute_batch_success(self):
        reg = ToolRegistry()
        reg.register(EchoTool())
        calls = [ToolCall(name="echo", arguments={"msg": "hello"}, id="c1")]
        results = await reg.execute_batch(calls)
        assert len(results) == 1
        assert results[0].output == {"msg": "hello"}

    @pytest.mark.asyncio
    async def test_execute_batch_unknown_tool(self):
        reg = ToolRegistry()
        calls = [ToolCall(name="nonexistent", arguments={}, id="c1")]
        results = await reg.execute_batch(calls)
        assert len(results) == 1
        assert "Unknown tool" in results[0].error
        assert "nonexistent" in results[0].error

    @pytest.mark.asyncio
    async def test_execute_batch_mixed(self):
        reg = ToolRegistry()
        reg.register(FailTool())
        calls = [ToolCall(name="fail", arguments={}, id="c1")]
        results = await reg.execute_batch(calls)
        assert len(results) == 1
        assert "I always fail" in results[0].error

    @pytest.mark.asyncio
    async def test_execute_batch_parallel(self):
        reg = ToolRegistry()
        reg.register(EchoTool())
        calls = [
            ToolCall(name="echo", arguments={"i": i}, id=f"c{i}")
            for i in range(5)
        ]
        results = await reg.execute_batch(calls)
        assert len(results) == 5
        for i, r in enumerate(results):
            assert r.output == {"i": i}
