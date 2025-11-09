from enum import Enum

class Condition(Enum):
    """
    Centralized enum for all game conditions to prevent string-based condition name mismatches.
    Each condition has a descriptive docstring explaining its effect.
    """
    
    # Damage over time conditions
    BURN = "Burn"
    """Deals 1 elemental damage at the end of each turn."""
    
    BLEED = "Bleed"
    """Deals 1 physical damage at the end of each turn."""
    
    # Healing over time conditions
    REGEN = "Regen"
    """Heals 1 health at the start of each turn."""
    
    # Movement affecting conditions
    SLOWED = "Slowed"
    """Reduces movement to maximum 1 space per turn."""
    
    STUNNED = "Stunned"
    """Prevents all actions: movement, attacks, and abilities."""
    
    # Defensive conditions
    SHIELDED = "Shielded"
    """Blocks incoming damage, reducing shield value by damage blocked."""

    def __str__(self):
        """Return the string value for backwards compatibility."""
        return self.value