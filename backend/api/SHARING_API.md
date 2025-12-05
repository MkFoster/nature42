# Sharing API Documentation

## Overview

The Sharing API allows players to create and share postcards of their game progress. Postcards include location information and keys collected, but exclude puzzle solutions and spoilers.

## Endpoints

### Create Share

**POST** `/api/share`

Create a shareable postcard from the current game state.

**Request Body:**
```json
{
  "game_state": {
    "player_location": "forest_clearing",
    "inventory": [],
    "keys_collected": [1, 2, 3],
    "visited_locations": {
      "forest_clearing": {
        "id": "forest_clearing",
        "description": "A mysterious forest clearing at twilight",
        "image_url": "https://example.com/forest.jpg",
        "exits": ["door_1", "door_2"],
        "items": [],
        "npcs": [],
        "generated_at": "2025-01-01T12:00:00"
      }
    },
    "npc_interactions": {},
    "puzzle_states": {},
    "decision_history": [],
    "current_door": 1,
    "game_started_at": "2025-01-01T10:00:00",
    "last_updated": "2025-01-01T12:00:00"
  },
  "location_id": "forest_clearing"  // Optional: defaults to current location
}
```

**Response:**
```json
{
  "success": true,
  "message": "Postcard created successfully",
  "postcard": {
    "share_code": "A1B2C3D4",
    "location_name": "forest_clearing",
    "location_description": "A mysterious forest clearing at twilight",
    "location_image_url": "https://example.com/forest.jpg",
    "keys_collected": 3,
    "created_at": "2025-01-01T12:00:00"
  }
}
```

### Get Share

**GET** `/api/share/{share_code}`

Retrieve a postcard by its share code.

**Response:**
```json
{
  "success": true,
  "message": "Postcard retrieved successfully",
  "postcard": {
    "share_code": "A1B2C3D4",
    "location_name": "forest_clearing",
    "location_description": "A mysterious forest clearing at twilight",
    "location_image_url": "https://example.com/forest.jpg",
    "keys_collected": 3,
    "created_at": "2025-01-01T12:00:00"
  }
}
```

**Error Response (404):**
```json
{
  "detail": "Share code 'INVALID' not found"
}
```

### List All Shares

**GET** `/api/shares`

List all stored shares.

**Response:**
```json
{
  "success": true,
  "message": "Retrieved 2 shares",
  "shares": {
    "A1B2C3D4": {
      "share_code": "A1B2C3D4",
      "location_name": "forest_clearing",
      "location_description": "A mysterious forest clearing at twilight",
      "location_image_url": "https://example.com/forest.jpg",
      "keys_collected": 3,
      "created_at": "2025-01-01T12:00:00"
    },
    "E5F6G7H8": {
      "share_code": "E5F6G7H8",
      "location_name": "ancient_temple",
      "location_description": "An ancient temple with mysterious inscriptions",
      "location_image_url": "https://example.com/temple.jpg",
      "keys_collected": 5,
      "created_at": "2025-01-01T14:00:00"
    }
  }
}
```

### Delete Share

**DELETE** `/api/share/{share_code}`

Delete a share by its code.

**Response:**
```json
{
  "success": true,
  "message": "Share deleted successfully"
}
```

**Error Response (404):**
```json
{
  "detail": "Share code 'INVALID' not found"
}
```

## Share Code Format

- **Length**: 8 characters
- **Characters**: Uppercase letters (A-Z) and digits (0-9)
- **Generation**: Cryptographically secure random generation
- **Uniqueness**: Guaranteed unique across all shares

## Postcard Contents

### Included Information
- Share code (unique identifier)
- Location name
- Location description
- Location image URL
- Number of keys collected
- Creation timestamp

### Excluded Information (Spoiler Prevention)
- Puzzle solutions
- Puzzle attempts
- NPC interaction details
- Decision history
- Inventory contents
- Specific puzzle states

## Usage Examples

### JavaScript/Fetch

```javascript
// Create a share
async function createShare(gameState, locationId = null) {
  const response = await fetch('/api/share', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      game_state: gameState,
      location_id: locationId
    })
  });
  
  const data = await response.json();
  return data.postcard;
}

// Get a share
async function getShare(shareCode) {
  const response = await fetch(`/api/share/${shareCode}`);
  const data = await response.json();
  return data.postcard;
}

// List all shares
async function listShares() {
  const response = await fetch('/api/shares');
  const data = await response.json();
  return data.shares;
}

// Delete a share
async function deleteShare(shareCode) {
  const response = await fetch(`/api/share/${shareCode}`, {
    method: 'DELETE'
  });
  return response.ok;
}
```

### Python

```python
import requests

# Create a share
def create_share(game_state, location_id=None):
    response = requests.post(
        'http://localhost:8080/api/share',
        json={
            'game_state': game_state,
            'location_id': location_id
        }
    )
    return response.json()['postcard']

# Get a share
def get_share(share_code):
    response = requests.get(f'http://localhost:8080/api/share/{share_code}')
    return response.json()['postcard']

# List all shares
def list_shares():
    response = requests.get('http://localhost:8080/api/shares')
    return response.json()['shares']

# Delete a share
def delete_share(share_code):
    response = requests.delete(f'http://localhost:8080/api/share/{share_code}')
    return response.ok
```

## Error Handling

### 400 Bad Request
- Invalid game state structure
- Missing required fields

### 404 Not Found
- Share code doesn't exist
- Location not found in visited locations

### 500 Internal Server Error
- Unexpected server error
- Check server logs for details

## Notes

- Shares are currently stored in-memory (development mode)
- For production, implement database persistence
- Consider implementing share expiration policies
- Rate limiting recommended for production deployment
