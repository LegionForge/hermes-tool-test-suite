# Docker Secrets Migration Guide

**Context:** `hermes-sandbox` currently loads Discord credentials via `env_file: discord.env`. This causes the token, allowed users, and channel ID to appear as plaintext in `docker inspect hermes-sandbox`. The `~/secrets/` directory with the correct secret files already exists — the migration is mostly a compose file update.

**Effort:** ~15 minutes for compose changes. Code changes to Hermes are needed if it reads credentials from env vars (see [Section 4](#4-hermes-code-changes-required)).

---

## Current State (the gap)

```yaml
# docker-compose.hermes-hardened.yml — current
env_file:
  - discord.env        # ← exposes DISCORD_BOT_TOKEN etc. in `docker inspect`
```

Running `docker inspect hermes-sandbox | grep -A5 '"Env"'` currently shows:

```
"DISCORD_BOT_TOKEN=<actual token>",
"DISCORD_ALLOWED_USERS=<actual ids>",
"DISCORD_HOME_CHANNEL=<actual id>",
```

With Docker secrets, those lines disappear from `docker inspect` entirely.

---

## 1. Secret Files (Already Done)

The files already exist at `~/secrets/` with correct permissions (`-rw-------`):

| Secret name (compose)    | File on host                    | Env var it replaces       |
|--------------------------|---------------------------------|---------------------------|
| `discord_bot_token`      | `~/secrets/discord_token.txt`   | `DISCORD_BOT_TOKEN`       |
| `discord_allowed_users`  | `~/secrets/discord_users.txt`   | `DISCORD_ALLOWED_USERS`   |
| `discord_home_channel`   | `~/secrets/discord_channel.txt` | `DISCORD_HOME_CHANNEL`    |

No `docker secret create` commands needed here — those are for Docker **Swarm** mode (see [Section 5](#5-swarm-secrets-future)). This guide uses Compose file-based secrets, which work on a standalone host without Swarm.

Verify the files are ready:

```bash
ls -la ~/secrets/discord_token.txt ~/secrets/discord_users.txt ~/secrets/discord_channel.txt
# All should be: -rw------- (owner read-only)
```

---

## 2. Updated Compose File

**Diff** from current `docker-compose.hermes-hardened.yml`:

```diff
 services:
   hermes:
     image: hermes:local-hardened-discord
     container_name: hermes-sandbox
     user: '501'
     cap_drop:
       - ALL
     cap_add:
       - NET_BIND_SERVICE
     security_opt:
       - no-new-privileges:true

     command: ["hermes", "gateway", "run"]

-    env_file:
-      - discord.env
-
     environment:
       HERMES_HOME: /opt/data
       HERMES_WRITE_SAFE_ROOT: /opt/data/workspace
       HERMES_LOG_LEVEL: DEBUG

+    secrets:
+      - discord_bot_token
+      - discord_allowed_users
+      - discord_home_channel
+
     volumes:
       - hermes-data:/opt/data:rw
       - ./hermes-config/config.yaml:/opt/data/config.yaml:ro
-      - ./discord.env:/env/discord.env:ro
       - ./secrets:/secrets:ro

     networks:
       - hermes-network

     restart: unless-stopped

+secrets:
+  discord_bot_token:
+    file: ./secrets/discord_token.txt
+  discord_allowed_users:
+    file: ./secrets/discord_users.txt
+  discord_home_channel:
+    file: ./secrets/discord_channel.txt
+
 networks:
   hermes-network:
     driver: bridge

 volumes:
   hermes-data:
     driver: local
```

**Full updated file** (drop-in replacement):

```yaml
version: '3.8'

services:
  hermes:
    image: hermes:local-hardened-discord
    container_name: hermes-sandbox
    user: '501'
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    security_opt:
      - no-new-privileges:true

    command: ["hermes", "gateway", "run"]

    environment:
      HERMES_HOME: /opt/data
      HERMES_WRITE_SAFE_ROOT: /opt/data/workspace
      HERMES_LOG_LEVEL: DEBUG

    secrets:
      - discord_bot_token
      - discord_allowed_users
      - discord_home_channel

    volumes:
      - hermes-data:/opt/data:rw
      - ./hermes-config/config.yaml:/opt/data/config.yaml:ro
      - ./secrets:/secrets:ro

    networks:
      - hermes-network

    restart: unless-stopped

secrets:
  discord_bot_token:
    file: ./secrets/discord_token.txt
  discord_allowed_users:
    file: ./secrets/discord_users.txt
  discord_home_channel:
    file: ./secrets/discord_channel.txt

networks:
  hermes-network:
    driver: bridge

volumes:
  hermes-data:
    driver: local
```

---

## 3. What Changes Inside the Container

With `env_file`, credentials are environment variables: `os.getenv("DISCORD_BOT_TOKEN")` works.

With secrets, they're **files** mounted at `/run/secrets/`:

```
/run/secrets/discord_bot_token      ← content: the raw token string (no trailing newline)
/run/secrets/discord_allowed_users  ← content: the raw allowed users string
/run/secrets/discord_home_channel   ← content: the raw channel ID
```

Secrets are:
- **Not** visible in `docker inspect` env section
- **Not** inherited by child processes via the environment
- Readable only by the process running as UID 501 (they're `root:root 0400` inside the container, but Hermes has access because Docker grants it)

Verify after redeployment:

```bash
# Should show NO discord vars in Env section
docker inspect hermes-sandbox | python3 -c "import json,sys; env=[e for e in json.load(sys.stdin)[0]['Config']['Env'] if 'DISCORD' in e]; print(env or 'CLEAN — no discord vars in env')"

# Confirm secrets are mounted
docker exec hermes-sandbox ls -la /run/secrets/
```

---

## 4. Hermes Code Changes Required

**Flag: This step requires changes to Hermes source before deploying.**

If Hermes reads credentials from environment variables (e.g., in `gateway/platforms/discord.py` or its config loader), it must be updated to read from `/run/secrets/` instead.

### Pattern to find in Hermes source

```bash
# On Dylan's Mac, find all credential reads in Hermes:
grep -rn "DISCORD_BOT_TOKEN\|DISCORD_ALLOWED_USERS\|DISCORD_HOME_CHANNEL" /opt/hermes/
# or inside the container:
docker exec hermes-sandbox grep -rn "DISCORD_BOT_TOKEN" /opt/hermes/
```

### Typical before/after

```python
# Before (env var)
token = os.environ["DISCORD_BOT_TOKEN"]

# After (Docker secret)
def read_secret(name: str) -> str:
    path = Path(f"/run/secrets/{name}")
    if path.exists():
        return path.read_text().strip()
    # Fallback to env var for local dev without Docker secrets
    return os.environ[name.upper()]

token = read_secret("discord_bot_token")
```

The fallback pattern preserves local dev workflow (where secrets files don't exist) while using the secure path in the container.

### Config-file-based credential loading

If Hermes loads `discord.env` or reads from `/env/discord.env` directly (not via env vars), point it at `/run/secrets/` paths instead, or use the helper above.

---

## 5. Swarm Secrets (Future Option)

`docker secret create` is a **Docker Swarm** command — it requires `docker swarm init` and stores secrets encrypted in the Swarm Raft log. On a single-host setup it works but adds Swarm management overhead with no practical benefit over file-based secrets (since there's only one host).

If Hermes ever moves to multi-host or needs stronger at-rest encryption guarantees:

```bash
# Initialize Swarm (one-time, harmless on a single host)
docker swarm init

# Create secrets from the existing files
docker secret create discord_bot_token ~/secrets/discord_token.txt
docker secret create discord_allowed_users ~/secrets/discord_users.txt
docker secret create discord_home_channel ~/secrets/discord_channel.txt

# List to confirm
docker secret ls
```

Then change the compose `secrets:` section to use `external: true` instead of `file:`:

```yaml
secrets:
  discord_bot_token:
    external: true
  discord_allowed_users:
    external: true
  discord_home_channel:
    external: true
```

And deploy with `docker stack deploy` instead of `docker compose up`. The container-side behavior (`/run/secrets/` paths) is identical.

---

## 6. Migration Steps

1. **Find credential reads in Hermes source** (Section 4) — do this first to scope the code change
2. Update Hermes to read from `/run/secrets/` with env var fallback
3. Rebuild the image: `docker build -t hermes:local-hardened-discord .`
4. Update `~/docker-compose.hermes-hardened.yml` with the diff from Section 2
5. Validate compose syntax: `docker compose -f ~/docker-compose.hermes-hardened.yml config`
6. Restart: `docker compose -f ~/docker-compose.hermes-hardened.yml up -d`
7. Verify secrets are not in env: `docker inspect hermes-sandbox | grep DISCORD` (should be empty)
8. Verify Hermes connects to Discord (check logs for "Gateway connected" or equivalent)
9. Once stable, delete `~/discord.env` from the host

---

## Related Files

- Production compose: `~/docker-compose.hermes-hardened.yml` (on Dylan's Mac Mini)
- Secret files: `~/secrets/` (already populated, `chmod 600`)
- Discord gateway: `gateway/platforms/discord.py` in Hermes source (likely where the code change lands)
