# CalPlaneBot Test Suite

Comprehensive test suite for finding edge cases and ensuring reliability.

## Test Files

### `test_edge_cases.py`
Edge case tests covering:
- **Datetime Edge Cases**: Leap years, DST transitions, far future dates
- **String Edge Cases**: Unicode, emojis, XSS/SQL injection attempts, very long strings
- **Priority Edge Cases**: Invalid priorities, edge values
- **Assignees & Labels**: Zero to hundreds of assignees/labels
- **ID & Sequence**: Extreme sequence numbers, unusual ID formats
- **Completion Status**: Various completion states and timing
- **Data Consistency**: Timezone consistency, Unicode normalization

### `test_stress.py`
Stress and performance tests:
- **High Volume**: 1000+ issues, 100+ projects
- **Concurrency**: Concurrent updates, race conditions
- **Memory**: Memory leak detection, large data handling
- **Boundary Conditions**: Maximum values, overflow prevention
- **Real World Scenarios**: Complex multi-project setups

## Running Tests

### Quick Start
```bash
# Install test dependencies
pip install -r tests/requirements-test.txt

# Run all tests
./run_tests.sh

# Or use pytest directly
pytest
```

### Advanced Usage

```bash
# Fast mode (unit tests only)
./run_tests.sh --fast

# With coverage report
./run_tests.sh --coverage

# Parallel execution
./run_tests.sh --parallel

# Run specific test file
pytest tests/test_edge_cases.py

# Run specific test class
pytest tests/test_edge_cases.py::TestIssueEdgeCases

# Run specific test
pytest tests/test_edge_cases.py::TestIssueEdgeCases::test_extreme_dates

# Run tests matching pattern
pytest -k "datetime"

# Run only edge case tests
pytest -m edge_case

# Run only stress tests
pytest -m stress

# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x
```

### Inside Docker

```bash
# Run tests in Docker container
docker-compose exec calplanebot pytest

# Or build and run
docker-compose run --rm calplanebot pytest
```

## Test Categories

Tests are marked with pytest markers:

- `@pytest.mark.edge_case` - Edge case tests
- `@pytest.mark.stress` - Stress/performance tests
- `@pytest.mark.slow` - Tests taking > 1 second
- `@pytest.mark.integration` - Requires external services
- `@pytest.mark.unit` - Fast, isolated unit tests

## Expected Results

### Edge Cases to Watch For

1. **Unicode Issues**
   - Emoji in issue names
   - RTL text (Hebrew, Arabic)
   - Mixed RTL/LTR
   - Zero-width characters
   - Combining characters

2. **Date/Time Issues**
   - Leap year dates
   - DST transitions
   - Far future dates (Y2K38, Y10K)
   - Very old dates
   - Timezone edge cases

3. **Numeric Boundaries**
   - Sequence ID overflow (2^31)
   - Very large sort orders
   - Negative values
   - Infinity/NaN

4. **String Lengths**
   - Empty strings
   - Very long strings (>1MB)
   - URL length limits
   - Description size limits

5. **Array Sizes**
   - Zero assignees/labels
   - Hundreds of assignees/labels
   - Empty arrays vs null

6. **Status Combinations**
   - Completed but has future deadline
   - Not completed but has completed_at
   - Invalid status values

7. **Concurrent Modifications**
   - Rapid successive updates
   - Clock skew scenarios
   - Race conditions

## Adding New Tests

### Test Structure

```python
import pytest
from app.services.sync_service import SyncService
from app.models.plane import PlaneIssue

class TestNewFeature:
    """Test new feature edge cases"""

    def setup_method(self):
        self.sync_service = SyncService()

    @pytest.mark.parametrize("input,expected", [
        (value1, result1),
        (value2, result2),
    ])
    def test_something(self, input, expected):
        """Test description"""
        # Arrange
        issue = PlaneIssue(...)

        # Act
        result = self.sync_service.plane_issue_to_caldav_event(issue)

        # Assert
        assert result == expected
```

### Best Practices

1. **Use parametrize** for testing multiple inputs
2. **Test both success and failure** cases
3. **Use descriptive names** that explain what's being tested
4. **Add docstrings** explaining why the test exists
5. **Keep tests independent** (no shared state)
6. **Mock external dependencies** (API calls, file system)
7. **Test edge cases first** then normal cases

## Coverage

To generate coverage report:

```bash
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

Target: 80%+ coverage for critical paths

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pip install -r tests/requirements-test.txt
    pytest --cov=app --cov-report=xml
```

## Known Issues

- Some stress tests may be slow (>10s)
- Integration tests require real CalDAV server
- Memory tests require monitoring tools

## Contributing

When adding new features:
1. Add edge case tests first (TDD)
2. Add stress tests for performance-critical code
3. Update this README with new test categories
4. Ensure all tests pass before PR

## Troubleshooting

**Tests fail with import errors:**
```bash
pip install -e .
```

**Tests hang:**
```bash
pytest --timeout=10  # Add timeout
```

**Parallel tests fail:**
```bash
pytest -n 0  # Disable parallel execution
```

**Can't find pytest:**
```bash
python -m pytest  # Use module syntax
```
