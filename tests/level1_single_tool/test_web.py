"""Level 1: Web tools tests (search and extraction).

Tests web_search and web_extract tools.
"""

import pytest
from harness.runner import HermesRunner
from harness.verifier import SideEffectVerifier


@pytest.mark.level1
@pytest.mark.slow
def test_web_search(hermes_runner: HermesRunner, verifier: SideEffectVerifier):
    """Test web_search tool.

    Note: Requires internet access. May fall back to DuckDuckGo if Tavily API not configured.
    """
    prompt = 'Search the web for "LegionForge GitHub" and return the first result URL.'

    result = hermes_runner.run(prompt, toolsets=["web"])

    # Basic checks
    assert result.success
    # Should mention GitHub or LegionForge
    assert "github" in result.response_text.lower() or "legionforge" in result.response_text.lower()


@pytest.mark.level1
@pytest.mark.slow
def test_web_extract(hermes_runner: HermesRunner, verifier: SideEffectVerifier):
    """Test web_extract tool.

    Fetches and converts a URL to markdown.
    """
    prompt = 'Go to https://www.wikipedia.org/ and extract the main heading text.'

    result = hermes_runner.run(prompt, toolsets=["web"])

    # Assertions
    assert result.success
    # Should mention Wikipedia or have some content from the page
    assert "wikipedia" in result.response_text.lower() or "free encyclopedia" in result.response_text.lower()
