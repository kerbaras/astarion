# Astarion Testing Guide

## Overview

This guide covers the testing strategy, tools, and best practices for the Astarion project. We aim for high code coverage (minimum 80%) and comprehensive testing across all components.

## Testing Stack

- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities
- **GitHub Actions**: CI/CD pipeline
- **Codecov**: Coverage tracking

## Test Categories

### Unit Tests
Fast, isolated tests that test individual components without external dependencies.

```bash
make test-unit
# or
pytest tests/ -m unit
```

### Integration Tests
Tests that verify components work together correctly. May require external services.

```bash
make test-integration
# or
pytest tests/ -m integration
```

### Smoke Tests
Quick tests to verify basic functionality.

```bash
make test-smoke
# or
pytest tests/ -m smoke
```

### RAG Pipeline Tests
Specific tests for the RAG components.

```bash
make test-rag
# or
pytest tests/ -m rag
```

## Running Tests

### Local Development

```bash
# Run all tests with coverage
make test-coverage

# Run specific test file
pytest tests/test_extractor.py -v

# Run specific test
pytest tests/test_extractor.py::TestPDFExtractor::test_init_default_config -v

# Run with specific marker
pytest -m "unit and not slow" -v

# Run with coverage report
pytest --cov=src/astarion --cov-report=html
```

### With Docker Services

Some tests require Qdrant to be running:

```bash
# Start services
make docker-up

# Run integration tests
make test-integration

# Stop services
make docker-down
```

## Writing Tests

### Test Structure

```python
"""Tests for module functionality."""

import pytest
from unittest.mock import MagicMock

from astarion.module import MyClass


class TestMyClass:
    """Test suite for MyClass."""
    
    def test_initialization(self):
        """Test class initialization."""
        obj = MyClass()
        assert obj is not None
        
    @pytest.mark.asyncio
    async def test_async_method(self):
        """Test async method."""
        obj = MyClass()
        result = await obj.async_method()
        assert result == expected_value
        
    def test_with_mock(self, monkeypatch):
        """Test with mocked dependency."""
        mock_dep = MagicMock()
        monkeypatch.setattr("astarion.module.dependency", mock_dep)
        
        obj = MyClass()
        obj.method_using_dep()
        
        mock_dep.assert_called_once()
```

### Using Fixtures

Common fixtures are defined in `tests/conftest.py`:

```python
def test_with_fixtures(sample_character, temp_dir, mock_qdrant_client):
    """Test using provided fixtures."""
    # sample_character: Pre-configured Character instance
    # temp_dir: Temporary directory (auto-cleaned)
    # mock_qdrant_client: Mocked Qdrant client
    pass
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async functionality."""
    result = await async_function()
    assert result is not None
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
    ("test3", "result3"),
])
def test_parametrized(input, expected):
    """Test with multiple inputs."""
    assert process(input) == expected
```

## Coverage

### Viewing Coverage Reports

```bash
# Generate and view HTML coverage report
make coverage-report
# Open htmlcov/index.html in browser

# Terminal coverage summary
pytest --cov=src/astarion --cov-report=term-missing
```

### Coverage Requirements

- Overall: 80% minimum
- New code: 80% minimum
- Critical modules (validators, agents): 90% recommended

### Excluding from Coverage

```python
def debug_function():  # pragma: no cover
    """This won't be included in coverage."""
    pass

if TYPE_CHECKING:  # Automatically excluded
    from typing import SomeType
```

## Mocking Strategies

### Mocking External Services

```python
@pytest.fixture
def mock_openai(monkeypatch):
    """Mock OpenAI API calls."""
    mock = MagicMock()
    mock.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="response"))]
    )
    monkeypatch.setattr("openai.OpenAI", lambda **kwargs: mock)
    return mock
```

### Mocking Qdrant

Use the provided `mock_qdrant_client` fixture for tests that need Qdrant:

```python
def test_with_qdrant(mock_qdrant_client):
    """Test that uses Qdrant."""
    retriever = RulebookRetriever(embedder)
    # Qdrant operations will use the mock
```

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Push to main/develop branches
- Pull requests
- Matrix testing: Python 3.11, 3.12, 3.13

### Workflow

1. **Linting**: ruff, black, mypy
2. **Unit Tests**: Fast tests without dependencies
3. **Integration Tests**: Tests with services
4. **Security Scan**: Trivy vulnerability scanning
5. **Coverage Upload**: Results sent to Codecov

## Best Practices

### 1. Test Naming
- Use descriptive names: `test_validate_character_with_invalid_ability_scores`
- Group related tests in classes
- Use docstrings to explain complex tests

### 2. Test Independence
- Tests should not depend on each other
- Use fixtures for setup/teardown
- Clean up resources in tests

### 3. Assertion Messages
```python
assert result == expected, f"Expected {expected}, got {result}"
```

### 4. Testing Errors
```python
with pytest.raises(ValueError, match="Invalid input"):
    function_that_should_fail()
```

### 5. Performance Tests
```python
@pytest.mark.slow
def test_large_pdf_processing():
    """Mark slow tests to run separately."""
    pass
```

## Debugging Tests

### Running with Debug Output

```bash
# Verbose output
pytest -vv

# Show print statements
pytest -s

# Show local variables on failure
pytest -l

# Drop into debugger on failure
pytest --pdb

# Run last failed tests
pytest --lf
```

### VS Code Integration

```json
// .vscode/settings.json
{
    "python.testing.pytestArgs": [
        "tests",
        "-v"
    ],
    "python.testing.unittestEnabled": false,
    "python.testing.pytestEnabled": true
}
```

## Common Issues

### 1. Async Test Warnings
Ensure test is marked with `@pytest.mark.asyncio`

### 2. Import Errors
Check that package is installed in editable mode: `pip install -e .`

### 3. Qdrant Connection Errors
Start Qdrant: `make docker-up`

### 4. Coverage Not Collected
Ensure pytest-cov is installed and source path is correct

## Adding New Tests

1. Create test file: `tests/test_new_module.py`
2. Import module to test
3. Write test class/functions
4. Add appropriate markers
5. Run tests locally
6. Check coverage
7. Submit PR

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Codecov documentation](https://docs.codecov.com/) 