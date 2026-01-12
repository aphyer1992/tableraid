"""Helper functions for event registration and management"""

from game_events import GameEvent


def register_temporary_listener(map, event, listener_fn, cleanup_event):
    """Register a listener that automatically cleans up when a specified event occurs
    
    Args:
        map: The game map with the event system
        event: The GameEvent to listen to
        listener_fn: The callback function to register
        cleanup_event: The GameEvent that triggers cleanup (e.g., HERO_TURN_START, BOSS_TURN_END)
    
    Example:
        # Listener that lasts until the next hero turn
        register_temporary_listener(map, GameEvent.DAMAGE_TAKEN, my_listener, GameEvent.HERO_TURN_START)
    """
    listener_id = map.events.register(event, listener_fn)
    
    def cleanup_listener():
        map.events.deregister(event, listener_id)
    
    cleanup_id = map.events.register(cleanup_event, cleanup_listener)
    
    def cleanup_cleanup():
        map.events.deregister(cleanup_event, cleanup_id)
    
    map.events.register(cleanup_event, cleanup_cleanup)


def schedule_callback(map, event, callback_fn):
    """Register a one-shot callback that runs once when an event fires, then deregisters itself
    
    Args:
        map: The game map with the event system
        event: The GameEvent to listen for
        callback_fn: The callback function to run (should accept **kwargs)
    
    Example:
        # Clear an effect at the end of the boss turn
        def clear_effect():
            figure.add_effect('extended_range', None, overwrite=True)
        schedule_callback(map, GameEvent.BOSS_TURN_END, clear_effect)
    """
    def oneshot_wrapper(**kwargs):
        callback_fn(**kwargs)
        map.events.deregister(event, listener_id)
    
    listener_id = map.events.register(event, oneshot_wrapper)


def modify_stat_temporarily(figure, stat_modifications, revert_event=GameEvent.HERO_TURN_START):
    """Temporarily modify figure stats and automatically revert them when an event fires
    
    Args:
        figure: The figure whose stats to modify
        stat_modifications: Dict mapping attribute names to delta values (e.g., {'physical_def': -1, 'elemental_def': -1})
        revert_event: The GameEvent that triggers the reversion (default: HERO_TURN_START)
    
    Example:
        # Reduce defense by 1 until next hero turn
        modify_stat_temporarily(figure, {'physical_def': -1, 'elemental_def': -1})
        
        # Increase targeting priority until next hero turn
        from game_targeting import TargetingContext
        modify_stat_temporarily(figure, {('targeting_parameters', TargetingContext.TARGETING_PRIORITY): 1})
    """
    # Apply the modifications
    for key, delta in stat_modifications.items():
        # Handle nested attributes like ('targeting_parameters', TargetingContext.TARGETING_PRIORITY)
        if isinstance(key, tuple):
            obj = getattr(figure, key[0])
            obj[key[1]] = obj[key[1]] + delta
        else:
            setattr(figure, key, getattr(figure, key) + delta)
    
    # Create revert function that undoes the modifications
    def revert_listener():
        for key, delta in stat_modifications.items():
            if isinstance(key, tuple):
                obj = getattr(figure, key[0])
                obj[key[1]] = obj[key[1]] - delta
            else:
                setattr(figure, key, getattr(figure, key) - delta)
        
        figure.map.events.deregister(revert_event, listener_id)
    
    # Register the revert listener
    listener_id = figure.map.events.register(revert_event, revert_listener)
