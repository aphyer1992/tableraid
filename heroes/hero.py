from figure import Figure, FigureType
import copy

from game_targeting import TargetingContext

class Hero:
    def __init__(self, archetype):
        self.name = archetype['name']
        self.archetype = archetype
        self.figure = Figure.from_hero_archetype(archetype)
        self.figure.hero = self
        self.max_energy = 5
        self.current_energy = self.max_energy
        self.abilities = [copy.deepcopy(ability) for ability in archetype['abilities']]
        for ability in self.abilities:
            ability.hero = self
        self.activated = False
        self.can_activate = True
        self.move_available = False
        self.attack_available = False

    @property
    def map(self):
        return self.figure.map

    def gain_energy(self, amount=1):
        self.current_energy = min(self.max_energy, self.current_energy + amount)

    def spend_energy(self, amount=1):
        if amount > self.current_energy:
            raise ValueError("Not enough energy to spend")
        self.current_energy -= amount

    def get_valid_move_destinations(self, distance):
        """
        Get valid move destinations with optimal path information.
        
        Returns:
            dict mapping Coords to path info:
            {
                coords: {
                    'move_cost': int,
                    'hazard_damage': int,
                    'path': [Coords]
                }
            }
        """
        # Use hazard-aware BFS to get all reachable squares with path info
        path_info = self.map.bfs_with_hazards(
            self.figure.position, 
            impassible_types=self.figure.impassible_types,
            max_distance=distance,
            figure=self.figure
        )
        
        # Filter out squares that contain blocking figures (but allow markers)
        valid_destinations = {}
        for coords, info in path_info.items():
            square_contents = self.map.get_square_contents(coords)
            blocking_figures = [f for f in square_contents if f.figure_type != FigureType.MARKER]
            if not blocking_figures:
                valid_destinations[coords] = info
        
        # Always allow staying in current position (no move)
        if self.figure.position not in valid_destinations:
            valid_destinations[self.figure.position] = {
                'move_cost': 0,
                'hazard_damage': 0,
                'path': [self.figure.position]
            }
        
        return valid_destinations

    def get_valid_attack_targets(self, range):
        figures = self.map.get_figures_within_distance(self.figure.position, range)
        figures = [f for f in figures if f.targeting_parameters[TargetingContext.ENEMY_TARGETABLE] and f.figure_type in [FigureType.BOSS, FigureType.MINION]]
        return figures
    
    def reset_turn(self):
        self.move_available = False
        self.attack_available = False
        self.activated = False
        self.gain_energy(1)
        for ability in self.abilities:
            ability.used = False
    
    def activate(self):
        if not self.can_activate:
            print(f'{self.name} cannot activate (disabled)')
            return False
        print('ACTIVATING HERO:', self.name)
        self.current_energy -= self.map.heroes_activated
        self.activated = True
        self.map.heroes_activated += 1
        self.move_available = True
        self.attack_available = True
        return True
            