# GitHub Actions AWS Deployment Setup

This document explains how to set up GitHub Actions with AWS permissions to deploy your Serverless Snacks application.

## Option 1: Access Keys (Simple Setup)

### Step 1: Create IAM User

1. Go to AWS IAM Console → Users → Create User
2. User name: `github-actions-serverless-snacks`
3. **Access type**: Programmatic access only (no console access needed)
4. Click Next: Permissions

### Step 2: Attach Required Policies

Attach the `PowerUserAccess` managed policy or create a custom policy with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "lambda:*",
        "dynamodb:*",
        "events:*",
        "iam:*",
        "logs:*",
        "s3:*",
        "sts:*",
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:DeleteRole",
        "iam:PassRole",
        "iam:GetRole",
        "iam:CreatePolicy",
        "iam:DeletePolicy",
        "iam:GetPolicy",
        "iam:GetPolicyVersion",
        "iam:ListPolicyVersions"
      ],
      "Resource": "*"
    }
  ]
}
```

### Step 3: Create Access Keys

1. Select the newly created user
2. Go to Security credentials tab
3. Click "Create access key"
4. Choose "Command Line Interface (CLI)"
5. Check "I understand the above recommendation"
6. Click Next → Create access key
7. **Important**: Copy both the Access Key ID and Secret Access Key (you won't see the secret again!)

### Step 4: Set GitHub Repository Secrets

1. Go to your GitHub repository: `https://github.com/BMustafa97/serverless-snacks`
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add these two secrets:

| Secret Name | Value |
|-------------|-------|
| `AWS_ACCESS_KEY_ID` | Your AWS Access Key ID |
| `AWS_SECRET_ACCESS_KEY` | Your AWS Secret Access Key |

## Option 2: OIDC Authentication (Advanced - More Secure)

### Step 1: Create an IAM Role for GitHub Actions

1. Go to AWS IAM Console → Roles → Create Role
2. Select "Web identity" as trusted entity
3. Choose "token.actions.githubusercontent.com" as Identity provider
4. Set Audience to: `sts.amazonaws.com`
5. Name the role: `GitHubActions-ServerlessSnacks-Role`

### Step 2: Configure Trust Policy and Permissions

Follow the same permission setup as Option 1, but use OIDC role instead of access keys.

### Step 3: Set GitHub Secret

Add this repository secret:
- `AWS_ROLE_ARN`: `arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActions-ServerlessSnacks-Role`

**Note**: To use OIDC, you'll need to modify the workflow file to use role assumption instead of access keys.

## Required Environment Variables

Update the workflow file with your specific values:

- `AWS_REGION`: Your preferred AWS region (e.g., `us-east-1`)
- Update the repository reference in trust policy: `YOUR_GITHUB_USERNAME/serverless-snacks`

## Workflow Triggers

The workflow runs on:
- Push to `main` or `master` branch
- Pull requests to `main` or `master` branch

## What the Workflow Does

1. **Setup Environment**: Installs Python, Node.js, AWS CLI, and CDK
2. **Authentication**: Configures AWS credentials using OIDC or access keys
3. **Bootstrap CDK**: Ensures CDK is bootstrapped in your AWS account
4. **Synthesize**: Generates CloudFormation templates
5. **Deploy & Test**: Runs your `deploy-and-test.sh` script
6. **Artifacts**: Uploads test results and CDK outputs

## Security Best Practices

1. **Rotate Access Keys**: Regularly rotate your AWS access keys (every 90 days recommended)
2. **Least Privilege**: Only grant necessary permissions (PowerUserAccess is sufficient)
3. **Branch Protection**: Restrict who can push to main/master
4. **Environment Protection**: Use GitHub environments for production deployments
5. **Monitor Usage**: Check CloudTrail for unusual AWS API activity
6. **Consider OIDC**: For enhanced security, consider migrating to OIDC authentication (Option 2)

## Troubleshooting

### Common Issues:

1. **Bootstrap Error**: Ensure CDK is bootstrapped in your region
2. **Permission Denied**: Check IAM role/user permissions
3. **Region Mismatch**: Ensure all resources use the same region
4. **Trust Policy**: Verify repository name and branch in trust policy

### Debug Commands:

Add these to your workflow for debugging:

```yaml
- name: Debug AWS Configuration
  run: |
    aws sts get-caller-identity
    aws configure list
    echo "Region: $AWS_DEFAULT_REGION"
```

## Cost Considerations

- The workflow will create AWS resources that may incur costs
- Consider implementing resource cleanup for failed deployments
- Monitor AWS costs and set up billing alerts

## Next Steps

1. **Create IAM User**: Follow Step 1-2 above to create user with PowerUserAccess
2. **Generate Access Keys**: Follow Step 3 to create and copy access keys
3. **Add GitHub Secrets**: Follow Step 4 to add AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
4. **Update Region** (optional): Change AWS_REGION in the workflow file if needed
5. **Test Deployment**: Push code to main branch and monitor GitHub Actions tab
6. **Check AWS Console**: Verify resources are created successfully

## Quick Setup Checklist

- [ ] Created IAM user `github-actions-serverless-snacks`
- [ ] Attached `PowerUserAccess` policy to user
- [ ] Generated access keys for the user
- [ ] Added `AWS_ACCESS_KEY_ID` secret to GitHub
- [ ] Added `AWS_SECRET_ACCESS_KEY` secret to GitHub
- [ ] Confirmed AWS region in workflow file
- [ ] Ready to push and deploy! 🚀