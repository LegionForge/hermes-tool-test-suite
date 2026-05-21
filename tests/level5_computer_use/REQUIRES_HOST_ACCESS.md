# Computer Use Tests - Host Access Required

⚠️ **WARNING**: These tests control Dylan's Mac Mini desktop.

## Security Model

- Tests are **skipped by default** unless `--computer-use` flag is passed
- This prevents accidental desktop automation
- Individual tests start with the safest operations (screenshot capture)

## Scope

Current tests:
- ✅ `test_capture.py` — Screenshot capture (read-only, safe)

Future tests (if needed):
- 🚫 Application interaction (requires explicit design review)
- 🚫 File system modification on host (blocked)
- 🚫 System administration (blocked)

## Running

```bash
# Skip computer_use tests (default)
pytest tests/

# EXPLICITLY opt-in to computer_use tests
pytest tests/level5_computer_use/ --computer-use
```

## Monitoring

While running tests with `--computer-use`, watch Dylan's desktop for:
- Screenshot captures (should see screen briefly accessed)
- No unexpected applications launching
- No files being modified
