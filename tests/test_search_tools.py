"""Tests for agentos.tools.search_tools — GrepTool, FileSearchTool, CodeSearchTool."""

import os
import tempfile

import pytest
from agentos.tools.search_tools import GrepTool, FileSearchTool, CodeSearchTool


# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def grep_tool():
    return GrepTool()


@pytest.fixture
def file_search_tool():
    return FileSearchTool()


@pytest.fixture
def code_search_tool():
    return CodeSearchTool()


@pytest.fixture
def search_fixture_dir():
    """Create a directory structure with various files for search tests."""
    path = tempfile.mkdtemp()
    # Subdir with Python files
    subdir = os.path.join(path, "src")
    os.makedirs(subdir, exist_ok=True)
    with open(os.path.join(subdir, "main.py"), "w") as f:
        f.write("import os\nimport sys\n\ndef hello():\n    return 'hello world'\n\nclass App:\n    pass\n")
    with open(os.path.join(subdir, "utils.py"), "w") as f:
        f.write("def add(a, b):\n    return a + b\n\ndef greet(name):\n    return f'Hello, {name}'\n")
    # Non-Python file
    with open(os.path.join(path, "readme.txt"), "w") as f:
        f.write("This is a readme file.\nIt documents the project.\nsearchable content here.\n")
    yield path
    import shutil
    shutil.rmtree(path, ignore_errors=True)


# ── GrepTool Tests ─────────────────────────────────────────

class TestGrepTool:
    def test_parameters_schema(self, grep_tool):
        params = grep_tool.parameters
        assert params["type"] == "object"
        assert "pattern" in params["properties"]
        assert "pattern" in params["required"]

    def test_name_and_description(self, grep_tool):
        assert grep_tool.name == "grep"
        assert len(grep_tool.description) > 0

    @pytest.mark.asyncio
    async def test_grep_finds_text(self, grep_tool, search_fixture_dir):
        result = await grep_tool.execute({"pattern": "hello", "directory": search_fixture_dir})
        assert result.error is None
        assert "hello" in result.output.lower()

    @pytest.mark.asyncio
    async def test_grep_regex(self, grep_tool, search_fixture_dir):
        result = await grep_tool.execute({"pattern": "def\\s+\\w+", "directory": search_fixture_dir})
        assert result.error is None
        assert "def hello" in result.output or "def add" in result.output

    @pytest.mark.asyncio
    async def test_grep_file_pattern_filter(self, grep_tool, search_fixture_dir):
        result = await grep_tool.execute({
            "pattern": "hello",
            "directory": search_fixture_dir,
            "file_pattern": "*.py",
        })
        assert result.error is None

    @pytest.mark.asyncio
    async def test_grep_txt_only(self, grep_tool, search_fixture_dir):
        result = await grep_tool.execute({
            "pattern": "readme",
            "directory": search_fixture_dir,
            "file_pattern": "*.txt",
        })
        assert result.error is None
        assert "readme" in result.output.lower()

    @pytest.mark.asyncio
    async def test_grep_no_match(self, grep_tool, search_fixture_dir):
        result = await grep_tool.execute({
            "pattern": "xyznonexistentzzz",
            "directory": search_fixture_dir,
        })
        assert result.error is None
        assert "No matches found" in result.output

    @pytest.mark.asyncio
    async def test_grep_case_insensitive(self, grep_tool, search_fixture_dir):
        result = await grep_tool.execute({
            "pattern": "HELLO",
            "directory": search_fixture_dir,
            "case_sensitive": False,
        })
        assert result.error is None
        assert "hello" in result.output.lower()

    @pytest.mark.asyncio
    async def test_grep_case_sensitive_no_match(self, grep_tool, search_fixture_dir):
        result = await grep_tool.execute({
            "pattern": "HELLO",
            "directory": search_fixture_dir,
            "case_sensitive": True,
        })
        assert result.error is None
        assert "No matches found" in result.output

    @pytest.mark.asyncio
    async def test_grep_invalid_regex(self, grep_tool, search_fixture_dir):
        result = await grep_tool.execute({
            "pattern": "[invalid(regex",
            "directory": search_fixture_dir,
        })
        assert result.error is not None
        assert "Invalid regex" in result.error

    @pytest.mark.asyncio
    async def test_grep_max_results_limit(self, grep_tool, search_fixture_dir):
        result = await grep_tool.execute({
            "pattern": ".",
            "directory": search_fixture_dir,
            "max_results": 2,
        })
        assert result.error is None
        lines = result.output.strip().split("\n")
        assert len(lines) <= 2

    @pytest.mark.asyncio
    async def test_grep_default_directory(self, grep_tool, search_fixture_dir):
        result = await grep_tool.execute({"pattern": "hello", "directory": "."})
        # Should not crash; directory may or may not have matches
        assert result.error is None


# ── FileSearchTool Tests ───────────────────────────────────

class TestFileSearchTool:
    def test_parameters_schema(self, file_search_tool):
        params = file_search_tool.parameters
        assert params["type"] == "object"
        assert "pattern" in params["properties"]
        assert "pattern" in params["required"]

    def test_name_and_description(self, file_search_tool):
        assert file_search_tool.name == "file_search"
        assert len(file_search_tool.description) > 0

    @pytest.mark.asyncio
    async def test_find_python_files(self, file_search_tool, search_fixture_dir):
        result = await file_search_tool.execute({
            "pattern": "*.py",
            "directory": search_fixture_dir,
        })
        assert result.error is None
        assert "main.py" in result.output
        assert "utils.py" in result.output

    @pytest.mark.asyncio
    async def test_find_txt_files(self, file_search_tool, search_fixture_dir):
        result = await file_search_tool.execute({
            "pattern": "*.txt",
            "directory": search_fixture_dir,
        })
        assert result.error is None
        assert "readme.txt" in result.output

    @pytest.mark.asyncio
    async def test_find_specific_file(self, file_search_tool, search_fixture_dir):
        result = await file_search_tool.execute({
            "pattern": "main.py",
            "directory": search_fixture_dir,
        })
        assert result.error is None
        assert "main.py" in result.output

    @pytest.mark.asyncio
    async def test_no_match(self, file_search_tool, search_fixture_dir):
        result = await file_search_tool.execute({
            "pattern": "*.xyzabc",
            "directory": search_fixture_dir,
        })
        assert result.error is None
        assert "No files found" in result.output

    @pytest.mark.asyncio
    async def test_max_results_limit(self, file_search_tool, search_fixture_dir):
        result = await file_search_tool.execute({
            "pattern": "*",
            "directory": search_fixture_dir,
            "max_results": 2,
        })
        assert result.error is None
        lines = [l for l in result.output.strip().split("\n") if l]
        assert len(lines) <= 2

    @pytest.mark.asyncio
    async def test_default_directory(self, file_search_tool):
        result = await file_search_tool.execute({"pattern": "*.py", "directory": "."})
        assert result.error is None


# ── CodeSearchTool Tests ───────────────────────────────────

class TestCodeSearchTool:
    def test_parameters_schema(self, code_search_tool):
        params = code_search_tool.parameters
        assert params["type"] == "object"
        assert "query" in params["properties"]
        assert "query" in params["required"]

    def test_name_and_description(self, code_search_tool):
        assert code_search_tool.name == "code_search"
        assert len(code_search_tool.description) > 0

    @pytest.mark.asyncio
    async def test_find_function(self, code_search_tool, search_fixture_dir):
        result = await code_search_tool.execute({
            "query": "hello",
            "directory": search_fixture_dir,
        })
        assert result.error is None
        assert "hello" in result.output

    @pytest.mark.asyncio
    async def test_find_function_with_type_filter(self, code_search_tool, search_fixture_dir):
        result = await code_search_tool.execute({
            "query": "add",
            "directory": search_fixture_dir,
            "symbol_type": "function",
        })
        assert result.error is None
        assert "add" in result.output

    @pytest.mark.asyncio
    async def test_find_class(self, code_search_tool, search_fixture_dir):
        result = await code_search_tool.execute({
            "query": "App",
            "directory": search_fixture_dir,
            "symbol_type": "class",
        })
        assert result.error is None
        assert "[class]" in result.output
        assert "App" in result.output

    @pytest.mark.asyncio
    async def test_find_import(self, code_search_tool, search_fixture_dir):
        result = await code_search_tool.execute({
            "query": "os",
            "directory": search_fixture_dir,
            "symbol_type": "import",
        })
        assert result.error is None
        assert "import" in result.output

    @pytest.mark.asyncio
    async def test_no_symbols_found(self, code_search_tool, search_fixture_dir):
        result = await code_search_tool.execute({
            "query": "nonexistentfunctionxyz",
            "directory": search_fixture_dir,
        })
        assert result.error is None
        assert "No symbols found" in result.output

    @pytest.mark.asyncio
    async def test_max_results_limit(self, code_search_tool, search_fixture_dir):
        result = await code_search_tool.execute({
            "query": "def",
            "directory": search_fixture_dir,
            "max_results": 1,
        })
        assert result.error is None
        lines = [l for l in result.output.strip().split("\n") if l]
        assert len(lines) <= 1

    @pytest.mark.asyncio
    async def test_case_insensitive_search(self, code_search_tool, search_fixture_dir):
        result = await code_search_tool.execute({
            "query": "HELLO",
            "directory": search_fixture_dir,
        })
        assert result.error is None
        assert "hello" in result.output

    @pytest.mark.asyncio
    async def test_async_function_detection(self, code_search_tool, search_fixture_dir):
        # Create a file with async function
        async_path = os.path.join(search_fixture_dir, "src", "async_util.py")
        with open(async_path, "w") as f:
            f.write("async def fetch_data():\n    return await something()\n")
        result = await code_search_tool.execute({
            "query": "fetch_data",
            "directory": search_fixture_dir,
        })
        assert result.error is None
        assert "fetch_data" in result.output

    @pytest.mark.asyncio
    async def test_syntax_error_file_skipped(self, code_search_tool):
        """Files with syntax errors should be skipped, not crash."""
        with tempfile.TemporaryDirectory() as td:
            bad_path = os.path.join(td, "bad.py")
            with open(bad_path, "w") as f:
                f.write("def broken(:\n    pass\n")
            result = await code_search_tool.execute({
                "query": "broken",
                "directory": td,
            })
            assert result.error is None
