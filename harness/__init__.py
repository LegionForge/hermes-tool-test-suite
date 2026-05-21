"""Hermes Tool Test Suite Harness

Core components for running, verifying, and scoring Hermes tool invocations.
"""

from harness.models import ToolResult, TestMetadata
from harness.runner import HermesRunner
from harness.verifier import SideEffectVerifier
from harness.backends import HermesBackend, InvokeResult, DockerSSHBackend

__all__ = [
    "ToolResult",
    "TestMetadata",
    "HermesRunner",
    "SideEffectVerifier",
    "HermesBackend",
    "InvokeResult",
    "DockerSSHBackend",
]

__version__ = "0.1.0"
