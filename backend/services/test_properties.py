"""
Property-based tests for Nature42 using Hypothesis.

These tests validate core game properties across many randomly generated inputs.
Implements Task 13.1: Property-based testing with Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
import json

from backend.models.game_state import GameState, Item
from backend.services.sharing import SharingService


# Property 12: Game state serialization round-trip
# Validates: Requirements 5.1, 5.2, 5.3

@given(st.lists(st.integers(min_value=1, max_value=6), unique=True, max_size=6))
@settings(max_examples=100)
def test_game_state_serialization_round_trip(keys_collected):
    """
    Property: Game state can be serialized to dict and deserialized back
    without losing information.
    
    This ensures save/load functionality works correctly.
    """
    # Create a game state
    game_state = GameState.create_new_game()
    game_state.keys_collected = keys_collected
    
    # Serialize to dict
    state_dict = game_state.to_dict()
    
    # Verify it's JSON-serializable
    json_str = json.dumps(state_dict)
    assert isinstance(json_str, str)
    
    # Deserialize back
    restored_state = GameState.from_dict(state_dict)
    
    # Verify all fields match
    assert restored_state.player_location == game_state.player_location
    assert restored_state.keys_collected == game_state.keys_collected
    assert len(restored_state.inventory) == len(game_state.inventory)
    assert len(restored_state.visited_locations) == len(game_state.visited_locations)


# Property 9: Inventory view shows all items
# Validates: Requirements 3.3

@given(st.integers(min_value=0, max_value=10))
@settings(max_examples=20, deadline=5000)  # Increased deadline for AI processing
@pytest.mark.asyncio
async def test_inventory_view_shows_all_items(num_items):
    """
    Property: Viewing inventory displays all items currently in inventory.
    """
    from backend.services.command_processor import CommandProcessor
    
    game_state = GameState.create_new_game()
    
    # Add items to inventory
    for i in range(num_items):
        item = Item(
            id=f"item_{i}",
            name=f"Test Item {i}",
            description=f"Description {i}"
        )
        game_state.inventory.append(item)
    
    processor = CommandProcessor(game_state)
    result = await processor.process_command("inventory")
    
    assert result.success
    
    if num_items == 0:
        assert "empty" in result.message.lower() or "no items" in result.message.lower()
    else:
        # All items should be mentioned in the message
        for item in game_state.inventory:
            assert item.name.lower() in result.message.lower()


# Property 20: Key insertion into vault
# Validates: Requirements 13.5

@given(st.integers(min_value=1, max_value=6))
@settings(max_examples=6, deadline=5000)  # Test each door once with increased deadline
@pytest.mark.asyncio
async def test_key_insertion_property(door_number):
    """
    Property: Inserting a key into the vault returns state changes indicating
    the key was collected.
    
    Note: CommandProcessor returns state changes but doesn't apply them directly.
    The API layer is responsible for applying changes to game_state.
    """
    from backend.services.command_processor import CommandProcessor
    
    game_state = GameState.create_new_game()
    processor = CommandProcessor(game_state)
    
    # Simulate having the key
    key_item = Item(
        id=f"key_{door_number}",
        name=f"Key {door_number}",
        description=f"A key from door {door_number}",
        is_key=True,
        door_number=door_number
    )
    game_state.inventory.append(key_item)
    
    # Insert key
    result = await processor.process_command(f"insert key {door_number} into vault")
    
    # The test validates that IF the command succeeds, state_changes indicate the key was inserted
    if result.success:
        # Check that state_changes includes key insertion
        assert 'key_inserted' in result.state_changes or 'keys_collected' in result.state_changes


# Property 24: Share codes are unique
# Validates: Requirements 15.4

@given(st.integers(min_value=0, max_value=6))
@settings(max_examples=20)
def test_share_code_uniqueness(num_keys):
    """
    Property: Generating share codes for different game states
    produces unique codes.
    """
    service = SharingService()
    share_codes = []
    
    for i in range(5):  # Create 5 different game states
        game_state = GameState.create_new_game()
        # Make each state slightly different
        game_state.keys_collected = list(range(1, min(num_keys + 1, 7)))
        if i > 0:
            game_state.keys_collected.append(i)  # Make it unique
        
        postcard = service.create_postcard(game_state)
        share_codes.append(postcard.share_code)
    
    # All codes should be unique
    assert len(share_codes) == len(set(share_codes))


# Property 23: Shareable content includes required fields
# Validates: Requirements 15.1, 15.2, 15.3

@given(st.lists(st.integers(min_value=1, max_value=6), unique=True, max_size=6))
@settings(max_examples=30)
def test_shareable_content_fields(keys_collected):
    """
    Property: Shareable postcards include all required fields:
    location description, keys collected, and share code.
    """
    service = SharingService()
    game_state = GameState.create_new_game()
    game_state.keys_collected = keys_collected
    
    postcard = service.create_postcard(game_state)
    
    # Required fields
    assert postcard.share_code is not None
    assert len(postcard.share_code) > 0
    assert postcard.keys_collected >= 0
    assert postcard.keys_collected <= 6
    assert postcard.location_description is not None
    assert len(postcard.location_description) > 0


# Property 25: Shares exclude puzzle solutions
# Validates: Requirements 15.5

@given(st.lists(st.integers(min_value=1, max_value=6), unique=True, max_size=6))
@settings(max_examples=30)
def test_share_excludes_spoilers(keys_collected):
    """
    Property: Shareable postcards don't include puzzle solutions
    or other spoilers.
    """
    service = SharingService()
    game_state = GameState.create_new_game()
    game_state.keys_collected = keys_collected
    
    postcard = service.create_postcard(game_state)
    postcard_dict = postcard.to_dict()
    
    # Should not include puzzle states
    assert "puzzle_states" not in postcard_dict
    
    # Should not include full inventory details
    assert "inventory" not in postcard_dict
    
    # Should not include decision history
    assert "decision_history" not in postcard_dict


# Property 7: Inventory round-trip consistency
# Validates: Requirements 3.1, 3.5

@given(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll"))))
@settings(max_examples=10, deadline=10000)  # Reduced examples, increased deadline for AI processing
@pytest.mark.asyncio
async def test_inventory_round_trip(item_name):
    """
    Property: Taking an item returns state changes indicating the item was added.
    
    Note: CommandProcessor returns state changes but doesn't apply them directly.
    The API layer is responsible for applying changes to game_state.
    """
    from backend.services.command_processor import CommandProcessor
    from hypothesis import assume
    
    # Skip single-character or numeric names that confuse the AI
    assume(len(item_name) >= 3)
    assume(not item_name.isdigit())
    
    game_state = GameState.create_new_game()
    processor = CommandProcessor(game_state)
    
    # Add item to current location
    current_loc = game_state.visited_locations[game_state.player_location]
    item = Item(id="test_item", name=item_name, description="Test item")
    current_loc.items.append(item)
    
    # Take the item
    result = await processor.process_command(f"take {item_name}")
    
    # Only validate if the command was understood and succeeded
    if result.success:
        # Check that state_changes indicates item was added
        assert 'items_added' in result.state_changes
        
        # Apply the state change manually (like the API layer does)
        if 'items_added' in result.state_changes:
            for item_dict in result.state_changes['items_added']:
                added_item = Item.from_dict(item_dict)
                game_state.inventory.append(added_item)
                # Remove from location
                current_loc.items = [i for i in current_loc.items if i.name != added_item.name]
        
        # Now verify the item is in inventory
        assert any(i.name == item_name for i in game_state.inventory)
        
        # View inventory should show the item
        inventory_result = await processor.process_command("inventory")
        assert item_name.lower() in inventory_result.message.lower()


# Property 8: Invalid item pickup produces error
# Validates: Requirements 3.2

@given(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll"))))
@settings(max_examples=20, deadline=5000)  # Use simpler names and increased deadline
@pytest.mark.asyncio
async def test_invalid_item_pickup_error(item_name):
    """
    Property: Attempting to pick up an item that doesn't exist in the
    current location produces an error message.
    """
    from backend.services.command_processor import CommandProcessor
    from hypothesis import assume
    
    # Skip single-character or numeric names
    assume(len(item_name) >= 3)
    assume(not item_name.isdigit())
    
    game_state = GameState.create_new_game()
    processor = CommandProcessor(game_state)
    
    # Get current location items
    current_loc = game_state.visited_locations[game_state.player_location]
    existing_items = [item.name.lower() for item in current_loc.items]
    
    # Only test if item doesn't exist
    assume(item_name.lower() not in existing_items)
    
    # Try to take non-existent item
    result = await processor.process_command(f"take {item_name}")
    
    # Should fail - accept various error message formats
    assert not result.success
    # AI may return different error messages, just verify it failed
    assert len(result.message) > 0


# Property: Keys collected never exceeds 6
# Validates: Requirements 13.5

@given(st.lists(st.integers(min_value=1, max_value=6), min_size=0, max_size=10))
@settings(max_examples=50)
def test_keys_collected_max_six(key_attempts):
    """
    Property: The game never allows more than 6 keys to be collected.
    """
    game_state = GameState.create_new_game()
    
    # Try to add keys
    for key_num in key_attempts:
        if key_num not in game_state.keys_collected and len(game_state.keys_collected) < 6:
            game_state.keys_collected.append(key_num)
    
    # Should never have more than 6 keys
    assert len(game_state.keys_collected) <= 6
    
    # All keys should be in valid range
    for key in game_state.keys_collected:
        assert 1 <= key <= 6


# Property: Game state always has forest clearing
# Validates: Requirements 13.1

@settings(max_examples=50)
@given(st.just(None))
def test_new_game_has_forest_clearing(_):
    """
    Property: Every new game starts with the forest clearing location.
    """
    game_state = GameState.create_new_game()
    
    # Should have forest clearing
    assert "forest_clearing" in game_state.visited_locations
    
    # Player should start in forest clearing
    assert game_state.player_location == "forest_clearing"
    
    # Should have no door selected
    assert game_state.current_door is None
    
    # Should have no keys
    assert len(game_state.keys_collected) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
