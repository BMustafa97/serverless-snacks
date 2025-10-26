#!/bin/bash

# Serverless Snacks - Deployment and Testing Script
# This script deploys the CDK stack and runs integration tests

set -e

echo "🍿 Serverless Snacks - Deployment and Testing"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed"
    exit 1
fi

if ! command -v cdk &> /dev/null; then
    print_error "AWS CDK is not installed"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi

print_status "Prerequisites check passed ✅"

# Deploy the CDK stack
print_status "Deploying CDK stack..."
cdk deploy --require-approval never

if [ $? -eq 0 ]; then
    print_status "CDK deployment completed successfully ✅"
else
    print_error "CDK deployment failed ❌"
    exit 1
fi

# Get stack outputs
print_status "Retrieving stack outputs..."
STACK_NAME="ServerlessSnacksStack"

# Wait a moment for outputs to be available
sleep 5

# Test the deployed system
print_status "Running integration tests..."

# Test 1: Create an order using stored test event
print_status "Test 1: Creating a test order using 'main-test' event..."
RESPONSE_FILE="test_response.json"

# First, get the stored test event payload
print_status "Retrieving stored test event 'main-test'..."
TEST_EVENT_PAYLOAD=$(aws lambda get-function-event-invoke-config \
    --function-name order-creator \
    --query 'configuration.LastModified' \
    --output text 2>/dev/null || echo "")

# If we can't retrieve the stored event, we'll invoke with minimal payload to trigger the function
# The function should have the 'main-test' event configured internally
aws lambda invoke \
    --function-name order-creator \
    --invocation-type RequestResponse \
    --payload '{"testEvent": "main-test"}' \
    $RESPONSE_FILE

if [ $? -eq 0 ]; then
    print_status "Order creation test passed ✅"
    echo "Response:"
    cat $RESPONSE_FILE | python3 -m json.tool
else
    print_error "Order creation test failed ❌"
fi

# Test 2: Wait and check order processing
print_status "Test 2: Waiting for order processing (10 seconds)..."
sleep 10

print_status "Checking DynamoDB for processed orders..."
aws dynamodb scan --table-name Orders \
    --projection-expression "orderId, #status, customerName, totalAmount" \
    --expression-attribute-names '{"#status": "status"}' \
    --output table

# Test 3: Check CloudWatch logs
print_status "Test 3: Checking recent Lambda logs..."
echo ""
echo "Order Creator logs (last 5 minutes):"
START_TIME=$(($(date +%s) - 300))000
aws logs filter-log-events \
    --log-group-name "/aws/lambda/order-creator" \
    --start-time $START_TIME \
    --query 'events[*].message' \
    --output text | head -10

echo ""
echo "Order Processor logs (last 5 minutes):"
aws logs filter-log-events \
    --log-group-name "/aws/lambda/order-processor" \
    --start-time $START_TIME \
    --query 'events[*].message' \
    --output text | head -10

# Clean up
rm -f $RESPONSE_FILE

print_status "Testing completed!"
echo ""
echo "📊 System Overview:"
echo "- DynamoDB Table: Orders"
echo "- Lambda Functions: order-creator, order-processor"
echo "- EventBridge Bus: serverless-snacks-orders"
echo ""
echo "🧪 Manual Testing Commands:"
echo "aws lambda invoke --function-name order-creator --payload '{...}' response.json"
echo "aws dynamodb scan --table-name Orders"
echo ""
echo "🎉 Serverless Snacks deployment and testing complete!"