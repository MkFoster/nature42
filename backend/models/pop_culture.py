"""
Pop culture reference database for Nature42.

Contains references spanning from the 1970s to 2025, organized by decade.
These references are used to add nostalgic and contemporary elements to
generated game content.
"""

import random
from typing import List, Dict


# Pop culture references organized by decade
POP_CULTURE_REFS: Dict[str, List[str]] = {
    "1970s": [
        "Holy Hand Grenade",
        "disco ball",
        "pet rock",
        "lava lamp",
        "8-track tape",
        "mood ring",
        "Rubik's Cube prototype",
        "bell-bottoms",
        "platform shoes",
        "Pong arcade machine",
        "rotary phone",
        "vinyl record",
        "cassette tape",
        "Atari 2600",
        "Star Wars action figure"
    ],
    "1980s": [
        "DeLorean",
        "Rubik's Cube",
        "Walkman",
        "boom box",
        "Pac-Man",
        "Cabbage Patch Kid",
        "Transformers",
        "He-Man figure",
        "Trapper Keeper",
        "Swatch watch",
        "Members Only jacket",
        "parachute pants",
        "Atari joystick",
        "VHS tape",
        "Nintendo Entertainment System"
    ],
    "1990s": [
        "Beanie Babies",
        "Tamagotchi",
        "pager",
        "Discman",
        "Game Boy",
        "Furby",
        "Pogs",
        "slap bracelet",
        "Troll doll",
        "Super Soaker",
        "Tickle Me Elmo",
        "Pokémon card",
        "dial-up modem",
        "floppy disk",
        "CD-ROM"
    ],
    "2000s": [
        "flip phone",
        "iPod",
        "MySpace profile",
        "Razor scooter",
        "Heelys",
        "Silly Bandz",
        "Webkinz",
        "Nintendo DS",
        "PSP",
        "USB flash drive",
        "Bluetooth headset",
        "BlackBerry",
        "Wii remote",
        "Guitar Hero controller",
        "Crocs"
    ],
    "2010s": [
        "fidget spinner",
        "selfie stick",
        "dabbing pose",
        "hoverboard",
        "Minecraft block",
        "Fortnite dance",
        "emoji pillow",
        "Apple Watch",
        "AirPods",
        "Ring doorbell",
        "Amazon Echo",
        "Tesla key card",
        "Nintendo Switch",
        "VR headset",
        "wireless charger"
    ],
    "2020s": [
        "Among Us crewmate",
        "sourdough starter",
        "Zoom fatigue",
        "hand sanitizer dispenser",
        "face mask",
        "TikTok dance",
        "NFT artwork",
        "cryptocurrency wallet",
        "ChatGPT prompt",
        "AI-generated image",
        "smart home hub",
        "electric scooter",
        "reusable water bottle",
        "AirTag",
        "foldable phone"
    ]
}


def get_all_decades() -> List[str]:
    """
    Get list of all available decades.
    
    Returns:
        List of decade strings
    """
    return list(POP_CULTURE_REFS.keys())


def get_references_by_decade(decade: str) -> List[str]:
    """
    Get all pop culture references for a specific decade.
    
    Args:
        decade: Decade string (e.g., "1970s", "1980s")
        
    Returns:
        List of pop culture references
        
    Raises:
        ValueError: If decade is not in the database
    """
    if decade not in POP_CULTURE_REFS:
        available = ", ".join(POP_CULTURE_REFS.keys())
        raise ValueError(f"Decade '{decade}' not found. Available: {available}")
    
    return POP_CULTURE_REFS[decade].copy()


def get_random_reference(decade: str) -> str:
    """
    Get a random pop culture reference from a specific decade.
    
    Args:
        decade: Decade string (e.g., "1970s", "1980s")
        
    Returns:
        Random pop culture reference
    """
    references = get_references_by_decade(decade)
    return random.choice(references)


def get_random_references(decade: str, count: int = 1) -> List[str]:
    """
    Get multiple random pop culture references from a specific decade.
    
    Args:
        decade: Decade string (e.g., "1970s", "1980s")
        count: Number of references to return
        
    Returns:
        List of random pop culture references (may contain duplicates if count > available)
    """
    references = get_references_by_decade(decade)
    
    if count <= len(references):
        return random.sample(references, count)
    else:
        # If requesting more than available, sample with replacement
        return random.choices(references, k=count)


def get_random_reference_any_era() -> str:
    """
    Get a random pop culture reference from any era.
    
    Returns:
        Random pop culture reference
    """
    decade = random.choice(get_all_decades())
    return get_random_reference(decade)


def get_random_references_mixed(count: int = 3) -> List[str]:
    """
    Get random pop culture references from mixed eras.
    
    Args:
        count: Number of references to return
        
    Returns:
        List of random pop culture references from various decades
    """
    all_refs = []
    for refs in POP_CULTURE_REFS.values():
        all_refs.extend(refs)
    
    if count <= len(all_refs):
        return random.sample(all_refs, count)
    else:
        return random.choices(all_refs, k=count)


def get_reference_decade(reference: str) -> str:
    """
    Find which decade a reference belongs to.
    
    Args:
        reference: Pop culture reference to look up
        
    Returns:
        Decade string
        
    Raises:
        ValueError: If reference is not found in any decade
    """
    for decade, refs in POP_CULTURE_REFS.items():
        if reference in refs:
            return decade
    
    raise ValueError(f"Reference '{reference}' not found in database")


def get_references_for_theme(theme: str) -> List[str]:
    """
    Get pop culture references appropriate for a theme or time period.
    
    This is a helper for content generation to select contextually
    appropriate references.
    
    Args:
        theme: Theme description (e.g., "retro", "modern", "80s nostalgia")
        
    Returns:
        List of appropriate pop culture references
    """
    theme_lower = theme.lower()
    
    # Map themes to decades
    if "70s" in theme_lower or "seventies" in theme_lower:
        return get_references_by_decade("1970s")
    elif "80s" in theme_lower or "eighties" in theme_lower:
        return get_references_by_decade("1980s")
    elif "90s" in theme_lower or "nineties" in theme_lower:
        return get_references_by_decade("1990s")
    elif "2000s" in theme_lower or "y2k" in theme_lower:
        return get_references_by_decade("2000s")
    elif "2010s" in theme_lower:
        return get_references_by_decade("2010s")
    elif "2020s" in theme_lower or "modern" in theme_lower or "contemporary" in theme_lower:
        return get_references_by_decade("2020s")
    elif "retro" in theme_lower or "vintage" in theme_lower:
        # Mix of 70s, 80s, 90s
        refs = []
        refs.extend(get_references_by_decade("1970s"))
        refs.extend(get_references_by_decade("1980s"))
        refs.extend(get_references_by_decade("1990s"))
        return refs
    else:
        # Default: return mixed references from all eras
        return get_random_references_mixed(10)
