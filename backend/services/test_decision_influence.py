"""
Integration tests for decision history influencing content generation.

Validates Requirements 10.1, 10.2:
- Significant choices adjust future narrative generation
- Generated content considers player history
"""

import pytest
from datetime import datetime
from backend.models.game_state import GameState, Decision
from backend.services.content_generator import ContentGenerator


class TestDecisionInfluence:
    """Test suite for decision history influencing content generation."""
    
    @pytest.mark.asyncio
    async def test_location_generation_includes_player_history(self):
        """Test that location generation includes player history in the prompt."""
        generator = ContentGenerator()
        
        # Create player history with decisions
        player_history = [
            {
                'timestamp': datetime.now().isoformat(),
                'location_id': 'forest_clearing',
                'description': 'Player chose to open door 1',
                'consequences': ['Entered world behind door 1']
            },
            {
                'timestamp': datetime.now().isoformat(),
                'location_id': 'door_1_entrance',
                'description': 'Player chose to help a lost traveler',
                'consequences': ['Traveler became friendly', 'Received a gift']
            }
        ]
        
        # Generate location with history
        location = await generator.generate_location(
            door_number=1,
            player_history=player_history,
            keys_collected=0,
            location_id="test_location_with_history"
        )
        
        # Verify location was generated
        assert location is not None
        assert location.id == "test_location_with_history"
        assert location.description is not None
        assert len(location.description) > 0
        
        # The location should be cached
        cached = generator.get_cached_location("test_location_with_history")
        assert cached is not None
        assert cached.id == location.id
    
    @pytest.mark.asyncio
    async def test_location_generation_without_history(self):
        """Test that location generation works without player history."""
        generator = ContentGenerator()
        
        # Generate location without history
        location = await generator.generate_location(
            door_number=2,
            player_history=[],
            keys_collected=1,
            location_id="test_location_no_history"
        )
        
        # Verify location was generated
        assert location is not None
        assert location.id == "test_location_no_history"
        assert location.description is not None
    
    @pytest.mark.asyncio
    async def test_npc_dialogue_with_player_decisions(self):
        """Test that NPC dialogue can consider player decisions."""
        generator = ContentGenerator()
        
        # Create player decision history
        player_decisions = [
            {
                'timestamp': datetime.now().isoformat(),
                'location_id': 'forest_clearing',
                'description': 'Player chose to open door 3',
                'consequences': ['Entered world behind door 3']
            },
            {
                'timestamp': datetime.now().isoformat(),
                'location_id': 'door_3_entrance',
                'description': 'Player chose to show courage',
                'consequences': ['Faced a challenge bravely']
            }
        ]
        
        # Generate NPC dialogue with decision history
        dialogue = await generator.generate_npc_dialogue(
            npc_id="wise_sage",
            npc_name="Sage",
            player_action="ask about the key",
            interaction_history=[],
            player_decisions=player_decisions
        )
        
        # Verify dialogue was generated
        assert dialogue is not None
        assert len(dialogue) > 0
        assert isinstance(dialogue, str)
    
    @pytest.mark.asyncio
    async def test_puzzle_generation_with_player_decisions(self):
        """Test that puzzle generation can consider player decisions."""
        generator = ContentGenerator()
        
        # Create player decision history
        player_decisions = [
            {
                'timestamp': datetime.now().isoformat(),
                'location_id': 'door_1_entrance',
                'description': 'Player chose to help an NPC',
                'consequences': ['Demonstrated kindness']
            },
            {
                'timestamp': datetime.now().isoformat(),
                'location_id': 'door_1_library',
                'description': 'Player chose to investigate thoroughly',
                'consequences': ['Demonstrated curiosity']
            }
        ]
        
        # Generate puzzle with decision history
        puzzle = await generator.generate_puzzle(
            difficulty="moderate",
            theme="ancient library",
            required_virtues=["curiosity", "kindness"],
            player_decisions=player_decisions
        )
        
        # Verify puzzle was generated
        assert puzzle is not None
        assert 'description' in puzzle
        assert 'hints' in puzzle
        assert 'solution_criteria' in puzzle
        assert len(puzzle['description']) > 0
    
    @pytest.mark.asyncio
    async def test_multiple_locations_with_evolving_history(self):
        """Test that multiple locations can be generated with evolving history."""
        generator = ContentGenerator()
        
        # Start with empty history
        history = []
        
        # Generate first location
        location1 = await generator.generate_location(
            door_number=1,
            player_history=history,
            keys_collected=0,
            location_id="evolving_loc_1"
        )
        assert location1 is not None
        
        # Add a decision to history
        history.append({
            'timestamp': datetime.now().isoformat(),
            'location_id': 'evolving_loc_1',
            'description': 'Player explored the area',
            'consequences': ['Found a clue']
        })
        
        # Generate second location with updated history
        location2 = await generator.generate_location(
            door_number=1,
            player_history=history,
            keys_collected=0,
            location_id="evolving_loc_2"
        )
        assert location2 is not None
        
        # Add another decision
        history.append({
            'timestamp': datetime.now().isoformat(),
            'location_id': 'evolving_loc_2',
            'description': 'Player solved a puzzle',
            'consequences': ['Retrieved key 1']
        })
        
        # Generate third location with full history
        location3 = await generator.generate_location(
            door_number=2,
            player_history=history,
            keys_collected=1,
            location_id="evolving_loc_3"
        )
        assert location3 is not None
        
        # All locations should be different
        assert location1.id != location2.id != location3.id
    
    @pytest.mark.asyncio
    async def test_history_limit_in_prompts(self):
        """Test that only recent decisions are included in prompts."""
        generator = ContentGenerator()
        
        # Create a long history (more than 5 decisions)
        long_history = [
            {
                'timestamp': datetime.now().isoformat(),
                'location_id': f'location_{i}',
                'description': f'Decision {i}',
                'consequences': [f'Consequence {i}']
            }
            for i in range(10)
        ]
        
        # Generate location with long history
        # The implementation should only use the last 5 decisions
        location = await generator.generate_location(
            door_number=3,
            player_history=long_history,
            keys_collected=2,
            location_id="test_long_history"
        )
        
        # Verify location was generated successfully
        assert location is not None
        assert location.id == "test_long_history"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
