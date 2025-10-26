# Serverless Snacks - Test Suite

This directory contains comprehensive unit tests for the Serverless Snacks order processing system.

## Test Structure

```
tests/
├── conftest.py                     # Shared test fixtures and utilities
├── lambda_functions/               # Lambda function tests
│   ├── test_order_creator.py      # Order Creator Lambda tests
│   └── test_order_processor.py    # Order Processor Lambda tests
└── cdk/                           # CDK infrastructure tests
    └── test_serverless_snacks_stack.py
```

## Test Categories

- **Unit Tests**: Test individual functions and components in isolation
- **Integration Tests**: Test component interactions (marked with `@pytest.mark.integration`)
- **Lambda Tests**: Specific tests for AWS Lambda functions (marked with `@pytest.mark.lambda`)
- **CDK Tests**: Infrastructure validation tests (marked with `@pytest.mark.cdk`)

## Prerequisites

Install test dependencies:

```bash
pip install -r requirements.txt
```

## Running Tests

### All Tests
```bash
# Using pytest directly
pytest

# Using the test runner script
./run-tests.sh
```

### Specific Test Categories
```bash
# Run only unit tests
pytest -m unit

# Run only Lambda function tests
pytest tests/lambda_functions/

# Run only CDK tests
pytest tests/cdk/

# Run with coverage
pytest --cov
```

### Test Runner Script Options
```bash
# Run unit tests only
./run-tests.sh unit

# Run integration tests only
./run-tests.sh integration

# Run Lambda tests only
./run-tests.sh lambda

# Run CDK tests only
./run-tests.sh cdk
```

## Test Coverage

The test suite aims for >80% code coverage. Coverage reports are generated in multiple formats:

- **Terminal**: Shows missing lines during test execution
- **HTML**: Detailed interactive report at `test-reports/htmlcov/index.html`
- **XML**: For CI/CD integration at `test-reports/coverage.xml`

## Mock Services

Tests use [moto](https://github.com/spulec/moto) to mock AWS services:

- **DynamoDB**: For database interactions
- **EventBridge**: For event publishing and processing
- **SQS**: For dead letter queue testing
- **Lambda**: For function invocation testing

## Test Fixtures

Common test fixtures are defined in `conftest.py`:

- `aws_credentials`: Mock AWS credentials
- `dynamodb_table`: Pre-configured DynamoDB table
- `eventbridge_bus`: Mock EventBridge bus
- `sample_order`: Sample order data
- `lambda_context`: Mock Lambda context

## Writing New Tests

### Lambda Function Tests

```python
def test_my_lambda_function(dynamodb_table, lambda_context):
    # Arrange
    event = {"test": "data"}
    
    # Act
    response = my_lambda.handler(event, lambda_context)
    
    # Assert
    assert response['statusCode'] == 200
```

### CDK Tests

```python
def test_my_infrastructure(template):
    # Test that a resource exists
    template.has_resource_properties("AWS::Lambda::Function", {
        "FunctionName": "my-function"
    })
    
    # Test resource count
    template.resource_count_is("AWS::DynamoDB::Table", 1)
```

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_unit_functionality():
    pass

@pytest.mark.integration
def test_component_integration():
    pass

@pytest.mark.lambda
def test_lambda_function():
    pass

@pytest.mark.cdk
def test_infrastructure():
    pass
```

## Continuous Integration

The test suite is designed to run in CI/CD pipelines:

- JUnit XML output for test result reporting
- Coverage XML for coverage reporting
- Configurable fail thresholds
- Proper exit codes for pipeline integration

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
2. **Moto Version Issues**: The tests use `mock_dynamodb2` - update moto if using older versions
3. **Path Issues**: Tests add Lambda function directories to Python path automatically
4. **AWS Credentials**: Tests use mocked credentials - no real AWS credentials needed

### Debug Mode

Run tests with extra verbosity:

```bash
pytest -v -s --tb=long
```

### Running Single Tests

```bash
# Run specific test file
pytest tests/lambda_functions/test_order_creator.py

# Run specific test function
pytest tests/lambda_functions/test_order_creator.py::TestOrderCreator::test_successful_order_creation

# Run tests matching pattern
pytest -k "test_order_creation"
```