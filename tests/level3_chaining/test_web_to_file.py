"""Level 3: Tool chaining - multi-step pipelines.

Tests that multiple tools can be chained: search → extract → save to file.
"""

import pytest
from harness.runner import HelmesRunner
from harness.verifier import SideEffectVerifier


@pytest.mark.level3
@pytest.mark.slow
def test_search_extract_save(hermes_runner: HermesRunner, verifier: SideEffectVerifier):
    """Test 5.1: Data pipeline - search, extract, save.

    Ported from HERMES-UAT-PROMPTS.md Level 5.1
    """
    output_path = "/tmp/hermes-test-5.1-result.txt"
    prompt = (
        '1. Search for "Python programming basics"\n'
        '2. Extract the first result\n'
        f'3. Save a summary to {output_path}\n'
        f'4. Show me the content of {output_path}'
    )

    result = hermes_runner.run(prompt, toolsets=["web", "file"])

    # Check execution
    assert result.success, f"Failed: {result.stderr}"

    # CRITICAL: Verify file actually exists on disk
    file_exists = verifier.file_exists(output_path)
    assert file_exists, f"File {output_path} was NOT created"

    # Verify it has content
    output = verifier.get_verification_output(f"cat {output_path}")
    assert len(output) > 0, "File is empty"


@pytest.mark.level3
def test_file_to_code_pipeline(hermes_runner: HermesRunner, verifier: SideEffectVerifier):
    """Test: Create file → read → process with code."""
    data_file = "/tmp/hermes-test-data.txt"
    result_file = "/tmp/hermes-test-result.txt"

    prompt = (
        f'1. Create {data_file} with content: "apple,5\\nbanana,3\\ncherry,8"\n'
        f'2. Read the file\n'
        f'3. Write Python code that parses it and calculates the total (5+3+8=16)\n'
        f'4. Save result to {result_file} as "TOTAL: 16"\n'
        f'5. Show the result file content'
    )

    result = hermes_runner.run(prompt, toolsets=["file", "code_execution"])

    assert result.success

    # Verify both files exist
    data_exists = verifier.file_exists(data_file)
    assert data_exists, f"Data file {data_file} not created"

    result_exists = verifier.file_exists(result_file)
    assert result_exists, f"Result file {result_file} not created"

    # Verify result content
    has_total = verifier.file_content_contains(result_file, "TOTAL: 16")
    assert has_total, "Result file doesn't contain expected total"
