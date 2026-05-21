"""LoopGuardMetric: Verifies the command completed without infinite loops.

Regression test for the catastrophic failure seen in prior validation:
browser_navigate being repeated 1000+ times, causing timeouts and stream failures.
"""

from deepeval.metrics import CustomMetric
from deepeval.test_case import LLMTestCase


class LoopGuardMetric(CustomMetric):
    """
    Verifies that a command completed within expected time (no infinite loops).

    Score: 1.0 if completed normally, 0.0 if timeout or excessive iterations.

    From prior validation (2026-05-14):
    "can you get me the first 4 headlines from https://news.ycomibnator.com..."
    → Model got stuck repeating browser_navigate 1000+ times
    → Stream dropped after 129 seconds with ReadTimeout
    → Response remained truncated after 3 continuation attempts

    This metric prevents similar failures in other models.
    """

    def __init__(self, max_elapsed_seconds: int = 30, max_tool_calls: int = 10):
        self.max_elapsed = max_elapsed_seconds
        self.max_tool_calls = max_tool_calls
        super().__init__(
            name="LoopGuard",
            threshold=0.5,
        )

    def measure(self, test_case: LLMTestCase) -> float:
        """
        Score based on completion time and tool call count.

        1.0 = completed quickly with reasonable tool calls
        0.0 = timeout or excessive calls (likely infinite loop)
        """
        # Check elapsed time
        elapsed = getattr(test_case, "elapsed_seconds", None)
        if elapsed is None and hasattr(test_case, "metadata"):
            elapsed = test_case.metadata.get("elapsed_seconds")

        # Check tool call count
        tool_calls = getattr(test_case, "tool_calls_detected", [])
        if not tool_calls and hasattr(test_case, "metadata"):
            tool_calls = test_case.metadata.get("tool_calls_detected", [])

        # Timeout indicator (test framework sets this)
        timed_out = getattr(test_case, "timed_out", False)
        if isinstance(test_case.metadata, dict):
            timed_out = test_case.metadata.get("timed_out", timed_out)

        if timed_out:
            return 0.0  # Immediate fail on timeout

        if elapsed and elapsed > self.max_elapsed:
            return 0.0  # Took too long

        if len(tool_calls) > self.max_tool_calls:
            return 0.0  # Too many tool calls (likely loop)

        return 1.0  # Completed normally

    def is_successful(self) -> bool:
        """Override: must complete without timeout or excessive calls."""
        return self.score >= 1.0
