from aws_cdk import (
    App,
    Stack,
    Tags,
    CfnOutput,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_sqs as sqs,
    aws_lambda_event_sources as lambda_event_sources,
    aws_iam as iam,
)

from constructs import Construct
import os

class MyAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a DynamoDB table
        table = dynamodb.Table(
            self, "MyTable",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY  # NOT recommended for production code
        )

        # Create an SQS queue
        queue = sqs.Queue(
            self, "MyQueue",
            visibility_timeout=Duration.seconds(300)
        )

        # Create a Lambda function
        lambda_function = _lambda.Function(
            self, "MyFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="handler.main",
            code=_lambda.Code.from_asset(os.path.join("lambda_a")),
            environment={
                "TABLE_NAME": table.table_name,
                "QUEUE_URL": queue.queue_url
            }
        )

        # Grant the Lambda function permissions to read/write to the DynamoDB table
        table.grant_read_write_data(lambda_function)

        # Grant the Lambda function permissions to send messages to the SQS queue
        queue.grant_send_messages(lambda_function)

        # Add SQS event source to the Lambda function
        lambda_function.add_event_source(
            lambda_event_sources.SqsEventSource(queue)
        )

        # Create Lambda A
        lambda_a = _lambda.Function(
            self, "LambdaA",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_a.handler",
            code=_lambda.Code.from_asset(os.path.join("lambda_a")),
            function_name="lambda-a",
            description="Lambda A function for serverless snacks"
        )

        # Output the table name and queue URL
        CfnOutput(self, "TableNameOutput", value=table.table_name)
        CfnOutput(self, "QueueUrlOutput", value=queue.queue_url)
        CfnOutput(self, "LambdaFunctionArnOutput", value=lambda_function.function_arn)
        CfnOutput(self, "LambdaAFunctionArnOutput", value=lambda_a.function_arn)



# Instantiate the app
app = App()
MyAppStack(app, "MyAppStack")
app.synth()
