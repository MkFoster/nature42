"""
Command processing service for Nature42.

This module handles parsing and executing player commands using AI-powered
natural language understanding. It validates actions based on game context
and provides helpful feedback for ambiguous or invalid commands.
"""

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel

from backend.models.game_state import GameState, Item, Decision, LocationData

# Load environment variables from .env file
load_dotenv()


@dataclass
class Intent:
    """
    Represents the parsed intent from a player command.
    
    Attributes:
        action: The primary action (e.g., "move", "take", "examine", "talk")
        target: The target of the action (e.g., "north", "key", "door")
        is_ambiguous: Whether the command needs clarification
        is_invalid: Whether the command is invalid
        clarification_needed: What clarification is needed (if ambiguous)
        suggestions: Suggested valid alternatives (if invalid)
    """
    action: str
    target: Optional[str] = None
    is_ambiguous: bool = False
    is_invalid: bool = False
    clarification_needed: Optional[str] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


@dataclass
class ValidationResult:
    """
    Result of validating an action against game context.
    
    Attributes:
        is_valid: Whether the action can be performed
        reason: Explanation of why action is valid/invalid
        context_info: Additional context information
    """
    is_valid: bool
    reason: str
    context_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context_info is None:
            self.context_info = {}


@dataclass
class ActionResult:
    """
    Result of executing an action.
    
    Attributes:
        success: Whether the action succeeded
        message: Response message to player
        state_changes: Changes to apply to game state
        new_location: New location ID if player moved
        items_added: Items added to inventory
        items_removed: Items removed from inventory
        decision: Significant decision to record (if any)
    """
    success: bool
    message: str
    state_changes: Dict[str, Any] = None
    new_location: Optional[str] = None
    items_added: List[Item] = None
    items_removed: List[Item] = None
    decision: Optional[Decision] = None
    
    def __post_init__(self):
        if self.state_changes is None:
            self.state_changes = {}
        if self.items_added is None:
            self.items_added = []
        if self.items_removed is None:
            self.items_removed = []


@dataclass
class CommandResult:
    """
    Complete result of processing a command.
    
    Attributes:
        success: Whether command was successfully processed
        message: Response message to player
        state_changes: Changes to apply to game state
        needs_clarification: Whether clarification is needed
    """
    success: bool
    message: str
    state_changes: Dict[str, Any] = None
    needs_clarification: bool = False
    
    def __post_init__(self):
        if self.state_changes is None:
            self.state_changes = {}


class CommandProcessor:
    """
    Processes natural language player commands.
    
    Uses Strands Agent SDK to parse commands, validate actions based on
    game context, and execute actions with appropriate state updates.
    """
    
    def __init__(self, game_state: GameState):
        """
        Initialize command processor with game state.
        
        Args:
            game_state: Current game state
        """
        self.game_state = game_state
        
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
        
        return CommandResult(
            success=action_result.success,
            message=action_result.message,
            state_changes=state_changes
        )
    
    def _parse_intent_sync(self, command: str) -> Intent:
        """
        Use AI to determine player intent from command (synchronous version).
        
        Implements Property 1: Command parsing produces intent
        
        Args:
            command: Player's text command
            
        Returns:
            Intent object with parsed action and target
        """
        system_prompt = """You are a command parser for a text adventure game.

Parse the player's command and extract:
1. The primary action (move, take, examine, use, talk, open, insert, etc.)
2. The target of the action (if any)
3. Whether the command is ambiguous and needs clarification
4. Whether the command is invalid/nonsensical

Common actions:
- Movement: go, move, walk, travel, enter, exit
- Interaction: take, get, pick up, drop, put down, use, examine, look at, inspect
- Communication: talk to, speak with, ask, tell
- Game mechanics: open door, insert key, check inventory, get hint

You MUST respond with ONLY valid JSON in this exact format:
{
    "action": "primary_action",
    "target": "target_object_or_direction",
    "is_ambiguous": false,
    "is_invalid": false,
    "clarification_needed": null,
    "suggestions": []
}

Examples:
- "go north" -> {"action": "move", "target": "north", "is_ambiguous": false, "is_invalid": false}
- "take the key" -> {"action": "take", "target": "key", "is_ambiguous": false, "is_invalid": false}
- "use it" -> {"action": "use", "target": null, "is_ambiguous": true, "clarification_needed": "What would you like to use?"}
- "fly to the moon" -> {"action": "fly", "target": "moon", "is_invalid": true, "suggestions": ["go north", "go south", "examine area"]}
"""
        
        agent = Agent(
            model=self.model,
            system_prompt=system_prompt
        )
        
        try:
            # Use synchronous call - agent is directly callable
            response = agent(f"Parse this command: {command}")
            
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
        """
        if not target:
            return ValidationResult(
                is_valid=False,
                reason="Where would you like to go? Try specifying a direction or exit.",
                context_info=context_info
            )
        
        # If we don't have location data yet, allow movement (will trigger generation)
        if not current_location:
            return ValidationResult(
                is_valid=True,
                reason="Movement to new area",
                context_info=context_info
            )
        
        # Check if exit exists in current location
        if target.lower() not in [exit.lower() for exit in current_location.exits]:
            available_exits = ", ".join(current_location.exits) if current_location.exits else "none"
            
            # Provide helpful explanation with context
            reason = f"You can't go '{target}' from here."
            if current_location.exits:
                reason += f" Available exits are: {available_exits}."
            else:
                reason += " There don't appear to be any obvious exits."
            
            return ValidationResult(
                is_valid=False,
                reason=reason,
                context_info=context_info
            )
        
        return ValidationResult(
            is_valid=True, 
            reason="Movement is valid",
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
        
        # Check if item exists in current location
        item_names = [item.name.lower() for item in current_location.items]
        if target.lower() not in item_names:
            # Provide helpful feedback about what IS available
            if current_location.items:
                available_items = ", ".join(item.name for item in current_location.items)
                reason = f"There is no '{target}' here. You can see: {available_items}."
            else:
                reason = f"There is no '{target}' here. In fact, there don't appear to be any items in this location."
            
            return ValidationResult(
                is_valid=False,
                reason=reason,
                context_info=context_info
            )
        
        return ValidationResult(
            is_valid=True, 
            reason="Item can be taken",
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
        
        Implements Requirement 12.1: Consider inventory and location
        Implements Requirement 12.4: Allow creative interpretations
        """
        if not target:
            return ValidationResult(
                is_valid=False,
                reason="What would you like to use? Try 'use [item name]'.",
                context_info=context_info
            )
        
        # Check if item is in inventory
        item_names = [item.name.lower() for item in self.game_state.inventory]
        if target.lower() not in item_names:
            if self.game_state.inventory:
                inventory_items = ", ".join(item.name for item in self.game_state.inventory)
                reason = f"You don't have a '{target}' to use. You are carrying: {inventory_items}."
            else:
                reason = f"You don't have a '{target}' to use. Your inventory is empty."
            
            return ValidationResult(
                is_valid=False,
                reason=reason,
                context_info=context_info
            )
        
        # Item exists in inventory - allow creative usage
        # The content generator will determine if the usage makes sense
        return ValidationResult(
            is_valid=True,
            reason="Item usage will be evaluated",
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
        
        # Check if the target NPC exists in current location
        if current_location:
            npc_names = [npc.lower() for npc in current_location.npcs]
            if target.lower() not in npc_names:
                if current_location.npcs:
                    npc_list = ", ".join(current_location.npcs)
                    reason = f"There's no '{target}' here to talk to. NPCs here: {npc_list}."
                else:
                    reason = f"There's no '{target}' here to talk to. In fact, there's no one here at all."
                
                return ValidationResult(
                    is_valid=False,
                    reason=reason,
                    context_info=context_info
                )
        
        return ValidationResult(
            is_valid=True,
            reason="NPC interaction is valid",
            context_info=context_info
        )
    
    async def _execute_action(self, intent: Intent) -> ActionResult:
        """
        Perform the action and update state.
        
        Args:
            intent: Validated intent to execute
            
        Returns:
            ActionResult with success status and state changes
        """
        action = intent.action
        target = intent.target
        
        # Handle different action types
        if action == "move":
            return await self._handle_movement(target)
        
        elif action == "take":
            return await self._handle_take_item(target)
        
        elif action == "drop":
            return await self._handle_drop_item(target)
        
        elif action == "use":
            return await self._handle_use_item(target)
        
        elif action in ["inventory", "check_inventory", "view_inventory"]:
            return await self._handle_inventory()
        
        elif action == "examine":
            return await self._handle_examine(target)
        
        elif action == "open":
            if target and "door" in target.lower():
                return await self._handle_open_door(target)
            return ActionResult(
                success=True,
                message=f"You open the {target}. Nothing special happens."
            )
        
        elif action == "insert":
            if target and "key" in target.lower():
                return await self._handle_insert_key()
            return ActionResult(
                success=False,
                message="You can't insert that."
            )
        
        # Default: generic response
        return ActionResult(
            success=True,
            message=f"You {action} {target if target else ''}."
        )
    
    async def _handle_movement(self, direction: str) -> ActionResult:
        """
        Handle player movement between locations.
        
        Special handling for:
        - Returning to forest clearing from door worlds
        - Moving between locations within door worlds
        - Generating new locations as needed
        
        Args:
            direction: Direction or destination to move to
            
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
        
        # Check if the direction is a valid exit
        if current_location and direction.lower() not in [exit.lower() for exit in current_location.exits]:
            available_exits = ", ".join(current_location.exits) if current_location.exits else "none"
            return ActionResult(
                success=False,
                message=f"You can't go '{direction}' from here. Available exits: {available_exits}."
            )
        
        # Generate new location ID based on current location and direction
        new_location_id = f"{self.game_state.player_location}_{direction.lower()}"
        
        # Check if we've already visited this location
        if new_location_id in self.game_state.visited_locations:
            cached_location = self.game_state.visited_locations[new_location_id]
            return ActionResult(
                success=True,
                message=f"You move {direction}.\n\n{cached_location.description}",
                new_location=new_location_id
            )
        
        # Need to generate new location
        # This will be handled by the content generator in the API layer
        return ActionResult(
            success=True,
            message=f"You move {direction}...",
            new_location=new_location_id,
            state_changes={
                'needs_location_generation': True,
                'direction': direction
            }
        )
    
    async def _handle_take_item(self, item_name: str) -> ActionResult:
        """
        Handle taking an item from the current location.
        
        Implements Requirement 3.1: Add item to inventory
        
        Special handling for keys: When a player takes a key item,
        it triggers the key retrieval logic which provides special
        messaging and state tracking.
        
        Args:
            item_name: Name of the item to take
            
        Returns:
            ActionResult with item added to inventory
        """
        current_location = self.game_state.visited_locations.get(
            self.game_state.player_location
        )
        
        if not current_location:
            return ActionResult(
                success=False,
                message="You can't take anything here."
            )
        
        # Find the item
        item_to_take = None
        for item in current_location.items:
            if item.name.lower() == item_name.lower():
                item_to_take = item
                break
        
        if not item_to_take:
            return ActionResult(
                success=False,
                message=f"There is no {item_name} here."
            )
        
        # Special handling for keys
        if item_to_take.is_key and item_to_take.door_number:
            # Use the key retrieval handler for special messaging
            return await self._handle_retrieve_key(item_to_take.door_number)
        
        # Regular item
        return ActionResult(
            success=True,
            message=f"You take the {item_to_take.name}.",
            items_added=[item_to_take],
            state_changes={'item_taken': item_to_take.id}
        )
    
    async def _handle_drop_item(self, item_name: str) -> ActionResult:
        """
        Handle dropping an item from inventory.
        
        Implements Requirement 3.5: Remove item from inventory
        """
        # Find the item in inventory
        item_to_drop = None
        for item in self.game_state.inventory:
            if item.name.lower() == item_name.lower():
                item_to_drop = item
                break
        
        if not item_to_drop:
            return ActionResult(
                success=False,
                message=f"You don't have a {item_name}."
            )
        
        return ActionResult(
            success=True,
            message=f"You drop the {item_to_drop.name}.",
            items_removed=[item_to_drop]
        )
    
    async def _handle_inventory(self) -> ActionResult:
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
    
    async def _handle_use_item(self, item_name: str) -> ActionResult:
        """
        Handle using an item from inventory.
        
        Implements Requirement 3.4: Evaluate item usage in context
        
        This method checks if the item can be used in the current context.
        The actual effects of using the item depend on the item's properties
        and the current game state.
        
        Args:
            item_name: Name of the item to use
            
        Returns:
            ActionResult with success status and message
        """
        # Find the item in inventory
        item_to_use = None
        for item in self.game_state.inventory:
            if item.name.lower() == item_name.lower():
                item_to_use = item
                break
        
        if not item_to_use:
            return ActionResult(
                success=False,
                message=f"You don't have a {item_name} to use."
            )
        
        # Check if it's a key - keys should be inserted, not used
        if item_to_use.is_key:
            return ActionResult(
                success=False,
                message=f"The {item_to_use.name} is meant to be inserted into the vault, not used directly. Try 'insert key into vault'."
            )
        
        # Get current location for context
        current_location = self.game_state.visited_locations.get(
            self.game_state.player_location
        )
        
        # Check item properties for usage hints
        usage_context = item_to_use.properties.get('usage_context', 'general')
        
        # Basic usage logic - can be extended with AI evaluation
        if usage_context == 'puzzle':
            # Item is meant for puzzle solving
            return ActionResult(
                success=True,
                message=f"You use the {item_to_use.name}. It seems to be important for solving a puzzle here.",
                state_changes={'item_used': item_to_use.id}
            )
        elif usage_context == 'tool':
            # Item is a tool
            return ActionResult(
                success=True,
                message=f"You use the {item_to_use.name}. It might come in handy.",
                state_changes={'item_used': item_to_use.id}
            )
        else:
            # Generic usage
            return ActionResult(
                success=True,
                message=f"You use the {item_to_use.name}. {item_to_use.description}",
                state_changes={'item_used': item_to_use.id}
            )
    
    async def _handle_examine(self, target: Optional[str]) -> ActionResult:
        """Handle examining objects or the environment."""
        if not target:
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
        
        # Examine specific target
        return ActionResult(
            success=True,
            message=f"You examine the {target}. It looks interesting."
        )
    
    async def _handle_open_door(self, door_target: str) -> ActionResult:
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
    
    async def _handle_retrieve_key(self, door_number: int) -> ActionResult:
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
    
    async def _handle_insert_key(self) -> ActionResult:
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
