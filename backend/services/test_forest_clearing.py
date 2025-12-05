"""
Tests for forest clearing initialization.

These tests verify that the forest clearing is correctly initialized
with the required elements: 6 doors, vault, and proper descriptions.
"""

import pytest
from backend.models.game_state import GameState
from backend.services.forest_clearing import (
    create_forest_clearing,
    get_vault_description,
    get_door_description,
    initialize_game_with_clearing
)


def test_create_forest_clearing():
    """Test that forest clearing is created with correct structure."""
    clearing = create_forest_clearing()
    
    # Verify basic properties
    assert clearing.id == "forest_clearing"
    assert clearing.description is not None
    assert len(clearing.description) > 0
    
    # Verify it mentions the key elements (Requirement 13.1)
    assert "six" in clearing.description.lower() or "6" in clearing.description
    assert "door" in clearing.description.lower()
    assert "vault" in clearing.description.lower()
    assert "The Ultimate Question" in clearing.description
    
    # Verify exits to all 6 doors
    assert len(clearing.exits) == 6
    for i in range(1, 7):
        assert f"door {i}" in clearing.exits
    
    # Verify no items or NPCs initially
    assert len(clearing.items) == 0
    assert len(clearing.npcs) == 0


def test_vault_description_empty():
    """Test vault description with no keys collected."""
    desc = get_vault_description(0)
    
    assert "The Ultimate Question" in desc
    assert "empty" in desc.lower() or "waiting" in desc.lower()
    assert "six" in desc.lower() or "6" in desc


def test_vault_description_partial():
    """Test vault description with some keys collected."""
    desc = get_vault_description(3)
    
    assert "3" in desc
    assert "key" in desc.lower()
    assert "remaining" in desc.lower() or "empty" in desc.lower()


def test_vault_description_complete():
    """Test vault description with all keys collected."""
    desc = get_vault_description(6)
    
    assert "six" in desc.lower() or "6" in desc or "all" in desc.lower()
    assert "open" in desc.lower() or "complete" in desc.lower()


def test_door_descriptions():
    """Test that each door has a unique description."""
    descriptions = []
    
    for i in range(1, 7):
        desc = get_door_description(i, False)
        assert desc is not None
        assert len(desc) > 0
        descriptions.append(desc)
    
    # Verify all descriptions are unique
    assert len(set(descriptions)) == 6


def test_door_description_with_key():
    """Test door description indicates when key is collected."""
    desc_without_key = get_door_description(1, False)
    desc_with_key = get_door_description(1, True)
    
    assert desc_without_key != desc_with_key
    assert "retrieved" in desc_with_key.lower() or "already" in desc_with_key.lower()


def test_new_game_has_clearing():
    """Test that new game is initialized with forest clearing (Requirement 13.1)."""
    game_state = GameState.create_new_game()
    
    # Verify player starts in clearing
    assert game_state.player_location == "forest_clearing"
    assert game_state.current_door is None
    
    # Verify clearing is in visited locations
    assert "forest_clearing" in game_state.visited_locations
    
    clearing = game_state.visited_locations["forest_clearing"]
    assert clearing.id == "forest_clearing"
    assert len(clearing.exits) == 6


def test_initialize_game_with_clearing():
    """Test the initialize_game_with_clearing helper function."""
    # Create a minimal game state
    game_state = GameState(
        player_location="unknown",
        inventory=[],
        keys_collected=[],
        visited_locations={},
        npc_interactions={},
        puzzle_states={},
        decision_history=[],
        current_door=None,
        game_started_at=None,
        last_updated=None
    )
    
    # Initialize with clearing
    initialize_game_with_clearing(game_state)
    
    # Verify clearing was added
    assert game_state.player_location == "forest_clearing"
    assert "forest_clearing" in game_state.visited_locations
    assert game_state.current_door is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
