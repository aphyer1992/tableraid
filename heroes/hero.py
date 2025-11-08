from figure import Figure, FigureType
import copy

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
        squares = self.map.get_squares_within_distance(self.figure.position, distance, impassible_types=self.figure.impassible_types)
        # Filter out squares that contain blocking figures (but allow markers)
        destinations = []
        for s in squares:
            square_contents = self.map.get_square_contents(s)
            # Allow empty squares or squares containing only markers
            blocking_figures = [f for f in square_contents if f.figure_type != FigureType.MARKER]
            if not blocking_figures:
                destinations.append(s)
        
        # Always allow staying in current position (no move)
        if self.figure.position not in destinations:
            destinations.append(self.figure.position)
        return destinations

    def get_valid_attack_targets(self, range):
        figures = self.map.get_figures_within_distance(self.figure.position, range)
        figures = [f for f in figures if f.targetable and f.figure_type in [FigureType.BOSS, FigureType.MINION]]
        return figures
    
    def reset_turn(self):
        self.move_available = False
        self.attack_available = False
        self.activated = False
        self.gain_energy(1)
        for ability in self.abilities:
            ability.used = False
    
    def activate(self):
        print('ACTIVATING HERO:', self.name)
        self.current_energy -= self.map.heroes_activated
        self.activated = True
        self.map.heroes_activated += 1
        self.move_available = True
        self.attack_available = True
            