from enum import Enum

class GameEvent(Enum):
    """
    Centralized enum for all game events to prevent string-based event name mismatches.
    Each event has a descriptive docstring explaining when it's triggered and what parameters are passed.
    """
    
    # Turn management events
    HERO_TURN_START = "hero_turn_start"
    """Triggered at the beginning of each hero turn phase."""
    
    HERO_TURN_END = "hero_turn_end"
    """Triggered at the end of each hero turn phase."""
    
    BOSS_TURN_START = "boss_turn_start"
    """Triggered at the beginning of each boss turn phase."""
    
    BOSS_TURN_END = "boss_turn_end"
    """Triggered at the end of each boss turn phase."""
    
    # Figure action events
    START_FIGURE_ACTION = "start_figure_action"
    """Triggered when a figure (hero/boss/minion) begins their individual action.
    Args: figure - the Figure object starting their action"""
    
    END_FIGURE_ACTION = "end_figure_action"
    """Triggered when a figure (hero/boss/minion) ends their individual action.
    Args: figure - the Figure object ending their action"""
    
    START_ACTION = "start_action"
    """Triggered when any action begins (more general than start_figure_action).
    Args: figure - the Figure object starting an action"""
    
    # Combat events
    DAMAGE_TAKEN = "damage_taken"
    """Triggered when a figure takes damage (after defense rolls).
    Args: figure - the Figure taking damage, damage_taken - dict with physical/elemental damage, damage_source - source of damage"""
    
    DEFENSE_ROLL = "defense_roll"
    """Triggered when a figure makes a defense roll.
    Args: figure - the Figure making the roll, roll - the dice result, damage_type - 'Physical' or 'Elemental', damage_source - source of damage"""
    
    HEALED = "healed"
    """Triggered when a figure is healed.
    Args: figure - the Figure being healed, amount - healing amount, source - source of healing"""
    
    # Movement events
    GET_MOVE = "get_move"
    """Triggered when calculating a figure's movement range (allows modification).
    Args: figure - the Figure, move_data - dict with 'value' key that can be modified"""
    
    # Map events
    FIGURE_ADDED = "figure_added"
    """Triggered when a figure is added to the map.
    Args: figure - the Figure being added, coords - the Coords where it's placed"""
    
    FIGURE_REMOVED = "figure_removed"
    """Triggered when a figure is removed from the map.
    Args: figure - the Figure being removed, coords - the Coords where it was"""
    
    FIGURE_DEATH = "figure_death"
    """Triggered when a figure dies (health reaches 0).
    Args: figure - the Figure that died"""
    
    # Condition events
    CONDITION_ADDED = "condition_added"
    """Triggered when a condition is applied to a figure.
    Args: figure - the Figure, condition - condition name, duration - condition duration"""
    
    CONDITION_REMOVED = "condition_removed"
    """Triggered when a condition is removed from a figure.
    Args: figure - the Figure, condition - condition name"""

    def __str__(self):
        """Return the string value for backwards compatibility."""
        return self.value