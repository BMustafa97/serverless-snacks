# Serverless Snacks - Documentation Hub

Welcome to the Serverless Snacks documentation! This section provides comprehensive information about the event-driven serverless order processing system.

## 📋 Documentation Contents

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Detailed system architecture, data flows, and component interactions

## 🏗️ System Architecture Overview

The Serverless Snacks platform is an AWS-based event-driven architecture that demonstrates modern serverless patterns for order processing.

### Core Components

#### 🚀 Lambda A - Order Creator (`order-creator`)
**Purpose**: Receives and processes incoming snack orders

**What it does**:
- Accepts JSON payloads containing customer orders
- Generates unique order IDs using UUID
- Stores orders in DynamoDB with status "NEW"
- Publishes "Order Created" events to EventBridge for downstream processing
- Handles both direct invocation and API Gateway integration

**Dependencies**:
- `boto3>=1.26.0` - AWS SDK for Python
- **AWS Services**:
  - DynamoDB (write access to Orders table)
  - EventBridge (publish events to custom bus)
  - CloudWatch Logs (logging and monitoring)

**Environment Variables**:
- `ORDERS_TABLE_NAME` - DynamoDB table name
- `EVENT_BUS_NAME` - EventBridge custom bus name

---

#### ⚙️ Lambda B - Order Processor (`order-processor`)
**Purpose**: Processes order events and updates order status

**What it does**:
- Triggered automatically by EventBridge events
- Updates order status from "NEW" to "PROCESSED"
- Simulates order fulfillment workflow
- Handles event processing errors gracefully

**Dependencies**:
- `boto3>=1.26.0` - AWS SDK for Python
- **AWS Services**:
  - DynamoDB (read/write access to Orders table)
  - EventBridge (receives events from custom bus)
  - CloudWatch Logs (logging and monitoring)

**Environment Variables**:
- `ORDERS_TABLE_NAME` - DynamoDB table name

---

#### 💾 DynamoDB - Orders Table
**Purpose**: Persistent storage for order data

**What it does**:
- Stores order information with `orderId` as partition key
- Tracks order status progression (NEW → PROCESSED)
- Maintains customer information and order details
- Provides fast, scalable data access

**Dependencies**:
- **AWS Services**:
  - CloudWatch (metrics and monitoring)
  - IAM (access control for Lambda functions)

**Configuration**:
- Partition Key: `orderId` (String)
- Billing Mode: Pay-per-request
- Removal Policy: Destroy (for demo purposes)

---

#### 🔄 EventBridge - Custom Event Bus
**Purpose**: Decouples order creation from processing

**What it does**:
- Receives "Order Created" events from Order Creator Lambda
- Routes events to appropriate processors based on event patterns
- Enables asynchronous, scalable event processing
- Supports future extensibility for additional event consumers

**Dependencies**:
- **AWS Services**:
  - Lambda (event targets)
  - CloudWatch (event monitoring)
  - IAM (cross-service permissions)

**Configuration**:
- Bus Name: `serverless-snacks-orders`
- Event Pattern: Source: `serverless.snacks`, DetailType: `Order Created`

---

#### 📊 CloudWatch Logs & Monitoring
**Purpose**: Observability and debugging

**What it provides**:
- Function execution logs for both Lambda functions
- Error tracking and debugging information
- Performance metrics and duration tracking
- Event processing visibility

**Dependencies**:
- **AWS Services**:
  - Lambda (log generation)
  - EventBridge (event metrics)
  - DynamoDB (table metrics)

**Log Groups**:
- `/aws/lambda/order-creator`
- `/aws/lambda/order-processor`

---

## 🔄 Data Flow

```
JSON Order → Order Creator → DynamoDB (NEW) → EventBridge → Order Processor → DynamoDB (PROCESSED)
```

1. **Order Submission**: JSON order payload sent to Order Creator Lambda
2. **Order Storage**: Order stored in DynamoDB with status "NEW"
3. **Event Publication**: "Order Created" event published to EventBridge
4. **Event Processing**: EventBridge triggers Order Processor Lambda
5. **Status Update**: Order Processor updates status to "PROCESSED"

## 🚀 Getting Started

1. **Deploy the system**: Use the deployment scripts in the root directory
2. **Test order creation**: Invoke the `order-creator` Lambda with sample JSON
3. **Monitor processing**: Check CloudWatch logs and DynamoDB for order status
4. **View results**: Query the Orders table to see processed orders

## 📚 Additional Resources

- **Main README**: `../README.md` - Project overview and setup instructions
- **Architecture Details**: `./ARCHITECTURE.md` - Deep dive into system design
- **Deployment Scripts**: `../deploy-and-test-cd.sh` - Automated deployment and testing
