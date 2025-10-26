"""
Unit tests for Order Processor Lambda function.

Tests cover:
- EventBridge event processing
- DynamoDB order status updates
- Error handling for various scenarios
- Event format validation
- Order state transitions
"""

import json
import pytest
import boto3
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime
try:
    from moto import mock_dynamodb
except ImportError:
    try:
        from moto import mock_dynamodb2 as mock_dynamodb
    except ImportError:
        from moto.dynamodb import mock_dynamodb
import sys
import os

# Add the lambda function directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda_functions/order_processor'))

# Import the lambda function
import order_processor


class TestOrderProcessor:
    """Test class for Order Processor Lambda function."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment variables."""
        os.environ['ORDERS_TABLE_NAME'] = 'test-orders-table'

    @pytest.fixture
    def sample_order_detail(self):
        """Sample order detail for testing."""
        return {
            "orderId": "12345678-1234-5678-9012-123456789012",
            "customerName": "John Doe",
            "totalAmount": 9.97,
            "status": "NEW",
            "createdAt": "2023-10-26T12:00:00"
        }

    @pytest.fixture
    def sample_eventbridge_event(self, sample_order_detail):
        """Sample EventBridge event format."""
        return {
            "version": "0",
            "id": "event-id",
            "detail-type": "Order Created",
            "source": "serverless.snacks",
            "account": "123456789012",
            "time": "2023-10-26T12:00:00Z",
            "region": "us-east-1",
            "detail": sample_order_detail
        }

    @pytest.fixture
    def sample_sqs_event(self, sample_order_detail):
        """Sample SQS event format (if using SQS as intermediate)."""
        return {
            "Records": [
                {
                    "messageId": "message-id",
                    "receiptHandle": "receipt-handle",
                    "body": json.dumps(sample_order_detail),
                    "attributes": {},
                    "messageAttributes": {},
                    "md5OfBody": "md5-hash",
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:test-queue",
                    "awsRegion": "us-east-1"
                }
            ]
        }

    @pytest.fixture
    def sample_context(self):
        """Mock Lambda context."""
        context = Mock()
        context.function_name = "order-processor"
        context.function_version = "$LATEST"
        context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:order-processor"
        context.memory_limit_in_mb = 128
        context.remaining_time_in_millis = 30000
        return context

    @pytest.fixture
    def existing_order_in_db(self):
        """Create an existing order in DynamoDB for testing."""
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

    @mock_dynamodb
    @patch('order_processor.datetime')
    def test_successful_order_processing_eventbridge(self, mock_datetime, sample_eventbridge_event, existing_order_in_db, sample_context):
        """Test successful order processing from EventBridge event."""
        # Setup mock datetime
        mock_datetime.utcnow.return_value.isoformat.return_value = '2023-10-26T12:30:00'

        # Create DynamoDB table and populate with existing order
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-orders-table',
            KeySchema=[{'AttributeName': 'orderId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'orderId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Put existing order in table
        table.put_item(Item=existing_order_in_db)

        with patch('order_processor.dynamodb', dynamodb):
            # Call the handler
            response = order_processor.handler(sample_eventbridge_event, sample_context)

            # Verify response
            assert response['statusCode'] == 200
            response_body = json.loads(response['body'])
            assert response_body['message'] == 'Orders processed successfully'

            # Verify order status was updated in DynamoDB
            updated_item = table.get_item(Key={'orderId': '12345678-1234-5678-9012-123456789012'})['Item']
            assert updated_item['status'] == 'PROCESSED'
            assert updated_item['updatedAt'] == '2023-10-26T12:30:00'
            assert updated_item['processedAt'] == '2023-10-26T12:30:00'

    @mock_dynamodb
    @patch('order_processor.datetime')
    def test_successful_order_processing_sqs(self, mock_datetime, sample_sqs_event, existing_order_in_db, sample_context):
        """Test successful order processing from SQS event."""
        # Setup mock datetime
        mock_datetime.utcnow.return_value.isoformat.return_value = '2023-10-26T12:30:00'

        # Create DynamoDB table and populate with existing order
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-orders-table',
            KeySchema=[{'AttributeName': 'orderId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'orderId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Put existing order in table
        table.put_item(Item=existing_order_in_db)

        with patch('order_processor.dynamodb', dynamodb):
            # Call the handler
            response = order_processor.handler(sample_sqs_event, sample_context)

            # Verify response
            assert response['statusCode'] == 200

            # Verify order status was updated
            updated_item = table.get_item(Key={'orderId': '12345678-1234-5678-9012-123456789012'})['Item']
            assert updated_item['status'] == 'PROCESSED'

    @mock_dynamodb
    def test_order_not_found_in_database(self, sample_eventbridge_event, sample_context):
        """Test error handling when order is not found in database."""
        # Create empty DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='test-orders-table',
            KeySchema=[{'AttributeName': 'orderId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'orderId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        with patch('order_processor.dynamodb', dynamodb):
            # Call the handler - should raise exception
            with pytest.raises(ValueError, match="Order .* not found"):
                order_processor.handler(sample_eventbridge_event, sample_context)

    @mock_dynamodb
    def test_order_already_processed(self, sample_eventbridge_event, sample_context):
        """Test handling of order that's already been processed."""
        # Create DynamoDB table with processed order
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-orders-table',
            KeySchema=[{'AttributeName': 'orderId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'orderId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        # Put order with PROCESSED status
        processed_order = {
            'orderId': '12345678-1234-5678-9012-123456789012',
            'status': 'PROCESSED',  # Already processed
            'customerName': 'John Doe',
            'totalAmount': Decimal('9.97'),
            'createdAt': '2023-10-26T12:00:00',
            'processedAt': '2023-10-26T12:15:00'
        }
        table.put_item(Item=processed_order)

        with patch('order_processor.dynamodb', dynamodb):
            # Call the handler
            response = order_processor.handler(sample_eventbridge_event, sample_context)

            # Should still return success but not update the order
            assert response['statusCode'] == 200

            # Verify order status remains unchanged
            item = table.get_item(Key={'orderId': '12345678-1234-5678-9012-123456789012'})['Item']
            assert item['status'] == 'PROCESSED'
            assert item['processedAt'] == '2023-10-26T12:15:00'  # Original timestamp

    @mock_dynamodb
    def test_dynamodb_update_error(self, sample_eventbridge_event, existing_order_in_db, sample_context):
        """Test error handling when DynamoDB update fails."""
        # Create DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-orders-table',
            KeySchema=[{'AttributeName': 'orderId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'orderId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Put existing order in table
        table.put_item(Item=existing_order_in_db)

        # Mock the update_item to raise an exception
        with patch('order_processor.dynamodb', dynamodb):
            with patch.object(table, 'update_item', side_effect=Exception("DynamoDB update failed")):
                with patch('order_processor.dynamodb.Table', return_value=table):
                    # Call the handler - should raise exception
                    with pytest.raises(Exception, match="DynamoDB update failed"):
                        order_processor.handler(sample_eventbridge_event, sample_context)

    def test_invalid_event_format(self, sample_context):
        """Test error handling for invalid event format."""
        invalid_event = {
            "invalid": "event_format"
        }

        # Call the handler - should raise exception due to invalid format
        with pytest.raises(ValueError, match="Invalid event format"):
            order_processor.handler(invalid_event, sample_context)

    def test_missing_order_id_in_detail(self, sample_context):
        """Test error handling when orderId is missing from event detail."""
        invalid_event = {
            "detail": {
                "customerName": "John Doe",
                "totalAmount": 9.97
                # Missing orderId
            }
        }

        # Should raise KeyError for missing orderId
        with pytest.raises(KeyError):
            order_processor.handler(invalid_event, sample_context)

    @mock_dynamodb
    def test_process_order_record_function(self, sample_order_detail, existing_order_in_db):
        """Test the process_order_record helper function directly."""
        # Create DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-orders-table',
            KeySchema=[{'AttributeName': 'orderId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'orderId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Put existing order in table
        table.put_item(Item=existing_order_in_db)

        with patch('order_processor.dynamodb', dynamodb), \
             patch('order_processor.datetime') as mock_datetime:
            
            mock_datetime.utcnow.return_value.isoformat.return_value = '2023-10-26T12:30:00'

            # Call the function directly
            order_processor.process_order_record(sample_order_detail)

            # Verify order was updated
            updated_item = table.get_item(Key={'orderId': '12345678-1234-5678-9012-123456789012'})['Item']
            assert updated_item['status'] == 'PROCESSED'

    def test_simulate_order_processing_steps(self, sample_order_detail):
        """Test the simulate_order_processing_steps function."""
        # This function should return True for successful processing
        result = order_processor.simulate_order_processing_steps(sample_order_detail)
        assert result is True

    @mock_dynamodb
    @patch('order_processor.simulate_order_processing_steps')
    def test_processing_simulation_failure(self, mock_simulate, sample_eventbridge_event, existing_order_in_db, sample_context):
        """Test handling when order processing simulation fails."""
        # Setup mock to return False (processing failed)
        mock_simulate.return_value = False

        # Create DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-orders-table',
            KeySchema=[{'AttributeName': 'orderId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'orderId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Put existing order in table
        table.put_item(Item=existing_order_in_db)

        with patch('order_processor.dynamodb', dynamodb):
            # Call the handler
            response = order_processor.handler(sample_eventbridge_event, sample_context)

            # Should still return success (the simulation doesn't affect the main flow)
            assert response['statusCode'] == 200

    @mock_dynamodb
    def test_multiple_records_processing(self, existing_order_in_db, sample_context):
        """Test processing multiple records in SQS event."""
        # Create multiple order details
        order_details = [
            {
                "orderId": "12345678-1234-5678-9012-123456789012",
                "customerName": "John Doe",
                "totalAmount": 9.97,
                "status": "NEW"
            },
            {
                "orderId": "87654321-4321-8765-2109-876543210987",
                "customerName": "Jane Smith",
                "totalAmount": 15.99,
                "status": "NEW"
            }
        ]

        # Create SQS event with multiple records
        sqs_event = {
            "Records": [
                {
                    "messageId": "message-id-1",
                    "body": json.dumps(order_details[0])
                },
                {
                    "messageId": "message-id-2",
                    "body": json.dumps(order_details[1])
                }
            ]
        }

        # Create DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-orders-table',
            KeySchema=[{'AttributeName': 'orderId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'orderId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        # Put existing orders in table
        table.put_item(Item=existing_order_in_db)
        second_order = existing_order_in_db.copy()
        second_order['orderId'] = '87654321-4321-8765-2109-876543210987'
        second_order['customerName'] = 'Jane Smith'
        second_order['totalAmount'] = Decimal('15.99')
        table.put_item(Item=second_order)

        with patch('order_processor.dynamodb', dynamodb), \
             patch('order_processor.datetime') as mock_datetime:
            
            mock_datetime.utcnow.return_value.isoformat.return_value = '2023-10-26T12:30:00'

            # Call the handler
            response = order_processor.handler(sqs_event, sample_context)

            # Verify response
            assert response['statusCode'] == 200

            # Verify both orders were processed
            for order_id in ['12345678-1234-5678-9012-123456789012', '87654321-4321-8765-2109-876543210987']:
                updated_item = table.get_item(Key={'orderId': order_id})['Item']
                assert updated_item['status'] == 'PROCESSED'

    def test_decimal_serialization(self, sample_order_detail):
        """Test the decimal_default JSON serializer function."""
        # Test with Decimal value
        result = order_processor.decimal_default(Decimal('9.97'))
        assert result == 9.97
        assert isinstance(result, float)

        # Test with non-Decimal value should raise TypeError
        with pytest.raises(TypeError):
            order_processor.decimal_default("not a decimal")

    @mock_dynamodb
    def test_get_item_error_handling(self, sample_eventbridge_event, sample_context):
        """Test error handling when DynamoDB get_item fails."""
        # Create DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-orders-table',
            KeySchema=[{'AttributeName': 'orderId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'orderId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        # Mock get_item to raise an exception
        with patch('order_processor.dynamodb', dynamodb):
            with patch.object(table, 'get_item', side_effect=Exception("DynamoDB get_item failed")):
                with patch('order_processor.dynamodb.Table', return_value=table):
                    # Call the handler - should raise exception
                    with pytest.raises(Exception):
                        order_processor.handler(sample_eventbridge_event, sample_context)

    @mock_dynamodb
    @patch('order_processor.datetime')
    def test_update_expression_attributes(self, mock_datetime, sample_eventbridge_event, existing_order_in_db, sample_context):
        """Test that DynamoDB update uses correct expression attributes."""
        # Setup mock datetime
        mock_datetime.utcnow.return_value.isoformat.return_value = '2023-10-26T12:30:00'

        # Create DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-orders-table',
            KeySchema=[{'AttributeName': 'orderId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'orderId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Put existing order in table
        table.put_item(Item=existing_order_in_db)

        # Mock update_item to capture the call
        with patch('order_processor.dynamodb', dynamodb):
            with patch.object(table, 'update_item') as mock_update:
                with patch('order_processor.dynamodb.Table', return_value=table):
                    # Call the handler
                    order_processor.handler(sample_eventbridge_event, sample_context)

                    # Verify update_item was called with correct parameters
                    mock_update.assert_called_once()
                    call_args = mock_update.call_args
                    
                    # Check the update expression and attributes
                    assert 'UpdateExpression' in call_args[1]
                    assert 'ExpressionAttributeNames' in call_args[1]
                    assert 'ExpressionAttributeValues' in call_args[1]
                    
                    # Verify status attribute is aliased due to reserved word
                    assert call_args[1]['ExpressionAttributeNames']['#status'] == 'status'
                    assert call_args[1]['ExpressionAttributeValues'][':status'] == 'PROCESSED'