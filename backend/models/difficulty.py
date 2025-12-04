"""
Difficulty progression configuration for Nature42.

Defines the difficulty curve across the six doors, with progressive increases
in complexity, time requirements, and challenge level.
"""

from typing import Dict, List, Any


# Difficulty progression for each door (1-6)
DIFFICULTY_CURVE: Dict[int, Dict[str, Any]] = {
    1: {
        "target_time_minutes": 7.5,  # 5-10 min range
        "puzzle_complexity": "simple",
        "world_size": "small",  # 3-5 locations
        "hint_generosity": "high",
        "required_virtues": ["kindness"]
    },
    2: {
        "target_time_minutes": 15,
        "puzzle_complexity": "moderate",
        "world_size": "medium",  # 5-8 locations
        "hint_generosity": "high",
        "required_virtues": ["curiosity"]
    },
    3: {
        "target_time_minutes": 30,
        "puzzle_complexity": "moderate",
        "world_size": "medium",
        "hint_generosity": "medium",
        "required_virtues": ["courage"]
    },
    4: {
        "target_time_minutes": 45,
        "puzzle_complexity": "complex",
        "world_size": "large",  # 8-12 locations
        "hint_generosity": "medium",
        "required_virtues": ["gratitude"]
    },
    5: {
        "target_time_minutes": 75,
        "puzzle_complexity": "complex",
        "world_size": "large",
        "hint_generosity": "low",
        "required_virtues": ["kindness", "curiosity"]
    },
    6: {
        "target_time_minutes": 150,  # 2-3 hours
        "puzzle_complexity": "very_complex",
        "world_size": "very_large",  # 12-20 locations
        "hint_generosity": "minimal",
        "required_virtues": ["kindness", "curiosity", "courage", "gratitude"]
    }
}


def get_difficulty_settings(door_number: int) -> Dict[str, Any]:
    """
    Get difficulty settings for a specific door.
    
    Args:
        door_number: Door number (1-6)
        
    Returns:
        Dictionary containing difficulty settings
        
    Raises:
        ValueError: If door_number is not between 1 and 6
    """
    if door_number not in DIFFICULTY_CURVE:
        raise ValueError(f"Door number must be between 1 and 6, got {door_number}")
    
    return DIFFICULTY_CURVE[door_number].copy()


def get_target_time(door_number: int) -> float:
    """
    Get target completion time in minutes for a door.
    
    Args:
        door_number: Door number (1-6)
        
    Returns:
        Target time in minutes
    """
    settings = get_difficulty_settings(door_number)
    return settings["target_time_minutes"]


def get_puzzle_complexity(door_number: int) -> str:
    """
    Get puzzle complexity level for a door.
    
    Args:
        door_number: Door number (1-6)
        
    Returns:
        Complexity level: "simple", "moderate", "complex", or "very_complex"
    """
    settings = get_difficulty_settings(door_number)
    return settings["puzzle_complexity"]


def get_world_size(door_number: int) -> str:
    """
    Get world size for a door.
    
    Args:
        door_number: Door number (1-6)
        
    Returns:
        World size: "small", "medium", "large", or "very_large"
    """
    settings = get_difficulty_settings(door_number)
    return settings["world_size"]


def get_hint_generosity(door_number: int) -> str:
    """
    Get hint generosity level for a door.
    
    Args:
        door_number: Door number (1-6)
        
    Returns:
        Hint generosity: "high", "medium", "low", or "minimal"
    """
    settings = get_difficulty_settings(door_number)
    return settings["hint_generosity"]


def get_required_virtues(door_number: int) -> List[str]:
    """
    Get required virtues for a door.
    
    Args:
        door_number: Door number (1-6)
        
    Returns:
        List of required virtues
    """
    settings = get_difficulty_settings(door_number)
    return settings["required_virtues"].copy()


def get_location_count_range(door_number: int) -> tuple[int, int]:
    """
    Get the range of locations for a door based on world size.
    
    Args:
        door_number: Door number (1-6)
        
    Returns:
        Tuple of (min_locations, max_locations)
    """
    world_size = get_world_size(door_number)
    
    size_ranges = {
        "small": (3, 5),
        "medium": (5, 8),
        "large": (8, 12),
        "very_large": (12, 20)
    }
    
    return size_ranges.get(world_size, (5, 8))


def is_difficulty_increasing(door_a: int, door_b: int) -> bool:
    """
    Check if difficulty increases from door A to door B.
    
    Compares target time as the primary difficulty metric.
    
    Args:
        door_a: First door number (1-6)
        door_b: Second door number (1-6)
        
    Returns:
        True if door B is more difficult than door A
    """
    time_a = get_target_time(door_a)
    time_b = get_target_time(door_b)
    return time_b >= time_a
