"""Level 3: Complex data pipelines with validation."""

import pytest
from harness.runner import HermesRunner
from harness.verifier import SideEffectVerifier


@pytest.mark.level3
def test_env_to_file_pipeline(hermes_runner: HermesRunner, verifier: SideEffectVerifier, container_user: str):
    """Test 5.2: Capture environment info, write file, process."""
    env_file = "/tmp/hermes-test-5.2-env.txt"
    prompt = (
        f'1. Get current date/time and user\n'
        f'2. Create {env_file} with format:\n'
        f'   timestamp: <date+time>\n'
        f'   user: <username>\n'
        f'3. Read the file\n'
        f'4. Print "Environment snapshot created at <timestamp> by <user>"\n'
        f'5. Show all output'
    )

    result = hermes_runner.run(prompt, toolsets=["file", "code_execution", "terminal"])

    assert result.success
    assert "timestamp" in result.response_text.lower()
    assert container_user in result.response_text.lower() or "user" in result.response_text.lower()
    assert verifier.file_exists(env_file)
