"""
Tests for sharing service.

Validates postcard generation, share code uniqueness, and spoiler exclusion.
"""

import pytest
from datetime import datetime

from backend.models.game_state import GameState, LocationData, Item, PuzzleState
from backend.services.sharing import SharingService


def test_generate_unique_share_codes():
    """Test that share codes are unique."""
    service = SharingService()
    
    # Generate multiple codes
    codes = set()
    for _ in range(100):
        code = service.generate_share_code()
        assert code not in codes, f"Duplicate share code generated: {code}"
        codes.add(code)
        assert len(code) == 8, f"Share code should be 8 characters, got {len(code)}"
        assert code.isalnum(), f"Share code should be alphanumeric, got {code}"
        assert code.isupper() or code.isdigit(), f"Share code should be uppercase or digit, got {code}"


def test_create_postcard_basic():
    """Test basic postcard creation."""
    service = SharingService()
    
    # Create a simple game state with one location
    location = LocationData(
        id="test_location",
        description="A mysterious forest clearing",
        image_url="https://example.com/image.jpg",
        exits=["north", "south"],
        items=[],
        npcs=[],
        generated_at=datetime.now()
    )
    
    game_state = GameState(
        player_location="test_location",
        inventory=[],
        keys_collected=[1, 2],
        visited_locations={"test_location": location},
        npc_interactions={},
        puzzle_states={},
        decision_history=[],
        current_door=1,
        game_started_at=datetime.now(),
        last_updated=datetime.now()
    )
    
    # Create postcard
    postcard = service.create_postcard(game_state)
    
    # Verify postcard fields
    assert postcard.share_code is not None
    assert len(postcard.share_code) == 8
    assert postcard.location_name == "test_location"
    assert postcard.location_description == "A mysterious forest clearing"
    assert postcard.location_image_url == "https://example.com/image.jpg"
    assert postcard.keys_collected == 2
    assert postcard.created_at is not None


def test_postcard_excludes_puzzle_solutions():
    """Test that postcards don't include puzzle solutions (spoilers)."""
    service = SharingService()
    
    # Create game state with puzzle solutions
    location = LocationData(
        id="puzzle_room",
        description="A room with a complex puzzle",
        image_url="https://example.com/puzzle.jpg",
        exits=["exit"],
        items=[],
        npcs=[],
        generated_at=datetime.now()
    )
    
    puzzle = PuzzleState(
        puzzle_id="secret_puzzle",
        description="A very secret puzzle",
        solved=True,
        attempts=["wrong answer", "correct answer"],
        hints_given=2
    )
    
    game_state = GameState(
        player_location="puzzle_room",
        inventory=[],
        keys_collected=[1],
        visited_locations={"puzzle_room": location},
        npc_interactions={},
        puzzle_states={"secret_puzzle": puzzle},
        decision_history=[],
        current_door=1,
        game_started_at=datetime.now(),
        last_updated=datetime.now()
    )
    
    # Create postcard
    postcard = service.create_postcard(game_state)
    
    # Verify puzzle information is NOT in postcard
    postcard_dict = postcard.to_dict()
    assert "puzzle_states" not in postcard_dict
    assert "secret_puzzle" not in str(postcard_dict)
    assert "correct answer" not in str(postcard_dict)
    
    # Verify only safe information is included
    assert "location_description" in postcard_dict
    assert "keys_collected" in postcard_dict
    assert postcard.keys_collected == 1


def test_postcard_includes_required_fields():
    """Test that postcards include all required fields."""
    service = SharingService()
    
    location = LocationData(
        id="test_loc",
        description="Test description",
        image_url="https://example.com/test.jpg",
        exits=["north"],
        items=[],
        npcs=[],
        generated_at=datetime.now()
    )
    
    game_state = GameState(
        player_location="test_loc",
        inventory=[],
        keys_collected=[1, 2, 3],
        visited_locations={"test_loc": location},
        npc_interactions={},
        puzzle_states={},
        decision_history=[],
        current_door=2,
        game_started_at=datetime.now(),
        last_updated=datetime.now()
    )
    
    postcard = service.create_postcard(game_state)
    postcard_dict = postcard.to_dict()
    
    # Verify all required fields are present
    required_fields = [
        'share_code',
        'location_name',
        'location_description',
        'location_image_url',
        'keys_collected',
        'created_at'
    ]
    
    for field in required_fields:
        assert field in postcard_dict, f"Required field '{field}' missing from postcard"


def test_retrieve_postcard_by_code():
    """Test retrieving a postcard by share code."""
    service = SharingService()
    
    location = LocationData(
        id="shared_location",
        description="A shared location",
        image_url="https://example.com/shared.jpg",
        exits=["exit"],
        items=[],
        npcs=[],
        generated_at=datetime.now()
    )
    
    game_state = GameState(
        player_location="shared_location",
        inventory=[],
        keys_collected=[1],
        visited_locations={"shared_location": location},
        npc_interactions={},
        puzzle_states={},
        decision_history=[],
        current_door=1,
        game_started_at=datetime.now(),
        last_updated=datetime.now()
    )
    
    # Create postcard
    postcard = service.create_postcard(game_state)
    share_code = postcard.share_code
    
    # Retrieve by code
    retrieved = service.get_postcard(share_code)
    
    assert retrieved is not None
    assert retrieved.share_code == share_code
    assert retrieved.location_name == "shared_location"
    assert retrieved.keys_collected == 1


def test_retrieve_nonexistent_postcard():
    """Test retrieving a postcard that doesn't exist."""
    service = SharingService()
    
    retrieved = service.get_postcard("NONEXIST")
    assert retrieved is None


def test_delete_postcard():
    """Test deleting a postcard."""
    service = SharingService()
    
    location = LocationData(
        id="temp_location",
        description="Temporary location",
        image_url="https://example.com/temp.jpg",
        exits=["exit"],
        items=[],
        npcs=[],
        generated_at=datetime.now()
    )
    
    game_state = GameState(
        player_location="temp_location",
        inventory=[],
        keys_collected=[],
        visited_locations={"temp_location": location},
        npc_interactions={},
        puzzle_states={},
        decision_history=[],
        current_door=None,
        game_started_at=datetime.now(),
        last_updated=datetime.now()
    )
    
    # Create postcard
    postcard = service.create_postcard(game_state)
    share_code = postcard.share_code
    
    # Verify it exists
    assert service.get_postcard(share_code) is not None
    
    # Delete it
    deleted = service.delete_share(share_code)
    assert deleted is True
    
    # Verify it's gone
    assert service.get_postcard(share_code) is None
    
    # Try to delete again
    deleted_again = service.delete_share(share_code)
    assert deleted_again is False


def test_create_postcard_for_specific_location():
    """Test creating a postcard for a specific location (not current)."""
    service = SharingService()
    
    location1 = LocationData(
        id="location1",
        description="First location",
        image_url="https://example.com/loc1.jpg",
        exits=["north"],
        items=[],
        npcs=[],
        generated_at=datetime.now()
    )
    
    location2 = LocationData(
        id="location2",
        description="Second location",
        image_url="https://example.com/loc2.jpg",
        exits=["south"],
        items=[],
        npcs=[],
        generated_at=datetime.now()
    )
    
    game_state = GameState(
        player_location="location1",  # Currently at location1
        inventory=[],
        keys_collected=[1, 2],
        visited_locations={
            "location1": location1,
            "location2": location2
        },
        npc_interactions={},
        puzzle_states={},
        decision_history=[],
        current_door=1,
        game_started_at=datetime.now(),
        last_updated=datetime.now()
    )
    
    # Create postcard for location2 (not current location)
    postcard = service.create_postcard(game_state, location_id="location2")
    
    assert postcard.location_name == "location2"
    assert postcard.location_description == "Second location"
    assert postcard.location_image_url == "https://example.com/loc2.jpg"


def test_create_postcard_invalid_location():
    """Test creating a postcard for a location that doesn't exist."""
    service = SharingService()
    
    location = LocationData(
        id="valid_location",
        description="Valid location",
        image_url="https://example.com/valid.jpg",
        exits=["exit"],
        items=[],
        npcs=[],
        generated_at=datetime.now()
    )
    
    game_state = GameState(
        player_location="valid_location",
        inventory=[],
        keys_collected=[],
        visited_locations={"valid_location": location},
        npc_interactions={},
        puzzle_states={},
        decision_history=[],
        current_door=None,
        game_started_at=datetime.now(),
        last_updated=datetime.now()
    )
    
    # Try to create postcard for non-existent location
    with pytest.raises(ValueError, match="not found in visited locations"):
        service.create_postcard(game_state, location_id="invalid_location")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
