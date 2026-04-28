"""
Serializers: convert game objects into JSON-safe dicts for the API response.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from figure import FigureType
from game_targeting import TargetingContext
from effects_display import EFFECTS_DISPLAY


def _sanitize_boss_display(items):
    """Strip non-serializable values (callables) from boss display card dicts."""
    result = []
    for item in items:
        result.append({k: v for k, v in item.items() if not callable(v)})
    return result


def serialize_pending_interaction(pending):
    """Serialize a controller.pending_interaction dict (strip non-JSON callback)."""
    if pending is None:
        return None
    result = {k: v for k, v in pending.items() if k != 'callback'}
    return result


def serialize_figure(figure, game_map):
    """Serialize a Figure to a dict."""
    pos = game_map.get_figure_position(figure)
    effects = []
    for key, display in EFFECTS_DISPLAY.items():
        if display.get('is_condition'):
            value = figure.get_condition(key)
        else:
            value = figure.get_effect(key)
        if value is not None and value != 0 and value is not False:
            effects.append({
                'key': key,
                'icon': display['icon'],
                'position': display['position'],
                'color': display.get('color', '#000'),
                'quantity': value if display.get('show_quantity') else None,
            })

    return {
        'id': getattr(figure, 'id', None),
        'name': figure.name,
        'type': figure.figure_type.value,
        'position': {'x': pos.x, 'y': pos.y} if pos else None,
        'current_health': figure.current_health,
        'max_health': figure.max_health,
        'conditions': dict(figure.conditions),
        'active_effects': dict(figure.active_effects),
        'cell_color': figure.cell_color,
        'fixed_representation': figure.fixed_representation,
        'rendering_priority': figure.targeting_parameters.get(TargetingContext.RENDERING_PRIORITY, 0),
        'effects_display': effects,
    }


def serialize_ability(ability):
    """Serialize an Ability to a dict."""
    return {
        'name': ability.name,
        'description': ability.description,
        'energy_cost': ability.energy_cost,
        'variable_cost': ability.variable_cost,
        'move_cost': ability.move_cost,
        'attack_cost': ability.attack_cost,
        'passive': ability.passive,
        'usable_off_turn': ability.usable_off_turn,
        'used': ability.used,
        'is_castable': ability.is_castable(),
    }


def serialize_hero(hero, game_map):
    """Serialize a Hero (and its underlying Figure) to a dict."""
    fig = hero.figure
    pos = game_map.get_figure_position(fig) if fig.map else None
    return {
        'name': hero.name,
        'current_energy': hero.current_energy,
        'max_energy': hero.max_energy,
        'activated': hero.activated,
        'can_activate': hero.can_activate,
        'move_available': hero.move_available,
        'attack_available': hero.attack_available,
        'activation_cost': game_map.heroes_activated,  # cost to activate next
        'current_health': fig.current_health,
        'max_health': fig.max_health,
        'physical_def': fig.physical_def,
        'elemental_def': fig.elemental_def,
        'conditions': dict(fig.conditions),
        'active_effects': {k: v for k, v in fig.active_effects.items()
                           if not k.startswith('_')},
        'position': {'x': pos.x, 'y': pos.y} if pos else None,
        'abilities': [serialize_ability(a) for a in hero.abilities],
    }


def serialize_map(game_map, heroes):
    """Serialize the full map state."""
    cells = []
    for y in range(game_map.height):
        row = []
        for x in range(game_map.width):
            contents = game_map.cell_contents[y][x]
            figures_in_cell = [serialize_figure(f, game_map) for f in contents]
            row.append({
                'x': x, 'y': y,
                'figures': figures_in_cell,
            })
        cells.append(row)

    # Special tiles (lava, blizzard borders, etc.)
    special_tiles = {}
    if hasattr(game_map.encounter, 'special_tiles'):
        for tile_name, tile_data in game_map.encounter.special_tiles.items():
            special_tiles[tile_name] = {
                'color': tile_data.get('color'),
                'coords': [{'x': c.x, 'y': c.y} for c in tile_data.get('coords', [])],
            }

    return {
        'width': game_map.width,
        'height': game_map.height,
        'cells': cells,
        'current_round': game_map.current_round,
        'heroes_activated': game_map.heroes_activated,
        'special_tiles': special_tiles,
    }


def serialize_session(session):
    """Full game state snapshot for the frontend."""
    if session.map is None:
        return {
            'phase': session.phase,
            'map': None,
            'heroes': [],
            'boss_display': [],
            'pending_interaction': None,
            'placement_zone': [],
            'placement_next_hero': None,
            'log': session.log_messages[-20:],
        }

    placement_next = (
        session.placement_queue[0].name if session.placement_queue else None
    )

    return {
        'phase': session.phase,
        'map': serialize_map(session.map, session.heroes),
        'heroes': [serialize_hero(h, session.map) for h in session.heroes],
        'boss_display': _sanitize_boss_display(session.map.encounter.get_boss_display_info()),
        'pending_interaction': serialize_pending_interaction(
            session.controller.pending_interaction if session.controller else None
        ),
        'placement_zone': [{'x': c.x, 'y': c.y} for c in session.placement_zone],
        'placement_next_hero': placement_next,
        'log': session.log_messages[-20:],
    }
