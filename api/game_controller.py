"""
GameController replaces the tkinter GameUI for the web API.

Ability effects call methods on this controller (same interface as GameUI),
which store a pending_interaction dict instead of updating any UI.
The FastAPI layer reads and resolves these interactions based on player input.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from figure import FigureType
from coords import Coords


class GameController:
    def __init__(self, game_map, heroes):
        self.map = game_map
        self.heroes = heroes
        # pending_interaction: None, or dict with keys:
        #   type, valid_choices (list of {x,y}), callback (callable), + type-specific extras
        self.pending_interaction = None

    # -------------------------------------------------------------------------
    # Methods called by ability_effects.py (same signatures as GameUI)
    # -------------------------------------------------------------------------

    def choose_friendly_target(self, coords, range, callback_fn, auto_cleanup=True):
        """Set up friendly target selection. auto_cleanup is ignored: clearing happens
        before the callback so that the callback can set a new interaction (Spirit Link)."""
        valid_targets = self.map.get_figures_within_distance(coords, range)
        valid_targets = [f for f in valid_targets if f.figure_type == FigureType.HERO]
        if not valid_targets:
            return

        targets_dict = {f.position: f for f in valid_targets}

        def resolve(coords_obj):
            target = targets_dict[coords_obj]
            self.pending_interaction = None  # clear before callback so it can set a new one
            callback_fn(target)

        self.pending_interaction = {
            'type': 'choose_friendly_target',
            'valid_choices': [{'x': pos.x, 'y': pos.y} for pos in targets_dict],
            'callback': resolve,
        }

    def hero_move(self, hero, move_distance=None, valid_destinations=None):
        """Set up movement interaction. Does NOT consume move_available (caller handles that)."""
        if move_distance is None:
            move_distance = hero.figure.move

        if valid_destinations is not None:
            if isinstance(valid_destinations, list):
                move_info = {
                    dest: {'move_cost': 0, 'hazard_damage': 0, 'path': [dest]}
                    for dest in valid_destinations
                }
            else:
                move_info = valid_destinations
        else:
            move_info = hero.get_valid_move_destinations(move_distance)

        def resolve(coords_obj):
            self.pending_interaction = None
            if coords_obj != hero.figure.position:
                path_data = move_info.get(coords_obj, {})
                path = path_data.get('path') if path_data else None
                self.map.move_figure(hero.figure, coords_obj, path=path)

        self.pending_interaction = {
            'type': 'hero_move',
            'hero_name': hero.name,
            'valid_choices': [{'x': c.x, 'y': c.y} for c in move_info],
            'move_paths': {
                f"{c.x},{c.y}": {
                    'move_cost': info.get('move_cost', 0),
                    'hazard_damage': info.get('hazard_damage', 0),
                }
                for c, info in move_info.items()
            },
            'callback': resolve,
        }

    def hero_attack(self, hero, range=None, physical_damage=None, elemental_damage=None,
                    after_attack_callback=None):
        """Set up attack target selection."""
        if physical_damage is None and elemental_damage is None:
            physical_damage = hero.archetype['physical_dmg']
            elemental_damage = hero.archetype['elemental_dmg']
        if range is None:
            range = hero.archetype['attack_range']

        targets = hero.get_valid_attack_targets(range)
        if not targets:
            return

        targets_dict = {t.position: t for t in targets}

        def resolve(coords_obj):
            target = targets_dict[coords_obj]
            self.pending_interaction = None
            self.execute_attack(
                hero.figure, target,
                physical_damage, elemental_damage,
                after_attack_callback
            )

        self.pending_interaction = {
            'type': 'hero_attack',
            'hero_name': hero.name,
            'valid_choices': [{'x': pos.x, 'y': pos.y} for pos in targets_dict],
            'callback': resolve,
        }

    def execute_attack(self, attacking_figure, target_figure, physical_damage,
                       elemental_damage, after_attack_callback=None):
        """Execute an attack directly. Called by combat_helpers (duck-typed on execute_attack)."""
        dmg_dealt = self.map.deal_damage(
            attacking_figure, target_figure, physical_damage, elemental_damage
        )
        if after_attack_callback:
            after_attack_callback(attacking_figure, target_figure, dmg_dealt, self)

    # -------------------------------------------------------------------------
    # Interaction resolution (called by the API layer)
    # -------------------------------------------------------------------------

    def resolve_selection(self, x, y):
        """Resolve the current pending interaction by selecting cell (x, y).
        Returns True on success, raises ValueError if invalid."""
        if self.pending_interaction is None:
            raise ValueError("No pending interaction")

        coords = Coords(x, y)
        valid = [Coords(c['x'], c['y']) for c in self.pending_interaction['valid_choices']]
        if coords not in valid:
            raise ValueError(f"({x},{y}) is not a valid choice")

        callback = self.pending_interaction['callback']
        callback(coords)
        return True
