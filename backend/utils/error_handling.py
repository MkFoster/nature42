"""
Error handling utilities for Nature42.

This module provides comprehensive error handling including:
- Custom exception classes
- Retry logic with exponential backoff
- Error response formatting
- Logging utilities

Implements Requirements 11.3, 11.4
"""

import asyncio
import logging
import time
from typing import Optional, Callable, Any, TypeVar, Dict
from functools import wraps
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


# Custom Exception Classes

class Nature42Error(Exception):
    """Base exception for all Nature42 errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class StrandsUnavailableError(Nature42Error):
    """Raised when Strands SDK is unavailable or fails."""
    pass


class ContentGenerationError(Nature42Error):
    """Raised when content generation fails."""
    pass


class StateValidationError(Nature42Error):
    """Raised when game state validation fails."""
    pass


class CommandProcessingError(Nature42Error):
    """Raised when command processing fails."""
    pass


class StorageError(Nature42Error):
    """Raised when storage operations fail."""
    pass


# Retry Logic with Exponential Backoff

@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True  # Add randomness to prevent thundering herd


def calculate_backoff_delay(
    attempt: int,
    config: RetryConfig
) -> float:
    """
    Calculate delay for exponential backoff.
    
    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration
        
    Returns:
        Delay in seconds
    """
    import random
    
    # Calculate exponential delay
    delay = min(
        config.initial_delay * (config.exponential_base ** attempt),
        config.max_delay
    )
    
    # Add jitter if enabled
    if config.jitter:
        delay = delay * (0.5 + random.random() * 0.5)
    
    return delay


def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        config: Retry configuration (uses defaults if None)
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback called on each retry
        
    Example:
        @retry_with_backoff(
            config=RetryConfig(max_attempts=3),
            exceptions=(StrandsUnavailableError,)
        )
        async def call_strands_api():
            # API call here
            pass
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < config.max_attempts - 1:
                        delay = calculate_backoff_delay(attempt, config)
                        
                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        
                        if on_retry:
                            on_retry(e, attempt)
                        
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} attempts failed for {func.__name__}: {e}"
                        )
            
            # All attempts failed
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < config.max_attempts - 1:
                        delay = calculate_backoff_delay(attempt, config)
                        
                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        
                        if on_retry:
                            on_retry(e, attempt)
                        
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} attempts failed for {func.__name__}: {e}"
                        )
            
            # All attempts failed
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Error Response Formatting

def format_error_response(
    error: Exception,
    user_friendly: bool = True,
    include_details: bool = False
) -> Dict[str, Any]:
    """
    Format an error into a standardized response.
    
    Args:
        error: The exception to format
        user_friendly: Whether to use user-friendly messages
        include_details: Whether to include technical details
        
    Returns:
        Dictionary with error information
    """
    response = {
        "success": False,
        "error_type": type(error).__name__
    }
    
    # Handle custom Nature42 errors
    if isinstance(error, Nature42Error):
        if user_friendly:
            response["message"] = get_user_friendly_message(error)
        else:
            response["message"] = error.message
        
        if include_details and error.details:
            response["details"] = error.details
    else:
        # Generic error
        if user_friendly:
            response["message"] = "An unexpected error occurred. Please try again."
        else:
            response["message"] = str(error)
    
    return response


def get_user_friendly_message(error: Nature42Error) -> str:
    """
    Get a user-friendly error message.
    
    Implements Requirement 1.3, 5.5, 18.4: User-friendly error messages
    
    Args:
        error: The Nature42 error
        
    Returns:
        User-friendly message string
    """
    if isinstance(error, StrandsUnavailableError):
        return (
            "The AI service is temporarily unavailable. "
            "Please check your connection and try again in a moment."
        )
    
    elif isinstance(error, ContentGenerationError):
        return (
            "I'm having trouble generating content right now. "
            "Please try your command again."
        )
    
    elif isinstance(error, StateValidationError):
        return (
            "There's an issue with your game state. "
            "You may need to start a new game. "
            "Your progress might be corrupted."
        )
    
    elif isinstance(error, CommandProcessingError):
        return (
            "I couldn't understand that command. "
            "Try rephrasing or type 'help' for assistance."
        )
    
    elif isinstance(error, StorageError):
        return (
            "There was a problem saving your progress. "
            "Your game state might not be preserved."
        )
    
    else:
        return (
            "Something unexpected happened. "
            "Please try again or start a new game if the problem persists."
        )


# Health Check Utilities

async def check_strands_health() -> Dict[str, Any]:
    """
    Check if Strands SDK is available and functioning.
    
    Implements Requirement 11.3: Handle Strands SDK unavailability
    
    Returns:
        Dictionary with health status
    """
    try:
        from strands import Agent
        from strands.models import BedrockModel
        
        # Try to create a simple agent
        model = BedrockModel(
            model_id="anthropic.claude-sonnet-4-20250514-v1:0",
            temperature=0.1,
            max_tokens=100
        )
        
        agent = Agent(
            model=model,
            system_prompt="You are a health check agent. Respond with 'OK'."
        )
        
        # Try a simple call with timeout
        response = agent("Health check")
        
        return {
            "healthy": True,
            "service": "strands",
            "message": "Strands SDK is available"
        }
        
    except ImportError as e:
        logger.error(f"Strands SDK not installed: {e}")
        return {
            "healthy": False,
            "service": "strands",
            "message": "Strands SDK not installed",
            "error": str(e)
        }
    
    except Exception as e:
        logger.error(f"Strands SDK health check failed: {e}")
        return {
            "healthy": False,
            "service": "strands",
            "message": "Strands SDK unavailable",
            "error": str(e)
        }


# Graceful Degradation

class GracefulDegradation:
    """
    Provides fallback behavior when services are unavailable.
    """
    
    @staticmethod
    def get_fallback_location_description(location_id: str) -> str:
        """
        Get a fallback location description when AI generation fails.
        
        Args:
            location_id: Location identifier
            
        Returns:
            Generic location description
        """
        return (
            f"You find yourself in a mysterious location ({location_id}). "
            "The details are hazy, but you sense there's more to discover here. "
            "Try examining your surroundings or looking for exits."
        )
    
    @staticmethod
    def get_fallback_command_response() -> str:
        """
        Get a fallback response when command processing fails.
        
        Returns:
            Generic command response
        """
        return (
            "I'm having trouble processing that command right now. "
            "Try a simpler command like 'go north', 'examine area', or 'check inventory'."
        )
    
    @staticmethod
    def get_fallback_npc_dialogue(npc_name: str) -> str:
        """
        Get a fallback NPC dialogue when AI generation fails.
        
        Args:
            npc_name: Name of the NPC
            
        Returns:
            Generic NPC dialogue
        """
        return (
            f"{npc_name} seems distracted and doesn't respond clearly. "
            "Perhaps try talking to them again later."
        )


# Context Manager for Error Handling

class ErrorContext:
    """
    Context manager for handling errors with logging and recovery.
    
    Example:
        async with ErrorContext("generate_location", recovery_fn=fallback_fn):
            location = await generator.generate_location(...)
    """
    
    def __init__(
        self,
        operation_name: str,
        recovery_fn: Optional[Callable[[], Any]] = None,
        log_errors: bool = True
    ):
        self.operation_name = operation_name
        self.recovery_fn = recovery_fn
        self.log_errors = log_errors
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if self.log_errors:
                logger.error(
                    f"Error in {self.operation_name}: {exc_type.__name__}: {exc_val}"
                )
            
            if self.recovery_fn:
                try:
                    return await self.recovery_fn()
                except Exception as recovery_error:
                    logger.error(
                        f"Recovery function failed for {self.operation_name}: {recovery_error}"
                    )
        
        return False  # Don't suppress the exception
