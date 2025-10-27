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

# Invoke the Lambda function with the main-test event
# The function should handle the test internally and log results
# names list
customerNames=("Bilal Mustafa" "John Doe" "Jane Smith" "Michael Brown" "Emily Davis" "David Wilson" "Sarah Miller" "Chris Moore" "Jessica Taylor")
# Choose one name at random
randomName=${customerNames[$RANDOM % ${#customerNames[@]}]}

aws lambda invoke \
    --function-name order-creator \
    --invocation-type RequestResponse \
    --payload "{\"customerName\": \"$randomName\", \"snackItems\": [{\"name\": \"Test Chips\", \"quantity\": 2, \"price\": 3.99}, {\"name\": \"Test Soda\", \"quantity\": 1, \"price\": 1.99}], \"totalAmount\": 9.97}" \
response.json && rm -f response.json

    if [ $? -eq 0 ]; then
        print_status "Order creation test invoked successfully ✅"
        print_status "Check CloudWatch logs for detailed results"
    else
        print_status "Order Check Logs"
    fi
done

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

# No cleanup needed - using /dev/null for response

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