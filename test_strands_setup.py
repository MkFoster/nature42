"""
Test script to verify Strands Agent SDK installation and Bedrock connectivity.

This script creates a simple test agent and verifies:
1. Strands SDK is properly installed
2. AWS Bedrock credentials are configured
3. Model access is enabled
4. Basic agent functionality works

IMPORTANT: Python 3.11, 3.12, or 3.13 required. Python 3.14 is not yet supported
due to pydantic-core compatibility issues.

Run this after setting up your environment variables:
    export AWS_BEDROCK_API_KEY=your_key
    # OR
    export AWS_ACCESS_KEY_ID=your_id
    export AWS_SECRET_ACCESS_KEY=your_secret
    export AWS_REGION=us-west-2
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def check_environment():
    """Check if required environment variables are set."""
    print("Checking environment configuration...")
    
    # Check for Bedrock API key (development)
    has_api_key = bool(os.environ.get("AWS_BEDROCK_API_KEY"))
    
    # Check for AWS credentials (production)
    has_aws_creds = all([
        os.environ.get("AWS_ACCESS_KEY_ID"),
        os.environ.get("AWS_SECRET_ACCESS_KEY"),
        os.environ.get("AWS_REGION")
    ])
    
    if has_api_key:
        print("✓ AWS_BEDROCK_API_KEY is set")
        return True
    elif has_aws_creds:
        print("✓ AWS credentials are configured")
        return True
    else:
        print("✗ No AWS credentials found!")
        print("\nPlease set one of the following:")
        print("  Option 1 (Development):")
        print("    export AWS_BEDROCK_API_KEY=your_bedrock_api_key")
        print("\n  Option 2 (Production):")
        print("    export AWS_ACCESS_KEY_ID=your_access_key_id")
        print("    export AWS_SECRET_ACCESS_KEY=your_secret_access_key")
        print("    export AWS_REGION=us-west-2")
        return False


def test_imports():
    """Test that Strands SDK is properly installed."""
    print("\nTesting Strands SDK imports...")
    
    try:
        from strands import Agent
        from strands.models import BedrockModel
        print("✓ Strands SDK imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import Strands SDK: {e}")
        print("\nPlease install the SDK:")
        print("  pip install strands-agents strands-agents-tools")
        return False


def test_agent_creation():
    """Test creating a basic agent."""
    print("\nTesting agent creation...")
    
    try:
        from strands import Agent
        
        # Create a simple agent with default Bedrock model
        agent = Agent(
            system_prompt="You are a helpful assistant. Respond briefly."
        )
        
        print("✓ Agent created successfully")
        return agent
    except Exception as e:
        print(f"✗ Failed to create agent: {e}")
        print("\nCommon issues:")
        print("  - Model access not enabled in Bedrock console")
        print("  - Invalid or expired API key")
        print("  - Incorrect AWS credentials")
        return None


def test_agent_response(agent):
    """Test getting a response from the agent."""
    print("\nTesting agent response...")
    
    try:
        response = agent("Say 'Hello from Nature42!' and nothing else.")
        print(f"✓ Agent responded: {response}")
        return True
    except Exception as e:
        print(f"✗ Failed to get response: {e}")
        print("\nCommon issues:")
        print("  - Model access not enabled in Bedrock console")
        print("  - Network connectivity issues")
        print("  - API rate limiting")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Strands Agent SDK Setup Verification")
    print("=" * 60)
    
    # Run checks
    if not check_environment():
        sys.exit(1)
    
    if not test_imports():
        sys.exit(1)
    
    agent = test_agent_creation()
    if not agent:
        sys.exit(1)
    
    if not test_agent_response(agent):
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ All tests passed! Strands SDK is ready to use.")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Enable model access in Bedrock console if not already done")
    print("  2. Start building your Nature42 game agent")
    print("  3. See DEPLOYMENT.md for production deployment guide")


if __name__ == "__main__":
    main()
