"""Level 5: Computer Use - Screenshot capture (safest operation).

⚠️ OPT-IN GATED: Requires --computer-use flag.
This controls Dylan's Mac Mini desktop.
"""

import pytest
from harness.runner import HermesRunner
from harness.verifier import SideEffectVerifier


@pytest.mark.level5
@pytest.mark.requires_computer_use
def test_screenshot_capture(hermes_runner: HermesRunner, verifier: SideEffectVerifier):
    """Test: Take a screenshot of Dylan's Mac desktop.

    This is the safest computer_use operation: read-only, no modification.
    """
    prompt = 'Take a screenshot of the current desktop and describe what you see.'

    result = hermes_runner.run(
        prompt,
        toolsets=["computer_use"],
        timeout_seconds=10,
    )

    # Should complete successfully
    assert result.success, f"Screenshot failed: {result.stderr}"

    # Should have response content
    assert len(result.response_text) > 0

    # Optional: verify screenshot file was created
    # (location depends on computer_use implementation)
    # screenshot_exists = verifier.screenshot_exists()
    # assert screenshot_exists, "Screenshot file not found"
