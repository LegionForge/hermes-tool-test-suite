"""Level 6: Cross-model comparison.

Parameterized tests that run against the model matrix.
Uncomment additional models in harness/providers.py to include them.

Run with: pytest tests/level6_model_matrix/ --model-matrix
"""

import pytest
from harness.providers import MODEL_MATRIX, DEFAULT_MODEL
from harness.runner import HermesRunner


@pytest.fixture(params=MODEL_MATRIX if hasattr(pytest, "model_matrix") else [DEFAULT_MODEL])
def model_config(request):
    """Parameterize tests across all configured models."""
    return request.param


@pytest.mark.level6
def test_simple_echo_all_models(model_config):
    """Test 1.1: Echo on all models.

    Currently configured model: DEFAULT_MODEL
    To test multiple models:
    1. Uncomment QWEN3_5_9B in harness/providers.py
    2. Add to MODEL_MATRIX list
    3. Run: pytest tests/level6_model_matrix/ --model-matrix
    """
    runner = HermesRunner()
    prompt = 'Echo the text: "MODEL_TEST_SUCCESS"'

    result = runner.run(prompt, toolsets=["terminal"])

    assert result.success
    assert "MODEL_TEST_SUCCESS" in result.response_text


@pytest.mark.level6
def test_tool_selection_all_models(model_config):
    """Test 2.1: Tool selection across models."""
    runner = HermesRunner()
    prompt = 'Write "test" to /tmp/model-test.txt'

    result = runner.run(prompt, toolsets=["file", "terminal"])

    assert result.success
    assert len(result.tool_calls_detected) > 0
