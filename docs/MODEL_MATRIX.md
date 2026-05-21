# Model Matrix

## Current Configuration

### Primary (Active)
- **Name:** qwen3-4b-hermes
- **Model:** qwen3-4b-hermes-64k:latest
- **Provider:** Ollama (local)
- **Parameters:** 4.0B (Hermes-finetuned)
- **Status:** ✅ Primary test target
- **Reasoning:** Specifically finetuned for function calling

### Candidates (Disabled by Default)

```python
# To enable, uncomment in harness/providers.py:
QWEN3_5_9B = ModelConfig(...)  # 9.7B parameter baseline
CLAUDE_HAIKU = ModelConfig(...)  # Cloud reference (excellent tool calling)
```

| Model | Params | Provider | Tool Calling | Notes |
|-------|--------|----------|--------------|-------|
| qwen3-4b-hermes | 4.0B | Ollama local | ✅ Hermes-finetuned | Primary |
| qwen3.5 | 9.7B | Ollama local | ⚠️ Plain (no finetuning) | Baseline |
| claude-haiku-4-5 | ? | Claude API | ✅ Excellent | Gold standard |

## Enabling Additional Models

### To test qwen3.5:

1. Edit `harness/providers.py`:
```python
MODEL_MATRIX = [
    QWEN3_4B_HERMES,
    QWEN3_5_9B,  # Uncomment
]
```

2. Download model (first run):
```bash
ssh $HERMES_SSH_HOST 'ollama pull qwen3.5:latest'
```

3. Run tests:
```bash
pytest tests/ --model-matrix -v
```

### To test Claude API:

1. Set API key:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

2. Edit `harness/providers.py`:
```python
MODEL_MATRIX = [
    QWEN3_4B_HERMES,
    CLAUDE_HAIKU,  # Uncomment
]
```

3. Run tests:
```bash
pytest tests/ --model-matrix -v
```

## Comparison Criteria

When testing multiple models, compare:

| Metric | How to Measure |
|--------|---|
| **Tool Invocation Rate** | % tests where tool_calls_detected > 0 |
| **Tool Selection Accuracy** | % tests where correct tool was chosen |
| **Side-Effect Success** | % tests where expected side effect occurred |
| **Response Latency** | Average elapsed_seconds per test |
| **Loop Safety** | 0 timeouts / total tests |
| **Overall Pass Rate** | % tests with side_effect_verified=True |

## Prior Results

### qwen3.5:latest (2026-05-14 validation)
- Tool invocation: ~50% (many text-only responses)
- Side-effect success: <50% (files not created, URLs not fetched)
- Loop safety: ⚠️ (browser_navigate infinite loop observed)
- **Verdict:** NOT READY for production

### qwen3-4b-hermes-64k (2026-05-20 — current)
- **Hypothesis:** Hermes finetuning should improve tool calling
- **Status:** UNTESTED (this test suite will validate)
- **Expected:** >80% tool invocation, >90% side-effect success

## Improvement Ideas

1. **Prompt engineering:** Better tool descriptions in system prompt
2. **Model selection:** Try qwen3.5-32b (larger base model with tuning)
3. **Context length:** Increase from 64k to 128k for complex chains
4. **Fine-tuning:** Create custom Hermes finetune on this tool set
