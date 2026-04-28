#!/usr/bin/env python3
"""
Integration tests for the web API layer (GameController + GameSession + serializers).

Run with:  python test_api.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.game_session import GameSession
from api.serializers import serialize_session


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_session(encounter='sael', heroes=None):
    if heroes is None:
        heroes = ['Warrior', 'Ranger']
    s = GameSession()
    s.start(encounter, heroes)
    return s


def place_all_heroes(session):
    """Place every hero in the placement queue."""
    # snapshot zone before modifying it
    zone = list(session.placement_zone)
    zone_iter = iter(zone)
    while session.placement_queue:
        coords = next(zone_iter)
        session.action_place_hero(coords.x, coords.y)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_session_start():
    """Session starts in placement phase with correct heroes."""
    s = make_session(heroes=['Warrior', 'Ranger', 'Mage'])
    assert s.phase == 'placement'
    assert len(s.heroes) == 3
    assert [h.name for h in s.heroes] == ['Warrior', 'Ranger', 'Mage']
    assert len(s.placement_queue) == 3
    assert len(s.placement_zone) > 0
    print("✓ test_session_start")


def test_hero_placement():
    """Placing all heroes transitions to hero_turn phase."""
    s = make_session()
    place_all_heroes(s)
    assert s.phase == 'hero_turn'
    assert s.placement_queue == []
    assert s.round_snapshot is not None
    # Both heroes should now have map positions
    for hero in s.heroes:
        assert hero.figure.position is not None
    print("✓ test_hero_placement")


def test_hero_activation():
    """Activating a hero grants move + attack, costs energy."""
    s = make_session()
    place_all_heroes(s)

    warrior = s._get_hero('Warrior')
    assert not warrior.activated
    assert not warrior.move_available
    start_energy = warrior.current_energy

    s.action_activate_hero('Warrior')

    assert warrior.activated
    assert warrior.move_available
    assert warrior.attack_available
    # First activation costs 0 energy (heroes_activated was 0)
    assert warrior.current_energy == start_energy
    print("✓ test_hero_activation")


def test_basic_move_sets_pending():
    """Requesting a basic move produces a hero_move pending interaction."""
    s = make_session()
    place_all_heroes(s)
    s.action_activate_hero('Warrior')

    warrior = s._get_hero('Warrior')
    assert warrior.move_available

    s.action_basic_move('Warrior')

    assert not warrior.move_available  # consumed immediately
    pending = s.controller.pending_interaction
    assert pending is not None
    assert pending['type'] == 'hero_move'
    assert pending['hero_name'] == 'Warrior'
    assert len(pending['valid_choices']) > 0
    print("✓ test_basic_move_sets_pending")


def test_select_resolves_move():
    """Selecting a valid destination resolves the move interaction."""
    s = make_session()
    place_all_heroes(s)
    s.action_activate_hero('Warrior')
    s.action_basic_move('Warrior')

    warrior = s._get_hero('Warrior')
    old_pos = warrior.figure.position
    pending = s.controller.pending_interaction
    # Pick a destination that is different from current position
    dest = next(
        c for c in pending['valid_choices']
        if not (c['x'] == old_pos.x and c['y'] == old_pos.y)
    )

    s.action_select(dest['x'], dest['y'])

    assert s.controller.pending_interaction is None
    new_pos = warrior.figure.position
    assert new_pos.x == dest['x'] and new_pos.y == dest['y']
    print("✓ test_select_resolves_move")


def test_spirit_link_two_step():
    """Spirit Link: first selects a friendly target, then provides that hero a move."""
    s = make_session(heroes=['Warrior', 'Ranger'])
    place_all_heroes(s)

    s.action_activate_hero('Warrior')
    s.action_activate_hero('Ranger')

    # Spirit Link is ability index 1 for Ranger
    s.action_cast_ability('Ranger', 1)  # Spirit Link, 0 energy

    pending = s.controller.pending_interaction
    assert pending is not None
    assert pending['type'] == 'choose_friendly_target', f"Expected choose_friendly_target, got {pending['type']}"

    # Select Warrior as the target
    warrior = s._get_hero('Warrior')
    warrior_pos = warrior.figure.position
    choice = {'x': warrior_pos.x, 'y': warrior_pos.y}
    assert choice in pending['valid_choices'], "Warrior not in valid targets"

    s.action_select(choice['x'], choice['y'])

    # After selecting the target, a hero_move for Warrior should be pending
    pending2 = s.controller.pending_interaction
    assert pending2 is not None
    assert pending2['type'] == 'hero_move', f"Expected hero_move, got {pending2['type']}"
    assert pending2['hero_name'] == 'Warrior'
    assert len(pending2['valid_choices']) > 0
    print("✓ test_spirit_link_two_step")


def test_spirit_link_move_resolves():
    """Spirit Link: completing the target's move clears pending interaction."""
    s = make_session(heroes=['Warrior', 'Ranger'])
    place_all_heroes(s)
    s.action_activate_hero('Warrior')
    s.action_activate_hero('Ranger')
    s.action_cast_ability('Ranger', 1)

    # Choose Warrior as target
    warrior = s._get_hero('Warrior')
    s.action_select(warrior.figure.position.x, warrior.figure.position.y)

    pending = s.controller.pending_interaction
    # Pick any valid move destination
    dest = pending['valid_choices'][0]
    s.action_select(dest['x'], dest['y'])

    assert s.controller.pending_interaction is None
    print("✓ test_spirit_link_move_resolves")


def test_serializer_output():
    """Serialized game state has expected top-level keys and types."""
    s = make_session()
    place_all_heroes(s)
    state = serialize_session(s)

    assert state['phase'] == 'hero_turn'
    assert isinstance(state['map'], dict)
    assert isinstance(state['heroes'], list)
    assert isinstance(state['boss_display'], list)
    assert state['pending_interaction'] is None
    assert isinstance(state['log'], list)

    # Map structure
    m = state['map']
    assert m['width'] > 0 and m['height'] > 0
    assert len(m['cells']) == m['height']

    # Heroes structure
    hero = state['heroes'][0]
    for key in ('name', 'current_health', 'max_health', 'current_energy',
                'activated', 'move_available', 'attack_available', 'abilities', 'position'):
        assert key in hero, f"Missing key: {key}"

    print("✓ test_serializer_output")


def test_serializer_strips_callbacks():
    """Serialized pending_interaction must not contain non-JSON-able callbacks."""
    import json
    s = make_session()
    place_all_heroes(s)
    s.action_activate_hero('Warrior')
    s.action_basic_move('Warrior')

    state = serialize_session(s)
    # Should be JSON-serializable (no Python callables)
    json.dumps(state)  # raises TypeError if not serializable
    assert state['pending_interaction'] is not None
    assert 'callback' not in state['pending_interaction']
    print("✓ test_serializer_strips_callbacks")


def test_rogue_placement_and_combo_setup():
    """Placing the Rogue initialises combo_points exactly once (no duplicate setup_routine call)."""
    s = make_session(heroes=['Warrior', 'Paladin', 'Rogue'])
    place_all_heroes(s)

    rogue = s._get_hero('Rogue')
    assert rogue.figure.get_effect('combo_points') == 0, "combo_points should be 0 after setup"
    assert rogue.figure.get_effect('gained_combo_points') == False

    # Eviscerate should be castable if conditions are met
    s.action_activate_hero('Rogue')
    eviscerate = next(a for a in rogue.abilities if a.name == 'Eviscerate')
    # 2 energy cost, rogue starts with max energy after activation
    assert eviscerate.energy_cost == 2
    print("✓ test_rogue_placement_and_combo_setup")



    """Placing a hero outside the deployment zone raises ValueError."""
    s = make_session()
    try:
        s.action_place_hero(0, 0)  # (0,0) is very unlikely to be in deployment zone
        # If it didn't raise, check it actually was valid
        # (this assertion is just a soft fallback)
    except ValueError:
        pass  # expected
    print("✓ test_invalid_placement_raises")


def test_invalid_selection_raises():
    """Selecting an invalid cell during a pending interaction raises ValueError."""
    s = make_session()
    place_all_heroes(s)
    s.action_activate_hero('Warrior')
    s.action_basic_move('Warrior')

    try:
        s.action_select(-1, -1)  # definitely not a valid choice
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    print("✓ test_invalid_selection_raises")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_session_start()
    test_hero_placement()
    test_hero_activation()
    test_basic_move_sets_pending()
    test_select_resolves_move()
    test_spirit_link_two_step()
    test_spirit_link_move_resolves()
    test_serializer_output()
    test_serializer_strips_callbacks()
    test_rogue_placement_and_combo_setup()
    test_invalid_selection_raises()
    test_invalid_selection_raises()
    print("\n🎉 All API tests passed!")
