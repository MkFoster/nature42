"""
Tests for decision tracking functionality.

Validates Requirements 10.1, 10.2, 10.5:
- Record significant player choices in decision_history
- Use history to influence future content generation
- Track player choices in game state
"""

import pytest
from datetime import datetime
from backend.models.game_state import GameState, Decision, Item
from backend.services.command_processor import CommandProcessor, Intent, ActionResult


class TestDecisionTracking:
    """Test suite for decision tracking functionality."""
    
    def test_is_significant_decision_door_opening(self):
        """Test that opening a door is identified as a significant decision."""
        game_state = GameState.create_new_game()
        processor = CommandProcessor(game_state)
        
        intent = Intent(action="open", target="door 1")
        action_result = ActionResult(
            success=True,
            message="You open door 1",
            state_changes={'door_number': 1}
        )
        
        is_significant = processor._is_significant_decision(intent, action_result)
        assert is_significant, "Opening a door should be a significant decision"
    
    def test_is_significant_decision_key_insertion(self):
        """Test that inserting a key is identified as a significant decision."""
        game_state = GameState.create_new_game()
        processor = CommandProcessor(game_state)
        
        intent = Intent(action="insert", target="key")
        action_result = ActionResult(
            success=True,
            message="You insert the key",
            state_changes={'key_inserted': 1}
        )
        
        is_significant = processor._is_significant_decision(intent, action_result)
        assert is_significant, "Inserting a key should be a significant decision"
    
    def test_is_significant_decision_puzzle_solved(self):
        """Test that solving a puzzle is identified as a significant decision."""
        game_state = GameState.create_new_game()
        processor = CommandProcessor(game_state)
        
        intent = Intent(action="solve", target="puzzle")
        action_result = ActionResult(
            success=True,
            message="You solved the puzzle",
            state_changes={'puzzle_solved': 'puzzle_1'}
        )
        
        is_significant = processor._is_significant_decision(intent, action_result)
        assert is_significant, "Solving a puzzle should be a significant decision"
    
    def test_is_not_significant_decision_movement(self):
        """Test that regular movement is not a significant decision."""
        game_state = GameState.create_new_game()
        processor = CommandProcessor(game_state)
        
        intent = Intent(action="move", target="north")
        action_result = ActionResult(
            success=True,
            message="You move north",
            state_changes={}
        )
        
        is_significant = processor._is_significant_decision(intent, action_result)
        assert not is_significant, "Regular movement should not be a significant decision"
    
    def test_create_decision_door_opening(self):
        """Test that a decision is properly created for door opening."""
        game_state = GameState.create_new_game()
        processor = CommandProcessor(game_state)
        
        intent = Intent(action="open", target="door 1")
        action_result = ActionResult(
            success=True,
            message="You open door 1",
            state_changes={'door_number': 1}
        )
        
        decision = processor._create_decision(intent, action_result)
        
        assert decision is not None
        assert isinstance(decision, Decision)
        assert "open" in decision.description.lower()
        assert "door 1" in decision.description.lower()
        assert len(decision.consequences) > 0
        assert "Entered world behind door 1" in decision.consequences
        assert decision.location_id == game_state.player_location
    
    def test_create_decision_key_retrieval(self):
        """Test that a decision is properly created for key retrieval."""
        game_state = GameState.create_new_game()
        processor = CommandProcessor(game_state)
        
        intent = Intent(action="take", target="key")
        action_result = ActionResult(
            success=True,
            message="You take the key",
            state_changes={'key_retrieved': 3}
        )
        
        decision = processor._create_decision(intent, action_result)
        
        assert decision is not None
        assert "Retrieved key 3" in decision.consequences
    
    def test_create_decision_key_insertion(self):
        """Test that a decision is properly created for key insertion."""
        game_state = GameState.create_new_game()
        processor = CommandProcessor(game_state)
        
        intent = Intent(action="insert", target="key")
        action_result = ActionResult(
            success=True,
            message="You insert the key",
            state_changes={'key_inserted': 2}
        )
        
        decision = processor._create_decision(intent, action_result)
        
        assert decision is not None
        assert "Inserted key 2 into vault" in decision.consequences
    
    def test_create_decision_vault_opening(self):
        """Test that a decision is properly created for vault opening."""
        game_state = GameState.create_new_game()
        processor = CommandProcessor(game_state)
        
        intent = Intent(action="insert", target="key")
        action_result = ActionResult(
            success=True,
            message="The vault opens!",
            state_changes={'vault_opened': True, 'key_inserted': 6}
        )
        
        decision = processor._create_decision(intent, action_result)
        
        assert decision is not None
        assert "Opened the vault and completed the game" in decision.consequences
        assert "Inserted key 6 into vault" in decision.consequences
    
    def test_apply_state_changes_decision(self):
        """Test that decisions are properly added to decision_history."""
        game_state = GameState.create_new_game()
        processor = CommandProcessor(game_state)
        
        # Create a decision
        decision = Decision(
            timestamp=datetime.now(),
            location_id="forest_clearing",
            description="Player chose to open door 1",
            consequences=["Entered world behind door 1"]
        )
        
        # Apply state changes with decision
        state_changes = {
            'decision': decision.to_dict()
        }
        
        initial_count = len(game_state.decision_history)
        processor.apply_state_changes(state_changes)
        
        assert len(game_state.decision_history) == initial_count + 1
        assert game_state.decision_history[-1].description == decision.description
        assert game_state.decision_history[-1].consequences == decision.consequences
    
    def test_apply_state_changes_multiple_decisions(self):
        """Test that multiple decisions accumulate in history."""
        game_state = GameState.create_new_game()
        processor = CommandProcessor(game_state)
        
        # Add first decision
        decision1 = Decision(
            timestamp=datetime.now(),
            location_id="forest_clearing",
            description="Opened door 1",
            consequences=["Entered world 1"]
        )
        processor.apply_state_changes({'decision': decision1.to_dict()})
        
        # Add second decision
        decision2 = Decision(
            timestamp=datetime.now(),
            location_id="door_1_entrance",
            description="Helped an NPC",
            consequences=["NPC became friendly"]
        )
        processor.apply_state_changes({'decision': decision2.to_dict()})
        
        assert len(game_state.decision_history) == 2
        assert game_state.decision_history[0].description == "Opened door 1"
        assert game_state.decision_history[1].description == "Helped an NPC"
    
    def test_decision_history_serialization(self):
        """Test that decision history can be serialized and deserialized."""
        game_state = GameState.create_new_game()
        
        # Add some decisions
        decision1 = Decision(
            timestamp=datetime.now(),
            location_id="forest_clearing",
            description="Opened door 1",
            consequences=["Entered world 1"]
        )
        decision2 = Decision(
            timestamp=datetime.now(),
            location_id="door_1_entrance",
            description="Solved puzzle",
            consequences=["Retrieved key 1"]
        )
        
        game_state.decision_history.append(decision1)
        game_state.decision_history.append(decision2)
        
        # Serialize
        state_dict = game_state.to_dict()
        assert 'decision_history' in state_dict
        assert len(state_dict['decision_history']) == 2
        
        # Deserialize
        restored_state = GameState.from_dict(state_dict)
        assert len(restored_state.decision_history) == 2
        assert restored_state.decision_history[0].description == "Opened door 1"
        assert restored_state.decision_history[1].description == "Solved puzzle"
    
    def test_decision_history_json_round_trip(self):
        """Test that decision history survives JSON serialization round-trip."""
        game_state = GameState.create_new_game()
        
        # Add a decision
        decision = Decision(
            timestamp=datetime.now(),
            location_id="forest_clearing",
            description="Made a choice",
            consequences=["Something happened", "Another thing happened"]
        )
        game_state.decision_history.append(decision)
        
        # Convert to JSON and back
        json_str = game_state.to_json()
        restored_state = GameState.from_json(json_str)
        
        assert len(restored_state.decision_history) == 1
        assert restored_state.decision_history[0].description == "Made a choice"
        assert len(restored_state.decision_history[0].consequences) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
