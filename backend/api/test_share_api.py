"""
Integration tests for sharing API endpoints.

Tests the FastAPI endpoints for creating and retrieving shareable postcards.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from backend.main import app
from backend.models.game_state import GameState, LocationData

client = TestClient(app)


def create_test_game_state():
    """Helper to create a test game state."""
    location = LocationData(
        id="test_location",
        description="A beautiful forest clearing",
        image_url="https://example.com/forest.jpg",
        exits=["north", "south"],
        items=[],
        npcs=[],
        generated_at=datetime.now()
    )
    
    game_state = GameState(
        player_location="test_location",
        inventory=[],
        keys_collected=[1, 2, 3],
        visited_locations={"test_location": location},
        npc_interactions={},
        puzzle_states={},
        decision_history=[],
        current_door=1,
        game_started_at=datetime.now(),
        last_updated=datetime.now()
    )
    
    return game_state


def test_create_share_endpoint():
    """Test POST /api/share endpoint."""
    game_state = create_test_game_state()
    
    response = client.post(
        "/api/share",
        json={
            "game_state": game_state.to_dict()
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "postcard" in data
    
    postcard = data["postcard"]
    assert "share_code" in postcard
    assert postcard["location_name"] == "test_location"
    assert postcard["location_description"] == "A beautiful forest clearing"
    assert postcard["keys_collected"] == 3


def test_get_share_endpoint():
    """Test GET /api/share/{share_code} endpoint."""
    # First create a share
    game_state = create_test_game_state()
    
    create_response = client.post(
        "/api/share",
        json={
            "game_state": game_state.to_dict()
        }
    )
    
    share_code = create_response.json()["postcard"]["share_code"]
    
    # Now retrieve it
    get_response = client.get(f"/api/share/{share_code}")
    
    assert get_response.status_code == 200
    data = get_response.json()
    
    assert data["success"] is True
    assert "postcard" in data
    assert data["postcard"]["share_code"] == share_code


def test_get_nonexistent_share():
    """Test GET /api/share/{share_code} with invalid code."""
    response = client.get("/api/share/INVALID123")
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["message"].lower()


def test_list_shares_endpoint():
    """Test GET /api/shares endpoint."""
    response = client.get("/api/shares")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "shares" in data
    assert isinstance(data["shares"], dict)


def test_delete_share_endpoint():
    """Test DELETE /api/share/{share_code} endpoint."""
    # First create a share
    game_state = create_test_game_state()
    
    create_response = client.post(
        "/api/share",
        json={
            "game_state": game_state.to_dict()
        }
    )
    
    share_code = create_response.json()["postcard"]["share_code"]
    
    # Delete it
    delete_response = client.delete(f"/api/share/{share_code}")
    
    assert delete_response.status_code == 200
    data = delete_response.json()
    assert data["success"] is True
    
    # Verify it's gone
    get_response = client.get(f"/api/share/{share_code}")
    assert get_response.status_code == 404


def test_create_share_with_specific_location():
    """Test creating a share for a specific location."""
    location1 = LocationData(
        id="location1",
        description="First location",
        image_url="https://example.com/loc1.jpg",
        exits=["north"],
        items=[],
        npcs=[],
        generated_at=datetime.now()
    )
    
    location2 = LocationData(
        id="location2",
        description="Second location",
        image_url="https://example.com/loc2.jpg",
        exits=["south"],
        items=[],
        npcs=[],
        generated_at=datetime.now()
    )
    
    game_state = GameState(
        player_location="location1",
        inventory=[],
        keys_collected=[1],
        visited_locations={
            "location1": location1,
            "location2": location2
        },
        npc_interactions={},
        puzzle_states={},
        decision_history=[],
        current_door=1,
        game_started_at=datetime.now(),
        last_updated=datetime.now()
    )
    
    response = client.post(
        "/api/share",
        json={
            "game_state": game_state.to_dict(),
            "location_id": "location2"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    postcard = data["postcard"]
    assert postcard["location_name"] == "location2"
    assert postcard["location_description"] == "Second location"


def test_create_share_invalid_location():
    """Test creating a share for a non-existent location."""
    game_state = create_test_game_state()
    
    response = client.post(
        "/api/share",
        json={
            "game_state": game_state.to_dict(),
            "location_id": "nonexistent_location"
        }
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["message"].lower()


def test_create_share_invalid_game_state():
    """Test creating a share with invalid game state."""
    response = client.post(
        "/api/share",
        json={
            "game_state": {
                "invalid": "data"
            }
        }
    )
    
    assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
