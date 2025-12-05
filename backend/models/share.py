"""
Share data models for Nature42.

These models represent shareable postcards that players can generate
to share their game progress and discoveries.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any
import json


@dataclass
class ShareablePostcard:
    """
    A shareable postcard containing non-spoiler game information.
    
    Includes location image, description, and keys collected count,
    but excludes puzzle solutions and other spoiler information.
    """
    share_code: str
    location_name: str
    location_description: str
    location_image_url: str
    keys_collected: int
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'share_code': self.share_code,
            'location_name': self.location_name,
            'location_description': self.location_description,
            'location_image_url': self.location_image_url,
            'keys_collected': self.keys_collected,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShareablePostcard':
        """Create ShareablePostcard from dictionary."""
        return cls(
            share_code=data['share_code'],
            location_name=data['location_name'],
            location_description=data['location_description'],
            location_image_url=data['location_image_url'],
            keys_collected=data['keys_collected'],
            created_at=datetime.fromisoformat(data['created_at'])
        )
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ShareablePostcard':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
