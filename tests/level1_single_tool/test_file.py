"""Level 1: File tool invocation tests.

These tests verify that file operations (read, write) actually work.
Ported from HERMES-UAT-PROMPTS.md Level 2-3.
"""

import pytest
from harness.runner import HermesRunner
from harness.verifier import SideEffectVerifier


@pytest.mark.level1
def test_create_and_verify_file(hermes_runner: HermesRunner, verifier: SideEffectVerifier):
    """Test 2.1: Create file and verify it exists on disk.

    CRITICAL: This is the regression test from prior validation.
    Old behavior: Model generates 'echo "text" > /tmp/test.txt' but file not created.
    New behavior: File should actually exist after hermes chat completes.
    """
    # Use a path that Hermes won't treat as protected (/tmp/hermes-* is protected)
    test_path = "/tmp/htest_file_2_1.txt"
    prompt = (
        f'Create a file at {test_path} with the content "Test 2.1 - Sequential operations".\n'
        f'Then run: cat {test_path}\n'
        f'Show me both the creation confirmation and the file contents.'
    )

    result = hermes_runner.run(prompt, toolsets=["terminal", "file"])

    # Check tool was invoked
    assert result.success, f"Command failed: {result.stderr}"
    assert len(result.tool_calls_detected) > 0, "No tools invoked"

    # CRITICAL: Verify the file actually exists on disk
    file_exists = verifier.file_exists(test_path)
    assert file_exists, f"File {test_path} was NOT created (text generation only?)"

    # Verify content
    content_correct = verifier.file_content_contains(test_path, "Test 2.1")
    assert content_correct, "File content doesn't match"


@pytest.mark.level1
def test_file_listing(hermes_runner: HermesRunner, verifier: SideEffectVerifier):
    """Test 2.2: List and count files."""
    prompt = 'Execute: ls -1 /tmp/htest_* 2>/dev/null | wc -l\nTell me the count of test files.'

    result = hermes_runner.run(prompt, toolsets=["terminal"])

    # Assertions
    assert result.success
    # Should have at least one file from test_create_and_verify_file
    assert "0" not in result.response_text or "1" in result.response_text
