#!/usr/bin/env python3
"""
Simple test script to verify the GameEvent enum integration works correctly.
This tests both enum and string event names to ensure backwards compatibility.
"""

from events import EventManager
from game_events import GameEvent

def test_event_enum():
    """Test that GameEvent enum works properly with EventManager."""
    em = EventManager()
    
    # Test with enum
    triggered_events = []
    
    def test_callback(event_name):
        triggered_events.append(event_name)
    
    # Register using enum
    listener_id1 = em.register(GameEvent.HERO_TURN_START, lambda: test_callback("enum_hero_start"))
    
    # Register using string (backwards compatibility)
    listener_id2 = em.register("hero_turn_start", lambda: test_callback("string_hero_start"))
    
    # Trigger using enum
    em.trigger(GameEvent.HERO_TURN_START)
    
    # Both listeners should have been called
    assert len(triggered_events) == 2
    assert "enum_hero_start" in triggered_events
    assert "string_hero_start" in triggered_events
    
    # Clear and test triggering with string
    triggered_events.clear()
    em.trigger("hero_turn_start")
    
    # Both listeners should still be called
    assert len(triggered_events) == 2
    assert "enum_hero_start" in triggered_events
    assert "string_hero_start" in triggered_events
    
    # Test deregistering with enum
    triggered_events.clear()
    em.deregister(GameEvent.HERO_TURN_START, listener_id1)
    em.trigger(GameEvent.HERO_TURN_START)
    
    # Only string listener should be called now
    assert len(triggered_events) == 1
    assert "string_hero_start" in triggered_events
    
    print("✓ All event enum tests passed!")

def test_event_documentation():
    """Test that all events have proper documentation."""
    for event in GameEvent:
        assert event.__doc__, f"Event {event.name} is missing documentation"
        assert len(event.__doc__.strip()) > 10, f"Event {event.name} has insufficient documentation"
    
    print("✓ All events have proper documentation!")

if __name__ == "__main__":
    test_event_enum()
    test_event_documentation()
    print("🎉 All tests passed! The GameEvent enum integration is working correctly.")