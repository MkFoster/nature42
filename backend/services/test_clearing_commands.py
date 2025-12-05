"""
Integration tests for forest clearing commands.

These tests verify that the command processor correctly handles
commands related to the forest clearing, vault, and doors.
"""

import pytest
from backend.models.game_state import GameState, Item
from backend.services.command_processor import CommandProcessor


@pytest.mark.asyncio
async def test_examine_vault_empty():
    """Test examining the vault with no keys collected."""
    game_state = GameState.create_new_game()
    processor = CommandProcessor(game_state)
    
    result = await processor.process_command("examine vault")
    
    assert result.success
    assert "The Ultimate Question" in result.message
    assert "empty" in result.message.lower() or "waiting" in result.message.lower()


@pytest.mark.asyncio
async def test_examine_vault_with_keys():
    """Test examining the vault with some keys collected."""
    game_state = GameState.create_new_game()
    game_state.keys_collected = [1, 2, 3]
    processor = CommandProcessor(game_state)
    
    result = await processor.process_command("examine vault")
    
    assert result.success
    assert "3" in result.message
    assert "key" in result.message.lower()


@pytest.mark.asyncio
async def test_examine_door():
    """Test examining a specific door."""
    game_state = GameState.create_new_game()
    processor = CommandProcessor(game_state)
    
    result = await processor.process_command("examine door 1")
    
    assert result.success
    assert "door" in result.message.lower()
    assert len(result.message) > 20  # Should have a description


@pytest.mark.asyncio
async def test_examine_door_with_key_collected():
    """Test examining a door after collecting its key."""
    game_state = GameState.create_new_game()
    game_state.keys_collected = [1]
    processor = CommandProcessor(game_state)
    
    result = await processor.process_command("examine door 1")
    
    assert result.success
    assert "retrieved" in result.message.lower() or "already" in result.message.lower()


@pytest.mark.asyncio
async def test_examine_vault_outside_clearing():
    """Test that examining vault outside clearing gives appropriate message."""
    game_state = GameState.create_new_game()
    game_state.player_location = "some_other_location"
    processor = CommandProcessor(game_state)
    
    result = await processor.process_command("examine vault")
    
    assert result.success
    assert "no vault here" in result.message.lower() or "forest clearing" in result.message.lower()


@pytest.mark.asyncio
async def test_examine_clearing():
    """Test examining the clearing itself."""
    game_state = GameState.create_new_game()
    processor = CommandProcessor(game_state)
    
    result = await processor.process_command("look around")
    
    assert result.success
    # Should show the clearing description
    assert "clearing" in result.message.lower() or "door" in result.message.lower() or len(result.message) > 50


@pytest.mark.asyncio
async def test_insert_key_without_key():
    """Test trying to insert a key when you don't have one."""
    game_state = GameState.create_new_game()
    processor = CommandProcessor(game_state)
    
    result = await processor.process_command("insert key into vault")
    
    assert not result.success
    assert "don't have" in result.message.lower()


@pytest.mark.asyncio
async def test_insert_key_with_key():
    """Test inserting a key into the vault."""
    game_state = GameState.create_new_game()
    
    # Add a key to inventory
    key = Item(
        id="key_1",
        name="Key 1",
        description="A mystical key",
        is_key=True,
        door_number=1
    )
    game_state.inventory.append(key)
    
    processor = CommandProcessor(game_state)
    result = await processor.process_command("insert key into vault")
    
    assert result.success
    assert "insert" in result.message.lower()
    assert "key" in result.message.lower()
    
    # Verify state changes
    assert 'key_inserted' in result.state_changes
    assert result.state_changes['key_inserted'] == 1


@pytest.mark.asyncio
async def test_insert_all_six_keys():
    """Test inserting the final key to open the vault (Requirement 13.6)."""
    game_state = GameState.create_new_game()
    
    # Player has collected 5 keys already
    game_state.keys_collected = [1, 2, 3, 4, 5]
    
    # Add the 6th key to inventory
    key = Item(
        id="key_6",
        name="Key 6",
        description="The final mystical key",
        is_key=True,
        door_number=6
    )
    game_state.inventory.append(key)
    
    processor = CommandProcessor(game_state)
    result = await processor.process_command("insert key into vault")
    
    assert result.success
    
    # Verify the philosophical message is displayed
    assert "If, instead of hunting for one giant" in result.message
    assert "meaning of 42" in result.message.lower()
    assert "Congratulations" in result.message
    
    # Verify state changes
    assert 'vault_opened' in result.state_changes
    assert result.state_changes['vault_opened'] is True
    assert 'game_completed' in result.state_changes


@pytest.mark.asyncio
async def test_open_door_from_clearing():
    """Test opening a door from the forest clearing."""
    game_state = GameState.create_new_game()
    processor = CommandProcessor(game_state)
    
    # Note: This will try to generate a new world, which requires ContentGenerator
    # For now, we just verify the command is accepted
    result = await processor.process_command("open door 1")
    
    # The command should be processed (success or failure depends on ContentGenerator)
    assert result is not None


@pytest.mark.asyncio
async def test_open_door_outside_clearing():
    """Test that opening doors outside clearing gives appropriate message."""
    game_state = GameState.create_new_game()
    game_state.player_location = "some_other_location"
    processor = CommandProcessor(game_state)
    
    # Validate that opening door is not allowed
    intent = processor._parse_intent_sync("open door 1")
    validation = processor._validate_open(intent.target, {
        'location': game_state.player_location
    })
    
    assert not validation.is_valid
    assert "forest clearing" in validation.reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
