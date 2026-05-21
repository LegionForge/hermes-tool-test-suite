# Hermes Container — Security Model

This documents what the Docker containment setup protects against and what it does not. Read this before using Hermes in any non-local context.

---

## What This Setup DOES Protect

**Filesystem isolation**
Hermes can only write to `/app/sandbox` (mapped to `./docker/sandbox/` on the host). It cannot reach `/Users`, `/Volumes`, `/etc`, or any other host path. The host filesystem is not mounted.

**Vault/Obsidian isolation**
No vault paths (`/Volumes/MAC_MINI_1TB`, Obsidian library directories) are mounted into the container. Hermes has no path by which to read or write vault contents.

**Network scoping**
Outbound connections from the container are limited by the host's firewall/routing rules. The container is not on a privileged network. The only required external connections are:
- `host.docker.internal:11434` — Ollama on the host
- `discord.com` — Discord API (for the bot)
- `api.anthropic.com` — Anthropic API (if `--provider anthropic` is used)

**Discord user allowlist**
`DISCORD_ALLOWED_USERS` gates which Discord user IDs can invoke Hermes. Users not on the list are silently ignored. This prevents arbitrary Discord users from triggering tool invocations.

**Non-root process**
The container runs as the `hermes` user (UID 1000), not root. A container escape would not immediately grant root on the host (though this is defense-in-depth, not a strong boundary).

**Crash visibility**
`restart: "no"` means container crashes surface rather than auto-recovering. During eval, a crash is signal — we want to see it.

---

## What This Setup Does NOT Protect

**Data exfiltration via Discord**
If Hermes reads data from its sandbox or generates sensitive output, it can send that content to any Discord channel it has access to. The containment controls what Hermes can read from the host; it does not control what it can say in Discord.

**API key misuse if leaked**
If `DISCORD_TOKEN` or `HERMES_ANTHROPIC_API_KEY` appear in logs, are visible in `docker inspect`, or are otherwise exposed, a compromised key can be used from outside the container. Key rotation is the remediation.

**Prompt injection via Discord**
A user who can send messages to the Hermes Discord bot can craft prompts intended to manipulate Hermes's behavior (jailbreaks, indirect instruction injection). The allowlist reduces surface area but does not eliminate this. Hermes should not be pointed at untrusted Discord channels.

**Container escape**
This config does not apply a `seccomp` profile, `AppArmor` policy, or `--cap-drop`. A kernel exploit or Docker daemon vulnerability could still allow container escape. This is acceptable for an isolated eval environment; it is not acceptable for production.

**Model output correctness**
The container enforces where Hermes can write, not what Hermes says. Tool-calling errors, hallucinations, and incorrect outputs are a model reliability problem, not a container security problem. That's what the test suite is for.

---

## Next Hardening Steps (Before Any Production Use)

These are not required for eval but should be addressed before Hermes handles real users or sensitive data:

1. **Network egress filtering** — restrict outbound connections to only `discord.com`, `api.anthropic.com`, and the Ollama host IP. Block all other egress. Implement via host firewall rules or a Docker network with explicit egress rules.

2. **Read-only root filesystem** — add `read_only: true` to the compose service with explicit `tmpfs` mounts for any paths that need write access (e.g., `/tmp`). This prevents Hermes from writing to paths outside the declared volumes.

3. **seccomp profile** — apply Docker's default seccomp profile or a custom one that drops syscalls Hermes doesn't need (e.g., `ptrace`, `mount`, `reboot`). This limits what a compromised Hermes process can do even inside the container.

4. **Capability dropping** — add `cap_drop: [ALL]` to the compose service. Hermes does not need any Linux capabilities.

5. **Resource limits** — add `mem_limit`, `cpus`, and `pids_limit` to the compose service to prevent runaway tool invocations from consuming host resources.

6. **Secrets management** — replace env var secrets with Docker secrets or a vault-backed approach. Env vars are visible in `docker inspect` and process listings.

---

## Reporting Security Issues

This is an internal eval setup. If you find an issue where Hermes can reach paths outside `/app/sandbox`, or where the allowlist can be bypassed, report it before running further eval tests.
