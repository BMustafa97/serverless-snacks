# GitHub Actions Setup with AWS Access Keys

## 🚀 Quick Setup Guide

### Step 1: Create AWS IAM User

1. **Go to AWS Console** → IAM → Users → Create User
2. **User name**: `github-actions-serverless-snacks`
3. **Check**: "Provide user access to the AWS Management Console" - **UNCHECKED**
4. **Select**: "I want to create an IAM user"
5. **Click**: Next

### Step 2: Attach Permissions

1. **Select**: "Attach policies directly"
2. **Search and select**: `PowerUserAccess`
3. **Click**: Next → Create User

### Step 3: Create Access Keys

1. **Click** on the newly created user
2. **Go to**: Security credentials tab
3. **Click**: "Create access key"
4. **Select**: "Command Line Interface (CLI)"
5. **Check**: "I understand the above recommendation"
6. **Click**: Next → Create access key
7. **Copy** the Access Key ID and Secret Access Key (you won't see the secret again!)

### Step 4: Add GitHub Secrets

1. **Go to your GitHub repository**: https://github.com/BMustafa97/serverless-snacks
2. **Navigate to**: Settings → Secrets and variables → Actions
3. **Click**: "New repository secret"

Add these two secrets:

| Secret Name | Value |
|-------------|-------|
| `AWS_ACCESS_KEY_ID` | Your AWS Access Key ID |
| `AWS_SECRET_ACCESS_KEY` | Your AWS Secret Access Key |

### Step 5: Configure AWS Region (Optional)

If you want to deploy to a different region than `eu-west-1`, update the workflow file:

```yaml
env:
  AWS_REGION: us-east-1  # Change to your preferred region
```

## ✅ That's it!

Your GitHub Actions workflow is now configured to:

- ✅ **Deploy** your CDK stack automatically on push to main/master
- ✅ **Run tests** against the deployed infrastructure  
- ✅ **Upload artifacts** with test results and deployment info
- ✅ **Cache dependencies** for faster builds

## 🔄 How to Use

1. **Push code** to main or master branch
2. **Check** the Actions tab in your GitHub repository
3. **Monitor** the deployment and test results
4. **View artifacts** if you need to debug issues

## 🛠️ Required AWS Permissions

Your IAM user needs these services (covered by PowerUserAccess):
- CloudFormation (for CDK deployments)
- Lambda (for your functions)  
- DynamoDB (for your database)
- EventBridge (for event routing)
- IAM (for role management)
- S3 (for CDK assets)
- CloudWatch Logs (for monitoring)

## 🔒 Security Notes

- ✅ Access keys are stored securely in GitHub Secrets
- ✅ Keys are never exposed in logs or workflow files
- ✅ PowerUserAccess provides necessary permissions without full admin
- ⚠️ Consider rotating access keys periodically
- ⚠️ Monitor CloudTrail for unusual activity

## 🎉 Ready to Deploy!

Push your code to the main branch and watch the magic happen in the Actions tab!