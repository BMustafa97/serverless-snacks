import json
import boto3
import logging
from datetime import datetime
from typing import Dict, Any
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
import os
ORDERS_TABLE_NAME = os.environ.get('ORDERS_TABLE_NAME', 'test-orders-table')

def decimal_default(obj):
    """JSON serializer for Decimal types"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Order Processor Lambda - Lambda B
    
    Processes EventBridge events from Order Creator,
    updates order status from NEW to PROCESSED in DynamoDB.
    
    This function is triggered by EventBridge when a new order is created.
    """
    
    try:
        logger.info(f"Order Processor received event: {json.dumps(event)}")
        
        # Extract order details from EventBridge event
        if 'Records' in event:
            # Handle SQS event (if using SQS as intermediate)
            for record in event['Records']:
                process_order_record(json.loads(record['body']))
        else:
            # Handle direct EventBridge event
            if 'detail' in event:
                order_detail = event['detail']
                process_order_record(order_detail)
            else:
                raise ValueError("Invalid event format")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Orders processed successfully'
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing order event: {str(e)}")
        # Re-raise to trigger retry mechanism
        raise e

def process_order_record(order_detail: Dict[str, Any]) -> None:
    """
    Process individual order record from EventBridge event
    """
    try:
        order_id = order_detail['orderId']
        logger.info(f"Processing order {order_id}")
        
        # Get the current order from DynamoDB
        table = dynamodb.Table(ORDERS_TABLE_NAME)
        
        response = table.get_item(Key={'orderId': order_id})
        
        if 'Item' not in response:
            logger.error(f"Order {order_id} not found in database")
            raise ValueError(f"Order {order_id} not found")
        
        current_order = response['Item']
        current_status = current_order.get('status')
        
        # Only process orders with NEW status
        if current_status != 'NEW':
            logger.warning(f"Order {order_id} has status {current_status}, skipping processing")
            return
        
        # Simulate order processing logic
        # In a real scenario, this might involve:
        # - Inventory checks
        # - Payment processing
        # - Kitchen/fulfillment center notification
        # - Delivery scheduling
        
        logger.info(f"Processing order {order_id} - checking inventory and preparing for fulfillment")
        
        # Update order status to PROCESSED
        timestamp = datetime.utcnow().isoformat()
        
        table.update_item(
            Key={'orderId': order_id},
            UpdateExpression='SET #status = :status, updatedAt = :timestamp, processedAt = :timestamp',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': 'PROCESSED',
                ':timestamp': timestamp
            }
        )
        
        logger.info(f"Order {order_id} status updated to PROCESSED")
        
        # Optional: Publish additional events for further downstream processing
        # For example, trigger packaging, shipping, or notification services
        
    except Exception as e:
        logger.error(f"Error processing order record: {str(e)}")
        raise e

def simulate_order_processing_steps(order_detail: Dict[str, Any]) -> bool:
    """
    Simulate various order processing steps
    Returns True if processing successful, False otherwise
    """
    try:
        # Simulate inventory check
        logger.info("Checking inventory availability...")
        
        # Simulate payment verification (if not already done)
        logger.info("Verifying payment information...")
        
        # Simulate kitchen/preparation notification
        logger.info("Notifying fulfillment center...")
        
        # All steps successful
        return True
        
    except Exception as e:
        logger.error(f"Order processing simulation failed: {str(e)}")
        return False