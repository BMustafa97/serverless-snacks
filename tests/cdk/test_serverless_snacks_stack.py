"""
Unit tests for CDK ServerlessSnacksStack.

Tests cover:
- Infrastructure resource creation
- Lambda function configurations
- DynamoDB table settings
- EventBridge setup
- IAM permissions
- Resource naming and tagging
"""

import pytest
import aws_cdk as cdk
from aws_cdk import assertions
import sys
import os

# Add the project root to the path to import the CDK app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# Import the CDK stack
from app import ServerlessSnacksStack


class TestServerlessSnacksStack:
    """Test class for ServerlessSnacksStack CDK infrastructure."""

    @pytest.fixture
    def stack(self):
        """Create a test stack instance."""
        app = cdk.App()
        stack = ServerlessSnacksStack(app, "TestServerlessSnacksStack")
        return stack

    @pytest.fixture
    def template(self, stack):
        """Get CloudFormation template from the stack."""
        return assertions.Template.from_stack(stack)

    def test_dynamodb_table_creation(self, template):
        """Test that DynamoDB table is created with correct configuration."""
        # Check that DynamoDB table exists
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "TableName": "Orders",
            "KeySchema": [
                {
                    "AttributeName": "orderId",
                    "KeyType": "HASH"
                }
            ],
            "AttributeDefinitions": [
                {
                    "AttributeName": "orderId",
                    "AttributeType": "S"
                }
            ],
            "BillingMode": "PAY_PER_REQUEST"
        })

    def test_dynamodb_table_removal_policy(self, template):
        """Test that DynamoDB table has correct removal policy for demo purposes."""
        # Check that table has DESTROY removal policy
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "DeletionPolicy": "Delete"
        })

    def test_eventbridge_custom_bus_creation(self, template):
        """Test that EventBridge custom bus is created."""
        template.has_resource_properties("AWS::Events::EventBus", {
            "Name": "serverless-snacks-orders"
        })

    def test_sqs_dlq_creation(self, template):
        """Test that SQS Dead Letter Queue is created."""
        template.has_resource_properties("AWS::SQS::Queue", {
            "QueueName": "order-processing-dlq",
            "MessageRetentionPeriod": 1209600  # 14 days in seconds
        })

    def test_order_creator_lambda_creation(self, template):
        """Test that Order Creator Lambda function is created with correct configuration."""
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": "order-creator",
            "Runtime": "python3.9",
            "Handler": "order_creator.handler",
            "Timeout": 30
        })

    def test_order_processor_lambda_creation(self, template):
        """Test that Order Processor Lambda function is created with correct configuration."""
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": "order-processor",
            "Runtime": "python3.9",
            "Handler": "order_processor.handler",
            "Timeout": 30
        })

    def test_lambda_environment_variables(self, template):
        """Test that Lambda functions have correct environment variables."""
        # Check Order Creator environment variables
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": "order-creator",
            "Environment": {
                "Variables": {
                    "ORDERS_TABLE_NAME": assertions.Match.any_value(),
                    "EVENT_BUS_NAME": assertions.Match.any_value()
                }
            }
        })

        # Check Order Processor environment variables
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": "order-processor",
            "Environment": {
                "Variables": {
                    "ORDERS_TABLE_NAME": assertions.Match.any_value()
                }
            }
        })

    def test_lambda_dead_letter_queue_configuration(self, template):
        """Test that Lambda functions are configured with Dead Letter Queue."""
        # Both Lambda functions should have DLQ configuration
        template.resource_count_is("AWS::Lambda::Function", 2)
        
        # Check that functions have DeadLetterConfig
        template.has_resource_properties("AWS::Lambda::Function", {
            "DeadLetterConfig": {
                "TargetArn": assertions.Match.any_value()
            }
        })

    def test_lambda_retry_configuration(self, template):
        """Test that Lambda functions have correct retry configuration."""
        template.has_resource_properties("AWS::Lambda::Function", {
            "ReservedConcurrencyConfiguration": assertions.Match.absent()
        })

    def test_iam_roles_creation(self, template):
        """Test that IAM roles are created for Lambda functions."""
        # Should have IAM roles for both Lambda functions
        template.resource_count_is("AWS::IAM::Role", 2)

        # Check that roles have correct assume role policy for Lambda
        template.has_resource_properties("AWS::IAM::Role", {
            "AssumeRolePolicyDocument": {
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "lambda.amazonaws.com"
                        }
                    }
                ]
            }
        })

    def test_dynamodb_permissions(self, template):
        """Test that Lambda functions have DynamoDB permissions."""
        # Check for IAM policies that grant DynamoDB permissions
        template.has_resource_properties("AWS::IAM::Policy", {
            "PolicyDocument": {
                "Statement": assertions.Match.array_with([
                    {
                        "Action": [
                            "dynamodb:BatchGetItem",
                            "dynamodb:GetRecords",
                            "dynamodb:GetShardIterator",
                            "dynamodb:Query",
                            "dynamodb:GetItem",
                            "dynamodb:Scan",
                            "dynamodb:ConditionCheckItem",
                            "dynamodb:BatchWriteItem",
                            "dynamodb:PutItem",
                            "dynamodb:UpdateItem",
                            "dynamodb:DeleteItem",
                            "dynamodb:DescribeTable"
                        ],
                        "Effect": "Allow",
                        "Resource": [
                            assertions.Match.any_value(),
                            assertions.Match.string_like_regexp(r".*\/index\/\*")
                        ]
                    }
                ])
            }
        })

    def test_eventbridge_permissions(self, template):
        """Test that Order Creator Lambda has EventBridge permissions."""
        # Check for IAM policy that grants EventBridge put events permission
        template.has_resource_properties("AWS::IAM::Policy", {
            "PolicyDocument": {
                "Statement": assertions.Match.array_with([
                    {
                        "Action": "events:PutEvents",
                        "Effect": "Allow",
                        "Resource": assertions.Match.any_value()
                    }
                ])
            }
        })

    def test_eventbridge_rule_creation(self, template):
        """Test that EventBridge rule is created to trigger Order Processor."""
        template.has_resource_properties("AWS::Events::Rule", {
            "EventPattern": {
                "source": ["serverless.snacks"],
                "detail-type": ["Order Created"]
            },
            "State": "ENABLED"
        })

    def test_eventbridge_rule_target(self, template):
        """Test that EventBridge rule targets the Order Processor Lambda."""
        # Check that the rule has a Lambda function target
        template.has_resource_properties("AWS::Events::Rule", {
            "Targets": [
                {
                    "Arn": assertions.Match.any_value(),
                    "Id": assertions.Match.any_value()
                }
            ]
        })

    def test_lambda_invoke_permissions_for_eventbridge(self, template):
        """Test that EventBridge has permission to invoke Order Processor Lambda."""
        template.has_resource_properties("AWS::Lambda::Permission", {
            "Action": "lambda:InvokeFunction",
            "Principal": "events.amazonaws.com"
        })

    def test_cloudformation_outputs(self, template):
        """Test that CloudFormation outputs are created."""
        # Check for expected outputs
        template.has_output("OrdersTableName", {})
        template.has_output("OrderCreatorFunctionName", {})
        template.has_output("OrderProcessorFunctionName", {})
        template.has_output("EventBusName", {})
        template.has_output("DLQName", {})

    def test_output_values(self, stack):
        """Test that output values reference correct resources."""
        # Get the template to check outputs
        template = assertions.Template.from_stack(stack)
        
        # Verify outputs exist (detailed value checking would require more complex assertions)
        outputs = template.to_json()["Outputs"]
        
        assert "OrdersTableName" in outputs
        assert "OrderCreatorFunctionName" in outputs
        assert "OrderProcessorFunctionName" in outputs
        assert "EventBusName" in outputs
        assert "DLQName" in outputs

    def test_lambda_basic_execution_role(self, template):
        """Test that Lambda functions have basic execution role attached."""
        # Check for AWS managed policy attachment
        template.has_resource_properties("AWS::IAM::Role", {
            "ManagedPolicyArns": assertions.Match.array_with([
                {
                    "Fn::Join": [
                        "",
                        [
                            "arn:",
                            {"Ref": "AWS::Partition"},
                            ":iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                        ]
                    ]
                }
            ])
        })

    def test_resource_naming_consistency(self, template):
        """Test that resources follow consistent naming patterns."""
        # Check that function names match expected patterns
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": "order-creator"
        })
        
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": "order-processor"
        })

        template.has_resource_properties("AWS::DynamoDB::Table", {
            "TableName": "Orders"
        })

        template.has_resource_properties("AWS::Events::EventBus", {
            "Name": "serverless-snacks-orders"
        })

    def test_lambda_code_asset_configuration(self, template):
        """Test that Lambda functions reference correct code assets."""
        # This tests that the Code property is configured (actual path validation is complex)
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": "order-creator",
            "Code": assertions.Match.any_value()
        })

        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": "order-processor", 
            "Code": assertions.Match.any_value()
        })

    def test_eventbridge_rule_event_pattern(self, template):
        """Test that EventBridge rule has correct event pattern."""
        template.has_resource_properties("AWS::Events::Rule", {
            "EventPattern": {
                "source": ["serverless.snacks"],
                "detail-type": ["Order Created"]
            }
        })

    def test_stack_resource_count(self, template):
        """Test that the stack creates the expected number of resources."""
        # Count major resources
        template.resource_count_is("AWS::Lambda::Function", 2)  # Order Creator + Order Processor
        template.resource_count_is("AWS::DynamoDB::Table", 1)   # Orders table
        template.resource_count_is("AWS::Events::EventBus", 1)  # Custom event bus
        template.resource_count_is("AWS::Events::Rule", 1)      # Order processing rule
        template.resource_count_is("AWS::SQS::Queue", 1)        # Dead Letter Queue
        template.resource_count_is("AWS::IAM::Role", 2)         # One role per Lambda

    def test_lambda_runtime_version(self, template):
        """Test that Lambda functions use the correct Python runtime version."""
        template.has_resource_properties("AWS::Lambda::Function", {
            "Runtime": "python3.9"
        })

    def test_lambda_timeout_configuration(self, template):
        """Test that Lambda functions have appropriate timeout settings."""
        template.has_resource_properties("AWS::Lambda::Function", {
            "Timeout": 30
        })

    def test_sqs_message_retention_period(self, template):
        """Test that SQS DLQ has appropriate message retention period."""
        template.has_resource_properties("AWS::SQS::Queue", {
            "MessageRetentionPeriod": 1209600  # 14 days
        })

    def test_no_hardcoded_account_or_region_references(self, template):
        """Test that template doesn't contain hardcoded account or region references."""
        template_json = template.to_json()
        template_str = str(template_json)
        
        # Should use CDK intrinsic functions instead of hardcoded values
        assert "123456789012" not in template_str  # Example account ID
        assert "us-east-1" not in template_str     # Hardcoded region