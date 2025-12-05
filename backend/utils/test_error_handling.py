"""
Tests for error handling utilities.

This module tests the error handling, retry logic, and user-friendly messages.
"""

import pytest
import asyncio
from backend.utils.error_handling import (
    Nature42Error,
    StrandsUnavailableError,
    ContentGenerationError,
    StateValidationError,
    CommandProcessingError,
    StorageError,
    RetryConfig,
    retry_with_backoff,
    format_error_response,
    get_user_friendly_message,
    GracefulDegradation
)
from backend.utils.error_messages import (
    ErrorMessages,
    get_contextual_error_message
)


def test_custom_exceptions():
    """Test custom exception classes."""
    # Test base exception
    error = Nature42Error("Test error", details={"key": "value"})
    assert error.message == "Test error"
    assert error.details == {"key": "value"}
    
    # Test specific exceptions
    strands_error = StrandsUnavailableError("Strands down")
    assert isinstance(strands_error, Nature42Error)
    
    content_error = ContentGenerationError("Generation failed")
    assert isinstance(content_error, Nature42Error)
    
    state_error = StateValidationError("Invalid state")
    assert isinstance(state_error, Nature42Error)
    
    command_error = CommandProcessingError("Command failed")
    assert isinstance(command_error, Nature42Error)
    
    storage_error = StorageError("Storage failed")
    assert isinstance(storage_error, Nature42Error)
    
    print("✓ Custom exceptions work correctly")


def test_format_error_response():
    """Test error response formatting."""
    error = StrandsUnavailableError("Service down", details={"status": 503})
    
    # User-friendly format
    response = format_error_response(error, user_friendly=True)
    assert response["success"] is False
    assert "AI service" in response["message"]
    assert response["error_type"] == "StrandsUnavailableError"
    
    # Technical format
    response = format_error_response(error, user_friendly=False, include_details=True)
    assert response["message"] == "Service down"
    assert response["details"] == {"status": 503}
    
    print("✓ Error response formatting works correctly")


def test_user_friendly_messages():
    """Test user-friendly message generation."""
    # Test different error types
    strands_error = StrandsUnavailableError("Test")
    message = get_user_friendly_message(strands_error)
    assert "AI service" in message
    assert "temporarily unavailable" in message
    
    content_error = ContentGenerationError("Test")
    message = get_user_friendly_message(content_error)
    assert "generating content" in message
    
    state_error = StateValidationError("Test")
    message = get_user_friendly_message(state_error)
    assert "game state" in message
    
    command_error = CommandProcessingError("Test")
    message = get_user_friendly_message(command_error)
    assert "command" in message
    
    storage_error = StorageError("Test")
    message = get_user_friendly_message(storage_error)
    assert "saving" in message or "progress" in message
    
    print("✓ User-friendly messages work correctly")


@pytest.mark.asyncio
async def test_retry_with_backoff_success():
    """Test retry logic with successful execution."""
    call_count = 0
    
    @retry_with_backoff(
        config=RetryConfig(max_attempts=3, initial_delay=0.1),
        exceptions=(ValueError,)
    )
    async def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Temporary failure")
        return "success"
    
    result = await flaky_function()
    assert result == "success"
    assert call_count == 2  # Failed once, succeeded on second try
    
    print("✓ Retry with backoff works for async functions")


@pytest.mark.asyncio
async def test_retry_with_backoff_failure():
    """Test retry logic with all attempts failing."""
    call_count = 0
    
    @retry_with_backoff(
        config=RetryConfig(max_attempts=3, initial_delay=0.1),
        exceptions=(ValueError,)
    )
    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise ValueError("Always fails")
    
    with pytest.raises(ValueError):
        await always_fails()
    
    assert call_count == 3  # All 3 attempts were made
    
    print("✓ Retry exhausts all attempts before failing")


def test_retry_sync_function():
    """Test retry logic with synchronous functions."""
    call_count = 0
    
    @retry_with_backoff(
        config=RetryConfig(max_attempts=3, initial_delay=0.1),
        exceptions=(ValueError,)
    )
    def flaky_sync_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Temporary failure")
        return "success"
    
    result = flaky_sync_function()
    assert result == "success"
    assert call_count == 2
    
    print("✓ Retry with backoff works for sync functions")


def test_graceful_degradation():
    """Test graceful degradation fallbacks."""
    # Test fallback location description
    desc = GracefulDegradation.get_fallback_location_description("test_location")
    assert "test_location" in desc
    assert len(desc) > 0
    
    # Test fallback command response
    response = GracefulDegradation.get_fallback_command_response()
    assert len(response) > 0
    assert "command" in response.lower()
    
    # Test fallback NPC dialogue
    dialogue = GracefulDegradation.get_fallback_npc_dialogue("TestNPC")
    assert "TestNPC" in dialogue
    assert len(dialogue) > 0
    
    print("✓ Graceful degradation fallbacks work correctly")


def test_error_messages_templates():
    """Test error message templates."""
    # Test command error
    error = ErrorMessages.format_error("COMMAND_EMPTY")
    assert error["success"] is False
    assert len(error["suggestions"]) > 0
    
    # Test state error with recovery action
    error = ErrorMessages.format_error("STATE_CORRUPTED")
    assert "recovery_action" in error
    assert error["recovery_action"] == "start_new_game"
    
    # Test AI error
    error = ErrorMessages.format_error("AI_UNAVAILABLE")
    assert "AI service" in error["message"]
    
    # Test with custom message
    error = ErrorMessages.format_error("COMMAND_INVALID", custom_message="Custom error")
    assert error["message"] == "Custom error"
    
    # Test with additional suggestions
    error = ErrorMessages.format_error("COMMAND_INVALID", additional_suggestions=["Extra tip"])
    assert "Extra tip" in error["suggestions"]
    
    print("✓ Error message templates work correctly")


def test_contextual_error_messages():
    """Test contextual error message generation."""
    # Test with error type
    error = get_contextual_error_message("CommandProcessingError")
    assert error["success"] is False
    assert len(error["message"]) > 0
    
    # Test with context
    error = get_contextual_error_message(
        "CommandProcessingError",
        context={"action": "move"}
    )
    assert len(error["suggestions"]) > 0
    
    # Test unknown error type
    error = get_contextual_error_message("UnknownError")
    assert error["error_type"] == "UNKNOWN_ERROR"
    
    print("✓ Contextual error messages work correctly")


def test_help_message():
    """Test help message generation."""
    help_text = ErrorMessages.get_help_message()
    assert len(help_text) > 0
    assert "go" in help_text.lower()
    assert "examine" in help_text.lower()
    assert "take" in help_text.lower()
    
    print("✓ Help message generation works correctly")


def test_recovery_instructions():
    """Test recovery instruction generation."""
    instructions = ErrorMessages.get_recovery_instructions("start_new_game")
    assert len(instructions) > 0
    assert "new game" in instructions.lower()
    
    instructions = ErrorMessages.get_recovery_instructions("refresh_page")
    assert "refresh" in instructions.lower()
    
    # Test unknown recovery action
    instructions = ErrorMessages.get_recovery_instructions("unknown_action")
    assert len(instructions) > 0
    
    print("✓ Recovery instructions work correctly")


if __name__ == "__main__":
    print("Running error handling tests...\n")
    
    try:
        # Run synchronous tests
        test_custom_exceptions()
        test_format_error_response()
        test_user_friendly_messages()
        test_retry_sync_function()
        test_graceful_degradation()
        test_error_messages_templates()
        test_contextual_error_messages()
        test_help_message()
        test_recovery_instructions()
        
        # Run async tests
        asyncio.run(test_retry_with_backoff_success())
        asyncio.run(test_retry_with_backoff_failure())
        
        print("\n" + "=" * 60)
        print("✓ All error handling tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise
