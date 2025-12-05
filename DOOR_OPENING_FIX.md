# Door Opening Error Fix

## Issue
When opening a door and entering a new world, the game displayed the location description but also showed an error: "ERROR: Failed to process command. Please try again."

## Root Cause
The backend was returning `state_changes` as a dictionary of changes to apply, but the frontend was expecting a complete updated `game_state` object. When a new location was generated, the state_changes included:
- `new_location_generated`: The new LocationData object
- `player_location`: The new location ID
- `current_door`: The door number

However, the frontend's `updateGameState()` method expected to receive the full game state, not just the changes. This mismatch caused the error.

## Solution
Modified `backend/api/command.py` to apply state changes to the game state object before sending it to the frontend.

### Changes Made

**File: `backend/api/command.py`**

1. **Added imports** for data models:
   ```python
   from backend.models.game_state import GameState, LocationData, Item, Decision
   ```

2. **Apply state changes to game state** before streaming response:
   - Update `player_location` if changed
   - Update `current_door` if changed
   - Add new generated locations to `visited_locations`
   - Add items to inventory
   - Remove items from inventory
   - Add keys to `keys_collected`
   - Add decisions to `decision_history`
   - Update `last_updated` timestamp

3. **Send complete game state** instead of just changes:
   ```python
   # Send updated game state
   yield f"data: {json.dumps({'type': 'state_changes', 'changes': game_state.to_dict()})}\n\n"
   ```

## How It Works Now

1. Player enters command: "open door 1"
2. Command processor generates new location and returns state_changes
3. API layer applies all state changes to the game_state object:
   - Adds new location to visited_locations
   - Updates player_location to the new location
   - Sets current_door to 1
4. API sends complete updated game_state to frontend
5. Frontend receives full state and updates successfully
6. Inventory panel updates automatically
7. No error occurs

## State Changes Handled

The API now properly handles these state changes:
- `player_location` - Moving to new location
- `current_door` - Entering/exiting door worlds
- `new_location_generated` - Adding new locations to visited_locations
- `items_added` - Adding items to inventory
- `items_removed` - Removing items from inventory
- `key_inserted` - Adding keys to keys_collected
- `decision` - Adding decisions to decision_history

## Testing

Tested the following scenarios:
- ✓ Opening door 1 - Works without error
- ✓ Location description displays correctly
- ✓ Player location updates
- ✓ Current door tracks correctly
- ✓ New location added to visited_locations
- ✓ No error messages

## Benefits

1. **Seamless door opening** - No more errors when entering new worlds
2. **Proper state management** - All state changes applied correctly
3. **Inventory updates** - Items automatically update in the panel
4. **Consistent behavior** - All commands now work the same way
5. **Better error handling** - Actual errors are now distinguishable from state update issues

## Files Modified

- `backend/api/command.py` - Apply state changes before sending to frontend
