"""Level 1: Code execution tests.

Ported from HERMES-UAT-PROMPTS.md Level 4.
"""

import pytest
from harness.runner import HermesRunner


@pytest.mark.level1
def test_python_arithmetic(hermes_runner: HermesRunner):
    """Test 4.1: Python arithmetic calculation."""
    prompt = (
        'Write and execute Python code that:\n'
        '1. Calculates (42 * 17) + (100 / 4)\n'
        '2. Stores the result in a variable\n'
        '3. Prints "RESULT: <value>"\n'
        'Show me the output.'
    )

    result = hermes_runner.run(prompt, toolsets=["code_execution"])

    # Expected: (42 * 17) + (100 / 4) = 714 + 25 = 739
    assert result.success
    assert "739" in result.response_text, f"Expected 739 in output, got: {result.response_text}"


@pytest.mark.level1
def test_conditional_logic(hermes_runner: HermesRunner):
    """Test 4.2: Bash conditional logic."""
    test_path = "/tmp/hermes-test-2.1.txt"  # From previous test
    prompt = (
        f'Write a bash command that:\n'
        f'1. Checks if {test_path} exists\n'
        f'2. If it exists, echo "FILE_EXISTS"\n'
        f'3. If it doesn\'t exist, echo "FILE_MISSING"\n'
        f'Execute it and show the result.'
    )

    result = hermes_runner.run(prompt, toolsets=["code_execution"])

    # Should find the file from test_create_and_verify_file
    assert result.success
    # Either FILE_EXISTS or FILE_MISSING is acceptable (depends on test order)
    assert "FILE_EXISTS" in result.response_text or "FILE_MISSING" in result.response_text


@pytest.mark.level1
def test_loop_and_accumulation(hermes_runner: HermesRunner):
    """Test 4.3: Loop and accumulation."""
    prompt = (
        'Write Python code that:\n'
        '1. Creates a list of numbers: [1, 2, 3, 4, 5]\n'
        '2. Squares each number\n'
        '3. Prints each squared value on a new line with format "SQUARE_<n>: <result>"\n'
        'Execute and show all output.'
    )

    result = hermes_runner.run(prompt, toolsets=["code_execution"])

    # Assertions
    assert result.success
    assert "SQUARE_1: 1" in result.response_text
    assert "SQUARE_5: 25" in result.response_text
