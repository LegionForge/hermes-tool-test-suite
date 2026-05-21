# Running Tests

## Quick Start

```bash
cd /path/to/hermes-tool-test-suite

# Install
pip install -e .

# Run all Level 1 tests
pytest tests/level1_single_tool/ -v
```

## Common Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific level
pytest tests/level1_single_tool/ -v
pytest tests/level2_tool_selection/ -v

# Run specific test
pytest tests/level1_single_tool/test_terminal.py::test_echo_with_timestamp -v

# Run and stop on first failure
pytest tests/ -x

# Run with timeout (30s per test)
pytest tests/ --timeout=30

# Run browser tests (slow, may take 10+ minutes)
pytest tests/level4_browser/ -v --timeout=60

# Run computer_use tests (opt-in)
pytest tests/level5_computer_use/ -v --computer-use

# Run model matrix comparison (uncomment models in harness/providers.py first)
pytest tests/level6_model_matrix/ -v --model-matrix
```

## Configuration

Edit `.env` for:
- `HERMES_SSH_HOST` — SSH destination
- `HERMES_MODEL` — Model to test
- `HERMES_TEST_TIMEOUT` — Default timeout (seconds)
- `HERMES_TOOL_RESTRICTIONS` — Enabled tools

## Interpreting Results

### PASS ✅
- Side effect verified (file exists, URL fetched, etc.)
- Response makes sense
- No timeouts or errors

### FAIL ❌
- Side effect missing despite text claiming success
- Tool didn't actually execute
- This is the critical case from prior validation

### SKIP ⏭️
- Test skipped (usually computer_use without --computer-use flag)
- Safe to ignore unless specifically targeting that test level

### XFAIL (Expected Fail)
- Known limitation documented
- Not a regression

## Reports

```bash
# Generate detailed HTML report
pytest tests/ -v --html=results/report.html --self-contained-html

# Generate with DeepEval metrics (if enabled)
pytest tests/ -v --deepeval-report
```

## Troubleshooting

### "SSH connection refused"
```bash
# Check SSH is available
ssh $HERMES_SSH_HOST 'docker ps'

# Check .env has correct host
grep HERMES_SSH_HOST .env
```

### "No such tool"
```bash
# Verify tool is enabled in Hermes
ssh $HERMES_SSH_HOST 'docker exec hermes-sandbox \
  /opt/hermes/.venv/bin/hermes tools list | grep file'
```

### "File not created (side effect missing)"
This is the #1 bug indicator. It means:
1. Model generated text that looks like a command
2. But tool didn't actually execute

Check:
```bash
# Is the file really missing?
ssh $HERMES_SSH_HOST 'ls -la /tmp/hermes-test-*.txt'

# Check container logs
ssh $HERMES_SSH_HOST 'docker logs hermes-sandbox --tail 20 | grep -i error'
```

### "Timeout after 120 seconds"
- Test ran too long (likely infinite loop)
- Decrease `HERMES_TEST_TIMEOUT` to catch faster
- Or increase timeout for known slow tests with `@pytest.mark.slow`

### "Tool loop infinite (browser navigation)"
- Regression of prior failure (infinite browser_navigate)
- Should be caught by `tests/level4_browser/test_loop_guard.py`
- If it happens, model may need reselection or prompt engineering
