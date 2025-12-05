"""
Sharing service for Nature42.

Handles generation of shareable postcards and unique share codes.
"""

import secrets
import string
from datetime import datetime
from typing import Dict, Optional

from backend.models.game_state import GameState, LocationData
from backend.models.share import ShareablePostcard


class SharingService:
    """
    Service for creating and managing shareable postcards.
    
    Generates unique share codes and creates formatted summaries
    that exclude puzzle solutions and spoiler information.
    """
    
    def __init__(self):
        """Initialize the sharing service with in-memory storage."""
        # In-memory storage for shares (in production, use database)
        self._shares: Dict[str, ShareablePostcard] = {}
    
    def generate_share_code(self, length: int = 8) -> str:
        """
        Generate a unique share code.
        
        Creates a cryptographically secure random code using uppercase letters
        and digits. Ensures uniqueness by checking against existing codes.
        
        Args:
            length: Length of the share code (default: 8)
            
        Returns:
            Unique share code string
        """
        alphabet = string.ascii_uppercase + string.digits
        
        # Keep generating until we get a unique code
        while True:
            code = ''.join(secrets.choice(alphabet) for _ in range(length))
            if code not in self._shares:
                return code
    
    def create_postcard(
        self,
        game_state: GameState,
        location_id: Optional[str] = None
    ) -> ShareablePostcard:
        """
        Create a shareable postcard from game state.
        
        Generates a formatted summary with location image, description,
        and keys collected count. Excludes puzzle solutions and other
        spoiler information.
        
        Args:
            game_state: Current game state
            location_id: Specific location to share (defaults to current location)
            
        Returns:
            ShareablePostcard object
            
        Raises:
            ValueError: If location not found in visited locations
        """
        # Determine which location to share
        target_location_id = location_id or game_state.player_location
        
        # Get location data
        if target_location_id not in game_state.visited_locations:
            raise ValueError(f"Location '{target_location_id}' not found in visited locations")
        
        location: LocationData = game_state.visited_locations[target_location_id]
        
        # Generate unique share code
        share_code = self.generate_share_code()
        
        # Create postcard (excluding puzzle solutions and spoilers)
        postcard = ShareablePostcard(
            share_code=share_code,
            location_name=location.id,
            location_description=location.description,
            location_image_url=location.image_url,
            keys_collected=len(game_state.keys_collected),
            created_at=datetime.now()
        )
        
        # Store the postcard
        self._shares[share_code] = postcard
        
        return postcard
    
    def get_postcard(self, share_code: str) -> Optional[ShareablePostcard]:
        """
        Retrieve a postcard by share code.
        
        Args:
            share_code: The unique share code
            
        Returns:
            ShareablePostcard if found, None otherwise
        """
        return self._shares.get(share_code)
    
    def list_shares(self) -> Dict[str, ShareablePostcard]:
        """
        Get all stored shares.
        
        Returns:
            Dictionary mapping share codes to postcards
        """
        return self._shares.copy()
    
    def delete_share(self, share_code: str) -> bool:
        """
        Delete a share by code.
        
        Args:
            share_code: The unique share code
            
        Returns:
            True if deleted, False if not found
        """
        if share_code in self._shares:
            del self._shares[share_code]
            return True
        return False


# Global instance for the application
_sharing_service: Optional[SharingService] = None


def get_sharing_service() -> SharingService:
    """
    Get the global sharing service instance.
    
    Returns:
        SharingService singleton instance
    """
    global _sharing_service
    if _sharing_service is None:
        _sharing_service = SharingService()
    return _sharing_service
