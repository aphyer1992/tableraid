import copy
from coords import Coords
from figure import FigureType

class GameStateSnapshot:
    """Captures complete game state at the start of a round for restart functionality."""
    
    def __init__(self, map_obj):
        """Create a snapshot of current game state."""
        self.map_state = self._snapshot_map(map_obj)
        self.figure_states = self._snapshot_figures(map_obj)
        self.encounter_state = self._snapshot_encounter(map_obj.encounter)
    
    def _snapshot_map(self, map_obj):
        """Snapshot map-level state."""
        return {
            'heroes_activated': map_obj.heroes_activated,
            'current_round': map_obj.current_round,
        }
    
    def _snapshot_figures(self, map_obj):
        """Snapshot all figure states including position and attributes."""
        figure_states = {}
        
        for figure in map_obj.figures:
            state = {
                'id': figure.id,
                'name': figure.name,
                'figure_type': figure.figure_type,
                'position': Coords(map_obj.positions[figure].x, map_obj.positions[figure].y),
                'current_health': figure.current_health,
                'max_health': figure.max_health,
                'conditions': copy.deepcopy(figure.conditions),
                'active_effects': copy.deepcopy(figure.active_effects),
                # Store all stats in case they were modified
                'physical_def': figure.physical_def,
                'elemental_def': figure.elemental_def,
                'base_move': figure.base_move,
                'physical_dmg': figure.physical_dmg,
                'elemental_dmg': figure.elemental_dmg,
                'attack_range': figure.attack_range,
                'hazard_damage': figure.hazard_damage,
                'targeting_parameters': copy.deepcopy(figure.targeting_parameters),
                'fixed_representation': figure.fixed_representation,
                'cell_color': figure.cell_color,
            }
            
            # For heroes, snapshot additional state
            if figure.figure_type == FigureType.HERO and hasattr(figure, 'hero'):
                state['hero_state'] = {
                    'current_energy': figure.hero.current_energy,
                    'activated': figure.hero.activated,
                    'can_activate': figure.hero.can_activate,
                    'move_available': figure.hero.move_available,
                    'attack_available': figure.hero.attack_available,
                    # Snapshot ability used states
                    'abilities_used': [ability.used for ability in figure.hero.abilities]
                }
            
            figure_states[figure.id] = state
        
        return figure_states
    
    def _snapshot_encounter(self, encounter):
        """Snapshot encounter-specific state."""
        state = {}
        
        # Snapshot the encounter's internal state
        # This may vary by encounter type, so we snapshot the whole __dict__
        # but exclude the map reference
        for key, value in encounter.__dict__.items():
            if key == 'map':
                continue  # Skip map reference
            # Deep copy to avoid shared references
            state[key] = copy.deepcopy(value)
        
        return state
    
    def restore(self, map_obj):
        """Restore game state from this snapshot."""
        # First, restore map-level state
        map_obj.heroes_activated = self.map_state['heroes_activated']
        map_obj.current_round = self.map_state['current_round']
        
        # Build a mapping of current figure IDs to figure objects
        current_figures = {fig.id: fig for fig in map_obj.figures}
        snapshot_figure_ids = set(self.figure_states.keys())
        current_figure_ids = set(current_figures.keys())
        
        # Remove figures that exist now but didn't at snapshot time
        figures_to_remove = current_figure_ids - snapshot_figure_ids
        for fig_id in figures_to_remove:
            map_obj.remove_figure(current_figures[fig_id])
        
        # Restore or recreate figures
        for fig_id, state in self.figure_states.items():
            if fig_id in current_figures:
                # Figure still exists - restore its state
                self._restore_figure(current_figures[fig_id], state, map_obj)
            else:
                # Figure was removed - need to recreate it
                # This is complex and may not be needed if we restart before any deaths
                # For now, we'll assume figures aren't permanently removed mid-round
                print(f"Warning: Figure {state['name']} (ID {fig_id}) was removed and cannot be restored")
        
        # Restore encounter state
        self._restore_encounter(map_obj.encounter, self.encounter_state)
        
    def _restore_figure(self, figure, state, map_obj):
        """Restore a figure's state from snapshot."""
        # Restore position if changed
        current_pos = map_obj.positions.get(figure)
        if current_pos != state['position']:
            # Move figure back to original position
            old_pos = current_pos
            new_pos = state['position']
            
            # Update map data structures
            map_obj.cell_contents[old_pos.y][old_pos.x].remove(figure)
            map_obj.cell_contents[new_pos.y][new_pos.x].append(figure)
            map_obj.positions[figure] = new_pos
        
        # Restore health and stats
        figure.current_health = state['current_health']
        figure.max_health = state['max_health']
        figure.conditions = copy.deepcopy(state['conditions'])
        figure.active_effects = copy.deepcopy(state['active_effects'])
        figure.physical_def = state['physical_def']
        figure.elemental_def = state['elemental_def']
        figure.base_move = state['base_move']
        figure.physical_dmg = state['physical_dmg']
        figure.elemental_dmg = state['elemental_dmg']
        figure.attack_range = state['attack_range']
        figure.hazard_damage = state['hazard_damage']
        figure.targeting_parameters = copy.deepcopy(state['targeting_parameters'])
        figure.fixed_representation = state['fixed_representation']
        figure.cell_color = state['cell_color']
        
        # Restore hero-specific state
        if 'hero_state' in state and hasattr(figure, 'hero'):
            hero_state = state['hero_state']
            figure.hero.current_energy = hero_state['current_energy']
            figure.hero.activated = hero_state['activated']
            figure.hero.can_activate = hero_state['can_activate']
            figure.hero.move_available = hero_state['move_available']
            figure.hero.attack_available = hero_state['attack_available']
            # Restore ability used states
            if 'abilities_used' in hero_state:
                for ability, was_used in zip(figure.hero.abilities, hero_state['abilities_used']):
                    ability.used = was_used
    
    def _restore_encounter(self, encounter, state):
        """Restore encounter state from snapshot."""
        for key, value in state.items():
            if key == 'map':
                continue
            # Deep copy to avoid shared references
            setattr(encounter, key, copy.deepcopy(value))
