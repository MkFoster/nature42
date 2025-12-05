"""
Sharing API endpoints for Nature42.

Handles creation and retrieval of shareable postcards.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from backend.models import GameState
from backend.services.sharing import get_sharing_service

router = APIRouter()


class CreateShareRequest(BaseModel):
    """Request model for creating a share."""
    game_state: dict
    location_id: Optional[str] = None


class ShareResponse(BaseModel):
    """Response model for share operations."""
    success: bool
    message: str
    postcard: Optional[dict] = None


@router.post("/api/share")
async def create_share(request: CreateShareRequest):
    """
    Create a shareable postcard from game state.
    
    Generates a formatted summary with location image, description,
    and keys collected count. Excludes puzzle solutions and spoilers.
    
    Args:
        request: CreateShareRequest with game state and optional location ID
        
    Returns:
        JSON response with shareable postcard
        
    Raises:
        HTTPException: If game state is invalid or location not found
    """
    try:
        # Deserialize game state
        game_state = GameState.from_dict(request.game_state)
        
        # Get sharing service
        sharing_service = get_sharing_service()
        
        # Create postcard
        postcard = sharing_service.create_postcard(
            game_state=game_state,
            location_id=request.location_id
        )
        
        return JSONResponse(
            content={
                "success": True,
                "message": "Postcard created successfully",
                "postcard": postcard.to_dict()
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create postcard: {str(e)}"
        )


@router.get("/api/share/{share_code}")
async def get_share(share_code: str):
    """
    Retrieve a shareable postcard by share code.
    
    Args:
        share_code: Unique share code
        
    Returns:
        JSON response with postcard data
        
    Raises:
        HTTPException: If share code not found
    """
    sharing_service = get_sharing_service()
    postcard = sharing_service.get_postcard(share_code)
    
    if postcard is None:
        raise HTTPException(
            status_code=404,
            detail=f"Share code '{share_code}' not found"
        )
    
    return JSONResponse(
        content={
            "success": True,
            "message": "Postcard retrieved successfully",
            "postcard": postcard.to_dict()
        }
    )


@router.get("/api/shares")
async def list_shares():
    """
    List all stored shares.
    
    Returns:
        JSON response with all postcards
    """
    sharing_service = get_sharing_service()
    shares = sharing_service.list_shares()
    
    return JSONResponse(
        content={
            "success": True,
            "message": f"Retrieved {len(shares)} shares",
            "shares": {
                code: postcard.to_dict()
                for code, postcard in shares.items()
            }
        }
    )


@router.delete("/api/share/{share_code}")
async def delete_share(share_code: str):
    """
    Delete a share by code.
    
    Args:
        share_code: Unique share code
        
    Returns:
        JSON response confirming deletion
        
    Raises:
        HTTPException: If share code not found
    """
    sharing_service = get_sharing_service()
    deleted = sharing_service.delete_share(share_code)
    
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Share code '{share_code}' not found"
        )
    
    return JSONResponse(
        content={
            "success": True,
            "message": "Share deleted successfully"
        }
    )
