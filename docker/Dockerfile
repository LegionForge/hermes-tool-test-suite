FROM python:3.11-slim

# Install system-level tools Hermes may invoke via its terminal toolset
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Install hermes-agent into the venv path the test harness expects.
# harness/runner.py hard-codes: /opt/hermes/.venv/bin/hermes
# Changing this path requires updating runner.py's hermes_cmd construction.
RUN python -m venv /opt/hermes/.venv && \
    /opt/hermes/.venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/hermes/.venv/bin/pip install --no-cache-dir "hermes-agent>=0.14.0"

# TODO: No requirements.txt found in the repo root (only pyproject.toml for the
# test suite). If Hermes has its own requirements file, COPY and install it here
# before the hermes-agent install above.

WORKDIR /app

# These are the only directories Hermes may write to.
# HERMES_WRITE_SAFE_ROOT=/app/sandbox is set in docker-compose.yml.
RUN mkdir -p /app/sandbox /app/logs

# Run as non-root to limit blast radius if a tool escapes the sandbox
RUN useradd -m -u 1000 hermes && \
    chown -R hermes:hermes /app /opt/hermes
USER hermes

# Start the Hermes Discord bot as the persistent service.
# TODO: Verify the exact subcommand — check `hermes --help` for the discord/serve
# subcommand name. Common patterns: `hermes discord`, `hermes serve`, `hermes bot`.
# The test harness reaches Hermes via `docker exec hermes-sandbox hermes chat ...`
# against this running container, so the main process just needs to stay alive.
CMD ["/opt/hermes/.venv/bin/hermes", "discord"]

# =============================================================================
# Suggested .dockerignore (place at docker/.dockerignore):
# =============================================================================
# sandbox/
# logs/
# .env
# __pycache__/
# *.pyc
# *.pyo
# .git/
# results/
# *.egg-info/
# =============================================================================
