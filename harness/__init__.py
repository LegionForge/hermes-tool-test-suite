"""Hermes Tool Test Suite Harness

Core components for running, verifying, and scoring Hermes tool invocations.
"""

from harness.backends import DockerSSHBackend, HermesBackend, InvokeResult
from harness.models import TestMetadata, ToolResult
from harness.runner import HermesRunner
from harness.verifier import SideEffectVerifier

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
