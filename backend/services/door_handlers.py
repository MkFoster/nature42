"""
Door-specific action handlers for Nature42.

This module contains handlers for door-related actions like opening doors,
retrieving keys, and inserting keys into the vault.
"""

from backend.services.command_models import ActionResult
from backend.models.game_state import GameState, Item


class DoorHandlers:
    """Handles door-related game actions."""
    
    def __init__(self, game_state: GameState):
        """
        Initialize door handlers.
        
        Args:
            game_state: Current game state
        """
        self.game_state = game_state
    
    async def handle_open_door(self, door_target: str) -> ActionResult:
        """
        Handle opening a door in the forest clearing.
        
        Implements Requirement 13.3: Generate world behind door
        Implements Requirement 13.4: Create diverse settings
        
        This method:
        1. Extracts the door number from the command
        2. Checks if the world behind that door already exists
        3. If not, generates a new world using the ContentGenerator
        4. Moves the player into the door world
        
        Args:
            door_target: The door target from the command (e.g., "door 1", "door three")
            
        Returns:
            ActionResult with the new location and state changes
        """
        # Extract door number from target
        door_number = None
        number_words = ["one", "two", "three", "four", "five", "six"]
        
        for i in range(1, 7):
            if str(i) in door_target or number_words[i-1] in door_target.lower():
                door_number = i
                break
        
        if not door_number:
            return ActionResult(
                success=False,
                message="Which door would you like to open? (1-6)"
            )
        
        # Check if door world already exists
        door_world_key = f"door_{door_number}_entrance"
        
        if door_world_key in self.game_state.visited_locations:
            # World already generated, just move player there
            return ActionResult(
                success=True,
                message=f"You open door {door_number} and step through into the familiar world beyond.",
                new_location=door_world_key,
                state_changes={'current_door': door_number}
            )
        
        # Generate new world for this door
        from backend.services.content_generator import ContentGenerator
        import asyncio
        
        generator = ContentGenerator()
        
        # Generate the entrance location for this door world
        try:
            # Run the async generation
            loop = asyncio.get_event_loop()
            location = await generator.generate_location(
                door_number=door_number,
                player_history=[d.to_dict() for d in self.game_state.decision_history],
                keys_collected=len(self.game_state.keys_collected),
                location_id=door_world_key
            )
            
            # Build descriptive message about entering the new world
            world_themes = [
                "a mystical forest realm",
                "an ancient library filled with forgotten knowledge",
                "a twilight carnival with mysterious attractions",
                "a steampunk city floating in the clouds",
                "a haunted mansion on a stormy hill",
                "a cosmic observatory at the edge of reality"
            ]
            
            theme_desc = world_themes[door_number - 1] if door_number <= len(world_themes) else "a strange new world"
            
            message = f"""You open door {door_number} and step through...

{location.description}

You've entered {theme_desc}. Somewhere in this world lies the key you seek."""
            
            return ActionResult(
                success=True,
                message=message,
                new_location=door_world_key,
                state_changes={
                    'current_door': door_number,
                    'new_location_generated': location.to_dict(),
                    'door_number': door_number
                }
            )
            
        except Exception as e:
            # Fallback if generation fails
            return ActionResult(
                success=False,
                message=f"The door creaks open, but something seems wrong. Try again. (Error: {str(e)})"
            )
    
    async def handle_retrieve_key(self, door_number: int) -> ActionResult:
        """
        Handle retrieving a key from a door world.
        
        Implements Requirement 13.2: Key retrieval from worlds
        
        This method is called when the player successfully completes the
        objective in a door world and earns the key. The key is added to
        their inventory and can later be inserted into the vault.
        
        Args:
            door_number: Which door world the key is from (1-6)
            
        Returns:
            ActionResult with key added to inventory and state changes
        """
        # Check if player already has this key
        for item in self.game_state.inventory:
            if item.is_key and item.door_number == door_number:
                return ActionResult(
                    success=False,
                    message=f"You already have the key from door {door_number}."
                )
        
        # Check if key was already collected and inserted
        if door_number in self.game_state.keys_collected:
            return ActionResult(
                success=False,
                message=f"You've already collected and inserted the key from door {door_number}."
            )
        
        # Create the key item
        key_item = Item(
            id=f"key_{door_number}",
            name=f"Key {door_number}",
            description=f"A mystical key from the world behind door {door_number}. It glows with an otherworldly light.",
            is_key=True,
            door_number=door_number,
            properties={
                'door_number': door_number,
                'obtained_at': self.game_state.player_location
            }
        )
        
        # Build congratulatory message
        keys_after = len(self.game_state.keys_collected) + 1
        remaining = 6 - keys_after
        
        message = f"""✨ You've obtained the key from door {door_number}! ✨

The key materializes in your hand, pulsing with energy. You now have {keys_after} of 6 keys."""
        
        if remaining > 0:
            message += f"\n\n{remaining} {'key' if remaining == 1 else 'keys'} remaining. Return to the forest clearing to insert this key into the vault, or continue exploring other doors."
        else:
            message += "\n\nYou have all six keys! Return to the forest clearing and insert them into the vault to complete your quest."
        
        return ActionResult(
            success=True,
            message=message,
            items_added=[key_item],
            state_changes={
                'key_retrieved': door_number,
                'keys_in_inventory': keys_after
            }
        )
    
    async def handle_insert_key(self) -> ActionResult:
        """
        Handle inserting a key into the vault.
        
        Implements Requirement 13.5: Insert key into vault
        Implements Requirement 13.6: Detect vault opening with all 6 keys
        """
        # Find a key in inventory
        key_item = None
        for item in self.game_state.inventory:
            if item.is_key:
                key_item = item
                break
        
        if not key_item:
            return ActionResult(
                success=False,
                message="You don't have any keys to insert."
            )
        
        # Check if key already inserted
        if key_item.door_number in self.game_state.keys_collected:
            return ActionResult(
                success=False,
                message=f"You've already inserted the key from door {key_item.door_number}."
            )
        
        # Calculate how many keys will be collected after this insertion
        keys_after_insertion = len(self.game_state.keys_collected) + 1
        
        # Build message
        if keys_after_insertion == 6:
            # All keys collected - vault opens! (Requirement 13.6)
            vault_message = f"""You insert the final key from door {key_item.door_number} into the vault.

The vault glows with a soft light as all six keys align. With a satisfying click, the door swings open, revealing a single piece of parchment inside.

You carefully unfold it and read:

"If, instead of hunting for one giant, dramatic 'purpose,' you decided that a good human life is just a repeating pattern of six tiny daily habits—one moment of kindness, one of curiosity, one of courage, one of gratitude, one of play, and one of real, guilt-free rest—and you deliberately did each of those every single day of the week as your quiet offering to life, the universe, and everyone stuck on this spinning rock with you, then how many small, conscious choices would you be making in a week before the cosmos had to admit that, actually, you're doing a pretty excellent job of being alive?"

Congratulations! You've completed Nature42 and discovered the meaning of 42."""
            
            return ActionResult(
                success=True,
                message=vault_message,
                items_removed=[key_item],
                state_changes={
                    'key_inserted': key_item.door_number,
                    'vault_opened': True,
                    'game_completed': True
                }
            )
        else:
            # More keys needed
            keys_remaining = 6 - keys_after_insertion
            return ActionResult(
                success=True,
                message=f"You insert the key from door {key_item.door_number} into the vault. {keys_remaining} {'key' if keys_remaining == 1 else 'keys'} remaining.",
                items_removed=[key_item],
                state_changes={
                    'key_inserted': key_item.door_number
                }
            )
