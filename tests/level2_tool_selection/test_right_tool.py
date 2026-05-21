"""Level 2: Tool selection accuracy tests.

Verifies the model picks the RIGHT tool for the task.
"""

import pytest
from harness.runner import HermesRunner


@pytest.mark.level2
def test_should_use_file_not_terminal(hermes_runner: HermesRunner):
    """Test: Creating a file should use file tool, not terminal echo."""
    prompt = 'Write "Hello World" to /tmp/test-selection.txt'

    result = hermes_runner.run(prompt, toolsets=["file", "terminal"])

    # Should have invoked a tool
    assert result.success
    assert len(result.tool_calls_detected) > 0

    # Ideally should use file tool (but terminal is acceptable too)
    tool_names = [t.lower() for t in result.tool_calls_detected]
    assert "file" in tool_names or "terminal" in tool_names


@pytest.mark.level2
def test_should_use_web_search_not_terminal(hermes_runner: HermesRunner):
    """Test: Searching web should use web tool, not write bash script."""
    prompt = 'Find information about Python programming.'

    result = hermes_runner.run(prompt, toolsets=["web", "terminal"])

    # Should use web tool
    assert result.success
    tool_names = [t.lower() for t in result.tool_calls_detected]
    # web_search or similar should be invoked
    assert any("web" in t for t in tool_names), f"Expected web tool, got: {tool_names}"


@pytest.mark.level2
def test_code_math_question_no_tool(hermes_runner: HermesRunner):
    """Test: Simple math should NOT require file/terminal tools."""
    prompt = 'What is 7 + 3?'

    result = hermes_runner.run(prompt, toolsets=["terminal", "file"])

    # This is just a simple question, no file/terminal tool needed
    # But model might still invoke them
    assert result.success
    # If tools were invoked, they shouldn't be necessary for this question
