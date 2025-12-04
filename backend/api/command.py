"""
Command processing API endpoint for Nature42.

Handles player commands with streaming responses using Strands Agent SDK.
"""

import os
import json
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from strands import Agent
from strands.models import BedrockModel

from backend.services.command_processor import CommandProcessor
from backend.models.game_state import GameState

router = APIRouter()


class CommandRequest(BaseModel):
    """Request model for command processing."""
    command: str
    game_state: dict


async def generate_response(command: str, game_state: dict) -> AsyncGenerator[str, None]:
    """
    Generate streaming response for a player command.
    
    Args:
        command: Player's text command
        game_state: Current game state as dictionary
        
    Yields:
        Server-Sent Events formatted strings
    """
    try:
        # Get model configuration from environment
        model_id = os.getenv("STRANDS_MODEL_ID", "anthropic.claude-sonnet-4-20250514-v1:0")
        temperature = float(os.getenv("STRANDS_TEMPERATURE", "0.7"))
        max_tokens = int(os.getenv("STRANDS_MAX_TOKENS", "4096"))
        
        # Create Bedrock model
        model = BedrockModel(
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Build system prompt with game context
        system_prompt = build_system_prompt(game_state)
        
        # Create agent
        agent = Agent(
            model=model,
            system_prompt=system_prompt,
            callback_handler=None  # Required for stream_async
        )
        
        # Stream agent response
        async for event in agent.stream_async(command):
            # Send text chunks to client
            if "data" in event:
                yield f"data: {json.dumps({'type': 'text', 'content': event['data']})}\n\n"
            
            # Send tool usage events
            if "current_tool_use" in event:
                tool_name = event["current_tool_use"].get("name")
                if tool_name:
                    yield f"data: {json.dumps({'type': 'tool', 'tool_name': tool_name})}\n\n"
            
            # Send final result
            if "result" in event:
                yield f"data: {json.dumps({'type': 'done', 'result': event['result']})}\n\n"
                
    except Exception as e:
        error_msg = f"Error processing command: {str(e)}"
        yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"


def build_system_prompt(game_state: dict) -> str:
    """
    Build system prompt with game context.
    
    Args:
        game_state: Current game state
        
    Returns:
        System prompt string
    """
    player_location = game_state.get("player_location", "unknown")
    keys_collected = game_state.get("keys_collected", [])
    current_door = game_state.get("current_door")
    
    prompt = f"""You are the game master for Nature42, an AI-powered text adventure game.

GAME CONTEXT:
- Player location: {player_location}
- Keys collected: {len(keys_collected)}/6
- Current door world: {current_door if current_door else "Forest Clearing (hub)"}

YOUR ROLE:
You narrate the game world, respond to player commands, and guide them through their quest to collect six keys from six different worlds. Maintain a mysterious yet humorous tone with pop culture references from 1970s-2025.

GAME RULES:
1. The game starts in a forest clearing with six numbered doors and a central vault
2. Each door leads to a unique fantasy world where a key can be found
3. Players must demonstrate virtues (kindness, curiosity, courage, gratitude) to progress
4. The vault opens when all six keys are collected, revealing a philosophical message

RESPONSE STYLE:
- Be descriptive and immersive
- Include subtle pop culture references
- Maintain age-appropriate content (13+)
- Respond naturally to player commands
- Provide helpful feedback for unclear commands

Process the player's command and respond accordingly."""
    
    return prompt


@router.post("/api/command")
async def process_command(request: CommandRequest):
    """
    Process a player command with streaming response.
    
    The response includes state changes that should be applied to the game state.
    
    State changes may include:
    - player_location: New location ID
    - current_door: Current door number (or None for clearing)
    - items_added: List of items to add to inventory
    - items_removed: List of items to remove from inventory
    - decision: Significant decision to add to decision_history (Requirement 10.5)
    - key_inserted: Key number that was inserted into vault
    - new_location_generated: New location data to add to visited_locations
    
    Clients should apply these changes to their local game state and persist
    to browser storage.
    
    Args:
        request: Command request with command text and game state
        
    Returns:
        StreamingResponse with Server-Sent Events
    """
    if not request.command or not request.command.strip():
        raise HTTPException(status_code=400, detail="Command cannot be empty")
    
    # Convert game_state dict to GameState object
    try:
        game_state = GameState.from_dict(request.game_state)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid game state: {str(e)}")
    
    # Create command processor
    processor = CommandProcessor(game_state)
    
    # Process command
    try:
        result = await processor.process_command(request.command)
        
        # Return result as streaming response
        async def generate_result():
            # Send the message
            yield f"data: {json.dumps({'type': 'text', 'content': result.message})}\n\n"
            
            # Send state changes if any
            if result.state_changes:
                yield f"data: {json.dumps({'type': 'state_changes', 'changes': result.state_changes})}\n\n"
            
            # Send done signal
            yield f"data: {json.dumps({'type': 'done', 'success': result.success})}\n\n"
        
        return StreamingResponse(
            generate_result(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing command: {str(e)}")
