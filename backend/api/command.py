"""
Command processing API endpoint for Nature42.

Handles player commands with streaming responses using Strands Agent SDK.

Implements Requirements 11.3, 11.4: Error handling and retry logic
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
from backend.models.game_state import GameState, LocationData, Item, Decision
from backend.utils.error_handling import (
    StrandsUnavailableError,
    CommandProcessingError,
    StateValidationError,
    retry_with_backoff,
    RetryConfig,
    format_error_response,
    logger
)

router = APIRouter()


class CommandRequest(BaseModel):
    """Request model for command processing."""
    command: str
    game_state: dict


async def generate_response(command: str, game_state: dict) -> AsyncGenerator[str, None]:
    """
    Generate streaming response for a player command.
    
    Implements Requirements 11.3, 11.4: Error handling with retry logic
    
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
        
        # Create Bedrock model with retry logic
        @retry_with_backoff(
            config=RetryConfig(max_attempts=3, initial_delay=1.0),
            exceptions=(Exception,)
        )
        async def create_model():
            try:
                return BedrockModel(
                    model_id=model_id,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            except Exception as e:
                logger.error(f"Failed to create Bedrock model: {e}")
                raise StrandsUnavailableError(
                    "Unable to connect to AI service",
                    details={"error": str(e)}
                )
        
        model = await create_model()
        
        # Build system prompt with game context
        system_prompt = build_system_prompt(game_state)
        
        # Create agent
        agent = Agent(
            model=model,
            system_prompt=system_prompt,
            callback_handler=None  # Required for stream_async
        )
        
        # Stream agent response with error handling
        try:
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
        
        except Exception as stream_error:
            logger.error(f"Error during streaming: {stream_error}")
            yield f"data: {json.dumps({'type': 'error', 'message': 'Connection interrupted. Please try again.'})}\n\n"
                
    except StrandsUnavailableError as e:
        logger.error(f"Strands unavailable: {e.message}")
        error_response = format_error_response(e, user_friendly=True)
        yield f"data: {json.dumps({'type': 'error', 'message': error_response['message']})}\n\n"
    
    except Exception as e:
        logger.error(f"Unexpected error in generate_response: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': 'An unexpected error occurred. Please try again.'})}\n\n"


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
    
    Implements Requirements 11.3, 11.4: Error handling and retry logic
    
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
    # Validate command
    if not request.command or not request.command.strip():
        raise HTTPException(
            status_code=400,
            detail="Command cannot be empty. Try 'help' for assistance."
        )
    
    # Convert game_state dict to GameState object with error handling
    try:
        game_state = GameState.from_dict(request.game_state)
    except Exception as e:
        logger.error(f"Invalid game state: {e}")
        raise HTTPException(
            status_code=400,
            detail="Your game state appears to be corrupted. You may need to start a new game."
        )
    
    # Create command processor
    try:
        processor = CommandProcessor(game_state)
    except Exception as e:
        logger.error(f"Failed to create command processor: {e}")
        raise HTTPException(
            status_code=500,
            detail="Unable to process commands right now. Please try again."
        )
    
    # Process command with retry logic
    @retry_with_backoff(
        config=RetryConfig(max_attempts=2, initial_delay=0.5),
        exceptions=(CommandProcessingError,)
    )
    async def process_with_retry():
        try:
            return await processor.process_command(request.command)
        except Exception as e:
            logger.error(f"Command processing failed: {e}")
            raise CommandProcessingError(
                "Failed to process command",
                details={"command": request.command, "error": str(e)}
            )
    
    try:
        result = await process_with_retry()
        
        # Apply state changes to game state
        if result.state_changes:
            # Update player location
            if 'player_location' in result.state_changes:
                game_state.player_location = result.state_changes['player_location']
            
            # Update current door
            if 'current_door' in result.state_changes:
                game_state.current_door = result.state_changes['current_door']
            
            # Add new location to visited locations
            if 'new_location_generated' in result.state_changes:
                location_dict = result.state_changes['new_location_generated']
                location = LocationData.from_dict(location_dict)
                game_state.visited_locations[location.id] = location
            
            # Add items to inventory
            if 'items_added' in result.state_changes:
                for item_dict in result.state_changes['items_added']:
                    item = Item.from_dict(item_dict)
                    game_state.inventory.append(item)
            
            # Remove items from inventory
            if 'items_removed' in result.state_changes:
                for item_dict in result.state_changes['items_removed']:
                    item_id = item_dict.get('id')
                    game_state.inventory = [i for i in game_state.inventory if i.id != item_id]
            
            # Add key to keys_collected
            if 'key_inserted' in result.state_changes:
                key_num = result.state_changes['key_inserted']
                if key_num not in game_state.keys_collected:
                    game_state.keys_collected.append(key_num)
            
            # Add decision to history
            if 'decision' in result.state_changes:
                decision_dict = result.state_changes['decision']
                decision = Decision.from_dict(decision_dict)
                game_state.decision_history.append(decision)
            
            # Update last_updated timestamp
            from datetime import datetime
            game_state.last_updated = datetime.now()
        
        # Return result as streaming response
        async def generate_result():
            try:
                # Send the message
                yield f"data: {json.dumps({'type': 'text', 'content': result.message})}\n\n"
                
                # Send updated game state
                yield f"data: {json.dumps({'type': 'state_changes', 'changes': game_state.to_dict()})}\n\n"
                
                # Send done signal
                yield f"data: {json.dumps({'type': 'done', 'success': result.success})}\n\n"
            
            except Exception as e:
                logger.error(f"Error generating result stream: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': 'Error sending response. Please try again.'})}\n\n"
        
        return StreamingResponse(
            generate_result(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
    
    except CommandProcessingError as e:
        logger.error(f"Command processing error: {e.message}")
        error_response = format_error_response(e, user_friendly=True)
        raise HTTPException(status_code=500, detail=error_response['message'])
    
    except Exception as e:
        logger.error(f"Unexpected error in process_command: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again or start a new game if the problem persists."
        )
