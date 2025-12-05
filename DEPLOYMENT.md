# AWS App Runner Deployment Guide

## Prerequisites

1. **AWS Account** with access to AWS App Runner and Amazon Bedrock
2. **Bedrock Model Access**: Enable Claude 4 Sonnet in Bedrock Console
   - Navigate to: Bedrock Console → Model access → Manage model access
   - Enable: `anthropic.claude-sonnet-4-20250514-v1:0`

## Environment Variables

Most configuration is in `apprunner.yaml`. For AWS credentials, App Runner uses IAM roles:

### AWS Credentials (Automatic via IAM)
App Runner will automatically use the IAM role you assign to the service. No need to set:
- ~~`AWS_ACCESS_KEY_ID`~~ (handled by IAM role)
- ~~`AWS_SECRET_ACCESS_KEY`~~ (handled by IAM role)
- `AWS_REGION`: Set in `apprunner.yaml` (default: us-east-1)

### Configuration (in apprunner.yaml)
- `PORT`: Application port (8080)
- `STRANDS_MODEL_ID`: Bedrock model ID
- `STRANDS_TEMPERATURE`: Model temperature (0.7)
- `STRANDS_MAX_TOKENS`: Max tokens per response (4096)

### Optional Override (if needed)
If you need to override any values, you can add them in App Runner Console:
- After creating the service, go to: Configuration → Edit
- Add custom environment variables in the "Environment variables" section

## Deployment Steps

1. **Push code to repository** (GitHub, GitLab, Bitbucket, or AWS CodeCommit)

2. **Create App Runner service**:
   - Go to AWS App Runner console
   - Click "Create service"
   - Select your repository
   - Choose "Python 3.11" runtime
   - App Runner will automatically detect `apprunner.yaml`

3. **Configure IAM permissions**:
   - During service creation, App Runner will ask for an "Instance role"
   - Create a new role or select existing role with these permissions:
     - `AmazonBedrockFullAccess` (or custom policy with `bedrock:InvokeModel`)
   - This allows the app to call Bedrock without hardcoded credentials

4. **Deploy**:
   - App Runner will build and deploy automatically
   - Health check endpoint: `/api/health`
   - Application will be available at the provided App Runner URL

## Health Check

The application exposes a health check endpoint at `/api/health` that App Runner uses to monitor service health.

## Static Files

Static files (HTML, CSS, JS, images) are served from the `/static` directory via FastAPI's StaticFiles middleware.

## Troubleshooting

- **Build failures**: Check that `requirements.txt` is at repository root
- **Runtime errors**: Verify environment variables are set correctly
- **Model access errors**: Ensure Bedrock model access is enabled in console
- **Port issues**: App Runner expects port 8080 (configurable via PORT env var)
