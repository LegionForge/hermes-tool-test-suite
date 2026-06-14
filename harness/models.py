"""Data models for Hermes tool testing."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ToolResult:
    """Result of a single Hermes tool invocation."""

    response_text: str
    exit_code: int = 0
    elapsed_seconds: float = 0.0
    stderr: str = ""
    tool_calls_detected: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def success(self) -> bool:
        """True if command exited cleanly (exit_code == 0)."""
        return self.exit_code == 0

    @property
    def has_tools(self) -> bool:
        """True if any tool calls were detected in logs."""
        return bool(self.tool_calls_detected)


@dataclass
class TestMetadata:
    """Metadata for a test case."""

    name: str
    level: int  # 1-6, corresponding to test level
    description: str
    expected_tools: list[str]  # e.g., ["file", "terminal"]
    expected_side_effect: str  # e.g., "file_exists:/tmp/test.txt"
    timeout_seconds: int = 30
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate test metadata."""
        if not 1 <= self.level <= 6:
            raise ValueError(f"Level must be 1-6, got {self.level}")
        if not self.name:
            raise ValueError("Test name cannot be empty")


@dataclass
class ModelConfig:
    """Configuration for a model provider."""

    name: str  # e.g., "qwen3-4b-hermes"
    model: str  # e.g., "qwen3-4b-hermes-64k:latest"
    provider: str  # "ollama", "openrouter", "claude-api"
    host: str  # e.g., "localhost", "api.openrouter.ai", "api.anthropic.com"
    base_url: str | None = None  # For custom endpoints
    api_key: str | None = None  # For cloud providers

    @property
    def is_local(self) -> bool:
        """True if this is a local Ollama model."""
        return self.provider == "ollama"
