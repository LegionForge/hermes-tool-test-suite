# Hermes Evaluation Container

Sandboxed Docker setup for evaluating Hermes (Discord-integrated LLM agent) during the tool-calling reliability phase. Hermes runs isolated from the host filesystem while the test harness (`harness/runner.py`) exercises it via SSH + `docker exec`.

## Prerequisites

1. **Docker Desktop** running on the Hermes host
2. **Ollama** running on the host with the required model pulled:
   ```bash
   ollama serve           # if not already running
   ollama pull llama3.1:8b
   ```
3. SSH access to the Hermes host from wherever you run the test suite

## Why llama3.1:8b (not qwen3)

qwen3 with 28+ tools silently drops `tool_calls` — the model outputs text that _looks_ like a tool invocation but the structured `tool_calls` field is missing or empty. This means tests pass the response-text check but fail side-effect verification.

`llama3.1:8b` reliably emits structured `tool_calls`. Use it for eval. Do not change `OLLAMA_MODEL` to a qwen3 variant without re-running the full Level 1 battery and verifying side effects (not just response text).

## Setup

```bash
cd docker/

# 1. Copy the env template and fill in values
cp .env.example .env
nano .env   # or your editor of choice

# 2. Build and start
docker compose up --build

# 3. Verify the container is up
docker ps | grep hermes-sandbox
```

## Running the Test Suite

The test harness SSH-es to the Hermes host and exec's into the container. From your machine:

```bash
cd /path/to/LegionForge-tool-test-suite-for-hermes

# Level 1: basic single-tool invocation
pytest tests/level1_single_tool/ -v

# Levels 1-3: skip browser/computer_use for speed
pytest tests/level1_single_tool tests/level2_tool_selection tests/level3_chaining -v

# Full suite with HTML report
pytest tests/ -v --html=results/report.html --self-contained-html
```

## Log Access

```bash
# Stream live container logs (Discord bot output + tool invocations)
docker compose logs -f hermes

# Or from a remote machine:
ssh $HERMES_SSH_HOST "docker logs hermes-sandbox --tail 100 -f"
```

## Exec Into the Container

```bash
# Open a shell inside the running container (useful for debugging)
docker compose exec hermes bash

# Run a one-shot hermes command manually
docker compose exec hermes /opt/hermes/.venv/bin/hermes chat -q "echo hello" -t terminal
```

## What the Sandbox Volume Is For

Any file operations Hermes attempts (write, read, patch) land in `./sandbox/` on the host (mounted at `/app/sandbox` in the container). This means:

- Hermes cannot write to `/Users`, `/Volumes`, or anywhere on the host filesystem
- The test suite's side-effect verifiers check `./sandbox/` for expected files
- `./sandbox/` is safe to inspect after tests — it contains only what Hermes wrote

```bash
# Inspect what Hermes wrote during a test run
ls -la docker/sandbox/
```

## Evaluation Checklist

After running a test batch, review these dimensions:

- **Stability** — Did the container stay up for the full run? (`docker inspect hermes-sandbox | grep Status`)
- **Latency** — Check `elapsed_seconds` in test output; `ToolResult` reports per-invocation timing
- **Tool-calling accuracy** — Level 1 PASS rate: were side effects verified (not just response text)?
- **Tool selection** — Level 2: did Hermes pick the right tool, avoid tools for simple queries?
- **Log review** — `docker compose logs hermes` for errors, unexpected exits, or tool exceptions

## Teardown

```bash
docker compose down

# Remove sandbox contents between runs to avoid test pollution
rm -rf docker/sandbox/* docker/logs/*
```

## Troubleshooting

**"Container exited immediately"**
- Check logs: `docker compose logs hermes`
- Likely cause: wrong `CMD` for the discord subcommand — see the TODO in `Dockerfile`
- Workaround for testing: override CMD with `sleep infinity` to keep container alive for `docker exec`

**"Ollama connection refused"**
```bash
# Verify Ollama is running on the host
curl http://localhost:11434/api/tags

# From inside the container:
docker compose exec hermes curl http://host.docker.internal:11434/api/tags
```

**"SSH connection refused" from test suite**
```bash
# Confirm the container is named correctly (runner.py expects hermes-sandbox)
docker ps --format '{{.Names}}' | grep hermes-sandbox
```

**"File not created (side effect missing)"**
1. Verify the model is actually `llama3.1:8b` — tool_calls silently fail with qwen3
2. Check that `HERMES_WRITE_SAFE_ROOT=/app/sandbox` is set
3. Exec in and run the command manually to see raw output:
   ```bash
   docker compose exec hermes /opt/hermes/.venv/bin/hermes chat -q "write hello to /app/sandbox/test.txt" -t file
   ```
