"""
Command processing service for Nature42.

This module coordinates command parsing, validation, and execution by delegating
to specialized handler modules.
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel

from backend.models.game_state import GameState, Decision, LocationData
from backend.services.command_models import Intent, ValidationResult, ActionResult, CommandResult
from backend.services.action_handlers import ActionHandlers
from backend.services.door_handlers import DoorHandlers

# Load environment variables from .env file
load_dotenv()

# Re-export models for backward compatibility
__all__ = ['CommandProcessor', 'Intent', 'ValidationResult', 'ActionResult', 'CommandResult']


class CommandProcessor:
    """
    Coordinates command processing by delegating to specialized handlers.
    
    Uses Strands Agent SDK to parse commands, validates actions based on
    game context, and routes to appropriate handlers for execution.
    """
    
    def __init__(self, game_state: GameState):
        """
        Initialize command processor with game state.
        
        Args:
            game_state: Current game state
        """
        self.game_state = game_state
        
        # Initialize handlers
        self.action_handlers = ActionHandlers(game_state)
        self.door_handlers = DoorHandlers(game_state)
        
        # Get model configuration from environment variables
        model_id = os.getenv("STRANDS_MODEL_ID", "anthropic.claude-sonnet-4-20250514-v1:0")
        region_name = os.getenv("AWS_REGION", "us-east-1")
        
        # Create Bedrock model for command parsing
        # Use lower temperature for more consistent parsing
        self.model = BedrockModel(
            model_id=model_id,
            region_name=region_name,
            temperature=0.3,  # Lower temperature for more consistent parsing
            max_tokens=2048
        )
        
        # Create a persistent agent for conversation management
        # This agent maintains conversation history across commands
        from strands.agent.conversation_manager import SlidingWindowConversationManager
        
        system_prompt = """You are a command parser for a text adventure game called Nature42.

Your job is to parse player commands and maintain conversation context. You remember previous 
interactions, so when a player says "yes" or "that one", you can refer back to what was 
discussed earlier.

When parsing commands, always respond with valid JSON containing the action and target.
Be helpful and conversational when the player needs clarification."""
        
        self.conversation_agent = Agent(
            model=self.model,
            system_prompt=system_prompt,
            conversation_manager=SlidingWindowConversationManager(
                window_size=20,  # Keep last 20 messages for context
                should_truncate_results=True
            )
        )
        
        # Restore conversation history from game state
        self._restore_conversation_history()
    
    def _restore_conversation_history(self) -> None:
        """
        Restore conversation history from game state into the agent.
        
        This allows the agent to maintain context across HTTP requests by
        loading previous messages from the persisted game state.
        """
        if not self.game_state.conversation_history:
            return
        
        # Restore messages to the agent's conversation
        # The conversation history is stored as a list of message dicts
        for message in self.game_state.conversation_history:
            # Messages are already in the format the agent expects
            self.conversation_agent.messages.append(message)
    
    def _save_conversation_history(self) -> None:
        """
        Save current conversation history to game state.
        
        This persists the agent's conversation context so it can be restored
        in future requests, enabling multi-turn conversations across HTTP requests.
        """
        # Save the agent's messages to game state
        # Only keep the last 20 messages to avoid bloating the state
        self.game_state.conversation_history = self.conversation_agent.messages[-20:]
    
    def apply_state_changes(self, state_changes: Dict[str, Any]) -> None:
        """
        Apply state changes to the game state.
        
        This method updates the game state based on the changes returned
        from command execution. It handles:
        - Location changes
        - Inventory updates (items added/removed)
        - Decision tracking (Requirement 10.5)
        - Key collection
        - Door transitions
        
        Args:
            state_changes: Dictionary of state changes to apply
        """
        from datetime import datetime
        
        # Update player location
        if 'player_location' in state_changes:
            self.game_state.player_location = state_changes['player_location']
        
        # Update current door
        if 'current_door' in state_changes:
            self.game_state.current_door = state_changes['current_door']
        
        # Add items to inventory
        if 'items_added' in state_changes:
            for item_dict in state_changes['items_added']:
                item = Item.from_dict(item_dict)
                self.game_state.inventory.append(item)
        
        # Remove items from inventory
        if 'items_removed' in state_changes:
            for item_dict in state_changes['items_removed']:
                item_id = item_dict.get('id')
                self.game_state.inventory = [
                    item for item in self.game_state.inventory 
                    if item.id != item_id
                ]
        
        # Record decision in history (Requirement 10.5)
        if 'decision' in state_changes:
            decision = Decision.from_dict(state_changes['decision'])
            self.game_state.decision_history.append(decision)
        
        # Track key insertion
        if 'key_inserted' in state_changes:
            key_num = state_changes['key_inserted']
            if key_num not in self.game_state.keys_collected:
                self.game_state.keys_collected.append(key_num)
        
        # Add new location to visited locations
        if 'new_location_generated' in state_changes:
            location_dict = state_changes['new_location_generated']
            location = LocationData.from_dict(location_dict)
            self.game_state.visited_locations[location.id] = location
        
        # Update last_updated timestamp
        self.game_state.last_updated = datetime.now()
    
    def _is_significant_decision(self, intent: Intent, action_result: ActionResult) -> bool:
        """
        Determine if an action represents a significant player choice.
        
        Significant decisions include:
        - Opening doors (choosing which world to explore)
        - Major puzzle solutions
        - Important NPC interactions
        - Key retrievals
        
        Args:
            intent: The parsed intent
            action_result: The result of the action
            
        Returns:
            True if this is a significant decision
        """
        # Opening a door is significant
        if intent.action == "open" and "door" in (intent.target or "").lower():
            return True
        
        # Inserting a key is significant
        if intent.action == "insert" and "key" in (intent.target or "").lower():
            return True
        
        # Check state changes for significance markers
        if action_result.state_changes:
            if any(key in action_result.state_changes for key in [
                'puzzle_solved', 'key_retrieved', 'npc_major_interaction',
                'door_number', 'vault_opened'
            ]):
                return True
        
        return False
    
    def _create_decision(self, intent: Intent, action_result: ActionResult) -> Decision:
        """
        Create a Decision object for a significant choice.
        
        Implements Requirement 10.5: Track player choices in decision history
        
        Args:
            intent: The parsed intent
            action_result: The result of the action
            
        Returns:
            Decision object
        """
        # Build description based on action
        description = f"Player chose to {intent.action}"
        if intent.target:
            description += f" {intent.target}"
        
        # Extract consequences from state changes
        consequences = []
        if action_result.state_changes:
            if 'door_number' in action_result.state_changes:
                door_num = action_result.state_changes['door_number']
                consequences.append(f"Entered world behind door {door_num}")
            
            if 'key_retrieved' in action_result.state_changes:
                key_num = action_result.state_changes['key_retrieved']
                consequences.append(f"Retrieved key {key_num}")
            
            if 'key_inserted' in action_result.state_changes:
                key_num = action_result.state_changes['key_inserted']
                consequences.append(f"Inserted key {key_num} into vault")
            
            if 'vault_opened' in action_result.state_changes:
                consequences.append("Opened the vault and completed the game")
            
            if 'puzzle_solved' in action_result.state_changes:
                consequences.append("Solved a puzzle")
        
        return Decision(
            timestamp=datetime.now(),
            location_id=self.game_state.player_location,
            description=description,
            consequences=consequences
        )
    
    async def process_command(self, command: str) -> CommandResult:
        """
        Parse and execute a player command.
        
        Implements Requirements 1.1, 1.2, 1.3:
        - Parse natural language commands
        - Request clarification for ambiguous commands
        - Provide helpful feedback for invalid commands
        
        Args:
            command: Player's text command
            
        Returns:
            CommandResult with success status, message, and state changes
        """
        import asyncio
        
        # Parse the command to determine intent (run sync function in executor)
        loop = asyncio.get_event_loop()
        intent = await loop.run_in_executor(None, self._parse_intent_sync, command)
        
        # Handle ambiguous commands (Requirement 1.2)
        if intent.is_ambiguous:
            return CommandResult(
                success=False,
                message=intent.clarification_needed,
                needs_clarification=True
            )
        
        # Handle invalid commands (Requirement 1.3)
        if intent.is_invalid:
            suggestions_text = ""
            if intent.suggestions:
                suggestions_text = f"\n\nDid you mean:\n" + "\n".join(
                    f"- {s}" for s in intent.suggestions
                )
            
            return CommandResult(
                success=False,
                message=f"I'm not sure how to do that.{suggestions_text}"
            )
        
        # Validate the action against current context
        validation = await self._validate_action(intent)
        
        if not validation.is_valid:
            return CommandResult(
                success=False,
                message=validation.reason
            )
        
        # Execute the action
        action_result = await self._execute_action(intent)
        
        # Track significant decisions (Requirement 10.1, 10.2, 10.5)
        if self._is_significant_decision(intent, action_result):
            decision = self._create_decision(intent, action_result)
            action_result.decision = decision
        
        # Build state changes
        state_changes = action_result.state_changes.copy()
        
        if action_result.new_location:
            state_changes['player_location'] = action_result.new_location
        
        if action_result.items_added:
            state_changes['items_added'] = [item.to_dict() for item in action_result.items_added]
        
        if action_result.items_removed:
            state_changes['items_removed'] = [item.to_dict() for item in action_result.items_removed]
        
        if action_result.decision:
            state_changes['decision'] = action_result.decision.to_dict()
        
        # Save conversation history to game state for persistence across requests
        self._save_conversation_history()
        
        return CommandResult(
            success=action_result.success,
            message=action_result.message,
            state_changes=state_changes
        )
    
    def _parse_intent_sync(self, command: str) -> Intent:
        """
        Use AI to determine player intent from command (synchronous version).
        
        Uses persistent conversation agent to maintain context across commands.
        This allows the agent to remember previous interactions and provide
        better responses to follow-up questions like "yes" or "that one".
        
        Implements Property 1: Command parsing produces intent
        
        Args:
            command: Player's text command
            
        Returns:
            Intent object with parsed action and target
        """
        # Build the parsing instruction as a user message
        # The system prompt is set once on the persistent agent
        parsing_instruction = f"""Parse the player's command and extract:
1. The primary action (move, take, examine, use, talk, open, insert, etc.)
2. The target of the action (if any)
3. Whether the command is ambiguous and needs clarification
4. Whether the command is invalid/nonsensical

Common actions:
- Movement: go, move, walk, travel, enter, exit
- Interaction: take, get, pick up, drop, put down, use, examine, look at, inspect
- Communication: talk to, speak with, ask, tell, say hello
- Game mechanics: open door, insert key, check inventory, new game, start over
- Help: help, ?, what do i do, how do i play, what can i do
- Hint: hint, give me a hint, i'm stuck, clue

IMPORTANT PARSING RULES:
- For general help about commands, use action "help"
- For hints about progressing in the game, use action "hint"
- For starting a new game, use action "new_game"
- Convert ordinal numbers to digits: "first" -> "1", "second" -> "2", "third" -> "3", etc.
- For door references, extract the number: "the first door" -> "door 1", "door number 3" -> "door 3"
- Simplify natural language: "the squirrel" -> "squirrel", "that rabbit" -> "rabbit"

You MUST respond with ONLY valid JSON in this exact format:
{{
    "action": "primary_action",
    "target": "target_object_or_direction",
    "is_ambiguous": false,
    "is_invalid": false,
    "clarification_needed": null,
    "suggestions": []
}}

Examples:
- "go north" -> {{"action": "move", "target": "north", "is_ambiguous": false, "is_invalid": false}}
- "take the key" -> {{"action": "take", "target": "key", "is_ambiguous": false, "is_invalid": false}}
- "open the first door" -> {{"action": "open", "target": "door 1", "is_ambiguous": false, "is_invalid": false}}
- "talk to the squirrel" -> {{"action": "talk", "target": "squirrel", "is_ambiguous": false, "is_invalid": false}}
- "head down the path with the bridge" -> {{"action": "move", "target": "path with bridge", "is_ambiguous": false, "is_invalid": false}}
- "use it" -> {{"action": "use", "target": null, "is_ambiguous": true, "clarification_needed": "What would you like to use?"}}
- "fly to the moon" -> {{"action": "fly", "target": "moon", "is_invalid": true, "suggestions": ["go north", "go south", "examine area"]}}

Player's command: {command}"""
        
        try:
            # Use the persistent conversation agent to maintain context
            response = self.conversation_agent(parsing_instruction)
            
            # Extract text from AgentResult object
            response_text = str(response) if not isinstance(response, str) else response
            
            # Extract JSON from response
            json_str = response_text.strip()
            if json_str.startswith("```"):
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1]) if len(lines) > 2 else json_str
            
            intent_data = json.loads(json_str)
            
            return Intent(
                action=intent_data.get("action", "unknown"),
                target=intent_data.get("target"),
                is_ambiguous=intent_data.get("is_ambiguous", False),
                is_invalid=intent_data.get("is_invalid", False),
                clarification_needed=intent_data.get("clarification_needed"),
                suggestions=intent_data.get("suggestions", [])
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback: treat as invalid command
            return Intent(
                action="unknown",
                is_invalid=True,
                suggestions=["try 'go [direction]'", "try 'examine [object]'", "try 'take [item]'"]
            )
    
    async def _validate_action(self, intent: Intent) -> ValidationResult:
        """
        Check if action is valid in current context.
        
        Implements Requirement 12.1, 12.2, 12.3:
        - Evaluate action validity based on location, inventory, and state
        - Execute valid actions
        - Explain why invalid actions cannot be performed
        
        This method provides comprehensive context-aware validation that considers:
        - Current location and available exits
        - Items in location vs items in inventory
        - Game state (keys collected, current door, etc.)
        - Logical constraints (can't drop what you don't have, etc.)
        
        Args:
            intent: Parsed intent from command
            
        Returns:
            ValidationResult indicating if action is valid with detailed explanation
        """
        action = intent.action
        target = intent.target
        
        # Get current location data
        current_location = self.game_state.visited_locations.get(
            self.game_state.player_location
        )
        
        # Build context information for validation
        context_info = {
            'location': self.game_state.player_location,
            'has_location_data': current_location is not None,
            'inventory_count': len(self.game_state.inventory),
            'keys_collected': len(self.game_state.keys_collected),
            'current_door': self.game_state.current_door
        }
        
        # Validate based on action type
        if action == "move":
            return self._validate_movement(target, current_location, context_info)
        
        elif action == "take":
            return self._validate_take_item(target, current_location, context_info)
        
        elif action == "drop":
            return self._validate_drop_item(target, context_info)
        
        elif action == "use":
            return self._validate_use_item(target, current_location, context_info)
        
        elif action == "examine":
            return self._validate_examine(target, current_location, context_info)
        
        elif action in ["inventory", "check_inventory", "view_inventory"]:
            # Checking inventory is always valid
            return ValidationResult(
                is_valid=True, 
                reason="Inventory check is valid",
                context_info=context_info
            )
        
        elif action == "open":
            return self._validate_open(target, context_info)
        
        elif action == "insert":
            return self._validate_insert(target, context_info)
        
        elif action in ["talk", "speak"]:
            return self._validate_talk(target, current_location, context_info)
        
        elif action == "hint":
            # Hints are always valid
            return ValidationResult(
                is_valid=True,
                reason="Hint request is valid",
                context_info=context_info
            )
        
        # Default: allow action (will be handled by content generator)
        # This supports creative solutions per Requirement 12.4
        return ValidationResult(
            is_valid=True, 
            reason="Action is valid",
            context_info=context_info
        )
    
    def _validate_movement(
        self, 
        target: Optional[str], 
        current_location: Optional[LocationData],
        context_info: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate movement action based on available exits.
        
        Implements Requirement 12.1: Consider location when validating
        Implements Requirement 12.3: Explain why movement is invalid
        
        Note: We allow the action if there are ANY exits, and let the AI
        handle semantic matching of the target to the actual exit names.
        """
        if not target:
            return ValidationResult(
                is_valid=False,
                reason="Where would you like to go? Try specifying a direction or exit.",
                context_info=context_info
            )
        
        # Special handling for "back" or "return" commands
        if target.lower() in ["back", "return", "clearing", "forest clearing", "exit"]:
            return ValidationResult(
                is_valid=True,
                reason="Returning to previous location",
                context_info=context_info
            )
        
        # If we don't have location data, player is in limbo - only allow "back"
        if not current_location:
            return ValidationResult(
                is_valid=False,
                reason="You can't move from here right now. Try 'back' or 'return to clearing' to go back.",
                context_info=context_info
            )
        
        # Check if there are any exits at all
        if not current_location.exits:
            return ValidationResult(
                is_valid=False,
                reason="There don't appear to be any obvious exits from here. Try 'back' to return.",
                context_info=context_info
            )
        
        # If there are exits, allow the movement and let the AI handle semantic matching
        # Add available exits to context for the AI to use
        context_info['available_exits'] = current_location.exits
        
        return ValidationResult(
            is_valid=True, 
            reason="Movement is valid - AI will handle exit matching",
            context_info=context_info
        )
    
    def _validate_take_item(
        self,
        target: Optional[str],
        current_location: Optional[LocationData],
        context_info: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate taking an item based on location contents.
        
        Implements Requirement 12.1: Consider location and inventory
        Implements Requirement 12.3: Explain why item can't be taken
        """
        if not target:
            return ValidationResult(
                is_valid=False,
                reason="What would you like to take? Try 'take [item name]'.",
                context_info=context_info
            )
        
        # Check if we have location data
        if not current_location:
            return ValidationResult(
                is_valid=False,
                reason="You look around but don't see anything to take here.",
                context_info=context_info
            )
        
        # Check if there are items in the location
        # Let the AI handle semantic matching of the target name
        if current_location.items:
            # Add item list to context for the AI to use
            context_info['available_items'] = [item.name for item in current_location.items]
            return ValidationResult(
                is_valid=True,
                reason="Take action is valid - AI will handle item matching",
                context_info=context_info
            )
        else:
            return ValidationResult(
                is_valid=False,
                reason=f"There is no '{target}' here. In fact, there don't appear to be any items in this location.",
                context_info=context_info
            )
    
    def _validate_drop_item(
        self,
        target: Optional[str],
        context_info: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate dropping an item based on inventory contents.
        
        Implements Requirement 12.1: Consider inventory
        Implements Requirement 12.3: Explain why item can't be dropped
        """
        if not target:
            return ValidationResult(
                is_valid=False,
                reason="What would you like to drop? Try 'drop [item name]'.",
                context_info=context_info
            )
        
        # Check if item is in inventory
        item_names = [item.name.lower() for item in self.game_state.inventory]
        if target.lower() not in item_names:
            # Provide helpful feedback about what IS in inventory
            if self.game_state.inventory:
                inventory_items = ", ".join(item.name for item in self.game_state.inventory)
                reason = f"You don't have a '{target}'. You are carrying: {inventory_items}."
            else:
                reason = f"You don't have a '{target}'. Your inventory is empty."
            
            return ValidationResult(
                is_valid=False,
                reason=reason,
                context_info=context_info
            )
        
        return ValidationResult(
            is_valid=True, 
            reason="Item can be dropped",
            context_info=context_info
        )
    
    def _validate_use_item(
        self,
        target: Optional[str],
        current_location: Optional[LocationData],
        context_info: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate using an item based on inventory and context.
        
        Simplified: Just check if inventory is empty, let AI handle semantic matching.
        
        Implements Requirement 12.1: Consider inventory and location
        Implements Requirement 12.4: Allow creative interpretations
        """
        if not target:
            return ValidationResult(
                is_valid=False,
                reason="What would you like to use? Try 'use [item name]'.",
                context_info=context_info
            )
        
        # Just check if inventory is empty - let AI handle semantic matching
        if not self.game_state.inventory:
            return ValidationResult(
                is_valid=False,
                reason="Your inventory is empty.",
                context_info=context_info
            )
        
        # Player has items - let AI handle semantic matching and usage
        return ValidationResult(
            is_valid=True,
            reason="Item usage will be evaluated by AI",
            context_info=context_info
        )
    
    def _validate_examine(
        self,
        target: Optional[str],
        current_location: Optional[LocationData],
        context_info: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate examination action.
        
        Examination is generally always valid - players can examine anything.
        """
        # Examination is always valid - players can look at anything
        return ValidationResult(
            is_valid=True, 
            reason="Examination is valid",
            context_info=context_info
        )
    
    def _validate_open(
        self,
        target: Optional[str],
        context_info: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate opening action based on location and target.
        
        Implements Requirement 12.1: Consider location
        Implements Requirement 13.1: Doors only in forest clearing
        """
        if not target:
            return ValidationResult(
                is_valid=False,
                reason="What would you like to open? Try 'open [object]'.",
                context_info=context_info
            )
        
        if "door" in target.lower():
            # Check if we're in the forest clearing
            if self.game_state.player_location == "forest_clearing":
                return ValidationResult(
                    is_valid=True, 
                    reason="Door can be opened",
                    context_info=context_info
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    reason="There are no doors to open here. The six numbered doors are in the forest clearing.",
                    context_info=context_info
                )
        
        # Allow opening other things (content generator will handle)
        return ValidationResult(
            is_valid=True, 
            reason="Opening is valid",
            context_info=context_info
        )
    
    def _validate_insert(
        self,
        target: Optional[str],
        context_info: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate inserting action based on inventory and location.
        
        Implements Requirement 12.1: Consider inventory and location
        Implements Requirement 13.5: Key insertion only in clearing
        """
        if not target:
            return ValidationResult(
                is_valid=False,
                reason="What would you like to insert? Try 'insert key' or 'insert key into vault'.",
                context_info=context_info
            )
        
        if "key" in target.lower():
            # Check if player has any keys
            has_key = any(item.is_key for item in self.game_state.inventory)
            if not has_key:
                if self.game_state.inventory:
                    inventory_items = ", ".join(item.name for item in self.game_state.inventory)
                    reason = f"You don't have any keys to insert. You are carrying: {inventory_items}."
                else:
                    reason = "You don't have any keys to insert. Your inventory is empty."
                
                return ValidationResult(
                    is_valid=False,
                    reason=reason,
                    context_info=context_info
                )
            
            # Check if we're in the forest clearing
            if self.game_state.player_location != "forest_clearing":
                return ValidationResult(
                    is_valid=False,
                    reason="There's nowhere to insert a key here. The vault is in the forest clearing.",
                    context_info=context_info
                )
            
            return ValidationResult(
                is_valid=True, 
                reason="Key can be inserted",
                context_info=context_info
            )
        
        # Other insertion attempts
        return ValidationResult(
            is_valid=False,
            reason=f"You can't insert a '{target}' here.",
            context_info=context_info
        )
    
    def _validate_talk(
        self,
        target: Optional[str],
        current_location: Optional[LocationData],
        context_info: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate talking action based on NPCs in location.
        
        Implements Requirement 12.1: Consider location
        Implements Requirement 8.1: NPC interactions
        
        Note: We don't do strict name matching here - the AI content generator
        will handle semantic understanding of who the player wants to talk to.
        """
        if not target:
            # Check if there are any NPCs in the current location
            if current_location and current_location.npcs:
                npc_list = ", ".join(current_location.npcs)
                return ValidationResult(
                    is_valid=False,
                    reason=f"Who would you like to talk to? NPCs here: {npc_list}.",
                    context_info=context_info
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    reason="There's no one here to talk to.",
                    context_info=context_info
                )
        
        # Check if there are any NPCs in the location
        # Let the AI handle semantic matching of the target name
        if current_location and current_location.npcs:
            # Add NPC list to context for the AI to use
            context_info['available_npcs'] = current_location.npcs
            return ValidationResult(
                is_valid=True,
                reason="Talk action is valid - AI will handle NPC matching",
                context_info=context_info
            )
        else:
            return ValidationResult(
                is_valid=False,
                reason="There's no one here to talk to.",
                context_info=context_info
            )
        
        return ValidationResult(
            is_valid=True,
            reason="NPC interaction is valid",
            context_info=context_info
        )
    
    async def _execute_action(self, intent: Intent) -> ActionResult:
        """
        Route action to appropriate handler.
        
        Args:
            intent: Validated intent to execute
            
        Returns:
            ActionResult with success status and state changes
        """
        action = intent.action
        target = intent.target
        
        # Route to action handlers
        if action == "move":
            return await self.action_handlers.handle_movement(target)
        
        elif action == "take":
            return await self.action_handlers.handle_take_item(target)
        
        elif action == "drop":
            return await self.action_handlers.handle_drop_item(target)
        
        elif action == "use":
            return await self.action_handlers.handle_use_item(target)
        
        elif action in ["inventory", "check_inventory", "view_inventory"]:
            return await self.action_handlers.handle_inventory()
        
        elif action == "examine":
            return await self.action_handlers.handle_examine(target)
        
        elif action in ["help", "?", "what", "how"]:
            return await self.action_handlers.handle_help()
        
        elif action == "hint":
            return await self.action_handlers.handle_hint()
        
        elif action in ["talk", "speak"]:
            return await self.action_handlers.handle_talk(target)
        
        # Route to door handlers
        elif action == "open":
            if target and "door" in target.lower():
                return await self.door_handlers.handle_open_door(target)
            return ActionResult(
                success=True,
                message=f"You open the {target}. Nothing special happens."
            )
        
        elif action == "insert":
            if target and "key" in target.lower():
                return await self.door_handlers.handle_insert_key()
            return ActionResult(
                success=False,
                message="You can't insert that."
            )
        
        # Default: Use AI to handle any unrecognized actions
        # This allows for creative interactions like "play the pacman game", "dance", etc.
        return await self._handle_generic_action(action, target)
    
    async def _handle_generic_action(self, action: str, target: Optional[str]) -> ActionResult:
        """
        Handle any unrecognized action using AI.
        
        This allows players to interact creatively with the environment:
        - "play the pacman game"
        - "dance with the gnome"
        - "press the red button"
        - "activate the portal"
        
        Args:
            action: The action verb
            target: The target of the action
            
        Returns:
            ActionResult with AI-generated response
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
                message=f"You try to {action} {target if target else 'something'}, but nothing happens."
            )
        
        # Use AI to generate contextual response
        model_id = os.getenv("STRANDS_MODEL_ID", "anthropic.claude-sonnet-4-20250514-v1:0")
        region_name = os.getenv("AWS_REGION", "us-east-1")
        
        model = BedrockModel(
            model_id=model_id,
            region_name=region_name,
            temperature=0.7,
            max_tokens=1024
        )
        
        inventory_list = "\n".join([f"- {item.name}" for item in self.game_state.inventory]) if self.game_state.inventory else "Empty"
        
        system_prompt = f"""You are the game master for Nature42. The player is trying an action.

CURRENT LOCATION:
{current_location.description}

PLAYER'S INVENTORY:
{inventory_list}

GAME CONTEXT:
- Keys collected: {len(self.game_state.keys_collected)}/6
- Current door: {self.game_state.current_door if self.game_state.current_door else "Forest Clearing"}

The player wants to: {action} {target if target else ''}

Generate a creative, contextual response. If the action could progress the puzzle or reveal something important, describe that.
If it's just a fun interaction, make it entertaining. If it doesn't make sense, explain why gently.
Keep responses 2-3 paragraphs max."""

        agent = Agent(model=model, system_prompt=system_prompt)
        
        try:
            # Run synchronously in executor
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: agent(f"Player action: {action} {target if target else ''}")
            )
            
            message = str(response).strip()
            
            return ActionResult(
                success=True,
                message=message
            )
        except Exception as e:
            # Fallback
            if target:
                return ActionResult(
                    success=True,
                    message=f"You {action} the {target}, but nothing happens."
                )
            else:
                return ActionResult(
                    success=False,
                    message=f"What would you like to {action}?"
                )
    
    # Backward compatibility methods for tests
    async def _handle_movement(self, direction: str) -> ActionResult:
        """Backward compatibility wrapper."""
        return await self.action_handlers.handle_movement(direction)
    
    async def _handle_take_item(self, item_name: str) -> ActionResult:
        """Backward compatibility wrapper."""
        return await self.action_handlers.handle_take_item(item_name)
    
    async def _handle_drop_item(self, item_name: str) -> ActionResult:
        """Backward compatibility wrapper."""
        return await self.action_handlers.handle_drop_item(item_name)
    
    async def _handle_inventory(self) -> ActionResult:
        """Backward compatibility wrapper."""
        return await self.action_handlers.handle_inventory()
    
    async def _handle_use_item(self, item_name: str) -> ActionResult:
        """Backward compatibility wrapper."""
        return await self.action_handlers.handle_use_item(item_name)
    
    async def _handle_examine(self, target: Optional[str]) -> ActionResult:
        """Backward compatibility wrapper."""
        return await self.action_handlers.handle_examine(target)
    
    async def _handle_help(self) -> ActionResult:
        """Backward compatibility wrapper."""
        return await self.action_handlers.handle_help()
    
    async def _handle_open_door(self, door_target: str) -> ActionResult:
        """Backward compatibility wrapper."""
        return await self.door_handlers.handle_open_door(door_target)
    
    async def _handle_retrieve_key(self, door_number: int) -> ActionResult:
        """Backward compatibility wrapper."""
        return await self.door_handlers.handle_retrieve_key(door_number)
    
    async def _handle_insert_key(self) -> ActionResult:
        """Backward compatibility wrapper."""
        return await self.door_handlers.handle_insert_key()
    
