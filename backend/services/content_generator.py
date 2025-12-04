"""
Content generation service using Strands Agent SDK.

This module handles AI-driven content generation for locations, NPCs,
puzzles, and other dynamic game elements.
"""

import os
from typing import List, Dict, Optional, Any
from strands import Agent
from strands.models import BedrockModel

from backend.models import (
    LocationData,
    Item,
    Interaction,
    PuzzleState,
    get_difficulty_settings,
    get_random_references
)


class ContentGenerator:
    """
    Handles AI-driven content generation for the game.
    
    Uses Strands Agent SDK with Bedrock to generate locations, NPCs,
    puzzles, and other dynamic content while maintaining age-appropriate
    standards and game consistency.
    """
    
    def __init__(self):
        """Initialize the content generator with Bedrock model."""
        # Get model configuration from environment
        model_id = os.getenv("STRANDS_MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
        temperature = float(os.getenv("STRANDS_TEMPERATURE", "0.7"))
        max_tokens = int(os.getenv("STRANDS_MAX_TOKENS", "4096"))
        
        # Create Bedrock model with creative settings for narrative generation
        self.model = BedrockModel(
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Content filtering guidelines
        self.age_rating = "13+"
        self.content_guidelines = """
CONTENT GUIDELINES (Age 13+):
- No violence, gore, or graphic descriptions
- No explicit language or profanity
- No sexual content or innuendo
- No mature themes (drugs, alcohol abuse, etc.)
- Maintain a mysterious yet humorous tone
- Include age-appropriate pop culture references
- Focus on adventure, puzzles, and character virtues
"""
        
        # Location cache for consistency (Requirement 2.4)
        # Maps location_id -> LocationData
        self._location_cache: Dict[str, LocationData] = {}
    
    def _create_agent(self, system_prompt: str) -> Agent:
        """
        Create a Strands Agent with the given system prompt.
        
        Args:
            system_prompt: System prompt for the agent
            
        Returns:
            Configured Strands Agent
        """
        full_prompt = f"{system_prompt}\n\n{self.content_guidelines}"
        
        return Agent(
            model=self.model,
            system_prompt=full_prompt
        )
    
    def validate_content_appropriateness(self, content: str) -> bool:
        """
        Validate that content is appropriate for 13+ audience.
        
        This is a basic validation. In production, you might use
        additional content moderation APIs.
        
        Args:
            content: Content to validate
            
        Returns:
            True if content appears appropriate
        """
        # Basic keyword filtering (expand as needed)
        inappropriate_keywords = [
            "kill", "murder", "blood", "gore", "death",
            "sex", "sexual", "nude", "naked",
            "drug", "cocaine", "heroin", "meth",
            "fuck", "shit", "damn", "hell", "ass"
        ]
        
        content_lower = content.lower()
        for keyword in inappropriate_keywords:
            if keyword in content_lower:
                return False
        
        return True
    
    def get_cached_location(self, location_id: str) -> Optional[LocationData]:
        """
        Retrieve a cached location by ID.
        
        Args:
            location_id: Location identifier
            
        Returns:
            Cached LocationData or None if not found
        """
        return self._location_cache.get(location_id)
    
    def cache_location(self, location: LocationData) -> None:
        """
        Store a location in the cache for consistency.
        
        Args:
            location: LocationData to cache
        """
        self._location_cache[location.id] = location
    
    def clear_location_cache(self) -> None:
        """Clear all cached locations (for new game)."""
        self._location_cache.clear()
    
    async def generate_location(
        self,
        door_number: int,
        player_history: List[Dict[str, Any]],
        keys_collected: int,
        location_id: Optional[str] = None
    ) -> LocationData:
        """
        Generate a new location with appropriate difficulty.
        
        Implements location caching for consistency (Requirement 2.4).
        When a player revisits a location, the cached description is returned.
        
        Args:
            door_number: Which door (1-6) this location is behind
            player_history: Player's decision history
            keys_collected: Number of keys already collected
            location_id: Optional specific location ID (for caching)
            
        Returns:
            Generated LocationData
        """
        import json
        from datetime import datetime
        
        # Check cache first if location_id provided (Requirement 2.4)
        if location_id:
            cached = self.get_cached_location(location_id)
            if cached:
                return cached
        
        # Get difficulty settings for this door
        difficulty = get_difficulty_settings(door_number)
        
        # Get pop culture references for variety
        decades = ["1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
        selected_decade = decades[door_number % len(decades)]
        pop_refs = get_random_references(selected_decade, 2)
        
        # Build player history context (Requirement 10.1, 10.2)
        history_context = ""
        if player_history:
            history_context = "\n\nPLAYER HISTORY (use to adapt content):\n"
            # Include recent significant decisions
            recent_decisions = player_history[-5:] if len(player_history) > 5 else player_history
            for decision in recent_decisions:
                desc = decision.get('description', 'Unknown action')
                consequences = decision.get('consequences', [])
                history_context += f"- {desc}"
                if consequences:
                    history_context += f" (led to: {', '.join(consequences)})"
                history_context += "\n"
            history_context += "\nAdapt the location and narrative to reflect these past choices where appropriate."
        
        # Build system prompt
        system_prompt = f"""You are a creative game master generating a location for Nature42.

LOCATION REQUIREMENTS:
- Door number: {door_number}
- Difficulty: {difficulty['puzzle_complexity']}
- World size: {difficulty['world_size']}
- Required virtues: {', '.join(difficulty['required_virtues'])}
- Keys collected so far: {keys_collected}/6{history_context}

STYLE:
- Mysterious yet humorous tone
- Include these pop culture references naturally: {', '.join(pop_refs)}
- Create at least 2 exits/paths
- Describe items, NPCs, or puzzles present
- Age-appropriate for 13+ audience

You MUST respond with ONLY valid JSON in this exact format:
{{
    "name": "Location name",
    "description": "Detailed description (2-3 paragraphs)",
    "exits": ["exit1", "exit2"],
    "items": [
        {{"id": "item1", "name": "Item Name", "description": "Item description"}}
    ],
    "npcs": ["npc1", "npc2"]
}}"""
        
        agent = self._create_agent(system_prompt)
        
        # Generate location
        prompt = f"Generate a unique fantasy location for door {door_number}."
        
        # Run synchronous agent call in executor for async context
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, agent, prompt)
        
        # Parse JSON response
        try:
            # Extract text from AgentResult object
            response_text = str(response) if not isinstance(response, str) else response
            
            # Extract JSON from response (handle markdown code blocks)
            json_str = response_text.strip()
            if json_str.startswith("```"):
                # Remove markdown code block markers
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1]) if len(lines) > 2 else json_str
            
            location_data = json.loads(json_str)
            
            # Create Item objects from items data
            items = []
            for item_data in location_data.get("items", []):
                items.append(Item(
                    id=item_data.get("id", "unknown"),
                    name=item_data.get("name", "Unknown Item"),
                    description=item_data.get("description", "")
                ))
            
            # Generate location ID if not provided
            if not location_id:
                location_id = f"door_{door_number}_loc_{hash(location_data['name']) % 10000}"
            
            location = LocationData(
                id=location_id,
                description=location_data.get("description", response),
                image_url="",  # TODO: Implement image generation in Task 10
                exits=location_data.get("exits", ["north", "south"]),
                items=items,
                npcs=location_data.get("npcs", []),
                generated_at=datetime.now()
            )
            
            # Cache the location for consistency (Requirement 2.4)
            self.cache_location(location)
            return location
            
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback if JSON parsing fails
            location = LocationData(
                id=location_id or f"door_{door_number}_fallback",
                description=response,
                image_url="",
                exits=["north", "south"],
                items=[],
                npcs=[],
                generated_at=datetime.now()
            )
            
            # Cache even fallback locations
            self.cache_location(location)
            return location
    
    async def generate_npc_dialogue(
        self,
        npc_id: str,
        npc_name: str,
        player_action: str,
        interaction_history: List[Interaction],
        player_decisions: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Generate NPC dialogue considering past interactions and player decisions.
        
        Implements Requirement 10.2: Consider player history when generating content
        
        Args:
            npc_id: NPC identifier
            npc_name: NPC name
            player_action: What the player said/did
            interaction_history: Previous interactions with this NPC
            player_decisions: Player's decision history (optional)
            
        Returns:
            NPC's response
        """
        # Build interaction context
        history_context = ""
        if interaction_history:
            history_context = "PREVIOUS INTERACTIONS:\n"
            for interaction in interaction_history[-3:]:  # Last 3 interactions
                history_context += f"- Player: {interaction.player_action}\n"
                history_context += f"- {npc_name}: {interaction.npc_response}\n"
                history_context += f"  (Sentiment: {interaction.sentiment})\n"
        
        # Build player decision context (Requirement 10.2)
        decision_context = ""
        if player_decisions:
            decision_context = "\n\nPLAYER'S JOURNEY (reference if relevant):\n"
            recent_decisions = player_decisions[-3:] if len(player_decisions) > 3 else player_decisions
            for decision in recent_decisions:
                desc = decision.get('description', 'Unknown action')
                decision_context += f"- {desc}\n"
        
        system_prompt = f"""You are {npc_name}, an NPC in Nature42.

{history_context}{decision_context}

PERSONALITY:
- Remember past interactions
- Maintain consistent personality
- React appropriately to player's actions
- Provide helpful hints when appropriate
- Stay in character
- Reference the player's journey if it's relevant to the conversation

Respond to the player's action naturally and in character."""
        
        agent = self._create_agent(system_prompt)
        
        # Run synchronous agent call in executor for async context
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, agent, f"Player action: {player_action}")
        
        # Extract text from AgentResult
        return str(response) if not isinstance(response, str) else response
    
    async def generate_puzzle(
        self,
        difficulty: str,
        theme: str,
        required_virtues: List[str],
        player_decisions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create a puzzle requiring specific virtues.
        
        Implements Requirement 10.2: Consider player history when generating content
        
        Args:
            difficulty: Puzzle complexity level
            theme: Puzzle theme/setting
            required_virtues: Virtues needed to solve (kindness, courage, etc.)
            player_decisions: Player's decision history (optional)
            
        Returns:
            Puzzle data dictionary
        """
        import json
        
        # Build player decision context (Requirement 10.2)
        decision_context = ""
        if player_decisions:
            decision_context = "\n\nPLAYER'S PAST CHOICES (consider when designing puzzle):\n"
            recent_decisions = player_decisions[-3:] if len(player_decisions) > 3 else player_decisions
            for decision in recent_decisions:
                desc = decision.get('description', 'Unknown action')
                consequences = decision.get('consequences', [])
                decision_context += f"- {desc}"
                if consequences:
                    decision_context += f" (resulted in: {', '.join(consequences)})"
                decision_context += "\n"
            decision_context += "\nDesign the puzzle to build on or contrast with these past experiences."
        
        system_prompt = f"""You are a puzzle designer for Nature42.

PUZZLE REQUIREMENTS:
- Difficulty: {difficulty}
- Theme: {theme}
- Required virtues: {', '.join(required_virtues)}
- Multiple valid solution paths
- Age-appropriate for 13+{decision_context}

Create a puzzle that tests the player's {', '.join(required_virtues)}.
The puzzle should have multiple creative solutions.

You MUST respond with ONLY valid JSON in this exact format:
{{
    "description": "Puzzle description",
    "hints": ["hint1", "hint2", "hint3"],
    "solution_criteria": "What makes a solution valid"
}}"""
        
        agent = self._create_agent(system_prompt)
        
        # Run synchronous agent call in executor for async context
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, agent, "Generate the puzzle.")
        
        # Parse JSON response
        try:
            # Extract text from AgentResult
            response_text = str(response) if not isinstance(response, str) else response
            json_str = response_text.strip()
            if json_str.startswith("```"):
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1]) if len(lines) > 2 else json_str
            
            puzzle_data = json.loads(json_str)
            return puzzle_data
            
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback if JSON parsing fails
            return {
                "description": response,
                "hints": ["Try thinking about the required virtues", "Consider multiple approaches"],
                "solution_criteria": f"Demonstrates {', '.join(required_virtues)}"
            }
    
    async def evaluate_puzzle_solution(
        self,
        puzzle_description: str,
        player_solution: str,
        required_virtues: List[str]
    ) -> Dict[str, Any]:
        """
        Determine if a creative solution is valid.
        
        Args:
            puzzle_description: The puzzle description
            player_solution: Player's attempted solution
            required_virtues: Virtues the puzzle tests
            
        Returns:
            Evaluation result with success flag and feedback
        """
        import json
        
        system_prompt = f"""You are evaluating a puzzle solution in Nature42.

PUZZLE:
{puzzle_description}

REQUIRED VIRTUES: {', '.join(required_virtues)}

Evaluate if the player's solution demonstrates the required virtues.
Be generous with creative solutions that show the right spirit.

You MUST respond with ONLY valid JSON in this exact format:
{{
    "success": true,
    "feedback": "Explanation of why it worked or didn't",
    "virtue_demonstrated": "Which virtue was shown"
}}"""
        
        agent = self._create_agent(system_prompt)
        
        # Run synchronous agent call in executor for async context
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, agent, f"Player's solution: {player_solution}")
        
        # Parse JSON response
        try:
            # Extract text from AgentResult
            response_text = str(response) if not isinstance(response, str) else response
            json_str = response_text.strip()
            if json_str.startswith("```"):
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1]) if len(lines) > 2 else json_str
            
            result = json.loads(json_str)
            return result
            
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback - be generous if parsing fails
            return {
                "success": True,
                "feedback": response,
                "virtue_demonstrated": required_virtues[0] if required_virtues else "creativity"
            }
    
    async def generate_hint(
        self,
        puzzle_description: str,
        keys_collected: int,
        previous_hints: List[str]
    ) -> str:
        """
        Generate a hint with appropriate specificity.
        
        Args:
            puzzle_description: The puzzle description
            keys_collected: Number of keys player has (affects hint generosity)
            previous_hints: Hints already given
            
        Returns:
            Hint text
        """
        # Determine hint generosity based on keys collected
        if keys_collected <= 1:
            generosity = "very helpful and specific"
        elif keys_collected <= 3:
            generosity = "moderately helpful"
        else:
            generosity = "subtle and minimal"
        
        system_prompt = f"""You are providing a hint for a puzzle in Nature42.

PUZZLE:
{puzzle_description}

PREVIOUS HINTS:
{chr(10).join(f'- {h}' for h in previous_hints) if previous_hints else 'None'}

HINT STYLE: {generosity}

Provide a hint that is {generosity}. Don't repeat previous hints."""
        
        agent = self._create_agent(system_prompt)
        
        # Run synchronous agent call in executor for async context
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, agent, "Generate a hint.")
        
        # Extract text from AgentResult
        return str(response) if not isinstance(response, str) else response
