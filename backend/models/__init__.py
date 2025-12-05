"""Data models for game state and entities"""

from .game_state import (
    GameState,
    LocationData,
    Item,
    Interaction,
    PuzzleState,
    Decision
)

from .share import (
    ShareablePostcard
)

from .difficulty import (
    DIFFICULTY_CURVE,
    get_difficulty_settings,
    get_target_time,
    get_puzzle_complexity,
    get_world_size,
    get_hint_generosity,
    get_required_virtues,
    get_location_count_range,
    is_difficulty_increasing
)

from .pop_culture import (
    POP_CULTURE_REFS,
    get_all_decades,
    get_references_by_decade,
    get_random_reference,
    get_random_references,
    get_random_reference_any_era,
    get_random_references_mixed,
    get_reference_decade,
    get_references_for_theme
)

__all__ = [
    # Game state models
    'GameState',
    'LocationData',
    'Item',
    'Interaction',
    'PuzzleState',
    'Decision',
    # Share models
    'ShareablePostcard',
    # Difficulty configuration
    'DIFFICULTY_CURVE',
    'get_difficulty_settings',
    'get_target_time',
    'get_puzzle_complexity',
    'get_world_size',
    'get_hint_generosity',
    'get_required_virtues',
    'get_location_count_range',
    'is_difficulty_increasing',
    # Pop culture references
    'POP_CULTURE_REFS',
    'get_all_decades',
    'get_references_by_decade',
    'get_random_reference',
    'get_random_references',
    'get_random_reference_any_era',
    'get_random_references_mixed',
    'get_reference_decade',
    'get_references_for_theme'
]
