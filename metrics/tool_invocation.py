"""ToolInvocationMetric: Verifies that a tool was actually invoked."""

from deepeval.metrics import CustomMetric  # type: ignore[attr-defined]
from deepeval.test_case import LLMTestCase


class ToolInvocationMetric(CustomMetric):
    """
    Measures whether a tool was actually invoked (not just text generation).

    Score: 1.0 if tool calls detected in logs, 0.0 if text-only response.

    This is the critical metric: prior validation showed models generating
    text like 'echo "test"' without actually executing the command.
    """

    def __init__(self, expected_tool: str):
        self.expected_tool = expected_tool
        super().__init__(
            name=f"ToolInvocation({expected_tool})",
            threshold=0.5,
        )

    def measure(self, test_case: LLMTestCase) -> float:
        """Score 1.0 if expected tool was invoked, 0.0 otherwise."""
        # tool_calls_detected is set by HermesRunner._detect_tool_calls()
        # It's passed via test_case.metadata
        if not hasattr(test_case, "tool_calls_detected"):
            return 0.0

        tool_calls = test_case.tool_calls_detected
        if not tool_calls:
            return 0.0

        # Check if expected tool is in the detected calls
        if self.expected_tool.lower() in [t.lower() for t in tool_calls]:
            return 1.0

        return 0.0

    def is_successful(self) -> bool:
        """Override: success if score >= 0.5."""
        return bool(self.score >= 0.5)
