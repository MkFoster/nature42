"""
Tests for inventory management commands.

Tests Requirements 3.1, 3.2, 3.3, 3.4, 3.5:
- Pick up items
- Handle invalid item pickup
- View inventory
- Use items
- Drop items
"""

import pytest
from datetime import datetime
from backend.services.command_processor import CommandProcessor
from backend.models.game_state import GameState, Item, LocationData


@pytest.fixture
def game_state_with_location():
    """Create a game state with a location containing items."""
    # Create test items
    test_items = [
        Item(
            id="sword_1",
            name="Rusty Sword",
            description="An old sword with a rusty blade",
            is_key=False,
            properties={"usage_context": "tool"}
        ),
        Item(
            id="potion_1",
            name="Health Potion",
            description="A red potion that restores health",
            is_key=False,
            properties={"usage_context": "consumable"}
        ),
        Item(
            id="key_1",
            name="Golden Key",
            description="A shiny golden key",
            is_key=True,
            door_number=1
        )
    ]
    
    # Create test location
    test_location = LocationData(
        id="test_room",
        description="A dusty room with stone walls",
        image_url="http://example.com/room.jpg",
        exits=["north", "south"],
        items=test_items,
        npcs=[],
        generated_at=datetime.now()
    )
    
    # Create game state
    game_state = GameState.create_new_game()
    game_state.player_location = "test_room"
    game_state.visited_locations["test_room"] = test_location
    
    return game_state


@pytest.fixture
def game_state_with_inventory():
    """Create a game state with items in inventory."""
    game_state = GameState.create_new_game()
    game_state.inventory = [
        Item(
            id="torch_1",
            name="Torch",
            description="A burning torch that provides light",
            is_key=False,
            properties={"usage_context": "tool"}
        ),
        Item(
            id="rope_1",
            name="Rope",
            description="A sturdy rope",
            is_key=False,
            properties={"usage_context": "tool"}
        )
    ]
    
    # Create empty location
    test_location = LocationData(
        id="empty_room",
        description="An empty room",
        image_url="http://example.com/empty.jpg",
        exits=["east"],
        items=[],
        npcs=[],
        generated_at=datetime.now()
    )
    game_state.player_location = "empty_room"
    game_state.visited_locations["empty_room"] = test_location
    
    return game_state


@pytest.mark.asyncio
async def test_take_item_success(game_state_with_location):
    """Test successfully taking an item from location."""
    processor = CommandProcessor(game_state_with_location)
    
    # Take the sword
    result = await processor.process_command("take rusty sword")
    
    assert result.success is True
    assert "take" in result.message.lower() or "rusty sword" in result.message.lower()
    assert "items_added" in result.state_changes
    assert len(result.state_changes["items_added"]) == 1
    assert result.state_changes["items_added"][0]["name"] == "Rusty Sword"


@pytest.mark.asyncio
async def test_take_nonexistent_item(game_state_with_location):
    """Test taking an item that doesn't exist in location."""
    processor = CommandProcessor(game_state_with_location)
    
    # Try to take an item that doesn't exist
    result = await processor.process_command("take magic wand")
    
    assert result.success is False
    assert "magic wand" in result.message.lower() or "no" in result.message.lower()


@pytest.mark.asyncio
async def test_view_inventory_with_items(game_state_with_inventory):
    """Test viewing inventory when it contains items."""
    processor = CommandProcessor(game_state_with_inventory)
    
    # View inventory
    result = await processor.process_command("inventory")
    
    assert result.success is True
    assert "torch" in result.message.lower()
    assert "rope" in result.message.lower()


@pytest.mark.asyncio
async def test_view_inventory_empty():
    """Test viewing inventory when it's empty."""
    game_state = GameState.create_new_game()
    processor = CommandProcessor(game_state)
    
    # View empty inventory
    result = await processor.process_command("inventory")
    
    assert result.success is True
    assert "empty" in result.message.lower()


@pytest.mark.asyncio
async def test_drop_item_success(game_state_with_inventory):
    """Test successfully dropping an item from inventory."""
    processor = CommandProcessor(game_state_with_inventory)
    
    # Drop the torch
    result = await processor.process_command("drop torch")
    
    assert result.success is True
    assert "drop" in result.message.lower() or "torch" in result.message.lower()
    assert "items_removed" in result.state_changes
    assert len(result.state_changes["items_removed"]) == 1
    assert result.state_changes["items_removed"][0]["name"] == "Torch"


@pytest.mark.asyncio
async def test_drop_item_not_in_inventory(game_state_with_inventory):
    """Test dropping an item that's not in inventory."""
    processor = CommandProcessor(game_state_with_inventory)
    
    # Try to drop an item we don't have
    result = await processor.process_command("drop sword")
    
    assert result.success is False
    assert "don't have" in result.message.lower() or "sword" in result.message.lower()


@pytest.mark.asyncio
async def test_use_item_success(game_state_with_inventory):
    """Test successfully using an item from inventory."""
    processor = CommandProcessor(game_state_with_inventory)
    
    # Use the torch
    result = await processor.process_command("use torch")
    
    assert result.success is True
    assert "torch" in result.message.lower()
    assert "item_used" in result.state_changes


@pytest.mark.asyncio
async def test_use_item_not_in_inventory():
    """Test using an item that's not in inventory."""
    game_state = GameState.create_new_game()
    processor = CommandProcessor(game_state)
    
    # Try to use an item we don't have
    result = await processor.process_command("use sword")
    
    assert result.success is False
    assert "don't have" in result.message.lower()


@pytest.mark.asyncio
async def test_use_key_item(game_state_with_location):
    """Test that using a key suggests inserting it instead."""
    processor = CommandProcessor(game_state_with_location)
    
    # First take the key
    take_result = await processor.process_command("take golden key")
    assert take_result.success is True
    
    # Update game state with the key
    game_state_with_location.inventory.append(
        Item(
            id="key_1",
            name="Golden Key",
            description="A shiny golden key",
            is_key=True,
            door_number=1
        )
    )
    
    # Try to use the key
    processor = CommandProcessor(game_state_with_location)
    result = await processor.process_command("use golden key")
    
    assert result.success is False
    assert "insert" in result.message.lower() or "vault" in result.message.lower()


@pytest.mark.asyncio
async def test_inventory_round_trip(game_state_with_location):
    """Test picking up and dropping an item (round-trip)."""
    processor = CommandProcessor(game_state_with_location)
    
    # Take the potion
    take_result = await processor.process_command("take health potion")
    assert take_result.success is True
    assert "items_added" in take_result.state_changes
    
    # Update game state
    potion = None
    for item in game_state_with_location.visited_locations["test_room"].items:
        if item.name == "Health Potion":
            potion = item
            break
    
    if potion:
        game_state_with_location.inventory.append(potion)
        game_state_with_location.visited_locations["test_room"].items.remove(potion)
    
    # Drop the potion
    processor = CommandProcessor(game_state_with_location)
    drop_result = await processor.process_command("drop health potion")
    assert drop_result.success is True
    assert "items_removed" in drop_result.state_changes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
