import json
import boto3
import uuid
import logging
from datetime import datetime
from typing import Dict, Any
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
eventbridge = boto3.client('events')

# Environment variables
import os
ORDERS_TABLE_NAME = os.environ.get('ORDERS_TABLE_NAME', 'test-orders-table')
EVENT_BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'test-event-bus')

def handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Order Creator Lambda - Lambda A
    
    Receives a JSON payload representing a snack order, writes to DynamoDB,
    and publishes an event to EventBridge for downstream processing.
    
    Expected input format:
    {
        "customerName": "John Doe",
        "snackItems": [
            {"name": "Chips", "quantity": 2, "price": 3.99},
            {"name": "Soda", "quantity": 1, "price": 1.99}
        ],
        "totalAmount": 9.97
    }
    """
    
    try:
        logger.info(f"Order Creator received event: {json.dumps(event)}")
        
        # Parse the order data
        if 'body' in event:
            # Handle API Gateway invocation
            try:
                order_data = json.loads(event['body'])
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {str(e)}")
        else:
            # Handle direct invocation
            order_data = event
            
        # Validate required fields
        required_fields = ['customerName', 'snackItems', 'totalAmount']
        for field in required_fields:
            if field not in order_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Generate unique order ID and timestamp
        order_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Convert float values to Decimal for DynamoDB compatibility
        def convert_floats_to_decimal(obj):
            if isinstance(obj, dict):
                return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_floats_to_decimal(item) for item in obj]
            elif isinstance(obj, float):
                return Decimal(str(obj))
            else:
                return obj
        
        # Prepare order record for DynamoDB
        order_record = {
            'orderId': order_id,
            'status': 'NEW',
            'customerName': order_data['customerName'],
            'snackItems': convert_floats_to_decimal(order_data['snackItems']),
            'totalAmount': Decimal(str(order_data['totalAmount'])),
            'createdAt': timestamp,
            'updatedAt': timestamp
        }
        
        # Write order to DynamoDB
        table = dynamodb.Table(ORDERS_TABLE_NAME)
        table.put_item(Item=order_record)
        
        logger.info(f"Order {order_id} written to DynamoDB with status NEW")
        
        # Publish event to EventBridge
        event_detail = {
            'orderId': order_id,
            'customerName': order_data['customerName'],
            'totalAmount': order_data['totalAmount'],
            'status': 'NEW',
            'createdAt': timestamp
        }
        
        response = eventbridge.put_events(
            Entries=[
                {
                    'Source': 'serverless.snacks',
                    'DetailType': 'Order Created',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        
        logger.info(f"Event published to EventBridge for order {order_id}")
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Order created successfully',
                'orderId': order_id,
                'status': 'NEW',
                'timestamp': timestamp
            })
        }
        
    except (ValueError, json.JSONDecodeError) as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Bad Request',
                'message': str(e)
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing order: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': 'Failed to process order'
            })
        }