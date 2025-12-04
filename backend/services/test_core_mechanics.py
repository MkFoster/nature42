"""
Tests for core game mechanics (Task 5.10).

Tests door opening, world generation, key retrieval, and vault opening.
"""

import pytest
from datetime import datetime
from backend.services.command_processor import CommandProcessor, Intent
from backend.models.game_state import GameState, Item, LocationData


@pytest.mark.asyncio
async def test_open_door_generates_world():
    """
    Test that opening a door generates a new world.
    
    Validates Requirement 13.3: Door opening generates world
    """
    # Create new game state in forest clearing
    game_state = GameState.create_new_game()
    processor = CommandProcessor(game_state)
    
    # Open door 1
    result = await processor._handle_open_door("door 1")
    
    # Should succeed
    assert result.success
    assert "door 1" in result.message.lower()
    
    # Should set current_door
    assert result.state_changes.get('current_door') == 1
    
    # Should generate new location
    assert result.new_location == "door_1_entrance"
    assert 'new_location_generated' in result.state_changes


@pytest.mark.asyncio
async def test_open_door_returns_to_existing_world():
    """
    Test that opening a door that was already opened returns to the cached world.
    
    Validates Requirement 2.4: Location consistency
    """
    # Create game state with door 1 already visited
    game_state = GameState.create_new_game()
    
    # Add a cached location for door 1
    door_1_location = LocationData(
        id="door_1_entrance",
        description="A mystical forest with glowing mushrooms.",
        image_url="",
        exits=["north", "south"],
        items=[],
        npcs=[],
        generated_at=datetime.now()
    )
    game_state.visited_locations["door_1_entrance"] = door_1_location
    
    processor = CommandProcessor(game_state)
    
    # Open door 1 again
    result = await processor._handle_open_door("door 1")
    
    # Should succeed
    assert result.success
    assert "familiar" in result.message.lower()
    
    # Should move to existing location
    assert result.new_location == "door_1_entrance"
    
    # Should NOT generate new location
    assert 'new_location_generated' not in result.state_changes


@pytest.mark.asyncio
async def test_retrieve_key_from_door_world():
    """
    Test retrieving a key from a door world.
    
    Validates Requirement 13.2: Key retrieval
    """
    game_state = GameState.create_new_game()
    processor = CommandProcessor(game_state)
    
    # Retrieve key from door 1
    result = await processor._handle_retrieve_key(1)
    
    # Should succeed
    assert result.success
    assert "key" in result.message.lower()
    assert "door 1" in result.message.lower()
    
    # Should add key to inventory
    assert len(result.items_added) == 1
    key = result.items_added[0]
    assert key.is_key
    assert key.door_number == 1
    
    # Should track key retrieval
    assert result.state_changes.get('key_retrieved') == 1


@pytest.mark.asyncio
async def test_cannot_retrieve_same_key_twice():
    """
    Test that a key cannot be retrieved twice.
    """
    game_state = GameState.create_new_game()
    
    # Add key 1 to inventory
    key_1 = Item(
        id="key_1",
        name="Key 1",
        description="A mystical key",
        is_key=True,
        door_number=1
    )
    game_state.inventory.append(key_1)
    
    processor = CommandProcessor(game_state)
    
    # Try to retrieve key 1 again
    result = await processor._handle_retrieve_key(1)
    
    # Should fail
    assert not result.success
    assert "already have" in result.message.lower()


@pytest.mark.asyncio
async def test_insert_key_into_vault():
    """
    Test inserting a key into the vault.
    
    Validates Requirement 13.5: Key insertion
    """
    game_state = GameState.create_new_game()
    
    # Add a key to inventory
    key_1 = Item(
        id="key_1",
        name="Key 1",
        description="A mystical key",
        is_key=True,
        door_number=1
    )
    game_state.inventory.append(key_1)
    
    processor = CommandProcessor(game_state)
    
    # Insert key
    result = await processor._handle_insert_key()
    
    # Should succeed
    assert result.success
    assert "insert" in result.message.lower()
    assert "key" in result.message.lower()
    
    # Should remove key from inventory
    assert len(result.items_removed) == 1
    assert result.items_removed[0].door_number == 1
    
    # Should track key insertion
    assert result.state_changes.get('key_inserted') == 1


@pytest.mark.asyncio
async def test_vault_opens_with_all_six_keys():
    """
    Test that the vault opens when all 6 keys are inserted.
    
    Validates Requirement 13.6: Vault opening with all keys
    """
    game_state = GameState.create_new_game()
    
    # Simulate 5 keys already collected
    game_state.keys_collected = [1, 2, 3, 4, 5]
    
    # Add the 6th key to inventory
    key_6 = Item(
        id="key_6",
        name="Key 6",
        description="The final key",
        is_key=True,
        door_number=6
    )
    game_state.inventory.append(key_6)
    
    processor = CommandProcessor(game_state)
    
    # Insert the final key
    result = await processor._handle_insert_key()
    
    # Should succeed
    assert result.success
    
    # Should indicate vault opened
    assert result.state_changes.get('vault_opened') is True
    assert result.state_changes.get('game_completed') is True
    
    # Should contain the philosophical message
    assert "42" in result.message
    assert "kindness" in result.message.lower()
    assert "curiosity" in result.message.lower()
    assert "courage" in result.message.lower()
    assert "gratitude" in result.message.lower()
    
    # Should remove key from inventory
    assert len(result.items_removed) == 1


@pytest.mark.asyncio
async def test_insert_key_shows_progress():
    """
    Test that inserting keys shows progress toward completion.
    """
    game_state = GameState.create_new_game()
    
    # Add key 1 to inventory
    key_1 = Item(
        id="key_1",
        name="Key 1",
        description="A mystical key",
        is_key=True,
        door_number=1
    )
    game_state.inventory.append(key_1)
    
    processor = CommandProcessor(game_state)
    
    # Insert first key
    result = await processor._handle_insert_key()
    
    # Should show progress
    assert "5 keys remaining" in result.message or "5 more" in result.message.lower()


@pytest.mark.asyncio
async def test_cannot_insert_key_outside_clearing():
    """
    Test that keys can only be inserted in the forest clearing.
    
    Validates Requirement 13.5: Key insertion location restriction
    """
    game_state = GameState.create_new_game()
    game_state.player_location = "door_1_entrance"  # Not in clearing
    
    # Add a key to inventory
    key_1 = Item(
        id="key_1",
        name="Key 1",
        description="A mystical key",
        is_key=True,
        door_number=1
    )
    game_state.inventory.append(key_1)
    
    processor = CommandProcessor(game_state)
    
    # Validate insertion
    intent = Intent(action="insert", target="key")
    validation = await processor._validate_action(intent)
    
    # Should be invalid
    assert not validation.is_valid
    assert "forest clearing" in validation.reason.lower()


@pytest.mark.asyncio
async def test_return_to_clearing_from_door_world():
    """
    Test returning to the forest clearing from a door world.
    """
    game_state = GameState.create_new_game()
    game_state.player_location = "door_1_entrance"
    game_state.current_door = 1
    
    processor = CommandProcessor(game_state)
    
    # Return to clearing
    result = await processor._handle_movement("back")
    
    # Should succeed
    assert result.success
    assert "forest clearing" in result.message.lower()
    
    # Should move to clearing
    assert result.new_location == "forest_clearing"
    
    # Should clear current_door
    assert result.state_changes.get('current_door') is None


@pytest.mark.asyncio
async def test_take_key_item_triggers_retrieval():
    """
    Test that taking a key item triggers the key retrieval logic.
    """
    game_state = GameState.create_new_game()
    game_state.player_location = "door_1_treasure_room"
    
    # Create a location with a key item
    key_item = Item(
        id="key_1",
        name="Golden Key",
        description="A golden key",
        is_key=True,
        door_number=1
    )
    
    location = LocationData(
        id="door_1_treasure_room",
        description="A treasure room",
        image_url="",
        exits=["back"],
        items=[key_item],
        npcs=[],
        generated_at=datetime.now()
    )
    game_state.visited_locations["door_1_treasure_room"] = location
    
    processor = CommandProcessor(game_state)
    
    # Take the key
    result = await processor._handle_take_item("Golden Key")
    
    # Should succeed with special key retrieval message
    assert result.success
    assert "obtained" in result.message.lower() or "key" in result.message.lower()
    
    # Should add key to inventory
    assert len(result.items_added) == 1
    assert result.items_added[0].is_key
    
    # Should track key retrieval
    assert result.state_changes.get('key_retrieved') == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
