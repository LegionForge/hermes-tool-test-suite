# Phase 1: Test Suite Validation (Fast Iteration)

## Goal
Prove the test suite infrastructure works by running against fast models.

## Setup

### 1. Set API Keys (Choose One)

**Option A: OpenRouter (Recommended for quick tests)**
```bash
export OPENROUTER_API_KEY="sk-or-v1-<your-key>"
cd /path/to/hermes-tool-test-suite
```

**Option B: InceptionLabs (If you have account)**
```bash
export INCEPTIONLABS_API_KEY="sk_<your-key>"
# Then configure .env to use InceptionLabs provider (pending)
```

### 2. Verify Environment

```bash
echo "HERMES_PROVIDER: $(grep HERMES_PROVIDER .env)"
echo "HERMES_MODEL: $(grep HERMES_MODEL .env)"
echo "API Key loaded: $([ -n "$OPENROUTER_API_KEY" ] && echo YES || echo NO)"
```

### 3. Run Level 1 Tests (5-10 min total)

```bash
pytest tests/level1_single_tool/ -v --timeout=300
```

**Expected:** 8-10/10 PASS
- terminal tests ✅ (should all pass)
- file creation ✅ (CRITICAL — was failing 50% with qwen3.5)
- code execution ✅ (Python runs)
- web tests ⚠️ (depends on container network)

## What You're Validating

✅ **Test Infrastructure Works**
- Side-effect verification (files actually created, commands executed)
- Tool invocation detection (patterns match Hermes output)
- Error handling (tests fail gracefully on real failures)

✅ **Metrics Are Correct**
- ToolInvocationMetric (1.0 if tool called, 0.0 if text-only)
- ToolSelectionMetric (correct tool chosen)
- SideEffectMetric (CRITICAL — side effect actually happened)

✅ **Hermes Integration**
- SSH + Docker orchestration works
- Model/provider switching works
- Timeout handling correct

## After Phase 1 Passes

Once you see 8+/10 PASS:
1. Phase 1 ✅ — test suite is solid
2. Move to Phase 2 — benchmark qwen3-4b-hermes with timing data
3. Compare against other models using same test suite

## Troubleshooting

**Tests still timeout?**
- Increase `HERMES_TEST_TIMEOUT` in .env
- Check API key is correct: `echo $OPENROUTER_API_KEY | head -c 20`

**File creation test fails?**
- Most critical failure — indicates model not invoking file tool
- Check Hermes tool schemas match model expectations
- May indicate model swap is needed

**All tests fail?**
- Check Hermes container is running: `ssh $HERMES_SSH_HOST '/opt/homebrew/bin/docker ps'`
- Check logs: `ssh $HERMES_SSH_HOST '/opt/homebrew/bin/docker logs hermes-sandbox --tail 10'`
