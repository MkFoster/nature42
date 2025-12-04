# Development Setup Guide

## Prerequisites

- Python 3.11, 3.12, or 3.13 (Python 3.14 not yet supported due to pydantic-core compatibility)
- pip package manager
- AWS account with Bedrock access

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd nature42
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# Activate on Windows
.venv\Scripts\activate

# Activate on macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI and Uvicorn (web framework)
- Strands Agent SDK (AI capabilities)
- Hypothesis (property-based testing)
- pytest (unit testing)
- Other utilities

### 4. Configure AWS Bedrock

#### Option A: Development (Recommended for Getting Started)

Use Bedrock API keys for quick setup:

1. **Get Bedrock API Key:**
   - Open [AWS Bedrock Console](https://console.aws.amazon.com/bedrock)
   - Navigate to "API keys" in the left sidebar
   - Click "Generate long-term API key"
   - Copy the key (shown only once!)
   - Note: Keys expire in 30 days

2. **Enable Model Access:**
   - In Bedrock Console, go to "Model access"
   - Click "Manage model access"
   - Enable "Claude 4 Sonnet" (`anthropic.claude-sonnet-4-20250514-v1:0`)
   - Wait a few minutes for access to propagate

3. **Set Environment Variable:**
   ```bash
   # Create .env file from template
   cp .env.example .env
   
   # Edit .env and add your key:
   AWS_BEDROCK_API_KEY=your_bedrock_api_key_here
   ```

#### Option B: Production (IAM Credentials)

For production deployments, use IAM credentials:

1. **Configure AWS CLI:**
   ```bash
   aws configure
   ```
   
   Or set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key_id
   export AWS_SECRET_ACCESS_KEY=your_secret_access_key
   export AWS_REGION=us-west-2
   ```

2. **Enable Model Access** (same as Option A step 2)

### 5. Verify Setup

Run the test script to verify everything is configured correctly:

```bash
python test_strands_setup.py
```

Expected output:
```
============================================================
Strands Agent SDK Setup Verification
============================================================
Checking environment configuration...
✓ AWS_BEDROCK_API_KEY is set

Testing Strands SDK imports...
✓ Strands SDK imported successfully

Testing agent creation...
✓ Agent created successfully

Testing agent response...
✓ Agent responded: Hello from Nature42!

============================================================
✓ All tests passed! Strands SDK is ready to use.
============================================================
```

### 6. Run the Application (Coming Soon)

Once the backend is implemented:

```bash
# Development server
uvicorn backend.main:app --reload --port 8080

# Production server
uvicorn backend.main:app --host 0.0.0.0 --port 8080
```

## Troubleshooting

### "Module 'strands' not found"

**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### "AWS credentials not found"

**Solution:** Set environment variables
```bash
# For development
export AWS_BEDROCK_API_KEY=your_key

# For production
aws configure
```

### "Access denied to model"

**Solution:** Enable model access in Bedrock console
1. Go to [Bedrock Console](https://console.aws.amazon.com/bedrock)
2. Click "Model access" → "Manage model access"
3. Enable Claude 4 Sonnet
4. Wait a few minutes

### "Invalid API key"

**Solution:** Check your API key
1. Verify the key is correct (no extra spaces)
2. Check if the key has expired (30-day limit)
3. Generate a new key if needed

### Test script fails

**Solution:** Run with verbose output
```bash
python test_strands_setup.py
```

Check the error message and follow the suggested fixes.

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `AWS_BEDROCK_API_KEY` | Yes (dev) | Bedrock API key for development |
| `AWS_ACCESS_KEY_ID` | Yes (prod) | AWS access key for production |
| `AWS_SECRET_ACCESS_KEY` | Yes (prod) | AWS secret key for production |
| `AWS_REGION` | Yes (prod) | AWS region (e.g., us-west-2) |
| `PORT` | No | Application port (default: 8080) |
| `STRANDS_MODEL_ID` | No | Bedrock model ID (default: Claude 4 Sonnet) |
| `STRANDS_TEMPERATURE` | No | Model temperature (default: 0.7) |
| `STRANDS_MAX_TOKENS` | No | Max tokens per response (default: 4096) |

## Next Steps

1. ✓ Complete setup and verification
2. Implement backend API (see tasks.md)
3. Build frontend terminal UI
4. Test locally
5. Deploy to AWS App Runner (see DEPLOYMENT.md)

## Additional Resources

- [Strands Agent SDK Documentation](https://docs.strands.ai/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hypothesis Testing Documentation](https://hypothesis.readthedocs.io/)
