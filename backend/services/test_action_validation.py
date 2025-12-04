"""
Test action validation with context.

This test verifies that the CommandProcessor correctly validates actions
based on the current game context (location, inventory, state).

Tests Requirements 12.1, 12.2, 12.3:
- Action validation considers context
- Valid actions are executed
- Invalid actions provide helpful explanations
"""

import pytest
import asyncio
from datetime import datetime
from backend.models.game_state import GameState, LocationData, Item
from backend.services.command_processor import CommandProcessor, Intent


def create_test_game_state() -> GameState:
    """Create a test game state with some initial data."""
    game_state = GameState.create_new_game()
    
    # Add a test location with exits and items
    test_location = LocationData(
        id="test_room",
        description="A test room",
        image_url="",
        exits=["north", "south", "east"],
        items=[
            Item(id="key1", name="brass key", description="A shiny brass key", is_key=False),
            Item(id="sword1", name="sword", description="A rusty sword", is_key=False)
        ],
        npcs=["guard", "merchant"],
        generated_at=datetime.now()
    )
    
    game_state.visited_locations["test_room"] = test_location
    game_state.player_location = "test_room"
    
    # Add an item to inventory
    game_state.inventory.append(
        Item(id="potion1", name="health potion", description="A red potion", is_key=False)
    )
    
    return game_state


@pytest.mark.asyncio
async def test_movement_validation():
    """Test that movement validation considers available exits."""
    print("\n=== Testing Movement Validation ===")
    
    game_state = create_test_game_state()
    processor = CommandProcessor(game_state)
    
    # Test valid movement
    intent = Intent(action="move", target="north")
    result = await processor._validate_action(intent)
    assert result.is_valid, "Valid movement should be allowed"
    print("✓ Valid movement (north) accepted")
    
    # Test invalid movement
    intent = Intent(action="move", target="west")
    result = await processor._validate_action(intent)
    assert not result.is_valid, "Invalid movement should be rejected"
    assert "north" in result.reason.lower() or "south" in result.reason.lower(), \
        "Error should mention available exits"
    print(f"✓ Invalid movement (west) rejected: {result.reason}")
    
    # Test movement without target
    intent = Intent(action="move", target=None)
    result = await processor._validate_action(intent)
    assert not result.is_valid, "Movement without target should be rejected"
    print(f"✓ Movement without target rejected: {result.reason}")


@pytest.mark.asyncio
async def test_take_item_validation():
    """Test that taking items validates against location contents."""
    print("\n=== Testing Take Item Validation ===")
    
    game_state = create_test_game_state()
    processor = CommandProcessor(game_state)
    
    # Test taking existing item
    intent = Intent(action="take", target="brass key")
    result = await processor._validate_action(intent)
    assert result.is_valid, "Taking existing item should be allowed"
    print("✓ Taking existing item (brass key) accepted")
    
    # Test taking non-existent item
    intent = Intent(action="take", target="diamond")
    result = await processor._validate_action(intent)
    assert not result.is_valid, "Taking non-existent item should be rejected"
    assert "brass key" in result.reason.lower() or "sword" in result.reason.lower(), \
        "Error should mention available items"
    print(f"✓ Taking non-existent item (diamond) rejected: {result.reason}")
    
    # Test taking without target
    intent = Intent(action="take", target=None)
    result = await processor._validate_action(intent)
    assert not result.is_valid, "Taking without target should be rejected"
    print(f"✓ Taking without target rejected: {result.reason}")


@pytest.mark.asyncio
async def test_drop_item_validation():
    """Test that dropping items validates against inventory contents."""
    print("\n=== Testing Drop Item Validation ===")
    
    game_state = create_test_game_state()
    processor = CommandProcessor(game_state)
    
    # Test dropping item in inventory
    intent = Intent(action="drop", target="health potion")
    result = await processor._validate_action(intent)
    assert result.is_valid, "Dropping inventory item should be allowed"
    print("✓ Dropping inventory item (health potion) accepted")
    
    # Test dropping item not in inventory
    intent = Intent(action="drop", target="sword")
    result = await processor._validate_action(intent)
    assert not result.is_valid, "Dropping non-inventory item should be rejected"
    assert "health potion" in result.reason.lower(), \
        "Error should mention inventory contents"
    print(f"✓ Dropping non-inventory item (sword) rejected: {result.reason}")


@pytest.mark.asyncio
async def test_use_item_validation():
    """Test that using items validates against inventory."""
    print("\n=== Testing Use Item Validation ===")
    
    game_state = create_test_game_state()
    processor = CommandProcessor(game_state)
    
    # Test using item in inventory
    intent = Intent(action="use", target="health potion")
    result = await processor._validate_action(intent)
    assert result.is_valid, "Using inventory item should be allowed"
    print("✓ Using inventory item (health potion) accepted")
    
    # Test using item not in inventory
    intent = Intent(action="use", target="magic wand")
    result = await processor._validate_action(intent)
    assert not result.is_valid, "Using non-inventory item should be rejected"
    print(f"✓ Using non-inventory item (magic wand) rejected: {result.reason}")


@pytest.mark.asyncio
async def test_talk_validation():
    """Test that talking validates against NPCs in location."""
    print("\n=== Testing Talk Validation ===")
    
    game_state = create_test_game_state()
    processor = CommandProcessor(game_state)
    
    # Test talking to existing NPC
    intent = Intent(action="talk", target="guard")
    result = await processor._validate_action(intent)
    assert result.is_valid, "Talking to existing NPC should be allowed"
    print("✓ Talking to existing NPC (guard) accepted")
    
    # Test talking to non-existent NPC
    intent = Intent(action="talk", target="wizard")
    result = await processor._validate_action(intent)
    assert not result.is_valid, "Talking to non-existent NPC should be rejected"
    assert "guard" in result.reason.lower() or "merchant" in result.reason.lower(), \
        "Error should mention available NPCs"
    print(f"✓ Talking to non-existent NPC (wizard) rejected: {result.reason}")


@pytest.mark.asyncio
async def test_door_validation():
    """Test that door actions validate location."""
    print("\n=== Testing Door Validation ===")
    
    game_state = create_test_game_state()
    processor = CommandProcessor(game_state)
    
    # Test opening door outside forest clearing
    intent = Intent(action="open", target="door 1")
    result = await processor._validate_action(intent)
    assert not result.is_valid, "Opening door outside clearing should be rejected"
    assert "forest clearing" in result.reason.lower(), \
        "Error should mention forest clearing"
    print(f"✓ Opening door outside clearing rejected: {result.reason}")
    
    # Test opening door in forest clearing
    game_state.player_location = "forest_clearing"
    intent = Intent(action="open", target="door 1")
    result = await processor._validate_action(intent)
    assert result.is_valid, "Opening door in clearing should be allowed"
    print("✓ Opening door in forest clearing accepted")


@pytest.mark.asyncio
async def test_key_insertion_validation():
    """Test that key insertion validates inventory and location."""
    print("\n=== Testing Key Insertion Validation ===")
    
    game_state = create_test_game_state()
    processor = CommandProcessor(game_state)
    
    # Test inserting key without having one
    intent = Intent(action="insert", target="key")
    result = await processor._validate_action(intent)
    assert not result.is_valid, "Inserting key without having one should be rejected"
    print(f"✓ Inserting key without having one rejected: {result.reason}")
    
    # Add a key to inventory
    game_state.inventory.append(
        Item(id="key_1", name="Key 1", description="Key from door 1", 
             is_key=True, door_number=1)
    )
    
    # Test inserting key outside forest clearing
    intent = Intent(action="insert", target="key")
    result = await processor._validate_action(intent)
    assert not result.is_valid, "Inserting key outside clearing should be rejected"
    assert "forest clearing" in result.reason.lower(), \
        "Error should mention forest clearing"
    print(f"✓ Inserting key outside clearing rejected: {result.reason}")
    
    # Test inserting key in forest clearing
    game_state.player_location = "forest_clearing"
    intent = Intent(action="insert", target="key")
    result = await processor._validate_action(intent)
    assert result.is_valid, "Inserting key in clearing should be allowed"
    print("✓ Inserting key in forest clearing accepted")


@pytest.mark.asyncio
async def test_context_info():
    """Test that validation results include context information."""
    print("\n=== Testing Context Information ===")
    
    game_state = create_test_game_state()
    processor = CommandProcessor(game_state)
    
    intent = Intent(action="move", target="north")
    result = await processor._validate_action(intent)
    
    assert result.context_info is not None, "Context info should be provided"
    assert 'location' in result.context_info, "Context should include location"
    assert 'inventory_count' in result.context_info, "Context should include inventory count"
    assert 'keys_collected' in result.context_info, "Context should include keys collected"
    
    print(f"✓ Context info provided: {result.context_info}")


async def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Action Validation Context Tests")
    print("Testing Requirements 12.1, 12.2, 12.3")
    print("=" * 60)
    
    try:
        await test_movement_validation()
        await test_take_item_validation()
        await test_drop_item_validation()
        await test_use_item_validation()
        await test_talk_validation()
        await test_door_validation()
        await test_key_insertion_validation()
        await test_context_info()
        
        print("\n" + "=" * 60)
        print("✓ All action validation tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
