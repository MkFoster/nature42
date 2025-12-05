"""
Command processing data models for Nature42.

This module contains the data classes used throughout the command processing system.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from backend.models.game_state import Item, Decision


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
        success: Whether the command succeeded
        message: Response message to player
        state_changes: Dictionary of state changes to apply
        needs_clarification: Whether the command needs clarification
    """
    success: bool
    message: str
    state_changes: Dict[str, Any] = None
    needs_clarification: bool = False
    
    def __post_init__(self):
        if self.state_changes is None:
            self.state_changes = {}
