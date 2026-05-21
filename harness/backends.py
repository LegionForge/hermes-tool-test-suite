"""Pluggable backend strategies for invoking Hermes in different deployment contexts.

Each backend encapsulates how to reach Hermes (Docker container, bare-metal host,
or local process) and exposes a uniform interface for test infrastructure.

Usage (via conftest.py):
    Set HERMES_BACKEND=docker|baremetal-ssh|local in .env (default: docker).

To implement a new backend, subclass HermesBackend and implement the three
abstract methods: invoke(), run_shell(), and health_check().
"""

import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class InvokeResult:
    """Raw result from a backend invocation."""
    stdout: str
    stderr: str
    exit_code: int

    @property
    def success(self) -> bool:
        return self.exit_code == 0


class HermesBackend(ABC):
    """Strategy for invoking Hermes commands in different deployment contexts."""

    @abstractmethod
    def invoke(self, tool: str, prompt: str, **kwargs) -> InvokeResult:
        """Invoke a Hermes tool call and return the raw result.

        Args:
            tool: Comma-separated toolset(s) to enable, e.g. "terminal" or "file,terminal"
            prompt: The prompt to send to Hermes
            **kwargs: Optional overrides — model, provider, quiet (bool), timeout (int seconds)
        """
        ...

    @abstractmethod
    def run_shell(self, command: str) -> InvokeResult:
        """Run a raw shell command in the Hermes environment.

        For Docker: executes inside the container.
        For bare-metal SSH: executes on the remote host.
        For local: executes on the current machine.

        Used by fixtures (e.g. container_user) that need direct command output
        without going through the LLM.
        """
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Verify the backend is reachable and Hermes is available.

        Returns True if the environment is ready to accept test runs.
        Called once at session start; a False return causes pytest.exit().
        """
        ...


class DockerSSHBackend(HermesBackend):
    """Invoke Hermes inside a Docker container on a remote SSH host.

    Execution path:
        local machine → SSH → remote host → docker exec → hermes-sandbox container

    Required env var:
        HERMES_SSH_HOST         SSH destination, e.g. user@hostname

    Optional env vars (all have defaults):
        HERMES_CONTAINER_NAME   Container name (also accepts HERMES_CONTAINER)
                                default: hermes-sandbox
        HERMES_BINARY           Path to hermes binary inside the container
                                default: /opt/hermes/.venv/bin/hermes
        HERMES_DOCKER_BIN       Path to docker binary on the SSH host
                                default: /opt/homebrew/bin/docker  (macOS)
        HERMES_PROVIDER         Model provider, used for API key resolution
                                default: ollama
        HERMES_API_KEY          API key for cloud providers
        OPENROUTER_API_KEY      Fallback when HERMES_PROVIDER=openrouter
        INCEPTIONLABS_API_KEY   Fallback when HERMES_PROVIDER=inceptionlabs
    """

    def __init__(self) -> None:
        self.ssh_host: str = os.getenv("HERMES_SSH_HOST", "")
        # Accept both HERMES_CONTAINER_NAME (new) and HERMES_CONTAINER (legacy)
        self.container: str = (
            os.getenv("HERMES_CONTAINER_NAME")
            or os.getenv("HERMES_CONTAINER", "hermes-sandbox")
        )
        self.hermes_bin: str = os.getenv("HERMES_BINARY", "/opt/hermes/.venv/bin/hermes")
        # Default is the macOS Homebrew path; Linux installs typically have docker in PATH
        self.docker_bin: str = os.getenv("HERMES_DOCKER_BIN", "/opt/homebrew/bin/docker")

    def invoke(self, tool: str, prompt: str, **kwargs) -> InvokeResult:
        model: Optional[str] = kwargs.get("model")
        provider: Optional[str] = kwargs.get("provider")
        quiet: bool = kwargs.get("quiet", True)
        timeout: int = kwargs.get("timeout", 150)

        model_arg = f"-m {model}" if model else ""
        provider_arg = f"--provider {provider}" if provider else ""
        quiet_flag = "-Q" if quiet else ""
        escaped = prompt.replace('"', '\\"')

        hermes_cmd = " ".join(filter(None, [
            self.hermes_bin, "chat",
            f'-q "{escaped}"',
            f"-t {tool}",
            model_arg,
            provider_arg,
            quiet_flag,
        ]))

        api_key = self._resolve_api_key(provider)
        env_prefix = f"HERMES_API_KEY={api_key} " if api_key else ""

        ssh_cmd = [
            "ssh", self.ssh_host,
            f"{env_prefix}{self.docker_bin} exec {self.container} {hermes_cmd}",
        ]

        try:
            result = subprocess.run(
                ssh_cmd, capture_output=True, text=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            return InvokeResult(stdout="", stderr="timeout", exit_code=1)

        return InvokeResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
        )

    def run_shell(self, command: str) -> InvokeResult:
        """Run a command inside the container via docker exec over SSH."""
        ssh_cmd = [
            "ssh", self.ssh_host,
            f"{self.docker_bin} exec {self.container} {command}",
        ]
        try:
            result = subprocess.run(
                ssh_cmd, capture_output=True, text=True, timeout=15
            )
        except subprocess.TimeoutExpired:
            return InvokeResult(stdout="", stderr="timeout", exit_code=1)

        return InvokeResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
        )

    def health_check(self) -> bool:
        """Check SSH connectivity and that the container is in a running state."""
        if not self.ssh_host:
            return False
        try:
            # docker ps -q returns the container ID when running, empty when stopped/absent
            result = subprocess.run(
                [
                    "ssh", "-o", "ConnectTimeout=5", self.ssh_host,
                    f"{self.docker_bin} ps -q -f name={self.container}",
                ],
                capture_output=True, text=True, timeout=10,
            )
            return result.returncode == 0 and bool(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _resolve_api_key(self, provider: Optional[str] = None) -> str:
        """Resolve API key, falling back to provider-specific env vars."""
        key = os.getenv("HERMES_API_KEY", "")
        if not key:
            p = provider or os.getenv("HERMES_PROVIDER", "ollama")
            if p == "openrouter":
                key = os.getenv("OPENROUTER_API_KEY", "")
            elif p == "inceptionlabs":
                key = os.getenv("INCEPTIONLABS_API_KEY", "")
        return key


class BaremetalSSHBackend(HermesBackend):
    """Invoke Hermes running natively on a remote SSH host (no container).

    Execution path:
        local machine → SSH → remote host → hermes binary

    Required env vars:
        HERMES_SSH_HOST    SSH destination, e.g. user@hostname
        HERMES_BINARY      Path to hermes binary on the remote host

    Status: stub — contributions welcome. See docs/ADDING_TESTS.md for guidance.
    """

    def __init__(self) -> None:
        self.ssh_host: str = os.getenv("HERMES_SSH_HOST", "")
        self.hermes_bin: str = os.getenv("HERMES_BINARY", "hermes")

    def invoke(self, tool: str, prompt: str, **kwargs) -> InvokeResult:
        raise NotImplementedError(
            "BaremetalSSHBackend.invoke() is not yet implemented. "
            "Set HERMES_BACKEND=docker to use the Docker backend, "
            "or implement this method and submit a PR."
        )

    def run_shell(self, command: str) -> InvokeResult:
        raise NotImplementedError(
            "BaremetalSSHBackend.run_shell() is not yet implemented."
        )

    def health_check(self) -> bool:
        raise NotImplementedError(
            "BaremetalSSHBackend.health_check() is not yet implemented."
        )


class LocalBackend(HermesBackend):
    """Invoke Hermes running on the same machine as the test runner (no SSH).

    Execution path:
        test process → subprocess → hermes binary (local)

    Required env vars:
        HERMES_BINARY    Path to hermes binary (default: hermes, assumes it is in PATH)

    Status: stub — contributions welcome. See docs/ADDING_TESTS.md for guidance.
    """

    def __init__(self) -> None:
        self.hermes_bin: str = os.getenv("HERMES_BINARY", "hermes")

    def invoke(self, tool: str, prompt: str, **kwargs) -> InvokeResult:
        raise NotImplementedError(
            "LocalBackend.invoke() is not yet implemented. "
            "Set HERMES_BACKEND=docker to use the Docker backend, "
            "or implement this method and submit a PR."
        )

    def run_shell(self, command: str) -> InvokeResult:
        raise NotImplementedError(
            "LocalBackend.run_shell() is not yet implemented."
        )

    def health_check(self) -> bool:
        raise NotImplementedError(
            "LocalBackend.health_check() is not yet implemented."
        )
