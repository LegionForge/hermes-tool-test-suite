"""Level 1: Basic terminal tool invocation tests.

These tests verify that simple shell commands actually execute.
Ported from HERMES-UAT-PROMPTS.md Level 1.
"""

import re
import pytest
from harness.runner import HermesRunner
from harness.verifier import SideEffectVerifier


@pytest.mark.level1
def test_echo_with_timestamp(hermes_runner: HermesRunner, verifier: SideEffectVerifier):
    """Test 1.1: Run echo command and return output."""
    prompt = 'Run this exact command and return only the output: echo "LEVEL1.1_TEST_$(date +%s)"'

    result = hermes_runner.run(prompt, toolsets=["terminal"])

    # Assertions
    assert result.success, f"Command failed with exit code {result.exit_code}"
    assert "LEVEL1.1_TEST_" in result.response_text
    assert len(result.tool_calls_detected) > 0, "No tool calls detected (text generation only?)"


@pytest.mark.level1
def test_pwd_current_directory(hermes_runner: HermesRunner, verifier: SideEffectVerifier):
    """Test 1.2: Get current working directory."""
    prompt = 'Execute: pwd\nShow me the full output.'

    result = hermes_runner.run(prompt, toolsets=["terminal"])

    assert result.success
    assert re.search(r'/\S+', result.response_text), \
        f"Expected absolute path in pwd response, got: {result.response_text!r}"


@pytest.mark.level1
def test_whoami_username(hermes_runner: HermesRunner, verifier: SideEffectVerifier, container_user: str):
    """Test 1.3: Get current username/UID."""
    prompt = 'Run: whoami\nTell me the exact output.'

    result = hermes_runner.run(prompt, toolsets=["terminal"])

    assert result.success
    assert container_user in result.response_text.lower(), \
        f"Expected container user '{container_user}' in response, got: {result.response_text!r}"
