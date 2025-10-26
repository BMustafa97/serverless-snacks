"""
Shared test fixtures and utilities for the Serverless Snacks test suite.
"""

import pytest
import boto3
import os
try:
    from moto import mock_dynamodb, mock_events, mock_sqs
except ImportError:
    # Try alternative import for older moto versions
    try:
        from moto import mock_dynamodb2 as mock_dynamodb, mock_events, mock_sqs
    except ImportError:
        # Try specific service imports
        from moto.dynamodb import mock_dynamodb
        from moto.events import mock_events
        from moto.sqs import mock_sqs
from decimal import Decimal


@pytest.fixture(scope="session")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    # Set Lambda environment variables for testing
    os.environ["ORDERS_TABLE_NAME"] = "test-orders-table"
    os.environ["EVENT_BUS_NAME"] = "test-event-bus"


@pytest.fixture
def dynamodb_table(aws_credentials):
    """Create a mocked DynamoDB table for testing."""
    with mock_dynamodb():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-orders-table',
            KeySchema=[
                {'AttributeName': 'orderId', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'orderId', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        yield table


@pytest.fixture
def eventbridge_bus(aws_credentials):
    """Create a mocked EventBridge bus for testing."""
    with mock_events():
        events_client = boto3.client('events', region_name='us-east-1')
        events_client.create_event_bus(Name='test-event-bus')
        yield events_client


@pytest.fixture
def sqs_queue(aws_credentials):
    """Create a mocked SQS queue for testing."""
    with mock_sqs():
        sqs = boto3.resource('sqs', region_name='us-east-1')
        queue = sqs.create_queue(QueueName='test-dlq')
        yield queue


@pytest.fixture
def sample_order():
    """Sample order data for testing."""
    return {
        "customerName": "John Doe",
        "snackItems": [
            {"name": "Chips", "quantity": 2, "price": 3.99},
            {"name": "Soda", "quantity": 1, "price": 1.99}
        ],
        "totalAmount": 9.97
    }


@pytest.fixture
def sample_order_in_db():
    """Sample order record as it would appear in DynamoDB."""
    return {
        'orderId': '12345678-1234-5678-9012-123456789012',
        'status': 'NEW',
        'customerName': 'John Doe',
        'snackItems': [
            {'name': 'Chips', 'quantity': Decimal('2'), 'price': Decimal('3.99')},
            {'name': 'Soda', 'quantity': Decimal('1'), 'price': Decimal('1.99')}
        ],
        'totalAmount': Decimal('9.97'),
        'createdAt': '2023-10-26T12:00:00',
        'updatedAt': '2023-10-26T12:00:00'
    }


@pytest.fixture
def lambda_context():
    """Mock Lambda context for testing."""
    class MockContext:
        def __init__(self):
            self.function_name = "test-function"
            self.function_version = "$LATEST"
            self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-function"
            self.memory_limit_in_mb = 128
            self.remaining_time_in_millis = 30000
            self.log_group_name = "/aws/lambda/test-function"
            self.log_stream_name = "test-stream"
            self.aws_request_id = "test-request-id"
    
    return MockContext()


class TestHelpers:
    """Helper methods for testing."""
    
    @staticmethod
    def create_eventbridge_event(order_detail):
        """Create a properly formatted EventBridge event."""
        return {
            "version": "0",
            "id": "test-event-id",
            "detail-type": "Order Created",
            "source": "serverless.snacks",
            "account": "123456789012",
            "time": "2023-10-26T12:00:00Z",
            "region": "us-east-1",
            "detail": order_detail
        }
    
    @staticmethod
    def create_sqs_event(order_detail):
        """Create a properly formatted SQS event."""
        return {
            "Records": [
                {
                    "messageId": "test-message-id",
                    "receiptHandle": "test-receipt-handle",
                    "body": str(order_detail) if isinstance(order_detail, dict) else order_detail,
                    "attributes": {},
                    "messageAttributes": {},
                    "md5OfBody": "test-md5",
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:test-queue",
                    "awsRegion": "us-east-1"
                }
            ]
        }
    
    @staticmethod
    def create_api_gateway_event(body):
        """Create a properly formatted API Gateway event."""
        return {
            "body": body,
            "headers": {
                "Content-Type": "application/json"
            },
            "httpMethod": "POST",
            "path": "/orders",
            "queryStringParameters": None,
            "requestContext": {
                "accountId": "123456789012",
                "requestId": "test-request-id"
            }
        }