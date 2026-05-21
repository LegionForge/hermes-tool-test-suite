"""Level 4: Browser loop guard - regression test.

CRITICAL: Tests that the model doesn't get stuck in infinite browser_navigate loops.

From prior validation (2026-05-14):
User: "Can you get me the first 4 headlines from https://news.ycombinator.com..."
Result: ❌ CATASTROPHIC - browser_navigate repeated 1000+ times, max tokens hit, timeout
This test prevents similar failures.
"""

import pytest
from harness.runner import HermesRunner


@pytest.mark.level4
@pytest.mark.slow
def test_browser_no_infinite_loop(hermes_runner: HermesRunner):
    """REGRESSION: Browser navigation shouldn't loop infinitely.

    This is a soft test - we just verify it completes in reasonable time.
    """
    prompt = 'Navigate to https://www.example.com and tell me the main heading.'

    result = hermes_runner.run(prompt, toolsets=["browser"], timeout_seconds=30)

    # Should complete within timeout (30s)
    assert result.elapsed_seconds < 30, f"Took too long: {result.elapsed_seconds}s (infinite loop?)"

    # Tool should have been invoked
    assert len(result.tool_calls_detected) > 0

    # Should have gotten some content
    assert len(result.response_text) > 0


@pytest.mark.level4
@pytest.mark.slow
def test_browser_navigate(hermes_runner: HermesRunner):
    """Test basic browser navigation."""
    prompt = 'Go to https://www.google.com and tell me what you see.'

    result = hermes_runner.run(prompt, toolsets=["browser"])

    assert result.success
    # Should mention Google or web search
    assert "google" in result.response_text.lower() or "search" in result.response_text.lower()
