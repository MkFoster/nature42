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
        
        # Check for debug mode - use debug locations if available
        if self.game_state.debug_mode:
            debug_location_key = f"debug_door_{door_number}"
            if debug_location_key in self.game_state.visited_locations:
                return ActionResult(
                    success=True,
                    message=f"🔧 DEBUG: Opening door {door_number}...\n\n{self.game_state.visited_locations[debug_location_key].description}",
                    new_location=debug_location_key,
                    state_changes={'current_door': door_number}
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
        
        # Build congratulatory message with teleport
        # Count keys currently in inventory (not yet inserted)
        keys_in_inventory = sum(1 for item in self.game_state.inventory if item.is_key)
        # Count keys already inserted into vault
        keys_inserted = len(self.game_state.keys_collected)
        # Total keys obtained (including this new one)
        total_keys = keys_in_inventory + keys_inserted + 1
        remaining = 6 - total_keys
        
        message = f"""✨ You've obtained the key from door {door_number}! ✨

The key materializes in your hand, pulsing with energy. You now have {total_keys} of 6 keys.

A brilliant flash of light surrounds you, and you feel yourself being pulled through space...

You find yourself back in the forest clearing. The six doors stand before you, and the vault awaits in the center."""
        
        if remaining > 0:
            message += f"\n\n{remaining} {'key' if remaining == 1 else 'keys'} remaining. You can insert this key into the vault now, or explore other doors to find more keys."
        else:
            message += "\n\nYou have all six keys! Insert them into the vault to complete your quest."
        
        return ActionResult(
            success=True,
            message=message,
            items_added=[key_item],
            new_location="forest_clearing",
            state_changes={
                'key_retrieved': door_number,
                'keys_in_inventory': total_keys,
                'current_door': None  # Clear current door since we're back in clearing
            }
        )
    
    async def handle_insert_key(self) -> ActionResult:
        """
        Handle inserting key(s) into the vault.
        
        If player has multiple keys, inserts all of them at once.
        
        Implements Requirement 13.5: Insert key into vault
        Implements Requirement 13.6: Detect vault opening with all 6 keys
        """
        # Find all keys in inventory that haven't been inserted yet
        keys_to_insert = []
        for item in self.game_state.inventory:
            if item.is_key and item.door_number not in self.game_state.keys_collected:
                keys_to_insert.append(item)
        
        if not keys_to_insert:
            return ActionResult(
                success=False,
                message="You don't have any keys to insert."
            )
        
        # Insert all keys
        keys_inserted_count = len(keys_to_insert)
        keys_after_insertion = len(self.game_state.keys_collected) + keys_inserted_count
        
        # Build message based on how many keys are being inserted
        if keys_inserted_count == 1:
            key_item = keys_to_insert[0]
            insertion_text = f"You insert the key from door {key_item.door_number} into the vault."
        else:
            door_numbers = sorted([k.door_number for k in keys_to_insert])
            door_list = ", ".join([f"#{n}" for n in door_numbers])
            insertion_text = f"You insert {keys_inserted_count} keys into the vault (doors {door_list})."
        
        # Check if vault opens
        if keys_after_insertion == 6:
            # All keys collected - vault opens! (Requirement 13.6)
            vault_message = f"""{insertion_text}

The vault glows with a soft light as all six keys align. With a satisfying click, the door swings open, revealing a single piece of parchment inside.

You carefully unfold it and read:

"If, instead of hunting for one giant, dramatic "purpose," you decided that a good human life is just a repeating pattern of six tiny daily habits—one moment of kindness, one of curiosity, one of courage, one of gratitude, one of play, and one of real, guilt-free rest—and you deliberately did each of those every single day of the week as your quiet offering to life, the universe, and everyone stuck on this spinning rock with you, then how many small, conscious choices would you be making in a week before the cosmos had to admit that, actually, you're doing a pretty excellent job of being alive?"

Congratulations! You've completed Nature42 and discovered the meaning of 42."""
            
            # Build state changes for all keys
            state_changes = {
                'keys_inserted': [k.door_number for k in keys_to_insert],
                'vault_opened': True,
                'game_completed': True
            }
            
            return ActionResult(
                success=True,
                message=vault_message,
                items_removed=keys_to_insert,
                state_changes=state_changes
            )
        else:
            # More keys needed
            keys_remaining = 6 - keys_after_insertion
            message = f"{insertion_text} {keys_remaining} {'key' if keys_remaining == 1 else 'keys'} remaining."
            
            # Build state changes for all keys
            state_changes = {
                'keys_inserted': [k.door_number for k in keys_to_insert]
            }
            
            return ActionResult(
                success=True,
                message=message,
                items_removed=keys_to_insert,
                state_changes=state_changes
            )
