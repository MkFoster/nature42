"""
Action handlers for Nature42 command processing.

This module contains handlers for basic game actions like movement,
inventory management, examination, and help.
"""

from typing import Optional
from backend.services.command_models import ActionResult
from backend.models.game_state import GameState


class ActionHandlers:
    """Handles basic game actions."""
    
    def __init__(self, game_state: GameState):
        """
        Initialize action handlers.
        
        Args:
            game_state: Current game state
        """
        self.game_state = game_state
    
    async def handle_movement(self, direction: str) -> ActionResult:
        """
        Handle player movement between locations.
        
        Uses AI to semantically match player's direction to actual exit names.
        
        Special handling for:
        - Returning to forest clearing from door worlds
        - Moving between locations within door worlds
        - Generating new locations as needed
        
        Args:
            direction: Direction or destination to move to (may be natural language)
            
        Returns:
            ActionResult with new location
        """
        # Check for special movement commands
        if direction.lower() in ["back", "return", "clearing", "forest clearing", "exit"]:
            # Return to forest clearing
            if self.game_state.current_door is not None:
                return ActionResult(
                    success=True,
                    message="You step back through the door and return to the forest clearing. The six doors and central vault stand before you once more.",
                    new_location="forest_clearing",
                    state_changes={'current_door': None}
                )
            else:
                return ActionResult(
                    success=False,
                    message="You're already in the forest clearing."
                )
        
        # Get current location
        current_location = self.game_state.visited_locations.get(
            self.game_state.player_location
        )
        
        if not current_location:
            return ActionResult(
                success=False,
                message="You can't move from here right now."
            )
        
        # Use AI to match the player's direction to an actual exit
        matched_exit = await self._match_exit_with_ai(direction, current_location.exits)
        
        if not matched_exit:
            available_exits = ", ".join(current_location.exits) if current_location.exits else "none"
            return ActionResult(
                success=False,
                message=f"You can't go '{direction}' from here. Available exits: {available_exits}."
            )
        
        # Generate new location ID based on current location and matched exit
        new_location_id = f"{self.game_state.player_location}_{matched_exit.lower().replace(' ', '_')}"
        
        # Check if we've already visited this location
        if new_location_id in self.game_state.visited_locations:
            cached_location = self.game_state.visited_locations[new_location_id]
            return ActionResult(
                success=True,
                message=f"You move toward {matched_exit}.\n\n{cached_location.description}",
                new_location=new_location_id
            )
        
        # Generate new location
        from backend.services.content_generator import ContentGenerator
        import asyncio
        
        generator = ContentGenerator()
        
        try:
            # Generate the new location
            location = await generator.generate_location(
                door_number=self.game_state.current_door or 1,
                player_history=[d.to_dict() for d in self.game_state.decision_history],
                keys_collected=len(self.game_state.keys_collected),
                location_id=new_location_id
            )
            
            # CRITICAL: Add location to game state BEFORE updating player location
            # This prevents the player from getting stuck in limbo
            self.game_state.visited_locations[new_location_id] = location
            
            message = f"You move toward {matched_exit}.\n\n{location.description}"
            
            return ActionResult(
                success=True,
                message=message,
                new_location=new_location_id,
                state_changes={
                    'new_location_generated': location.to_dict()
                }
            )
        except Exception as e:
            # Log the error
            import traceback
            print(f"Error generating location: {e}")
            print(traceback.format_exc())
            
            # CRITICAL: Do NOT update player location on error
            # Stay in current location to prevent limbo
            return ActionResult(
                success=False,
                message=f"You try to move toward {matched_exit}, but the path seems blocked. Try again or explore other directions."
            )
    
    async def _match_exit_with_ai(self, player_direction: str, available_exits: list[str]) -> Optional[str]:
        """
        Use AI to semantically match player's direction to an actual exit.
        
        Args:
            player_direction: What the player said (e.g., "path with old stone bridge")
            available_exits: List of actual exit names (e.g., ["The Luminescent Bridge", "The Whispering Forest Path"])
            
        Returns:
            The matched exit name, or None if no match
        """
        import os
        import json
        from strands import Agent
        from strands.models import BedrockModel
        
        # Quick exact match first
        for exit_name in available_exits:
            if player_direction.lower() == exit_name.lower():
                return exit_name
        
        # Use AI for semantic matching
        model_id = os.getenv("STRANDS_MODEL_ID", "anthropic.claude-sonnet-4-20250514-v1:0")
        region_name = os.getenv("AWS_REGION", "us-east-1")
        
        model = BedrockModel(
            model_id=model_id,
            region_name=region_name,
            temperature=0.1,
            max_tokens=256
        )
        
        prompt = f"""Match the player's direction to one of the available exits.

Player wants to go: "{player_direction}"

Available exits:
{chr(10).join(f"- {exit}" for exit in available_exits)}

Respond with ONLY the exact exit name that best matches what the player wants, or "NONE" if no match.
Do not include any explanation or extra text."""

        agent = Agent(model=model)
        
        try:
            response = agent(prompt)
            matched = str(response).strip()
            
            # Check if the response is one of the available exits
            for exit_name in available_exits:
                if exit_name.lower() in matched.lower() or matched.lower() in exit_name.lower():
                    return exit_name
            
            return None
        except Exception:
            # Fallback: try simple substring matching
            for exit_name in available_exits:
                if player_direction.lower() in exit_name.lower():
                    return exit_name
            return None
    
    async def handle_take_item(self, item_name: str) -> ActionResult:
        """
        Handle taking an item using AI to determine if it exists and can be taken.
        
        Simplified approach: Let AI decide based on location description.
        
        Args:
            item_name: Name of the item to take
            
        Returns:
            ActionResult with item added to inventory
        """
        import os
        from strands import Agent
        from strands.models import BedrockModel
        from backend.models.game_state import Item
        
        current_location = self.game_state.visited_locations.get(
            self.game_state.player_location
        )
        
        if not current_location:
            return ActionResult(
                success=False,
                message="You can't take anything here."
            )
        
        # First check if item is in the items array (structured data)
        item_to_take = None
        for item in current_location.items:
            if item_name.lower() in item.name.lower() or item.name.lower() in item_name.lower():
                item_to_take = item
                break
        
        if item_to_take:
            # Import here to avoid circular dependency
            from backend.services.door_handlers import DoorHandlers
            
            # Special handling for keys
            if item_to_take.is_key and item_to_take.door_number:
                door_handlers = DoorHandlers(self.game_state)
                return await door_handlers.handle_retrieve_key(item_to_take.door_number)
            
            # Regular item from items array
            return ActionResult(
                success=True,
                message=f"You take the {item_to_take.name}.",
                items_added=[item_to_take],
                state_changes={'item_taken': item_to_take.id}
            )
        
        # Item not in array - use AI to determine if it can be taken from description
        model_id = os.getenv("STRANDS_MODEL_ID", "anthropic.claude-sonnet-4-20250514-v1:0")
        region_name = os.getenv("AWS_REGION", "us-east-1")
        
        model = BedrockModel(
            model_id=model_id,
            region_name=region_name,
            temperature=0.3,
            max_tokens=512
        )
        
        system_prompt = f"""You are the game master for Nature42. Determine if the player can take an item.

CURRENT LOCATION:
{current_location.description}

The player wants to take: {item_name}

Respond with JSON in this format:
{{
    "can_take": true/false,
    "item_name": "exact name of item",
    "message": "response to player",
    "is_key": true/false
}}

If the item is mentioned in the description and could reasonably be picked up, set can_take to true.
If it's the key for this world, set is_key to true."""

        agent = Agent(model=model, system_prompt=system_prompt)
        
        try:
            # Run synchronously in executor
            import asyncio
            import json
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: agent(f"Can player take: {item_name}?")
            )
            
            response_text = str(response).strip()
            # Extract JSON
            if "```" in response_text:
                lines = response_text.split("\n")
                response_text = "\n".join([l for l in lines if not l.strip().startswith("```")])
            
            result = json.loads(response_text)
            
            if result.get("can_take"):
                # Create item and add to inventory
                new_item = Item(
                    id=f"{item_name.lower().replace(' ', '_')}_{self.game_state.current_door}",
                    name=result.get("item_name", item_name),
                    description=f"A {item_name} you found",
                    is_key=result.get("is_key", False),
                    door_number=self.game_state.current_door if result.get("is_key") else None
                )
                
                # If it's a key, use special handler
                if new_item.is_key and new_item.door_number:
                    from backend.services.door_handlers import DoorHandlers
                    door_handlers = DoorHandlers(self.game_state)
                    return await door_handlers.handle_retrieve_key(new_item.door_number)
                
                return ActionResult(
                    success=True,
                    message=result.get("message", f"You take the {new_item.name}."),
                    items_added=[new_item],
                    state_changes={'item_taken': new_item.id}
                )
            else:
                return ActionResult(
                    success=False,
                    message=result.get("message", f"There is no {item_name} here.")
                )
        except Exception as e:
            # Fallback
            return ActionResult(
                success=False,
                message=f"There is no {item_name} here."
            )
    
    async def handle_drop_item(self, item_name: str) -> ActionResult:
        """
        Handle dropping an item from inventory with semantic matching.
        
        Implements Requirement 3.5: Remove item from inventory
        """
        if not self.game_state.inventory:
            return ActionResult(
                success=False,
                message="Your inventory is empty."
            )
        
        # Try semantic matching - "watch" should match "Giant Neon Swatch Watch"
        item_to_drop = None
        item_name_lower = item_name.lower()
        
        # First try exact match
        for item in self.game_state.inventory:
            if item.name.lower() == item_name_lower:
                item_to_drop = item
                break
        
        # Then try partial match
        if not item_to_drop:
            for item in self.game_state.inventory:
                if item_name_lower in item.name.lower() or any(word in item.name.lower() for word in item_name_lower.split()):
                    item_to_drop = item
                    break
        
        if not item_to_drop:
            inventory_list = ", ".join([item.name for item in self.game_state.inventory])
            return ActionResult(
                success=False,
                message=f"You don't have a '{item_name}'. You are carrying: {inventory_list}."
            )
        
        return ActionResult(
            success=True,
            message=f"You drop the {item_to_drop.name}.",
            items_removed=[item_to_drop]
        )
    
    async def handle_inventory(self) -> ActionResult:
        """
        Handle viewing inventory.
        
        Implements Requirement 3.3: Display all items in inventory
        """
        if not self.game_state.inventory:
            return ActionResult(
                success=True,
                message="Your inventory is empty."
            )
        
        items_list = "\n".join(
            f"- {item.name}: {item.description}"
            for item in self.game_state.inventory
        )
        
        return ActionResult(
            success=True,
            message=f"You are carrying:\n{items_list}"
        )
    
    async def handle_use_item(self, item_name: str) -> ActionResult:
        """
        Handle using an item from inventory using AI to understand context.
        
        Simplified approach: Let AI match the item name semantically and determine
        what happens when it's used in the current context.
        
        Args:
            item_name: Name of the item to use (may be partial or natural language)
            
        Returns:
            ActionResult with success status and message
        """
        import os
        from strands import Agent
        from strands.models import BedrockModel
        
        if not self.game_state.inventory:
            return ActionResult(
                success=False,
                message="Your inventory is empty."
            )
        
        # Get current location for context
        current_location = self.game_state.visited_locations.get(
            self.game_state.player_location
        )
        
        # Build inventory list for AI
        inventory_list = "\n".join([f"- {item.name}: {item.description}" for item in self.game_state.inventory])
        
        # Use AI to match item and determine usage
        model_id = os.getenv("STRANDS_MODEL_ID", "anthropic.claude-sonnet-4-20250514-v1:0")
        region_name = os.getenv("AWS_REGION", "us-east-1")
        
        model = BedrockModel(
            model_id=model_id,
            region_name=region_name,
            temperature=0.7,
            max_tokens=1024
        )
        
        location_desc = current_location.description if current_location else "Unknown location"
        
        system_prompt = f"""You are the game master for Nature42. The player wants to use an item.

CURRENT LOCATION:
{location_desc}

PLAYER'S INVENTORY:
{inventory_list}

GAME CONTEXT:
- Keys collected: {len(self.game_state.keys_collected)}/6
- Current door: {self.game_state.current_door if self.game_state.current_door else "Forest Clearing"}

The player wants to use: "{item_name}"

Match this to an item in their inventory (use semantic understanding - "watch" matches "Giant Neon Swatch Watch").
Then describe what happens when they use it in this context.

If it's a key, remind them to insert it into the vault instead.
If using the item reveals something important or progresses the puzzle, describe that.
Be creative and contextual. Keep responses 2-3 paragraphs max."""

        agent = Agent(model=model, system_prompt=system_prompt)
        
        try:
            # Run synchronously in executor
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: agent(f"Player uses: {item_name}")
            )
            
            message = str(response).strip()
            
            return ActionResult(
                success=True,
                message=message,
                state_changes={'item_used': item_name}
            )
        except Exception as e:
            # Fallback
            return ActionResult(
                success=False,
                message=f"You don't have a '{item_name}' to use."
            )
    
    async def handle_examine(self, target: Optional[str]) -> ActionResult:
        """
        Handle examining objects or the environment using AI.
        
        Simplified approach: Let AI generate examination responses based on
        the location description and what the player wants to examine.
        """
        import os
        from strands import Agent
        from strands.models import BedrockModel
        
        # Get current location
        current_location = self.game_state.visited_locations.get(
            self.game_state.player_location
        )
        
        if not current_location:
            return ActionResult(
                success=True,
                message="You look around but see nothing special."
            )
        
        # Handle examining the area/room/surroundings as examining the location
        if not target or target.lower() in ["area", "room", "surroundings", "location", "here"]:
            # Examine current location
            current_location = self.game_state.visited_locations.get(
                self.game_state.player_location
            )
            if current_location:
                return ActionResult(
                    success=True,
                    message=current_location.description
                )
            return ActionResult(
                success=True,
                message="You look around but see nothing special."
            )
        
        # Special handling for vault examination (Requirement 13.2)
        if "vault" in target.lower():
            if self.game_state.player_location == "forest_clearing":
                from backend.services.forest_clearing import get_vault_description
                vault_desc = get_vault_description(len(self.game_state.keys_collected))
                return ActionResult(
                    success=True,
                    message=vault_desc
                )
            else:
                return ActionResult(
                    success=True,
                    message="There's no vault here. The vault is in the forest clearing."
                )
        
        # Special handling for door examination
        if "door" in target.lower():
            if self.game_state.player_location == "forest_clearing":
                # Extract door number
                door_number = None
                number_words = ["one", "two", "three", "four", "five", "six"]
                
                for i in range(1, 7):
                    if str(i) in target or number_words[i-1] in target.lower():
                        door_number = i
                        break
                
                if door_number:
                    from backend.services.forest_clearing import get_door_description
                    has_key = door_number in self.game_state.keys_collected
                    door_desc = get_door_description(door_number, has_key)
                    return ActionResult(
                        success=True,
                        message=door_desc
                    )
                else:
                    return ActionResult(
                        success=True,
                        message="Which door would you like to examine? (1-6)"
                    )
            else:
                return ActionResult(
                    success=True,
                    message="There are no numbered doors here. The six doors are in the forest clearing."
                )
        
        # Use AI to examine specific target based on location description
        model_id = os.getenv("STRANDS_MODEL_ID", "anthropic.claude-sonnet-4-20250514-v1:0")
        region_name = os.getenv("AWS_REGION", "us-east-1")
        
        model = BedrockModel(
            model_id=model_id,
            region_name=region_name,
            temperature=0.7,
            max_tokens=512
        )
        
        system_prompt = f"""You are the game master for Nature42. The player wants to examine something.

CURRENT LOCATION:
{current_location.description}

GAME CONTEXT:
- Keys collected: {len(self.game_state.keys_collected)}/6
- Current door: {self.game_state.current_door if self.game_state.current_door else "Forest Clearing"}

Generate a detailed examination response for what the player is looking at.
Be descriptive and provide hints if the object is important for finding the key.
Keep responses concise (1-2 paragraphs)."""

        agent = Agent(model=model, system_prompt=system_prompt)
        
        try:
            # Run synchronously in executor
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: agent(f"Player examines: {target}")
            )
            
            examination = str(response).strip()
            
            return ActionResult(
                success=True,
                message=examination
            )
        except Exception as e:
            # Fallback
            return ActionResult(
                success=True,
                message=f"You examine the {target}. It looks interesting."
            )
    
    async def handle_help(self) -> ActionResult:
        """
        Handle help requests from the player.
        
        Provides brief instructions on how to interact with the game,
        including common commands and actions.
        
        Returns:
            ActionResult with help message
        """
        help_message = """Here are some things you can do:

• LOOK AROUND - Examine your surroundings
• EXAMINE [object] - Look at something closely (e.g., "examine vault", "examine door 1")
• OPEN DOOR [number] - Open one of the six doors (1-6)
• GO [direction] - Move in a direction or through an exit
• TAKE [item] - Pick up an item
• USE [item] - Use an item from your inventory
• INVENTORY - Check what you're carrying
• INSERT KEY - Insert a key into the vault
• HINT - Ask for a hint if you're stuck

You can use natural language - the game understands various phrasings!

Your goal: Collect all six keys from the six door worlds and unlock the vault."""
        
        return ActionResult(
            success=True,
            message=help_message
        )
    
    async def handle_hint(self) -> ActionResult:
        """
        Handle hint requests using AI to provide contextual, helpful hints.
        
        AI considers:
        - Current location and what's there
        - What the player has done so far
        - What items they're carrying
        - Keys collected
        - Recent interactions
        
        Returns:
            ActionResult with contextual hint
        """
        import os
        from strands import Agent
        from strands.models import BedrockModel
        
        # Get current location
        current_location = self.game_state.visited_locations.get(
            self.game_state.player_location
        )
        
        location_desc = current_location.description if current_location else "Unknown location"
        inventory_list = "\n".join([f"- {item.name}" for item in self.game_state.inventory]) if self.game_state.inventory else "Empty"
        
        # Build context about recent actions
        recent_context = ""
        if self.game_state.decision_history:
            recent_decisions = self.game_state.decision_history[-3:]
            recent_context = "\n\nRecent actions:\n" + "\n".join([f"- {d.description}" for d in recent_decisions])
        
        # Use AI to generate contextual hint
        model_id = os.getenv("STRANDS_MODEL_ID", "anthropic.claude-sonnet-4-20250514-v1:0")
        region_name = os.getenv("AWS_REGION", "us-east-1")
        
        model = BedrockModel(
            model_id=model_id,
            region_name=region_name,
            temperature=0.7,
            max_tokens=512
        )
        
        system_prompt = f"""You are the game master for Nature42. Provide a helpful hint.

CURRENT LOCATION:
{location_desc}

PLAYER'S INVENTORY:
{inventory_list}

GAME PROGRESS:
- Keys collected: {len(self.game_state.keys_collected)}/6
- Current door world: {self.game_state.current_door if self.game_state.current_door else "Forest Clearing"}
{recent_context}

Provide a contextual hint that:
1. Acknowledges what the player has done
2. Suggests a specific next step based on the current situation
3. Doesn't spoil the solution but points them in the right direction
4. References specific objects or NPCs in the current location

Keep it concise (2-3 sentences) and helpful."""

        agent = Agent(model=model, system_prompt=system_prompt)
        
        try:
            # Run synchronously in executor
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: agent("Give the player a helpful hint")
            )
            
            hint = str(response).strip()
            
            return ActionResult(
                success=True,
                message=hint
            )
        except Exception as e:
            # Fallback
            return ActionResult(
                success=True,
                message="Try examining objects around you, talking to NPCs, or exploring different areas. The key is hidden somewhere in this world!"
            )
    
    async def handle_talk(self, npc_target: str) -> ActionResult:
        """
        Handle talking to NPCs using simple AI-generated dialogue.
        
        Simplified approach: Just use AI to generate a response based on the
        location description and what the player said.
        
        Args:
            npc_target: The NPC the player wants to talk to (may be natural language)
            
        Returns:
            ActionResult with NPC dialogue
        """
        import os
        from strands import Agent
        from strands.models import BedrockModel
        
        # Get current location
        current_location = self.game_state.visited_locations.get(
            self.game_state.player_location
        )
        
        if not current_location:
            return ActionResult(
                success=False,
                message="There's no one here to talk to."
            )
        
        # Simple AI call to generate dialogue
        model_id = os.getenv("STRANDS_MODEL_ID", "anthropic.claude-sonnet-4-20250514-v1:0")
        region_name = os.getenv("AWS_REGION", "us-east-1")
        
        model = BedrockModel(
            model_id=model_id,
            region_name=region_name,
            temperature=0.7,
            max_tokens=1024
        )
        
        system_prompt = f"""You are the game master for Nature42. The player wants to talk to someone.

CURRENT LOCATION:
{current_location.description}

GAME CONTEXT:
- Keys collected: {len(self.game_state.keys_collected)}/6
- Current door: {self.game_state.current_door if self.game_state.current_door else "Forest Clearing"}

Generate a natural, in-character response from the NPC the player is trying to talk to.
Be helpful, stay in character, and provide hints if appropriate.
Keep responses concise (2-3 paragraphs max)."""

        agent = Agent(model=model, system_prompt=system_prompt)
        
        try:
            # Run synchronously in executor
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: agent(f"Player says: talk to {npc_target}")
            )
            
            dialogue = str(response).strip()
            
            return ActionResult(
                success=True,
                message=dialogue
            )
        except Exception as e:
            # Log the error for debugging
            import traceback
            print(f"Error in handle_talk: {e}")
            print(traceback.format_exc())
            
            # Fallback response
            return ActionResult(
                success=True,
                message=f"You try to talk to {npc_target}, but they seem preoccupied at the moment."
            )
    
    async def _match_npc_with_ai(self, player_target: str, available_npcs: list[str]) -> Optional[str]:
        """
        Use AI to semantically match player's target to an actual NPC.
        
        Args:
            player_target: What the player said (e.g., "the squirrel", "rabbit")
            available_npcs: List of actual NPC names (e.g., ["Thumper the Wise Rabbit", "The Cabbage Patch Keeper"])
            
        Returns:
            The matched NPC name, or None if no match
        """
        import os
        import json
        from strands import Agent
        from strands.models import BedrockModel
        
        # Quick exact match first
        for npc_name in available_npcs:
            if player_target.lower() == npc_name.lower():
                return npc_name
        
        # Use AI for semantic matching
        model_id = os.getenv("STRANDS_MODEL_ID", "anthropic.claude-sonnet-4-20250514-v1:0")
        region_name = os.getenv("AWS_REGION", "us-east-1")
        
        model = BedrockModel(
            model_id=model_id,
            region_name=region_name,
            temperature=0.1,
            max_tokens=256
        )
        
        prompt = f"""Match the player's target to one of the available NPCs.

Player wants to talk to: "{player_target}"

Available NPCs:
{chr(10).join(f"- {npc}" for npc in available_npcs)}

Respond with ONLY the exact NPC name that best matches what the player wants, or "NONE" if no match.
Do not include any explanation or extra text.

Examples:
- "the squirrel" matches "A peculiar squirrel with intelligent eyes"
- "rabbit" matches "Thumper the Wise Rabbit"
- "keeper" matches "The Cabbage Patch Keeper"
"""

        agent = Agent(model=model)
        
        try:
            response = agent(prompt)
            matched = str(response).strip()
            
            # Check if the response is one of the available NPCs
            for npc_name in available_npcs:
                if npc_name.lower() in matched.lower() or matched.lower() in npc_name.lower():
                    return npc_name
            
            return None
        except Exception:
            # Fallback: try simple substring matching
            player_lower = player_target.lower()
            for npc_name in available_npcs:
                npc_lower = npc_name.lower()
                # Check if any word from player_target is in the NPC name
                for word in player_lower.split():
                    if len(word) > 2 and word in npc_lower:
                        return npc_name
            return None
