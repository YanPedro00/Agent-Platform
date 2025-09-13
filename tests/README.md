# 🧪 Testing Documentation

## 📁 Test Structure

```
tests/
├── backend/
│   ├── conftest.py         # Configurations and fixtures
│   ├── pytest.ini         # Pytest configuration
│   ├── test_*.py          # Test modules
│   └── coverage/          # Coverage reports
└── frontend/
    ├── setup.js           # Test configuration
    └── api.test.js        # API service tests
```

## 🚀 Running Tests

### Backend Tests (Python)

```bash
# Install test dependencies
cd backend
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific tests
pytest tests/backend/test_llm_manager.py

# Run with verbose output
pytest -v

# Run only fast tests (exclude slow)
pytest -m "not slow"
```

### Frontend Tests (JavaScript)

```bash
# Install dependencies
cd frontend
npm install

# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode
npm test -- --watch
```

## 📊 Coverage Reports

After running tests with coverage, reports are generated in:
- **HTML**: `tests/coverage/html/index.html`
- **XML**: `tests/coverage/coverage.xml`
- **Terminal**: Displayed directly in console

### 1. Unit Tests

**Purpose**: Test individual functions and methods in isolation

**Examples**:
```python
def test_create_llm_success(db_session, sample_llm_data):
    """Test: Should create LLM successfully"""
    # Arrange
    llm_data = schemas.LLMCreate(**sample_llm_data)
    
    # Act
    result = LLMManager.create_llm(db_session, llm_data)
    
    # Assert
    assert result.name == sample_llm_data["name"]
    assert result.provider == sample_llm_data["provider"]
```

### 2. Integration Tests

**Purpose**: Test interaction between multiple components

**Examples**:
```python
def test_agent_execution_flow(db_session, created_agent, created_llm):
    """Test: Should execute complete agent flow"""
    # Arrange
    input_data = schemas.AgentRun(input="Test message")
    
    # Act
    result = AgentManager.run_agent(db_session, created_agent.id, input_data)
    
    # Assert
    assert "response" in result
    assert result["actions_used"]
```

## 🔧 Test Configuration

### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests/backend
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=app
    --cov-report=html:tests/coverage/html
    --cov-report=xml:tests/coverage/coverage.xml
    --cov-report=term-missing
    --cov-fail-under=80
```

### Test Fixtures (`conftest.py`)

**Database Fixtures**:
```python
@pytest.fixture(scope="function")
def db_session(test_db):
    """Create database session for tests"""
    session = test_db()
    try:
        yield session
    finally:
        session.close()
```

**Data Fixtures**:
```python
@pytest.fixture
def sample_llm_data():
    """Sample LLM data for tests"""
    return {
        "name": "Test LLM",
        "provider": "openai",
        "model_name": "gpt-3.5-turbo",
        "api_key": "test-key"
    }
```

## 🎯 Best Practices

### 1. Test Structure (AAA Pattern)
```python
def test_example():
    # Arrange - Set up test data
    data = create_test_data()
    
    # Act - Execute action
    result = function_under_test(data)
    
    # Assert - Verify results
    assert result.success == True
```

### 2. Descriptive Test Names
```python
# ✅ Good
def test_create_agent_with_valid_data_should_return_agent()

# ❌ Bad
def test_agent()
```

### 3. Use Fixtures for Common Setup
```python
@pytest.fixture
def created_agent(db_session, sample_agent_data):
    """Create agent for testing"""
    return AgentManager.create_agent(db_session, sample_agent_data)
```

### 4. Test Edge Cases
```python
def test_create_agent_with_duplicate_name_should_raise_error()
def test_run_agent_with_invalid_id_should_return_error()
def test_execute_action_with_missing_parameters_should_handle_gracefully()
```

## 🐛 Troubleshooting

### 1. Database Issues
```bash
# Clean test database
rm -rf tests/coverage/
pytest --cache-clear

# Run specific test
pytest tests/backend/test_llm_manager.py::test_create_llm_success

# Check if tables are being created
pytest -s -v tests/backend/test_api_endpoints.py::test_root_endpoint
```

### 2. Import Errors
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
pytest
```

### 3. Mocks Not Working
```python
# Use pytest-mock for better mocking
def test_with_mock(mocker):
    mock_function = mocker.patch('module.function')
    mock_function.return_value = "mocked_result"
    
    result = function_that_calls_mocked()
    
    assert result == "expected_result"
    mock_function.assert_called_once()
```

### 4. Slow Tests
```python
# Mark slow tests
@pytest.mark.slow
def test_heavy_operation():
    pass

# Run without slow tests
pytest -m "not slow"
```

## 📈 Quality Metrics

### Coverage by Module

| Module | Coverage | Tests |
|--------|----------|-------|
| LLMManager | 95% | 12 tests |
| ActionManager | 90% | 15 tests |
| AgentManager | 90% | 18 tests |
| API Endpoints | 85% | 20 tests |

### Execution Time

- **Unit Tests**: < 1s each
- **Integration Tests**: 1-3s each
- **Full Suite**: < 30s
- **With Coverage**: < 45s

## 🎯 Test Goals

- **Coverage**: Maintain 80%+ code coverage
- **Speed**: Keep test suite under 1 minute
- **Reliability**: Tests should be deterministic
- **Maintainability**: Clear, readable test code

**Keep tests fast, reliable, and comprehensive!** 🚀