"""Side-effect verification for Hermes tool invocations.

Critical: Tests must verify that tools actually execute, not just
that models generate text that looks like tool calls.
"""

import os
from typing import Optional
from harness.runner import HermesRunner


class SideEffectVerifier:
    """Verifies that tool side effects actually occurred."""

    def __init__(self, runner: HermesRunner, ssh_host: str = ""):
        self.runner = runner
        self.ssh_host = ssh_host

    def file_exists(self, path: str) -> bool:
        """Verify that a file was actually created."""
        cmd = f"test -f {path} && echo 'exists' || echo 'missing'"
        output = self.runner.get_verification_output(cmd)
        return "exists" in output.lower()

    def file_content_contains(self, path: str, text: str) -> bool:
        """Verify that a file contains expected text."""
        if not self.file_exists(path):
            return False
        cmd = f"grep -q '{self._escape_grep(text)}' {path} && echo 'found' || echo 'not_found'"
        output = self.runner.get_verification_output(cmd)
        return "found" in output.lower()

    def directory_exists(self, path: str) -> bool:
        """Verify that a directory was created."""
        cmd = f"test -d {path} && echo 'exists' || echo 'missing'"
        output = self.runner.get_verification_output(cmd)
        return "exists" in output.lower()

    def command_output_contains(self, command: str, text: str) -> bool:
        """Run a command and check if output contains text."""
        output = self.runner.get_verification_output(command)
        return text in output

    def file_count_in_directory(self, directory: str, pattern: str = "*") -> int:
        """Count files matching pattern in directory."""
        cmd = f"ls -1 {directory}/{pattern} 2>/dev/null | wc -l"
        output = self.runner.get_verification_output(cmd)
        try:
            return int(output.strip())
        except ValueError:
            return 0

    def screenshot_exists(self, screenshot_path: Optional[str] = None) -> bool:
        """Verify that a screenshot was captured (for computer_use tests)."""
        if screenshot_path is None:
            screenshot_path = "/tmp/hermes-screenshot-*.png"
        cmd = f"ls {screenshot_path} 2>/dev/null | wc -l"
        output = self.runner.get_verification_output(cmd)
        try:
            count = int(output.strip())
            return count > 0
        except ValueError:
            return False

    def url_response_contains(self, expected_text: str, response: str) -> bool:
        """
        Verify that a web_extract response contains expected content.
        The expected_text should NOT be in the original prompt.
        """
        return expected_text in response

    def no_infinite_loop(self, response: str, timeout_occurred: bool) -> bool:
        """
        Verify that a command didn't hit an infinite loop.
        Returns True if the response completed normally (timeout_occurred=False).
        """
        return not timeout_occurred

    @staticmethod
    def _escape_grep(text: str) -> str:
        """Escape text for safe use in grep."""
        # Basic escaping: just escape single quotes
        return text.replace("'", "'\\''")
