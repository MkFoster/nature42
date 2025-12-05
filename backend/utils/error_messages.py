"""
User-friendly error message templates for Nature42.

This module provides consistent, helpful error messages for players.

Implements Requirements 1.3, 5.5, 18.4
"""

from typing import Dict, Optional, List


class ErrorMessages:
    """
    Centralized error message templates with recovery options.
    """
    
    # Command Processing Errors (Requirement 1.3)
    
    COMMAND_EMPTY = {
        "message": "I didn't catch that. What would you like to do?",
        "suggestions": [
            "Try 'go [direction]' to move",
            "Try 'examine [object]' to look at something",
            "Try 'take [item]' to pick up an item",
            "Type 'help' for more commands"
        ]
    }
    
    COMMAND_AMBIGUOUS = {
        "message": "I'm not sure what you mean. Could you be more specific?",
        "suggestions": [
            "Try being more specific about what you want to do",
            "Include the object or direction you're referring to",
            "Type 'help' to see available commands"
        ]
    }
    
    COMMAND_INVALID = {
        "message": "I don't understand that command.",
        "suggestions": [
            "Try 'go [direction]' to move around",
            "Try 'examine area' to look around",
            "Try 'check inventory' to see what you're carrying",
            "Type 'help' for a list of commands"
        ]
    }
    
    COMMAND_PROCESSING_FAILED = {
        "message": "I'm having trouble processing that command right now.",
        "suggestions": [
            "Try rephrasing your command",
            "Try a simpler action like 'go north' or 'look around'",
            "Wait a moment and try again"
        ]
    }
    
    # State Management Errors (Requirement 5.5)
    
    STATE_CORRUPTED = {
        "message": "Your game save appears to be corrupted. This can happen if your browser storage was cleared or modified.",
        "suggestions": [
            "Start a new game to continue playing",
            "Check if you have another save in a different browser",
            "Make sure cookies and local storage are enabled"
        ],
        "recovery_action": "start_new_game"
    }
    
    STATE_INVALID = {
        "message": "There's a problem with your game state. Some data doesn't look right.",
        "suggestions": [
            "Try refreshing the page",
            "If the problem persists, start a new game",
            "Your progress may have been partially lost"
        ],
        "recovery_action": "refresh_or_new_game"
    }
    
    STATE_SAVE_FAILED = {
        "message": "I couldn't save your progress. Your game state might not be preserved.",
        "suggestions": [
            "Check if your browser has enough storage space",
            "Make sure cookies and local storage are enabled",
            "Try clearing old browser data",
            "Continue playing, but be aware progress may not save"
        ]
    }
    
    STATE_LOAD_FAILED = {
        "message": "I couldn't load your saved game.",
        "suggestions": [
            "Start a new game to begin playing",
            "Check if cookies and local storage are enabled",
            "Your save may have been cleared by your browser"
        ],
        "recovery_action": "start_new_game"
    }
    
    # AI Service Errors (Requirement 11.3, 11.4)
    
    AI_UNAVAILABLE = {
        "message": "The AI service is temporarily unavailable. This might be a connection issue.",
        "suggestions": [
            "Check your internet connection",
            "Wait a moment and try again",
            "Refresh the page if the problem persists",
            "The service may be experiencing high demand"
        ]
    }
    
    AI_TIMEOUT = {
        "message": "The AI is taking longer than expected to respond.",
        "suggestions": [
            "Try your command again",
            "Try a simpler command",
            "Check your internet connection",
            "The service may be slow right now"
        ]
    }
    
    CONTENT_GENERATION_FAILED = {
        "message": "I'm having trouble generating content for this area.",
        "suggestions": [
            "Try your action again",
            "Try moving to a different area",
            "The AI service may be temporarily overloaded"
        ]
    }
    
    # Streaming Errors (Requirement 18.4)
    
    STREAM_INTERRUPTED = {
        "message": "The connection was interrupted while I was responding.",
        "suggestions": [
            "Try your command again",
            "Check your internet connection",
            "Refresh the page if problems continue"
        ]
    }
    
    STREAM_FAILED = {
        "message": "I couldn't stream the response to you.",
        "suggestions": [
            "Try again in a moment",
            "Check your internet connection",
            "Refresh the page if the problem persists"
        ]
    }
    
    # Network Errors
    
    NETWORK_ERROR = {
        "message": "There's a problem connecting to the game server.",
        "suggestions": [
            "Check your internet connection",
            "Try refreshing the page",
            "Wait a moment and try again",
            "The server may be temporarily down"
        ]
    }
    
    SERVER_ERROR = {
        "message": "The game server encountered an error.",
        "suggestions": [
            "Try your action again",
            "Refresh the page if problems continue",
            "The server may be experiencing issues",
            "Your progress should be saved locally"
        ]
    }
    
    # Generic Fallback
    
    UNKNOWN_ERROR = {
        "message": "Something unexpected happened.",
        "suggestions": [
            "Try your action again",
            "Refresh the page if problems continue",
            "Start a new game if the problem persists",
            "Your progress should be saved locally"
        ]
    }
    
    @staticmethod
    def format_error(
        error_key: str,
        custom_message: Optional[str] = None,
        additional_suggestions: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """
        Format an error message with suggestions and recovery options.
        
        Args:
            error_key: Key for the error template (e.g., "STATE_CORRUPTED")
            custom_message: Optional custom message to override template
            additional_suggestions: Optional additional suggestions to append
            
        Returns:
            Dictionary with formatted error information
        """
        # Get template
        template = getattr(ErrorMessages, error_key, ErrorMessages.UNKNOWN_ERROR)
        
        # Build response
        response = {
            "success": False,
            "error_type": error_key,
            "message": custom_message or template["message"],
            "suggestions": template.get("suggestions", []).copy()
        }
        
        # Add additional suggestions if provided
        if additional_suggestions:
            response["suggestions"].extend(additional_suggestions)
        
        # Add recovery action if available
        if "recovery_action" in template:
            response["recovery_action"] = template["recovery_action"]
        
        return response
    
    @staticmethod
    def get_help_message() -> str:
        """
        Get a helpful message about available commands.
        
        Returns:
            Help message string
        """
        return """
**Available Commands:**

**Movement:**
- go [direction] - Move in a direction (north, south, east, west, etc.)
- enter [place] - Enter a location
- back / return - Return to the forest clearing

**Interaction:**
- examine [object] - Look at something closely
- examine area - Look around your current location
- take [item] - Pick up an item
- drop [item] - Drop an item from your inventory
- use [item] - Use an item
- talk to [npc] - Speak with someone

**Game Actions:**
- open door [number] - Open one of the six doors (1-6)
- insert key - Insert a key into the vault
- check inventory - See what you're carrying
- hint - Get a hint for the current challenge

**Other:**
- help - Show this help message
- new game - Start a new game

You can use natural language - I'll do my best to understand what you mean!
"""
    
    @staticmethod
    def get_recovery_instructions(recovery_action: str) -> str:
        """
        Get instructions for a specific recovery action.
        
        Args:
            recovery_action: The recovery action identifier
            
        Returns:
            Instructions string
        """
        instructions = {
            "start_new_game": "Click the 'New Game' button or type 'new game' to start fresh.",
            "refresh_or_new_game": "Try refreshing the page first. If that doesn't work, start a new game.",
            "refresh_page": "Refresh your browser page to reload the game.",
            "check_connection": "Check your internet connection and try again.",
            "wait_and_retry": "Wait a moment for the service to recover, then try again."
        }
        
        return instructions.get(recovery_action, "Try again or contact support if the problem persists.")


def get_contextual_error_message(
    error_type: str,
    context: Optional[Dict[str, any]] = None
) -> Dict[str, any]:
    """
    Get a contextual error message based on error type and game context.
    
    Args:
        error_type: Type of error that occurred
        context: Optional context information (location, action, etc.)
        
    Returns:
        Formatted error message dictionary
    """
    context = context or {}
    
    # Map error types to message keys
    error_map = {
        "CommandProcessingError": "COMMAND_PROCESSING_FAILED",
        "StateValidationError": "STATE_INVALID",
        "StrandsUnavailableError": "AI_UNAVAILABLE",
        "ContentGenerationError": "CONTENT_GENERATION_FAILED",
        "StorageError": "STATE_SAVE_FAILED",
        "NetworkError": "NETWORK_ERROR",
        "TimeoutError": "AI_TIMEOUT"
    }
    
    error_key = error_map.get(error_type, "UNKNOWN_ERROR")
    
    # Add contextual suggestions
    additional_suggestions = []
    
    if context.get("action") == "move" and error_type == "CommandProcessingError":
        additional_suggestions.append("Try 'examine area' to see available exits")
    
    if context.get("location") == "forest_clearing" and error_type == "ContentGenerationError":
        additional_suggestions.append("The forest clearing should always be available - try 'examine area'")
    
    return ErrorMessages.format_error(error_key, additional_suggestions=additional_suggestions)
