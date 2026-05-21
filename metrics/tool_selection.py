"""ToolSelectionMetric: Verifies the model chose the right tool."""

from deepeval.metrics import CustomMetric
from deepeval.test_case import LLMTestCase


class ToolSelectionMetric(CustomMetric):
    """
    Measures whether the model selected the correct tool for the task.

    Score: 1.0 if correct tool, 0.0 if wrong or no tool.

    Example: Given "What is the weather in NYC?" with tools [get_weather, web_search],
    score 1.0 only if get_weather was invoked.
    """

    def __init__(self, correct_tool: str, incorrect_tools: list[str] = None):
        self.correct_tool = correct_tool.lower()
        self.incorrect_tools = [t.lower() for t in (incorrect_tools or [])]
        super().__init__(
            name=f"ToolSelection({correct_tool})",
            threshold=0.5,
        )

    def measure(self, test_case: LLMTestCase) -> float:
        """Score based on which tool was actually invoked."""
        if not hasattr(test_case, "tool_calls_detected"):
            return 0.0

        tool_calls = [t.lower() for t in test_case.tool_calls_detected]
        if not tool_calls:
            return 0.0

        # Check if correct tool was used
        if self.correct_tool in tool_calls:
            # Bonus: penalize if wrong tools were also used
            wrong_tools_used = any(t in tool_calls for t in self.incorrect_tools)
            return 0.7 if wrong_tools_used else 1.0

        # Check if wrong tools were used (penalty)
        if any(t in tool_calls for t in self.incorrect_tools):
            return 0.0

        return 0.0

    def is_successful(self) -> bool:
        """Override: success requires correct tool selection."""
        return self.score >= 0.7
