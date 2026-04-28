"""
GameSession manages the full lifecycle of one game instance.
It owns the Map, Hero list, GameController, and exposes action methods
that the FastAPI routes call.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from map import Map
from figure import FigureType
from heroes.hero import Hero
from heroes.hero_archetypes import hero_archetypes
from game_state_snapshot import GameStateSnapshot
from coords import Coords

from api.game_controller import GameController

# Available encounters by name
ENCOUNTER_REGISTRY = {}
try:
    from encounters.encounter_sael import EncounterSael
    ENCOUNTER_REGISTRY['sael'] = EncounterSael
except Exception:
    pass
try:
    from encounters.encounter_como import EncounterComo
    ENCOUNTER_REGISTRY['como'] = EncounterComo
except Exception:
    pass
try:
    from encounters.encounter_across import EncounterAcross
    ENCOUNTER_REGISTRY['across'] = EncounterAcross
except Exception:
    pass


class GameSession:
    def __init__(self):
        self.map = None
        self.heroes = []
        self.controller = None
        self.round_snapshot = None
        self.placement_queue = []
        self.placement_zone = []  # valid coords for hero placement
        self.phase = 'idle'  # idle | placement | hero_turn | game_over
        self.log_messages = []

    # -------------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------------

    def start(self, encounter_name: str, hero_names: list[str]):
        """Initialise a new game with selected encounter and hero roster."""
        encounter_name = encounter_name.lower()
        if encounter_name not in ENCOUNTER_REGISTRY:
            raise ValueError(f"Unknown encounter '{encounter_name}'. Available: {list(ENCOUNTER_REGISTRY)}")

        archetype_by_name = {a['name']: a for a in hero_archetypes}
        missing = [n for n in hero_names if n not in archetype_by_name]
        if missing:
            raise ValueError(f"Unknown hero class(es): {missing}")
        if not hero_names:
            raise ValueError("No heroes selected")

        selected_archetypes = [archetype_by_name[n] for n in hero_names]

        encounter = ENCOUNTER_REGISTRY[encounter_name]()
        self.map = Map(encounter)
        self.heroes = [Hero(a) for a in selected_archetypes]
        self.controller = GameController(self.map, self.heroes)

        # Expose controller as map.ui so encounter card effects can call it
        self.map.ui = self.controller

        # Run passive ability setups (after figure is on map, so we do this after placement)
        self.placement_zone = [Coords(x, y) for (x, y) in encounter.get_deployment_zone()]
        self.placement_queue = list(self.heroes)
        self.phase = 'placement'
        self.log_messages = [f"Game started: {encounter_name}. Place your heroes."]

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------

    def action_place_hero(self, x: int, y: int):
        """Place next hero in placement queue at (x, y)."""
        if self.phase != 'placement':
            raise ValueError("Not in placement phase")
        coords = Coords(x, y)
        if coords not in self.placement_zone:
            raise ValueError("Invalid placement position")

        hero = self.placement_queue.pop(0)
        self.map.add_figure(hero.figure, coords)  # map.add_figure runs setup_routines for heroes

        self.placement_zone.remove(coords)
        self.log_messages.append(f"Placed {hero.name} at ({x},{y})")

        if not self.placement_queue:
            self.phase = 'hero_turn'
            self.map.begin_hero_turn()
            self.round_snapshot = GameStateSnapshot(self.map)
            self.log_messages.append("All heroes placed. Hero turn begins!")

    def action_activate_hero(self, hero_name: str):
        hero = self._get_hero(hero_name)
        if not hero.activate():
            raise ValueError(f"Cannot activate {hero_name}")
        self.log_messages.append(f"{hero_name} activated (cost {self.map.heroes_activated - 1} energy)")

    def action_basic_move(self, hero_name: str):
        """Initiate basic movement for a hero (consumes move_available)."""
        hero = self._get_hero(hero_name)
        if not hero.move_available:
            raise ValueError(f"{hero_name} has no move available")
        hero.move_available = False
        self.controller.hero_move(hero)
        if self.controller.pending_interaction is not None:
            self.controller.pending_interaction['undo'] = {
                'hero_name': hero_name, 'restore_move': True,
            }
        self.log_messages.append(f"{hero_name} choosing move destination")

    def action_basic_attack(self, hero_name: str):
        """Initiate basic attack for a hero (consumes attack_available)."""
        hero = self._get_hero(hero_name)
        if not hero.attack_available:
            raise ValueError(f"{hero_name} has no attack available")
        hero.attack_available = False
        self.controller.hero_attack(hero)
        if self.controller.pending_interaction is None:
            self.log_messages.append(f"{hero_name} basic attack: no valid targets")
        else:
            self.controller.pending_interaction['undo'] = {
                'hero_name': hero_name, 'restore_attack': True,
            }
            self.log_messages.append(f"{hero_name} choosing attack target")

    def action_cast_ability(self, hero_name: str, ability_index: int, energy_amount: int = None):
        """Cast a hero ability."""
        hero = self._get_hero(hero_name)
        if ability_index < 0 or ability_index >= len(hero.abilities):
            raise ValueError("Invalid ability index")
        ability = hero.abilities[ability_index]
        if not ability.is_castable():
            raise ValueError(f"Ability '{ability.name}' is not castable right now")

        if energy_amount is None:
            energy_amount = ability.energy_cost

        # Validate energy
        if ability.variable_cost:
            if energy_amount < ability.energy_cost:
                raise ValueError(f"Must spend at least {ability.energy_cost} energy")
        else:
            energy_amount = ability.energy_cost

        hero.spend_energy(energy_amount)
        move_consumed = ability.move_cost
        attack_consumed = ability.attack_cost
        if ability.move_cost:
            hero.move_available = False
        if ability.attack_cost:
            hero.attack_available = False
        ability.used = True

        # Call the effect function with the controller as ui
        ability.effect_fn(hero.figure, energy_amount, ui=self.controller)
        if self.controller.pending_interaction is not None:
            self.controller.pending_interaction['undo'] = {
                'hero_name': hero_name,
                'restore_energy': energy_amount,
                'restore_ability_idx': ability_index,
                'restore_move': move_consumed,
                'restore_attack': attack_consumed,
            }
        self.log_messages.append(f"{hero_name} cast {ability.name}")

    def action_select(self, x: int, y: int):
        """Resolve the current pending interaction by selecting cell (x, y)."""
        if self.controller.pending_interaction is None:
            raise ValueError("No pending interaction to resolve")
        self.controller.resolve_selection(x, y)
        self.log_messages.append(f"Selected ({x},{y})")

    def action_end_turn(self):
        """End hero turn, run boss turn, begin next hero turn."""
        if self.phase != 'hero_turn':
            raise ValueError("Not in hero turn")
        if self.controller.pending_interaction is not None:
            raise ValueError("Resolve pending interaction first")
        self.map.end_hero_turn()
        self.map.execute_boss_turn()
        self.map.begin_hero_turn()
        self.round_snapshot = GameStateSnapshot(self.map)
        self.log_messages.append(f"Round {self.map.current_round} begins")

        # Check win/loss conditions
        bosses = self.map.get_figures_by_type(FigureType.BOSS)
        heroes_alive = self.map.get_figures_by_type(FigureType.HERO)
        if not bosses:
            self.phase = 'game_over'
            self.log_messages.append("Victory! All bosses defeated.")
        elif not heroes_alive:
            self.phase = 'game_over'
            self.log_messages.append("Defeat. All heroes have fallen.")

    def action_restart_round(self):
        """Restore game state to start of current round."""
        if self.round_snapshot is None:
            raise ValueError("No snapshot available")
        self.round_snapshot.restore(self.map)
        self.controller.pending_interaction = None
        self.phase = 'hero_turn'
        self.log_messages.append(f"Round {self.map.current_round} restarted")

    def action_cancel(self):
        """Cancel the current pending interaction and undo the action that triggered it."""
        pi = self.controller.pending_interaction
        if pi is None:
            return
        undo = pi.get('undo', {})
        if undo:
            hero = self._get_hero(undo['hero_name'])
            if undo.get('restore_move'):
                hero.move_available = True
            if undo.get('restore_attack'):
                hero.attack_available = True
            restore_energy = undo.get('restore_energy', 0)
            if restore_energy:
                hero.gain_energy(restore_energy)
            idx = undo.get('restore_ability_idx')
            if idx is not None:
                hero.abilities[idx].used = False
        self.controller.pending_interaction = None
        self.log_messages.append("Action cancelled")

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _get_hero(self, hero_name: str) -> Hero:
        for h in self.heroes:
            if h.name == hero_name:
                return h
        raise ValueError(f"Hero '{hero_name}' not found")

    def get_encounters(self) -> list[dict]:
        return [{'id': k, 'name': k.capitalize()} for k in ENCOUNTER_REGISTRY]

    def get_hero_archetypes(self) -> list[str]:
        return [a['name'] for a in hero_archetypes]
