# Serverless Snacks - Order Processing System

## Overview

The Serverless Snacks platform is an event-driven, serverless architecture for processing snack orders. The system consists of two main Lambda functions that handle order creation and processing through an asynchronous, resilient workflow.

## Architecture

### Components

1. **Order Creator Lambda (Lambda A)** - `order-creator`
   - Receives JSON payload representing snack orders
   - Writes orders to DynamoDB with status "NEW"
   - Publishes events to EventBridge for downstream processing

2. **Order Processor Lambda (Lambda B)** - `order-processor`
   - Triggered by EventBridge events
   - Updates order status from "NEW" to "PROCESSED"
   - Simulates order fulfillment steps

3. **DynamoDB Table** - `Orders`
   - Stores order information with `orderId` as partition key
   - Tracks order status and timestamps

4. **EventBridge Custom Bus** - `serverless-snacks-orders`
   - Decouples order creation from processing
   - Enables future extensibility for additional processors

5. **Dead Letter Queue (DLQ)**
   - Captures failed messages for analysis
   - Provides resilience and error handling

## Data Flow

```
Manual Invocation → Order Creator Lambda → DynamoDB (NEW) → EventBridge → Order Processor Lambda → DynamoDB (PROCESSED)
```

1. Order Creator receives JSON order payload
2. Generates unique `orderId` and writes to DynamoDB with status "NEW"
3. Publishes "Order Created" event to EventBridge
4. EventBridge triggers Order Processor Lambda
5. Order Processor updates status to "PROCESSED" in DynamoDB

## Order Schema

### Input Order Format
```json
{
  "customerName": "John Doe",
  "snackItems": [
    {
      "name": "Chips",
      "quantity": 2,
      "price": 3.99
    },
    {
      "name": "Soda", 
      "quantity": 1,
      "price": 1.99
    }
  ],
  "totalAmount": 9.97
}
```

### DynamoDB Record Format
```json
{
  "orderId": "uuid-string",
  "status": "NEW|PROCESSED",
  "customerName": "John Doe",
  "snackItems": [...],
  "totalAmount": 9.97,
  "createdAt": "2025-10-26T10:30:00.000Z",
  "updatedAt": "2025-10-26T10:31:00.000Z",
  "processedAt": "2025-10-26T10:31:00.000Z"
}
```

## Deployment

### Prerequisites
- AWS CLI configured
- AWS CDK installed (`npm install -g aws-cdk`)
- Python 3.9+

### Single Command Deployment
```bash
cdk deploy
```

This will provision:
- DynamoDB table
- Both Lambda functions
- EventBridge custom bus and rules
- IAM roles and policies
- Dead Letter Queue

### Environment Variables
The CDK automatically configures environment variables:
- `ORDERS_TABLE_NAME`: DynamoDB table name
- `EVENT_BUS_NAME`: EventBridge bus name

## Testing

### Manual Testing via AWS CLI

#### 1. Test Order Creation (Lambda A)
```bash
aws lambda invoke \
  --function-name order-creator \
  --payload '{
    "customerName": "Alice Smith",
    "snackItems": [
      {"name": "Pretzels", "quantity": 1, "price": 2.99},
      {"name": "Coffee", "quantity": 1, "price": 4.50}
    ],
    "totalAmount": 7.49
  }' \
  response.json
```

#### 2. Verify Order in DynamoDB
```bash
aws dynamodb scan --table-name Orders
```

#### 3. Check CloudWatch Logs
```bash
# Order Creator logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/order-creator"

# Order Processor logs  
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/order-processor"
```

### Integration Testing

#### Test Complete Flow
```bash
# 1. Create order
ORDER_RESPONSE=$(aws lambda invoke \
  --function-name order-creator \
  --payload '{
    "customerName": "Bob Wilson", 
    "snackItems": [{"name": "Nuts", "quantity": 3, "price": 5.99}],
    "totalAmount": 17.97
  }' \
  --output text response.json)

# 2. Wait for processing (5-10 seconds)
sleep 10

# 3. Check final status
aws dynamodb scan --table-name Orders \
  --filter-expression "#status = :status" \
  --expression-attribute-names '{"#status": "status"}' \
  --expression-attribute-values '{":status": {"S": "PROCESSED"}}'
```

## Monitoring and Observability

### CloudWatch Metrics
- Lambda invocation count and duration
- DynamoDB read/write capacity
- EventBridge rule matches
- DLQ message count

### CloudWatch Logs
- Structured logging with correlation IDs
- Error tracking and debugging
- Performance monitoring

### Key Metrics to Monitor
1. **Order Creation Rate**: Lambda invocations/minute
2. **Processing Latency**: Time from NEW to PROCESSED
3. **Error Rate**: Failed invocations percentage
4. **DLQ Messages**: Failed processing attempts

## Resilience Features

### Error Handling
- Input validation with proper error responses
- Exception catching with detailed logging
- Graceful degradation for missing data

### Retry Mechanisms
- Lambda retry attempts: 2 retries on failure
- DLQ captures permanently failed messages
- EventBridge built-in retry policies

### Dead Letter Queue
- 14-day message retention
- Enables manual replay of failed orders
- Provides audit trail for troubleshooting

## Security

### IAM Permissions
- Least privilege access for each Lambda
- DynamoDB table-specific permissions
- EventBridge bus-specific permissions

### Data Protection
- Encryption at rest (DynamoDB)
- Encryption in transit (HTTPS/TLS)
- No sensitive data in logs

## Future Enhancements

### Scalability
- Auto-scaling based on demand
- Multi-region deployment capability
- Caching layer for high-frequency reads

### Additional Features
- Order cancellation workflow
- Real-time order status updates
- Customer notifications
- Inventory management integration
- Payment processing integration

### Monitoring Improvements
- Custom CloudWatch dashboards
- Automated alerting
- Performance optimization
- Cost optimization

## Troubleshooting

### Common Issues

#### Order Not Processing
1. Check EventBridge rule configuration
2. Verify Lambda permissions
3. Review CloudWatch logs for errors

#### DynamoDB Errors
1. Check table exists and is active
2. Verify IAM permissions
3. Monitor read/write capacity

#### High Error Rates
1. Check DLQ messages
2. Review input validation
3. Monitor external dependencies

### Debugging Commands
```bash
# Check stack status
cdk list
cdk diff

# View recent logs
aws logs tail /aws/lambda/order-creator --follow
aws logs tail /aws/lambda/order-processor --follow

# Check DLQ messages
aws sqs receive-message --queue-url <DLQ-URL>
```