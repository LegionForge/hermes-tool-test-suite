# hermes-tool-test-suite

![Tests](https://img.shields.io/badge/Phase%201-8%2F10%20PASS-brightgreen) ![License](https://img.shields.io/badge/license-MIT-blue) ![Python](https://img.shields.io/badge/python-3.11+-blue)

A pytest-based tool-calling validation harness for [Hermes](https://github.com/NousResearch/hermes-agent) (by Nous Research), testing whether LLM agents correctly invoke tools rather than hallucinating answers. Tests run against a live Hermes instance in Docker via SSH.

## How It Works

```
local pytest ──SSH──▶ remote Docker host ──docker exec──▶ hermes-sandbox
     │                                                            │
     │                                               hermes chat -q "..." -t <tools>
     │                                                            │
     └──── side-effect verification ◀────────── SSH ─────────────┘
```

Tests send prompts to Hermes and verify that tools *actually executed* — not just that the model generated text resembling a tool call. A file test checks the file exists on disk. A web test checks the response contains content not present in the original prompt.

## Test Levels

**Level 1 — Single Tool Invocation** *(implemented)*
- Terminal: `echo`, `pwd`, `whoami`
- File I/O: create, read, list
- Code execution: Python arithmetic, loops, conditionals
- Web: search, extract

**Level 2+ — Planned**
- Level 2: Tool selection accuracy (correct tool for the job)
- Level 3: Tool chaining (multi-step pipelines)
- Level 4: Browser automation + loop guard regression
- Level 5: Host computer use (opt-in, requires `--computer-use`)
- Level 6: Model matrix comparison (cross-model benchmarking)

## Phase 1 Results

Run 5 — 2026-05-21 — `qwen3-4b-hermes-64k:latest` via local Ollama

| Test | Status | Notes |
|------|--------|-------|
| test_python_arithmetic | ✅ PASS | |
| test_conditional_logic | ✅ PASS | |
| test_loop_and_accumulation | ✅ PASS | |
| test_create_and_verify_file | ❌ FAIL | Hardened container write path — fix in progress |
| test_file_listing | ✅ PASS | |
| test_echo_with_timestamp | ❌ FAIL | Model answered without tool invocation — prompt fix in progress |
| test_pwd_current_directory | ✅ PASS | |
| test_whoami_username | ✅ PASS | |
| test_web_search | ✅ PASS | |
| test_web_extract | ✅ PASS | |

## Prerequisites

- Python 3.11+
- A running [Hermes](https://github.com/NousResearch/hermes-agent) instance in Docker, accessible via SSH
- Ollama with a supported model (e.g. `qwen3-4b-hermes-64k:latest`) — or an OpenRouter/Anthropic API key
- SSH key-based access configured to the Docker host

## Configuration

Copy `.env.example` to `.env` and fill in your values. **Never commit `.env`.**

| Variable | Description | Example |
|----------|-------------|---------|
| `HERMES_SSH_HOST` | SSH destination (`user@host`) | `user@your-hermes-host` |
| `HERMES_CONTAINER` | Container name | `hermes-sandbox` |
| `HERMES_PROVIDER` | Model provider | `ollama` or `openrouter` |
| `HERMES_MODEL` | Model identifier | `qwen3-4b-hermes-64k:latest` |
| `HERMES_TEST_TIMEOUT` | Seconds per test | `120` |
| `HERMES_API_KEY` | API key for cloud providers | set via environment, never in `.env` |

## Quick Start

```bash
git clone https://github.com/LegionForge/hermes-tool-test-suite
cd hermes-tool-test-suite
pip install -e ".[dev]"
cp .env.example .env   # fill in your SSH host and model config
pytest tests/level1_single_tool/ -v
```

## Architecture

```
harness/
  runner.py       — HermesRunner: SSH → docker exec orchestration
  verifier.py     — Side-effect checkers: file_exists(), url_fetched()
  models.py       — ToolResult, TestCase, ModelConfig dataclasses
  providers.py    — Model matrix: qwen3-4b-hermes, qwen3.5, claude-haiku

metrics/
  tool_invocation.py    — CustomMetric: did a tool actually fire?
  tool_selection.py     — CustomMetric: was it the right tool?
  side_effect.py        — CustomMetric: did the side effect happen?
  loop_guard.py         — CustomMetric: completed without infinite loop?

tests/
  conftest.py           — pytest fixtures (HermesRunner, SideEffectVerifier)
  level1_single_tool/   — Basic single-tool invocation
  level2_tool_selection/— Tool selection accuracy (planned)
  level3_chaining/      — Multi-step pipelines (planned)
  level4_browser/       — Browser automation + loop guard
  level5_computer_use/  — Host desktop (opt-in, --computer-use flag)
  level6_model_matrix/  — Parameterized cross-model tests

docker/
  Dockerfile            — Hermes evaluation container
  docker-compose.yml    — Container + sandbox volume setup
```

## Supported Backends

| Backend | `HERMES_BACKEND` | Status | Use case |
|---------|-----------------|--------|----------|
| Docker via SSH | `docker` | ✅ Implemented | Containerized Hermes on a remote host (default) |
| Bare metal via SSH | `baremetal-ssh` | 🔧 Stub | Hermes running natively on a remote host |
| Local | `local` | 🔧 Stub | Hermes running on the same machine as the tests |

Docker is the tested and recommended path. Bare-metal and local backends accept PRs — see `harness/backends.py` for the interface.

**OS portability notes:**
- Shell results (`whoami`, `pwd`) are resolved dynamically via the `container_user` fixture — no hardcoded usernames
- File write tests use `HERMES_WRITE_SAFE_ROOT` — set this to a writable path appropriate for your deployment
- The harness uses Python's `subprocess` for SSH — works on macOS, Linux, and Windows (WSL)

## Known Issues & Roadmap

**Active failures (Phase 1, Run 5):**

1. `test_create_and_verify_file` — The hardened container restricts writes to `/app/sandbox`. The test prompt needs updating to use the sandbox path. Fix: update prompt to `write to /app/sandbox/...` and update verifier path accordingly.

2. `test_echo_with_timestamp` — `qwen3-4b-hermes` occasionally responds to echo prompts with plain text instead of invoking the terminal tool. Fix: strengthen the prompt to explicitly require tool invocation.

**Phase 2 roadmap:**
- Model comparison benchmarking (qwen3-4b-hermes vs qwen3.5 vs Claude Haiku)
- Level 2–4 test implementations
- DeepEval metric integration for detailed per-test scoring

## Troubleshooting

**"SSH connection refused"**
```bash
# Verify your .env has HERMES_SSH_HOST set
grep HERMES_SSH_HOST .env

# Test SSH manually
ssh $HERMES_SSH_HOST 'docker ps'
```

**"File not created (side effect missing)"**
This is the critical failure case — the model generated text but didn't invoke the tool.
1. Verify the tool is enabled in Hermes: `docker exec hermes-sandbox hermes tools list | grep file`
2. Check container logs: `docker logs hermes-sandbox --tail 50 | grep -i error`
3. Confirm `HERMES_WRITE_SAFE_ROOT` is set if the container restricts write paths

**"Browser loop infinite (timeout)"**
This is a known regression test. Should timeout after 30s and report "EXPECTED: loop guard caught infinite navigation".

## Contributing

To add a test:
1. See `docs/ADDING_TESTS.md`
2. Follow the pattern: `def test_<name>(hermes_runner, verifier):`
3. Use verifiers from `harness/verifier.py` to validate side effects (not response text)
4. Run: `pytest tests/<level>/<your_test>.py -v`

## License

MIT — see [LICENSE](LICENSE)

---

**Project:** LegionForge / hermes-tool-test-suite  
**Hermes Version:** 0.14.0+ (qwen3-4b-hermes-64k)  
**Python:** 3.11+
