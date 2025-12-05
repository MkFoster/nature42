"""
State management API endpoints for Nature42.

Handles game state retrieval, saving, and deletion.

Implements Requirements 5.5, 11.4: Error handling for corrupted state
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from backend.models import GameState
from backend.utils.error_handling import (
    StateValidationError,
    format_error_response,
    logger
)

router = APIRouter()


class StateResponse(BaseModel):
    """Response model for state operations."""
    success: bool
    message: str
    state: Optional[dict] = None


@router.get("/api/state")
async def get_state():
    """
    Get current game state.
    
    Note: In this implementation, state is managed client-side in browser storage.
    This endpoint is provided for future server-side state management.
    
    Returns:
        JSON response with state information
    """
    return JSONResponse(
        content={
            "success": True,
            "message": "State management is client-side. Use browser storage.",
            "note": "This endpoint is reserved for future server-side state management"
        }
    )


@router.post("/api/state")
async def save_state(state: dict):
    """
    Save game state.
    
    Implements Requirement 5.5: Handle corrupted storage gracefully
    
    Note: In this implementation, state is managed client-side in browser storage.
    This endpoint validates the state structure but doesn't persist it server-side.
    
    Args:
        state: Game state dictionary
        
    Returns:
        JSON response confirming validation
    """
    try:
        # Validate state structure by attempting to deserialize
        game_state = GameState.from_dict(state)
        
        # Additional validation checks
        if not game_state.player_location:
            raise StateValidationError(
                "Invalid state: missing player location",
                details={"state": state}
            )
        
        if game_state.keys_collected and not all(1 <= k <= 6 for k in game_state.keys_collected):
            raise StateValidationError(
                "Invalid state: invalid key numbers",
                details={"keys": game_state.keys_collected}
            )
        
        return JSONResponse(
            content={
                "success": True,
                "message": "State validated successfully",
                "note": "State is managed client-side in browser storage"
            }
        )
    
    except StateValidationError as e:
        logger.error(f"State validation error: {e.message}")
        error_response = format_error_response(e, user_friendly=True)
        raise HTTPException(
            status_code=400,
            detail=error_response['message']
        )
    
    except Exception as e:
        logger.error(f"Error validating state: {e}")
        raise HTTPException(
            status_code=400,
            detail="Your game state appears to be corrupted. You may need to start a new game."
        )


@router.delete("/api/state")
async def delete_state():
    """
    Delete game state (start new game).
    
    Implements Requirement 5.5: Offer to start new game when state is corrupted
    
    Note: In this implementation, state is managed client-side in browser storage.
    This endpoint provides a new game state template.
    
    Returns:
        JSON response with new game state
    """
    try:
        new_state = GameState.create_new_game()
        
        return JSONResponse(
            content={
                "success": True,
                "message": "New game state created",
                "state": new_state.to_dict()
            }
        )
    
    except Exception as e:
        logger.error(f"Error creating new game state: {e}")
        raise HTTPException(
            status_code=500,
            detail="Unable to create new game. Please refresh the page and try again."
        )


@router.post("/api/state/validate")
async def validate_state(state: dict):
    """
    Validate game state structure without saving.
    
    Implements Requirement 5.5: Detect corrupted state
    
    Args:
        state: Game state dictionary to validate
        
    Returns:
        JSON response with validation result
    """
    try:
        # Attempt to deserialize to validate structure
        game_state = GameState.from_dict(state)
        
        # Perform additional validation
        validation_errors = []
        
        if not game_state.player_location:
            validation_errors.append("Missing player location")
        
        if game_state.keys_collected and not all(1 <= k <= 6 for k in game_state.keys_collected):
            validation_errors.append("Invalid key numbers")
        
        if len(game_state.keys_collected) > 6:
            validation_errors.append("Too many keys collected")
        
        if validation_errors:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "valid": False,
                    "message": "State has validation errors",
                    "errors": validation_errors
                }
            )
        
        return JSONResponse(
            content={
                "success": True,
                "valid": True,
                "message": "State structure is valid",
                "details": {
                    "player_location": game_state.player_location,
                    "keys_collected": len(game_state.keys_collected),
                    "inventory_items": len(game_state.inventory),
                    "visited_locations": len(game_state.visited_locations)
                }
            }
        )
    
    except Exception as e:
        logger.warning(f"State validation failed: {e}")
        return JSONResponse(
            status_code=200,  # Return 200 but indicate invalid
            content={
                "success": True,
                "valid": False,
                "message": "State structure is invalid",
                "error": str(e),
                "recovery_suggestion": "Start a new game to continue playing"
            }
        )
