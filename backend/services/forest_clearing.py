"""
Forest clearing initialization for Nature42.

This module provides the static forest clearing location that serves as the
hub world for the game. The clearing contains six numbered doors and a central
vault, and is the starting point for all players.

Implements Requirements 13.1, 13.2:
- Starting location with 6 doors and vault
- Vault examination showing "The Ultimate Question" inscription
"""

from datetime import datetime
from backend.models.game_state import LocationData, Item


def create_forest_clearing() -> LocationData:
    """
    Create the static forest clearing location.
    
    The forest clearing is the hub world where players start the game.
    It contains:
    - Six numbered wooden doors (1-6)
    - A central vault with "The Ultimate Question" inscription
    - Six keyholes in the vault
    
    This location is consistent across all playthroughs and never changes.
    
    Implements Requirement 13.1: Starting location with 6 doors and vault
    Implements Requirement 13.2: Vault with "The Ultimate Question" inscription
    
    Returns:
        LocationData for the forest clearing
    """
    description = """You stand in a twilight forest clearing, where ancient trees form a perfect circle around you. The air is thick with mystery and possibility.

Before you stand six wooden doors, each marked with a number from 1 to 6. They're arranged in a semicircle, each door unique in its weathering and character. Despite being freestanding with no walls around them, they somehow feel solid and real.

In the center of the clearing sits a stone vault, about waist-high. Its surface is covered in intricate carvings that seem to shift in the fading light. Engraved across the top in elegant script are the words: "The Ultimate Question"

The vault has six keyholes arranged in a circle on its face, each numbered to correspond with one of the doors. The keyholes are empty, waiting.

The forest around you is quiet, expectant. Your quest begins here."""
    
    # The forest clearing has exits to each of the six doors
    # Players can also examine the vault and doors
    exits = [
        "door 1",
        "door 2", 
        "door 3",
        "door 4",
        "door 5",
        "door 6"
    ]
    
    # No items in the clearing initially
    # Keys are found in the door worlds
    items = []
    
    # No NPCs in the clearing
    npcs = []
    
    return LocationData(
        id="forest_clearing",
        description=description,
        image_url="",  # No image for the static clearing
        exits=exits,
        items=items,
        npcs=npcs,
        generated_at=datetime.now()
    )


def get_vault_description(keys_collected: int) -> str:
    """
    Get the description of the vault based on how many keys have been collected.
    
    The vault description changes as keys are inserted, providing visual
    feedback on progress.
    
    Args:
        keys_collected: Number of keys currently inserted (0-6)
        
    Returns:
        Description string for the vault
    """
    if keys_collected == 0:
        return """The stone vault sits in the center of the clearing, its surface covered in mysterious carvings. Engraved across the top are the words: "The Ultimate Question"

Six empty keyholes are arranged in a circle on the vault's face, numbered 1 through 6. The vault is locked tight, waiting for all six keys."""
    
    elif keys_collected < 6:
        plural = "key" if keys_collected == 1 else "keys"
        remaining = 6 - keys_collected
        remaining_plural = "keyhole" if remaining == 1 else "keyholes"
        
        return f"""The stone vault sits in the center of the clearing, its surface covered in mysterious carvings. Engraved across the top are the words: "The Ultimate Question"

{keys_collected} {plural} glow softly in their keyholes, while {remaining} {remaining_plural} remain empty. The vault is still locked, waiting for all six keys."""
    
    else:  # keys_collected == 6
        return """The stone vault sits in the center of the clearing, all six keys glowing brilliantly in their keyholes. The vault is open, revealing the parchment inside with its philosophical message about the meaning of 42.

Your quest is complete."""


def get_door_description(door_number: int, has_key: bool) -> str:
    """
    Get the description of a specific door.
    
    Doors have unique descriptions and may indicate whether the key
    has been retrieved from that world.
    
    Args:
        door_number: Which door (1-6)
        has_key: Whether the key from this door has been collected
        
    Returns:
        Description string for the door
    """
    door_descriptions = {
        1: "A weathered oak door with brass fittings. It looks sturdy and inviting.",
        2: "An ornate door carved with intricate patterns. It seems to shimmer slightly.",
        3: "A dark wooden door with iron bands. It has an ominous yet intriguing presence.",
        4: "A painted door with faded colors. It looks like it's seen many travelers.",
        5: "A tall door made of pale wood. It stands elegant and mysterious.",
        6: "An ancient door covered in moss and vines. It radiates an aura of deep secrets."
    }
    
    base_description = door_descriptions.get(
        door_number,
        f"Door {door_number} stands before you."
    )
    
    if has_key:
        base_description += f"\n\nYou've already retrieved the key from the world behind this door."
    
    return base_description


def initialize_game_with_clearing(game_state) -> None:
    """
    Initialize a new game state with the forest clearing location.
    
    This function should be called when creating a new game to ensure
    the forest clearing location data is added to visited_locations.
    
    Args:
        game_state: GameState object to initialize
    """
    clearing = create_forest_clearing()
    game_state.visited_locations[clearing.id] = clearing
    game_state.player_location = clearing.id
    game_state.current_door = None
