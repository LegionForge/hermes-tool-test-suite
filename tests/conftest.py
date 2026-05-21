"""Pytest configuration and fixtures for Hermes tool testing."""

import os
import pytest
from dotenv import load_dotenv
from harness.runner import HermesRunner
from harness.verifier import SideEffectVerifier
from harness.backends import DockerSSHBackend, BaremetalSSHBackend, LocalBackend, HermesBackend


# Load environment variables from .env
load_dotenv()


_BACKENDS = {
    "docker": DockerSSHBackend,
    "baremetal-ssh": BaremetalSSHBackend,
    "local": LocalBackend,
}


@pytest.fixture(scope="session")
def backend() -> HermesBackend:
    """Select and health-check the active Hermes backend.

    Controlled by HERMES_BACKEND env var (default: docker).
    Aborts the session immediately if the backend is unreachable.
    """
    backend_type = os.getenv("HERMES_BACKEND", "docker")
    cls = _BACKENDS.get(backend_type)
    if cls is None:
        pytest.exit(
            f"Unknown HERMES_BACKEND={backend_type!r}. "
            f"Valid options: {list(_BACKENDS)}"
        )
    b = cls()
    if not b.health_check():
        pytest.exit(
            f"Backend {backend_type!r} health check failed — "
            "is Hermes running and HERMES_SSH_HOST set?"
        )
    return b


@pytest.fixture(scope="session")
def container_user(backend: HermesBackend) -> str:
    """Resolve the actual username inside the Hermes environment at session start.

    Uses the backend's run_shell() to avoid going through the LLM.
    """
    result = backend.run_shell("whoami")
    username = result.stdout.strip()
    if not username:
        pytest.skip(
            "Could not resolve container username — "
            "is HERMES_SSH_HOST set and the container running?"
        )
    return username


# ── Legacy fixtures ─────────────────────────────────────────────────────────
# Kept for backward compatibility: existing tests receive hermes_runner directly.

@pytest.fixture(scope="session")
def hermes_ssh_host():
    """Get Hermes SSH host from environment."""
    host = os.getenv("HERMES_SSH_HOST", "")
    if not host:
        pytest.skip("HERMES_SSH_HOST not set — copy .env.example to .env and configure")
    return host


@pytest.fixture(scope="session")
def hermes_runner(hermes_ssh_host):
    """Create a HermesRunner instance for the test session."""
    return HermesRunner(
        ssh_host=hermes_ssh_host,
        container_name=os.getenv("HERMES_CONTAINER", "hermes-sandbox"),
        timeout_seconds=int(os.getenv("HERMES_TEST_TIMEOUT", "120")),
    )


@pytest.fixture
def verifier(hermes_runner, hermes_ssh_host):
    """Create a SideEffectVerifier instance for the test."""
    return SideEffectVerifier(hermes_runner, ssh_host=hermes_ssh_host)


def pytest_addoption(parser):
    """Add custom command-line options."""
    parser.addoption(
        "--computer-use",
        action="store_true",
        default=False,
        help="Enable computer_use tests (requires explicit opt-in for host desktop access)",
    )
    parser.addoption(
        "--model-matrix",
        action="store_true",
        default=False,
        help="Run tests across all models in the matrix (qwen3-4b-hermes, qwen3.5, claude)",
    )
    parser.addoption(
        "--deepeval-report",
        action="store_true",
        default=False,
        help="Generate DeepEval HTML report after tests",
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on command-line options."""
    # Skip computer_use tests unless --computer-use is passed
    if not config.getoption("--computer-use"):
        skip_marker = pytest.mark.skip(reason="computer_use tests require --computer-use flag")
        for item in items:
            if "level5_computer_use" in str(item.fspath):
                item.add_marker(skip_marker)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    markers = [
        "level1: Basic single-tool invocation tests",
        "level2: Tool selection accuracy tests",
        "level3: Tool chaining and pipelines",
        "level4: Browser automation tests",
        "level5: Host machine control (computer_use)",
        "slow: Tests that take >10 seconds",
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)
