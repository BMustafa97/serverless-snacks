# Serverless Snacks

A technical exercise demonstrating event-driven serverless architecture using AWS Lambda functions and DynamoDB.

## Overview

This project creates a small serverless system with two Lambda functions and DynamoDB, connected by an event-driven mechanism. The architecture showcases modern serverless patterns and AWS best practices.

### Start Time: 20:24 26/10/2025
### Finish Time: 22:00 26/10/2025

## Architecture

- **Lambda A**: [Description to be added]
- **Lambda B**: [Description to be added]
- **DynamoDB**: Data persistence layer
- **Event-driven communication**: Connecting the Lambda functions

## Development Phases

### Phase 1: Initial Setup

- ✅ Review all requirements in the technical exercise PDF
- ✅ Create a GitHub repository for the project
- ✅ Upload initial README to repository (this marks the official start time)
- ✅ Verify AWS credentials are working correctly
- ✅ Set up AWS CDK environment and dependencies (blocked by import issues)
- ✅ Initialise CDK project structure

### Phase 2: Infrastructure Development

- ✅ Design the architecture for Lambda A and Lambda B
- ✅ Create Lambda A using CDK
- ✅ Create Lambda B using CDK
- ✅ Implement event-driven connection between Lambda A and Lambda B, event buses
- ✅ Configure IAM roles and permissions for both Lambdas
- [ ] Set up CloudWatch logging for both functions

### Phase 3: Implementation & Testing

- ✅ Implement business logic for Lambda functions
- ✅ Set up DynamoDB tables and schemas
- ✅ Test event-driven communication between functions
- ✅ Implement error handling and monitoring
- ✅ Create deployment pipeline
- [ ] Document API endpoints and usage

## Getting Started

### Prerequisites

- AWS CLI configured with appropriate permissions
- Node.js (version 18.x or later)

### Installation

```bash
# Clone the repository
git clone https://github.com/BMustafa97/serverless-snacks.git
cd serverless-snacks

# Install dependencies
npm install

# Deploy to AWS
cdk deploy
```

## Project Structure

```
serverless-snacks/
├── lib/              # CDK infrastructure code
├── lambda/           # Lambda function source code
├── docs/            # Documentation
├── README.md        # This file
└── package.json     # Project dependencies
```

## Technologies Used

- **AWS Lambda**: Serverless compute service
- **AWS CDK**: Infrastructure as Code
- **DynamoDB**: NoSQL database service
- **CloudWatch**: Monitoring and logging
- **EventBridge/SQS/SNS**: Event-driven messaging (TBD)

## Contributing

This is a technical exercise project. Please follow standard Git practices for commits and documentation.

## License

See [LICENSE](LICENSE) file for details.