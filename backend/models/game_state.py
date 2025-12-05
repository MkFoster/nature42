"""
Game state data models for Nature42.

These models represent the complete state of the game including player location,
inventory, collected keys, visited locations, NPC interactions, puzzles, and decisions.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any
import json


@dataclass
class Item:
    """An item in the game."""
    id: str
    name: str
    description: str
    is_key: bool = False
    door_number: Optional[int] = None  # If is_key, which door it belongs to
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Item':
        """Create Item from dictionary."""
        return cls(**data)


@dataclass
class LocationData:
    """Cached data for a generated location."""
    id: str
    description: str
    image_url: str
    exits: List[str]
    items: List[Item]
    npcs: List[str]
    generated_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'description': self.description,
            'image_url': self.image_url,
            'exits': self.exits,
            'items': [item.to_dict() for item in self.items],
            'npcs': self.npcs,
            'generated_at': self.generated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LocationData':
        """Create LocationData from dictionary."""
        return cls(
            id=data['id'],
            description=data['description'],
            image_url=data['image_url'],
            exits=data['exits'],
            items=[Item.from_dict(item) for item in data['items']],
            npcs=data['npcs'],
            generated_at=datetime.fromisoformat(data['generated_at'])
        )


@dataclass
class Interaction:
    """Record of player-NPC interaction."""
    timestamp: datetime
    npc_id: str
    player_action: str
    npc_response: str
    sentiment: str  # positive, neutral, negative

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'npc_id': self.npc_id,
            'player_action': self.player_action,
            'npc_response': self.npc_response,
            'sentiment': self.sentiment
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Interaction':
        """Create Interaction from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            npc_id=data['npc_id'],
            player_action=data['player_action'],
            npc_response=data['npc_response'],
            sentiment=data['sentiment']
        )


@dataclass
class PuzzleState:
    """State of a puzzle."""
    puzzle_id: str
    description: str
    solved: bool
    attempts: List[str]
    hints_given: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PuzzleState':
        """Create PuzzleState from dictionary."""
        return cls(**data)


@dataclass
class Decision:
    """Significant player choice."""
    timestamp: datetime
    location_id: str
    description: str
    consequences: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'location_id': self.location_id,
            'description': self.description,
            'consequences': self.consequences
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Decision':
        """Create Decision from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            location_id=data['location_id'],
            description=data['description'],
            consequences=data['consequences']
        )


@dataclass
class GameState:
    """Complete state of the game."""
    player_location: str
    inventory: List[Item]
    keys_collected: List[int]  # Door numbers (1-6)
    visited_locations: Dict[str, LocationData]
    npc_interactions: Dict[str, List[Interaction]]
    puzzle_states: Dict[str, PuzzleState]
    decision_history: List[Decision]
    current_door: Optional[int]  # Which door world player is in (None = clearing)
    game_started_at: datetime
    last_updated: datetime
    conversation_history: List[Dict[str, str]] = field(default_factory=list)  # AI conversation context

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'player_location': self.player_location,
            'inventory': [item.to_dict() for item in self.inventory],
            'keys_collected': self.keys_collected,
            'visited_locations': {
                loc_id: loc.to_dict() 
                for loc_id, loc in self.visited_locations.items()
            },
            'npc_interactions': {
                npc_id: [interaction.to_dict() for interaction in interactions]
                for npc_id, interactions in self.npc_interactions.items()
            },
            'puzzle_states': {
                puzzle_id: puzzle.to_dict()
                for puzzle_id, puzzle in self.puzzle_states.items()
            },
            'decision_history': [decision.to_dict() for decision in self.decision_history],
            'current_door': self.current_door,
            'game_started_at': self.game_started_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'conversation_history': self.conversation_history
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameState':
        """Create GameState from dictionary."""
        return cls(
            player_location=data['player_location'],
            inventory=[Item.from_dict(item) for item in data['inventory']],
            keys_collected=data['keys_collected'],
            visited_locations={
                loc_id: LocationData.from_dict(loc)
                for loc_id, loc in data['visited_locations'].items()
            },
            npc_interactions={
                npc_id: [Interaction.from_dict(interaction) for interaction in interactions]
                for npc_id, interactions in data['npc_interactions'].items()
            },
            puzzle_states={
                puzzle_id: PuzzleState.from_dict(puzzle)
                for puzzle_id, puzzle in data['puzzle_states'].items()
            },
            decision_history=[Decision.from_dict(decision) for decision in data['decision_history']],
            current_door=data['current_door'],
            game_started_at=datetime.fromisoformat(data['game_started_at']),
            last_updated=datetime.fromisoformat(data['last_updated']),
            conversation_history=data.get('conversation_history', [])
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'GameState':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def create_new_game(cls) -> 'GameState':
        """
        Create a new game state with default values.
        
        Implements Requirement 13.1: Place player in forest clearing with 6 doors and vault
        
        The game always starts in the forest clearing, which is automatically
        initialized with its static location data.
        """
        from backend.services.forest_clearing import create_forest_clearing
        
        now = datetime.now()
        
        # Create the forest clearing location
        clearing = create_forest_clearing()
        
        return cls(
            player_location="forest_clearing",
            inventory=[],
            keys_collected=[],
            visited_locations={"forest_clearing": clearing},
            npc_interactions={},
            puzzle_states={},
            decision_history=[],
            current_door=None,
            game_started_at=now,
            last_updated=now
        )
