from aws_cdk import (
    App,
    Stack,
    Tags,
    CfnOutput,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_sqs as sqs,
    aws_iam as iam,
)

from constructs import Construct
import os

class ServerlessSnacksStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create DynamoDB table for Orders
        orders_table = dynamodb.Table(
            self, "OrdersTable",
            table_name="Orders",
            partition_key=dynamodb.Attribute(
                name="orderId",
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY,  # For demo purposes
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )

        # Create EventBridge custom bus for order events
        order_event_bus = events.EventBus(
            self, "OrderEventBus",
            event_bus_name="serverless-snacks-orders"
        )

        # Create Dead Letter Queue for resilience
        dlq = sqs.Queue(
            self, "OrderProcessingDLQ",
            queue_name="order-processing-dlq",
            retention_period=Duration.days(14)
        )

        # Lambda A: Order Creator (receives order, writes to DynamoDB, publishes event)
        order_creator_lambda = _lambda.Function(
            self, "OrderCreatorFunction",
            function_name="order-creator",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="order_creator.handler",
            code=_lambda.Code.from_asset("lambda_functions/order_creator"),
            timeout=Duration.seconds(30),
            environment={
                "ORDERS_TABLE_NAME": orders_table.table_name,
                "EVENT_BUS_NAME": order_event_bus.event_bus_name
            },
            dead_letter_queue=dlq,
            retry_attempts=2
        )

        # Lambda B: Order Processor (processes events, updates order status)
        order_processor_lambda = _lambda.Function(
            self, "OrderProcessorFunction",
            function_name="order-processor",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="order_processor.handler",
            code=_lambda.Code.from_asset("lambda_functions/order_processor"),
            timeout=Duration.seconds(30),
            environment={
                "ORDERS_TABLE_NAME": orders_table.table_name
            },
            dead_letter_queue=dlq,
            retry_attempts=2
        )

        # Grant DynamoDB permissions
        orders_table.grant_read_write_data(order_creator_lambda)
        orders_table.grant_read_write_data(order_processor_lambda)

        # Grant EventBridge permissions to Order Creator
        order_event_bus.grant_put_events_to(order_creator_lambda)

        # Create EventBridge rule to trigger Order Processor
        order_processing_rule = events.Rule(
            self, "OrderProcessingRule",
            event_bus=order_event_bus,
            event_pattern=events.EventPattern(
                source=["serverless.snacks"],
                detail_type=["Order Created"]
            )
        )

        # Add Order Processor Lambda as target for the rule
        order_processing_rule.add_target(targets.LambdaFunction(order_processor_lambda))

        # Outputs for testing and monitoring
        CfnOutput(self, "OrdersTableName", value=orders_table.table_name)
        CfnOutput(self, "OrderCreatorFunctionName", value=order_creator_lambda.function_name)
        CfnOutput(self, "OrderProcessorFunctionName", value=order_processor_lambda.function_name)
        CfnOutput(self, "EventBusName", value=order_event_bus.event_bus_name)
        CfnOutput(self, "DLQName", value=dlq.queue_name)



# Instantiate the app
app = App()
ServerlessSnacksStack(app, "ServerlessSnacksStack")
app.synth()
