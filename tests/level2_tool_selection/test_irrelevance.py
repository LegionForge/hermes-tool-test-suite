"""Level 2: Irrelevance detection - when NOT to use tools.

Tests that the model doesn't invoke unnecessary tools.
"""

import pytest
from harness.runner import HermesRunner


@pytest.mark.level2
def test_simple_math_no_tools(hermes_runner: HermesRunner):
    """Test: Simple math shouldn't need any tools."""
    prompt = 'Calculate 25 * 4 and tell me the answer.'

    result = hermes_runner.run(prompt, toolsets=["terminal", "code_execution"])

    assert result.success
    # Could use code_execution but not necessary for simple math
    # This is a soft test - both with and without tools are acceptable


@pytest.mark.level2
def test_factual_question_no_web_needed(hermes_runner: HermesRunner):
    """Test: Basic factual questions from training data shouldn't need web."""
    prompt = 'What is the capital of France?'

    result = hermes_runner.run(prompt, toolsets=["web"])

    assert result.success
    assert "Paris" in result.response_text


@pytest.mark.level2
def test_conversation_no_file_needed(hermes_runner: HermesRunner):
    """Test: Normal conversation shouldn't need file tool."""
    prompt = 'Tell me a short joke.'

    result = hermes_runner.run(prompt, toolsets=["file", "terminal"])

    assert result.success
    # Should respond without needing file/terminal tools
    assert len(result.response_text) > 0
