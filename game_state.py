import copy
from dataclasses import dataclass
from typing import Dict, Any, List
from coords import Coords

@dataclass
class GameSnapshot:
    """Captures the essential game state at the start of a hero turn for restart functionality."""
    
    # Hero state
    hero_states: List[Dict[str, Any]]
    
    # Figure states (health, conditions, effects, positions)
    figure_states: Dict[int, Dict[str, Any]]  # figure_id -> state dict
    
    # Map state
    heroes_activated: int
    
    # Boss/encounter state
    encounter_state: Dict[str, Any]
    
    # Event listeners that need to be cleaned up
    active_listeners: List[str]  # listener IDs to clean up

class GameStateManager:
    """Manages saving and restoring game state for round restart functionality."""
    
    def __init__(self, map_obj):
        self.map = map_obj
        self.round_start_snapshot = None
    
    def capture_round_start_snapshot(self):
        """Capture the state at the beginning of a hero turn."""
        
        # Capture hero states
        hero_states = []
        for hero_figure in self.map.get_figures_by_type(FigureType.HERO):
            hero = hero_figure.hero
            hero_state = {
                'current_energy': hero.current_energy,
                'activated': hero.activated,
                'move_available': hero.move_available,
                'attack_available': hero.attack_available,
                'ability_used_states': [ability.used for ability in hero.abilities]
            }
            hero_states.append(hero_state)
        
        # Capture figure states (health, conditions, effects, positions)
        figure_states = {}
        for figure in self.map.figures:
            figure_state = {
                'current_health': figure.current_health,
                'position': copy.deepcopy(figure.position),
                'conditions': copy.deepcopy(figure.conditions),
                'active_effects': copy.deepcopy(figure.active_effects),
                'physical_def': figure.physical_def,
                'elemental_def': figure.elemental_def,
                'targetable': figure.targetable
            }
            figure_states[figure.id] = figure_state
        
        # Capture map state
        heroes_activated = self.map.heroes_activated
        
        # Capture encounter state
        encounter_state = {
            'biting_cold_counters': self.map.encounter.biting_cold_counters,
            'next_card_name': self.map.encounter.next_card['name'],
            'deck_state': copy.deepcopy(self.map.encounter.deck)
        }
        
        self.round_start_snapshot = GameSnapshot(
            hero_states=hero_states,
            figure_states=figure_states,
            heroes_activated=heroes_activated,
            encounter_state=encounter_state,
            active_listeners=[]  # We'll implement listener tracking separately
        )
        
        print("📸 Round start snapshot captured!")
    
    def restore_round_start_snapshot(self):
        """Restore the game to the state captured at round start."""
        if not self.round_start_snapshot:
            print("❌ No snapshot available to restore!")
            return False
        
        snapshot = self.round_start_snapshot
        
        # Restore hero states
        hero_figures = self.map.get_figures_by_type(FigureType.HERO)
        for i, hero_figure in enumerate(hero_figures):
            hero = hero_figure.hero
            hero_state = snapshot.hero_states[i]
            
            hero.current_energy = hero_state['current_energy']
            hero.activated = hero_state['activated']
            hero.move_available = hero_state['move_available']
            hero.attack_available = hero_state['attack_available']
            
            # Restore ability used states
            for j, ability in enumerate(hero.abilities):
                ability.used = hero_state['ability_used_states'][j]
        
        # Restore figure states
        for figure in self.map.figures:
            if figure.id in snapshot.figure_states:
                figure_state = snapshot.figure_states[figure.id]
                
                figure.current_health = figure_state['current_health']
                figure.conditions = copy.deepcopy(figure_state['conditions'])
                figure.active_effects = copy.deepcopy(figure_state['active_effects'])
                figure.physical_def = figure_state['physical_def']
                figure.elemental_def = figure_state['elemental_def']
                figure.targetable = figure_state['targetable']
                
                # Restore position
                old_position = figure.position
                new_position = figure_state['position']
                if old_position != new_position:
                    self.map.move_figure(figure, new_position)
        
        # Remove figures that were added during the round
        figures_to_remove = []
        for figure in self.map.figures:
            if figure.id not in snapshot.figure_states:
                figures_to_remove.append(figure)
        
        for figure in figures_to_remove:
            self.map.remove_figure(figure)
        
        # Restore map state
        self.map.heroes_activated = snapshot.heroes_activated
        
        # Restore encounter state
        self.map.encounter.biting_cold_counters = snapshot.encounter_state['biting_cold_counters']
        self.map.encounter.deck = copy.deepcopy(snapshot.encounter_state['deck_state'])
        # Find the card by name and restore it
        for card in self.map.encounter.card_list:
            if card['name'] == snapshot.encounter_state['next_card_name']:
                self.map.encounter.next_card = card
                break
        
        print("🔄 Game state restored to round start!")
        return True