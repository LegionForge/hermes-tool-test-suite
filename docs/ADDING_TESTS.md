# Adding New Tests

## Test Structure

All tests follow this pattern:

```python
@pytest.mark.level<N>
def test_<name>(hermes_runner: HermesRunner, verifier: SideEffectVerifier):
    """Test description."""
    prompt = "Your prompt here"
    
    result = hermes_runner.run(prompt, toolsets=["tool1", "tool2"])
    
    # Always check execution succeeded
    assert result.success
    
    # CRITICAL: Verify side effects independently
    assert verifier.file_exists("/tmp/test.txt")
    
    # Check response content
    assert "expected text" in result.response_text
```

## Key Rules

1. **Always verify side effects independently**, never just inspect response text
   - Use `verifier.file_exists()` to check files
   - Use `verifier.command_output_contains()` for output
   - Use `verifier.file_content_contains()` for file content

2. **Assign pytest markers** by level
   ```python
   @pytest.mark.level1  # or level2, level3, etc.
   ```

3. **Use meaningful names**
   - `test_echo_with_timestamp` (good)
   - `test_1` (bad)

4. **Handle timeouts for slow tests**
   ```python
   @pytest.mark.slow
   def test_web_search(...):
   ```

5. **Gate computer_use tests**
   ```python
   @pytest.mark.requires_computer_use
   def test_screenshot_capture(...):
   ```

## File Organization

```
tests/
  level1_single_tool/         # Basic single-tool tests
  level2_tool_selection/      # Right tool choice tests
  level3_chaining/            # Multi-step pipelines
  level4_browser/             # Browser automation
  level5_computer_use/        # Host machine control
  level6_model_matrix/        # Cross-model comparison
```

## Example: Adding a Test to Level 1

1. Edit `tests/level1_single_tool/test_new_tool.py`
2. Create test function:

```python
@pytest.mark.level1
def test_my_new_tool(hermes_runner: HermesRunner, verifier: SideEffectVerifier):
    """Test description (one line)."""
    prompt = "What do you want Hermes to do?"
    
    result = hermes_runner.run(
        prompt,
        toolsets=["tool_name"],  # e.g., ["file", "terminal"]
        timeout_seconds=30,
    )
    
    # Verify execution
    assert result.success, f"Failed: {result.stderr}"
    
    # Verify side effect (CRITICAL)
    assert verifier.file_exists("/tmp/expected-file.txt")
    
    # Verify response
    assert "expected output" in result.response_text
```

3. Run the test:
```bash
pytest tests/level1_single_tool/test_new_tool.py -v
```

## Available Verifiers

```python
verifier.file_exists(path)
verifier.file_content_contains(path, text)
verifier.directory_exists(path)
verifier.command_output_contains(command, text)
verifier.file_count_in_directory(path, pattern)
verifier.screenshot_exists(path)
verifier.url_response_contains(expected_text, response)
verifier.no_infinite_loop(response, timeout_occurred)
```

## Adding Fixtures

If you need a custom fixture, add to `tests/conftest.py`:

```python
@pytest.fixture
def my_fixture():
    """Setup/teardown for your test."""
    # setup
    yield value
    # teardown
```

## Debugging

Run with verbose output:
```bash
pytest tests/level1/ -v -s
```

Show print statements:
```bash
pytest tests/level1/ -s
```

Drop into debugger on failure:
```bash
pytest tests/level1/ --pdb
```
