# AWS App Runner Deployment Guide

## Prerequisites

1. **AWS Account** with access to AWS App Runner and Amazon Bedrock
2. **Bedrock Model Access**: Enable Claude 4 Sonnet in Bedrock Console
   - Navigate to: Bedrock Console → Model access → Manage model access
   - Enable: `anthropic.claude-sonnet-4-20250514-v1:0`

## Environment Variables

Configure the following environment variables in App Runner:

### Required for Development
- `AWS_BEDROCK_API_KEY`: Bedrock API key (30-day expiration)
  - Generate from: Bedrock Console → API keys

### Required for Production
- `AWS_ACCESS_KEY_ID`: IAM access key
- `AWS_SECRET_ACCESS_KEY`: IAM secret key
- `AWS_REGION`: AWS region (e.g., `us-west-2`)

### Optional Configuration
- `PORT`: Application port (default: 8080)
- `STRANDS_MODEL_ID`: Bedrock model ID (default: `anthropic.claude-sonnet-4-20250514-v1:0`)
- `STRANDS_TEMPERATURE`: Model temperature (default: 0.7)
- `STRANDS_MAX_TOKENS`: Max tokens per response (default: 4096)

## Deployment Steps

1. **Push code to repository** (GitHub, GitLab, Bitbucket, or AWS CodeCommit)

2. **Create App Runner service**:
   - Go to AWS App Runner console
   - Click "Create service"
   - Select your repository
   - Choose "Python 3.11" runtime
   - App Runner will automatically detect `apprunner.yaml`

3. **Configure environment variables**:
   - In service settings, add required environment variables
   - For development: Add `AWS_BEDROCK_API_KEY`
   - For production: Add IAM credentials

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
