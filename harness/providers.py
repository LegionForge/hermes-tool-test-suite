"""Model provider configurations and matrix."""

import os
from harness.models import ModelConfig

_ollama_host = os.getenv("HERMES_OLLAMA_HOST", "localhost")

# Primary test target: Hermes-finetuned 4B model
QWEN3_4B_HERMES = ModelConfig(
    name="qwen3-4b-hermes",
    model="qwen3-4b-hermes-64k:latest",
    provider="ollama",
    host=_ollama_host,
    base_url="http://host.docker.internal:11434/v1",
)

# Baseline candidate: Plain qwen3.5 9.7B (for comparison)
QWEN3_5_9B = ModelConfig(
    name="qwen3.5-9b",
    model="qwen3.5:latest",
    provider="ollama",
    host=_ollama_host,
    base_url="http://host.docker.internal:11434/v1",
)

# Reference: Cloud provider (known excellent tool calling)
CLAUDE_HAIKU = ModelConfig(
    name="claude-haiku-4-5",
    model="claude-haiku-4-5-20251001",
    provider="claude-api",
    host="api.anthropic.com",
)

# Test matrix: models to compare
# Run with: pytest tests/level6_model_matrix/ --model-matrix
MODEL_MATRIX = [
    QWEN3_4B_HERMES,  # Primary
    # QWEN3_5_9B,      # Uncomment to include in matrix comparison
    # CLAUDE_HAIKU,    # Uncomment to include cloud baseline
]

# Single model for quick testing
DEFAULT_MODEL = QWEN3_4B_HERMES
