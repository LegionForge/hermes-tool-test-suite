"""Hermes command runner via SSH and Docker."""

import os
import re
import subprocess
import time
from typing import Optional
from pathlib import Path
from harness.models import ToolResult, ModelConfig


class HermesRunner:
    """Orchestrates Hermes invocation via SSH → docker exec."""

    def __init__(
        self,
        ssh_host: str = "",
        container_name: str = "hermes-sandbox",
        timeout_seconds: int = 120,
    ):
        self.ssh_host = ssh_host
        self.container_name = container_name
        self.timeout_seconds = timeout_seconds

    def run(
        self,
        prompt: str,
        toolsets: list[str],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        quiet: bool = True,
    ) -> ToolResult:
        """
        Run a hermes chat prompt via SSH/Docker.

        Args:
            prompt: The prompt to send to Hermes
            toolsets: List of toolsets to enable (e.g., ["terminal", "file"])
            model: Model override (default: use container's configured model)
            provider: Provider override (e.g., "openrouter", "anthropic")
            quiet: Suppress non-essential output

        Returns:
            ToolResult with response, tool calls detected, timing info
        """
        # Build hermes command
        toolsets_str = ",".join(toolsets)
        model_arg = f"-m {model}" if model else ""
        provider_arg = f"--provider {provider}" if provider else ""
        quiet_flag = "-Q" if quiet else ""

        hermes_cmd = (
            f'/opt/hermes/.venv/bin/hermes chat '
            f'-q "{self._escape_prompt(prompt)}" '
            f'-t {toolsets_str} '
            f'{model_arg} {provider_arg} {quiet_flag}'
        ).strip()

        # Build full SSH command with environment variables (use full path to docker for macOS)
        # Support both HERMES_API_KEY and provider-specific keys (OPENROUTER_API_KEY, INCEPTIONLABS_API_KEY)
        api_key = os.getenv("HERMES_API_KEY", "")
        if not api_key:
            # Try provider-specific keys as fallback
            provider = os.getenv("HERMES_PROVIDER", "ollama")
            if provider == "openrouter":
                api_key = os.getenv("OPENROUTER_API_KEY", "")
            elif provider == "inceptionlabs":
                api_key = os.getenv("INCEPTIONLABS_API_KEY", "")
        env_prefix = f"HERMES_API_KEY={api_key} " if api_key else ""

        ssh_cmd = [
            "ssh",
            self.ssh_host,
            f"{env_prefix}/opt/homebrew/bin/docker exec {self.container_name} {hermes_cmd}",
        ]

        # Execute with subprocess timeout (higher than test timeout to let pytest handle it)
        start_time = time.time()
        subprocess_timeout = self.timeout_seconds + 30  # Give pytest 30s buffer
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=subprocess_timeout,
        )
        elapsed = time.time() - start_time

        # Parse response
        return ToolResult(
            response_text=result.stdout,
            exit_code=result.returncode,
            stderr=result.stderr,
            elapsed_seconds=elapsed,
            tool_calls_detected=self._detect_tool_calls(result.stdout),
        )

    def run_verification_command(self, command: str) -> bool:
        """
        Run a verification command on the remote host (not in container).
        Used to verify side effects (file exists, etc.)

        Args:
            command: Shell command to execute on the remote host

        Returns:
            True if command succeeded (exit code 0), False otherwise
        """
        ssh_cmd = ["ssh", self.ssh_host, command]
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0

    def get_verification_output(self, command: str) -> str:
        """Get output from a verification command."""
        ssh_cmd = ["ssh", self.ssh_host, command]
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()

    @staticmethod
    def _escape_prompt(prompt: str) -> str:
        """Escape prompt for shell safety."""
        # Replace double quotes with escaped quotes
        return prompt.replace('"', '\\"')

    @staticmethod
    def _detect_tool_calls(output: str) -> list[str]:
        """
        Detect tool invocations from Hermes output.

        Looks for patterns like:
        - "Messages: N tool calls" (meta indicator)
        - "💻 preparing <toolname>…" (emoji + text indicator)
        - "preparing terminal…", "preparing file…", etc.
        - Legacy: [TOOL: X], [tool_call: X], Using tool: X
        """
        patterns = [
            # Hermes emoji indicators: 💻 preparing terminal/file/etc
            r'💻\s+preparing\s+(\w+)',
            r'preparing\s+(\w+)…',
            # Meta indicator: "Messages: N tool calls"
            r'Messages:\s+\d+\s+user,\s+(\d+)\s+tool calls',
            # Legacy format support
            r'\[TOOL:\s*(\w+)\]',
            r'\[tool_call:\s*(\w+)',
            r'Using tool:\s*(\w+)',
            r'Invoking:\s*(\w+)',
        ]

        tools = set()
        for pattern in patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            # Skip numeric matches (from "N tool calls" pattern)
            for match in matches:
                if not match.isdigit():
                    tools.add(match)

        return sorted(list(tools))
