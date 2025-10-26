#!/bin/bash

# Test runner script for Serverless Snacks
# This script runs all tests with coverage reporting

set -e

echo "🧪 Running Serverless Snacks Test Suite"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo -e "${BLUE}[SECTION]${NC} $1"
}

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    print_error "pytest is not installed. Installing test dependencies..."
    pip install -r requirements.txt
fi

# Create test reports directory
mkdir -p test-reports

# Run unit tests
print_section "Running Unit Tests"
pytest tests/ \
    --junitxml=test-reports/junit.xml \
    --cov-report=xml:test-reports/coverage.xml \
    --cov-report=html:test-reports/htmlcov \
    --cov-report=term-missing \
    -v

# Check if tests passed
if [ $? -eq 0 ]; then
    print_status "All tests passed! ✅"
else
    print_error "Some tests failed! ❌"
    exit 1
fi

# Display coverage summary
print_section "Coverage Summary"
coverage report --show-missing

# Optional: Run specific test categories
if [ "$1" = "unit" ]; then
    print_section "Running Unit Tests Only"
    pytest tests/ -m "unit" -v
elif [ "$1" = "integration" ]; then
    print_section "Running Integration Tests Only"
    pytest tests/ -m "integration" -v
elif [ "$1" = "lambda" ]; then
    print_section "Running Lambda Function Tests Only"
    pytest tests/lambda_functions/ -v
elif [ "$1" = "cdk" ]; then
    print_section "Running CDK Tests Only"
    pytest tests/cdk/ -v
fi

print_status "Test execution completed!"
print_status "Coverage report available at: test-reports/htmlcov/index.html"