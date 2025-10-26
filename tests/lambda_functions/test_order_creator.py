"""
Unit tests for Order Creator Lambda function.

Tests cover:
- Successful order creation
- Input validation
- DynamoDB interactions
- EventBridge publishing
- Error handling
- Response formatting
"""

import json
import pytest
import boto3
import uuid
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime
try:
    from moto import mock_dynamodb, mock_events
except ImportError:
    try:
        from moto import mock_dynamodb2 as mock_dynamodb, mock_events
    except ImportError:
        from moto.dynamodb import mock_dynamodb
        from moto.events import mock_events
import sys
import os

# Add the lambda function directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda_functions/order_creator'))

# Import the lambda function
import order_creator


class TestOrderCreator:
    """Test class for Order Creator Lambda function."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment variables."""
        os.environ['ORDERS_TABLE_NAME'] = 'test-orders-table'
        os.environ['EVENT_BUS_NAME'] = 'test-event-bus'

    @pytest.fixture
    def sample_order_data(self):
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
    def sample_api_gateway_event(self, sample_order_data):
        """Sample API Gateway event format."""
        return {
            "body": json.dumps(sample_order_data),
            "headers": {"Content-Type": "application/json"}
        }

    @pytest.fixture
    def sample_context(self):
        """Mock Lambda context."""
        context = Mock()
        context.function_name = "order-creator"
        context.function_version = "$LATEST"
        context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:order-creator"
        context.memory_limit_in_mb = 128
        context.remaining_time_in_millis = 30000
        return context

    @mock_dynamodb
    @mock_events
    @patch('order_creator.uuid.uuid4')
    @patch('order_creator.datetime')
    def test_successful_order_creation_direct_invocation(self, mock_datetime, mock_uuid, sample_order_data, sample_context):
        """Test successful order creation with direct Lambda invocation."""
        # Setup mocks
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9012-123456789012')
        mock_datetime.utcnow.return_value.isoformat.return_value = '2023-10-26T12:00:00'

        # Create DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-orders-table',
            KeySchema=[{'AttributeName': 'orderId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'orderId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        # Create EventBridge bus
        events_client = boto3.client('events', region_name='us-east-1')
        events_client.create_event_bus(Name='test-event-bus')

        # Mock the clients in the lambda function
        with patch('order_creator.dynamodb', dynamodb), \
             patch('order_creator.eventbridge', events_client):

            # Call the handler
            response = order_creator.handler(sample_order_data, sample_context)

            # Verify response
            assert response['statusCode'] == 200
            response_body = json.loads(response['body'])
            assert response_body['message'] == 'Order created successfully'
            assert response_body['orderId'] == '12345678-1234-5678-9012-123456789012'
            assert response_body['status'] == 'NEW'
            assert response_body['timestamp'] == '2023-10-26T12:00:00'

            # Verify DynamoDB record
            item = table.get_item(Key={'orderId': '12345678-1234-5678-9012-123456789012'})['Item']
            assert item['customerName'] == 'John Doe'
            assert item['status'] == 'NEW'
            assert item['totalAmount'] == Decimal('9.97')
            assert len(item['snackItems']) == 2

    @mock_dynamodb
    @mock_events
    @patch('order_creator.uuid.uuid4')
    @patch('order_creator.datetime')
    def test_successful_order_creation_api_gateway(self, mock_datetime, mock_uuid, sample_api_gateway_event, sample_context):
        """Test successful order creation with API Gateway event format."""
        # Setup mocks
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9012-123456789012')
        mock_datetime.utcnow.return_value.isoformat.return_value = '2023-10-26T12:00:00'

        # Create DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-orders-table',
            KeySchema=[{'AttributeName': 'orderId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'orderId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        # Create EventBridge bus
        events_client = boto3.client('events', region_name='us-east-1')
        events_client.create_event_bus(Name='test-event-bus')

        # Mock the clients in the lambda function
        with patch('order_creator.dynamodb', dynamodb), \
             patch('order_creator.eventbridge', events_client):

            # Call the handler
            response = order_creator.handler(sample_api_gateway_event, sample_context)

            # Verify response
            assert response['statusCode'] == 200
            response_body = json.loads(response['body'])
            assert response_body['message'] == 'Order created successfully'

    def test_missing_required_fields(self, sample_context):
        """Test validation error for missing required fields."""
        invalid_order_data = {
            "customerName": "John Doe",
            # Missing snackItems and totalAmount
        }

        response = order_creator.handler(invalid_order_data, sample_context)

        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert response_body['error'] == 'Bad Request'
        assert 'Missing required field' in response_body['message']

    def test_missing_customer_name(self, sample_context):
        """Test validation error for missing customer name."""
        invalid_order_data = {
            "snackItems": [{"name": "Chips", "quantity": 1, "price": 2.99}],
            "totalAmount": 2.99
            # Missing customerName
        }

        response = order_creator.handler(invalid_order_data, sample_context)

        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert 'Missing required field: customerName' in response_body['message']

    def test_missing_snack_items(self, sample_context):
        """Test validation error for missing snack items."""
        invalid_order_data = {
            "customerName": "John Doe",
            "totalAmount": 2.99
            # Missing snackItems
        }

        response = order_creator.handler(invalid_order_data, sample_context)

        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert 'Missing required field: snackItems' in response_body['message']

    def test_missing_total_amount(self, sample_context):
        """Test validation error for missing total amount."""
        invalid_order_data = {
            "customerName": "John Doe",
            "snackItems": [{"name": "Chips", "quantity": 1, "price": 2.99}]
            # Missing totalAmount
        }

        response = order_creator.handler(invalid_order_data, sample_context)

        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert 'Missing required field: totalAmount' in response_body['message']

    @patch('order_creator.dynamodb')
    def test_dynamodb_error_handling(self, mock_dynamodb, sample_order_data, sample_context):
        """Test error handling when DynamoDB operations fail."""
        # Mock DynamoDB to raise an exception
        mock_table = Mock()
        mock_table.put_item.side_effect = Exception("DynamoDB error")
        mock_dynamodb.Table.return_value = mock_table

        response = order_creator.handler(sample_order_data, sample_context)

        assert response['statusCode'] == 500
        response_body = json.loads(response['body'])
        assert response_body['error'] == 'Internal Server Error'
        assert response_body['message'] == 'Failed to process order'

    @mock_dynamodb
    @patch('order_creator.eventbridge')
    @patch('order_creator.uuid.uuid4')
    @patch('order_creator.datetime')
    def test_eventbridge_error_handling(self, mock_datetime, mock_uuid, mock_eventbridge, sample_order_data, sample_context):
        """Test error handling when EventBridge operations fail."""
        # Setup mocks
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9012-123456789012')
        mock_datetime.utcnow.return_value.isoformat.return_value = '2023-10-26T12:00:00'

        # Create DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='test-orders-table',
            KeySchema=[{'AttributeName': 'orderId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'orderId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        # Mock EventBridge to raise an exception
        mock_eventbridge.put_events.side_effect = Exception("EventBridge error")

        with patch('order_creator.dynamodb', dynamodb):
            response = order_creator.handler(sample_order_data, sample_context)

            assert response['statusCode'] == 500
            response_body = json.loads(response['body'])
            assert response_body['error'] == 'Internal Server Error'

    def test_convert_floats_to_decimal(self):
        """Test the float to Decimal conversion utility function."""
        # Access the function using its module path
        convert_func = order_creator.handler.__code__.co_consts
        
        # Test data with floats
        test_data = {
            "price": 3.99,
            "items": [
                {"cost": 1.50, "tax": 0.15},
                {"cost": 2.49, "tax": 0.25}
            ],
            "total": 5.99
        }

        # Since convert_floats_to_decimal is defined inside the handler,
        # we'll test it by calling the handler and checking DynamoDB storage
        # This is an integration test approach for the conversion function

    @mock_dynamodb
    @mock_events
    @patch('order_creator.uuid.uuid4')
    @patch('order_creator.datetime')
    def test_decimal_conversion_in_dynamodb(self, mock_datetime, mock_uuid, sample_context):
        """Test that float values are properly converted to Decimal for DynamoDB."""
        # Setup mocks
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9012-123456789012')
        mock_datetime.utcnow.return_value.isoformat.return_value = '2023-10-26T12:00:00'

        # Order data with float values
        order_data = {
            "customerName": "Test Customer",
            "snackItems": [
                {"name": "Item1", "quantity": 1, "price": 1.50},
                {"name": "Item2", "quantity": 2, "price": 2.25}
            ],
            "totalAmount": 5.99
        }

        # Create DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-orders-table',
            KeySchema=[{'AttributeName': 'orderId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'orderId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        # Create EventBridge bus
        events_client = boto3.client('events', region_name='us-east-1')
        events_client.create_event_bus(Name='test-event-bus')

        with patch('order_creator.dynamodb', dynamodb), \
             patch('order_creator.eventbridge', events_client):

            # Call the handler
            response = order_creator.handler(order_data, sample_context)

            # Verify response
            assert response['statusCode'] == 200

            # Verify that values are stored as Decimal in DynamoDB
            item = table.get_item(Key={'orderId': '12345678-1234-5678-9012-123456789012'})['Item']
            assert isinstance(item['totalAmount'], Decimal)
            assert item['totalAmount'] == Decimal('5.99')
            
            # Check snack items prices are also Decimal
            for snack_item in item['snackItems']:
                assert isinstance(snack_item['price'], Decimal)

    def test_response_headers(self, sample_order_data, sample_context):
        """Test that response headers are correctly set."""
        with patch('order_creator.dynamodb'), \
             patch('order_creator.eventbridge'):

            response = order_creator.handler(sample_order_data, sample_context)

            # Check headers
            assert 'headers' in response
            assert response['headers']['Content-Type'] == 'application/json'
            assert response['headers']['Access-Control-Allow-Origin'] == '*'

    def test_malformed_json_in_api_gateway_event(self, sample_context):
        """Test error handling for malformed JSON in API Gateway event."""
        malformed_event = {
            "body": "{ invalid json }"
        }

        response = order_creator.handler(malformed_event, sample_context)

        assert response['statusCode'] == 500
        response_body = json.loads(response['body'])
        assert response_body['error'] == 'Internal Server Error'

    @mock_dynamodb
    @mock_events
    @patch('order_creator.uuid.uuid4')
    @patch('order_creator.datetime')
    def test_eventbridge_event_structure(self, mock_datetime, mock_uuid, sample_order_data, sample_context):
        """Test that EventBridge events are published with correct structure."""
        # Setup mocks
        test_uuid = uuid.UUID('12345678-1234-5678-9012-123456789012')
        mock_uuid.return_value = test_uuid
        mock_datetime.utcnow.return_value.isoformat.return_value = '2023-10-26T12:00:00'

        # Create DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='test-orders-table',
            KeySchema=[{'AttributeName': 'orderId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'orderId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        # Mock EventBridge client to capture the event
        mock_eventbridge = Mock()
        mock_eventbridge.put_events.return_value = {'FailedEntryCount': 0}

        with patch('order_creator.dynamodb', dynamodb), \
             patch('order_creator.eventbridge', mock_eventbridge):

            # Call the handler
            response = order_creator.handler(sample_order_data, sample_context)

            # Verify EventBridge was called
            mock_eventbridge.put_events.assert_called_once()
            
            # Get the call arguments
            call_args = mock_eventbridge.put_events.call_args
            entries = call_args[1]['Entries']
            
            # Verify event structure
            assert len(entries) == 1
            event = entries[0]
            assert event['Source'] == 'serverless.snacks'
            assert event['DetailType'] == 'Order Created'
            assert event['EventBusName'] == 'test-event-bus'
            
            # Verify event detail
            event_detail = json.loads(event['Detail'])
            assert event_detail['orderId'] == str(test_uuid)
            assert event_detail['customerName'] == 'John Doe'
            assert event_detail['totalAmount'] == 9.97
            assert event_detail['status'] == 'NEW'
            assert event_detail['createdAt'] == '2023-10-26T12:00:00'