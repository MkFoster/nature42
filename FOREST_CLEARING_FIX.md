# Forest Clearing Display Fix

## Issue
When starting a new game, the player saw "You look around but see nothing special" instead of the forest clearing description with six doors and the vault.

## Root Cause
The frontend `initializeNewGame()` method in `static/js/game-client.js` was creating a game state with an empty `visited_locations` object:

```javascript
this.gameState = {
    player_location: 'forest_clearing',
    inventory: [],
    keys_collected: [],
    visited_locations: {},  // ← Empty! No forest clearing data
    // ...
};
```

When the command processor tried to display the location description, it couldn't find the forest clearing in `visited_locations`, so it returned the default message "You look around but see nothing special."

## Solution
Updated `initializeNewGame()` to call the backend API (`DELETE /api/state`) to get a properly initialized game state that includes the forest clearing location data:

```javascript
async initializeNewGame() {
    try {
        // Get properly initialized game state from backend
        const response = await fetch('/api/state', {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success && data.state) {
            this.gameState = data.state;  // ← Now includes forest clearing!
            this.terminal.print('\nStarting new game...', 'system');
            this.sendInitialCommand();
        }
    } catch (error) {
        console.error('Error initializing new game:', error);
        this.terminal.showError('Failed to start new game. Please refresh the page and try again.');
    }
}
```

## Backend Implementation
The backend `GameState.create_new_game()` method (in `backend/models/game_state.py`) correctly initializes the forest clearing:

```python
@classmethod
def create_new_game(cls) -> 'GameState':
    from backend.services.forest_clearing import create_forest_clearing
    
    now = datetime.now()
    clearing = create_forest_clearing()  # ← Creates forest clearing with full description
    
    return cls(
        player_location="forest_clearing",
        visited_locations={"forest_clearing": clearing},  # ← Includes clearing data
        # ... other fields
    )
```

## Files Changed
- `static/js/game-client.js`: Updated `initializeNewGame()` to fetch state from backend

## Testing
Verified that:
1. Backend correctly creates game state with forest clearing
2. Forest clearing description includes:
   - Twilight forest setting
   - Six numbered doors
   - Central vault with "The Ultimate Question" inscription
   - Six keyholes
3. "look around" command displays the full forest clearing description

## Result
Players now see the proper forest clearing description when starting a new game, including all six doors and the vault, as specified in Requirements 13.1 and 13.2.
