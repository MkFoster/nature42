"""
State management API endpoints for Nature42.

Handles game state retrieval, saving, and deletion.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from backend.models import GameState

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
        
        return JSONResponse(
            content={
                "success": True,
                "message": "State validated successfully",
                "note": "State is managed client-side in browser storage"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid state structure: {str(e)}"
        )


@router.delete("/api/state")
async def delete_state():
    """
    Delete game state (start new game).
    
    Note: In this implementation, state is managed client-side in browser storage.
    This endpoint provides a new game state template.
    
    Returns:
        JSON response with new game state
    """
    new_state = GameState.create_new_game()
    
    return JSONResponse(
        content={
            "success": True,
            "message": "New game state created",
            "state": new_state.to_dict()
        }
    )


@router.post("/api/state/validate")
async def validate_state(state: dict):
    """
    Validate game state structure without saving.
    
    Args:
        state: Game state dictionary to validate
        
    Returns:
        JSON response with validation result
    """
    try:
        # Attempt to deserialize to validate structure
        game_state = GameState.from_dict(state)
        
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
        return JSONResponse(
            status_code=200,  # Return 200 but indicate invalid
            content={
                "success": True,
                "valid": False,
                "message": "State structure is invalid",
                "error": str(e)
            }
        )
