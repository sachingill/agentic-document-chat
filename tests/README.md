# Test Suite Documentation

This directory contains comprehensive tests for the API project.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures and configuration
├── test_routers.py      # API endpoint tests
├── test_models.py       # Model class tests
├── test_agents.py       # Agent module tests
├── test_integration.py # Integration and E2E tests
└── README.md           # This file
```

## Running Tests

### Run all tests:
```bash
pytest
```

### Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

### Run specific test file:
```bash
pytest tests/test_routers.py
```

### Run specific test class:
```bash
pytest tests/test_models.py::TestMemory
```

### Run specific test:
```bash
pytest tests/test_models.py::TestMemory::test_add_turn
```

### Run by marker:
```bash
pytest -m unit          # Run only unit tests
pytest -m integration   # Run only integration tests
pytest -m api           # Run only API tests
pytest -m "not slow"    # Run all except slow tests
```

### Run with verbose output:
```bash
pytest -v
```

### Run with detailed output:
```bash
pytest -vv
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Test individual functions and classes in isolation
- Fast execution
- Use mocks to isolate dependencies

### Integration Tests (`@pytest.mark.integration`)
- Test interactions between components
- May use real dependencies (with test data)
- Slower execution

### API Tests (`@pytest.mark.api`)
- Test FastAPI endpoints
- Use TestClient for HTTP requests
- Verify request/response handling

## Test Fixtures

### Common Fixtures (in `conftest.py`)

- `test_client`: FastAPI TestClient instance
- `mock_openai_response`: Mock OpenAI API response
- `mock_chat_openai`: Mock ChatOpenAI instance
- `mock_embeddings`: Mock HuggingFaceEmbeddings
- `mock_vector_db`: Mock ChromaDB vector store
- `sample_documents`: Sample document texts for testing
- `sample_metadata`: Sample metadata for testing
- `clean_memory`: Clears memory before/after test
- `mock_model_loader`: Mock ModelLoader for sentiment tests

## Writing New Tests

### Example Unit Test:
```python
@pytest.mark.unit
class TestMyFunction:
    def test_basic_case(self):
        result = my_function("input")
        assert result == "expected"
    
    def test_edge_case(self):
        result = my_function("")
        assert result is None
```

### Example API Test:
```python
@pytest.mark.api
def test_endpoint(test_client):
    response = test_client.get("/endpoint")
    assert response.status_code == 200
    assert response.json()["key"] == "value"
```

### Example Integration Test:
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_flow():
    # Test complete workflow
    result = await full_workflow()
    assert result is not None
```

## Mocking Best Practices

1. **Mock external APIs**: Always mock OpenAI, HuggingFace, etc.
2. **Use fixtures**: Create reusable mocks in `conftest.py`
3. **Isolate tests**: Each test should be independent
4. **Clean up**: Use fixtures to clean up state (e.g., `clean_memory`)

## Coverage Goals

- **Target**: >80% code coverage
- **Critical paths**: 100% coverage
- **Edge cases**: Test error handling and boundary conditions

## Continuous Integration

Tests should be run:
- Before committing code
- In CI/CD pipeline
- Before deploying to production

## Troubleshooting

### Tests failing with import errors:
- Ensure virtual environment is activated
- Install test dependencies: `pip install -r requirements.txt`

### Tests failing with API key errors:
- Tests use mocked APIs, should not need real keys
- Check that mocks are properly configured

### Async tests not running:
- Ensure `pytest-asyncio` is installed
- Use `@pytest.mark.asyncio` decorator
- Check `pytest.ini` for asyncio configuration


