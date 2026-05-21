"""SideEffectMetric: Verifies the expected side effect actually occurred."""

from deepeval.metrics import CustomMetric
from deepeval.test_case import LLMTestCase


class SideEffectMetric(CustomMetric):
    """
    The CRITICAL metric: does the actual side effect exist?

    Score: 1.0 if side effect verified, 0.0 if missing.

    This is the ultimate test of tool invocation. A model can generate
    perfect text, but if the file doesn't exist or URL wasn't fetched,
    the test fails.

    Example: "Write to /tmp/test.txt" → verify file exists with `ls`
    """

    def __init__(self, side_effect_verified: bool):
        self.side_effect_verified = side_effect_verified
        super().__init__(
            name="SideEffect",
            threshold=0.5,
        )

    def measure(self, test_case: LLMTestCase) -> float:
        """Score 1.0 if side effect verified, 0.0 otherwise."""
        # side_effect_verified is set by the test via fixture
        # It's passed via test_case.metadata["side_effect_verified"]
        if hasattr(test_case, "side_effect_verified"):
            return 1.0 if test_case.side_effect_verified else 0.0

        # Fallback: check metadata
        if hasattr(test_case, "metadata") and isinstance(test_case.metadata, dict):
            verified = test_case.metadata.get("side_effect_verified", False)
            return 1.0 if verified else 0.0

        return 0.0

    def is_successful(self) -> bool:
        """Override: absolute requirement for side effect."""
        return self.score >= 1.0
