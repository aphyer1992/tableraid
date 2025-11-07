from coords import Coords
from figure import FigureType
from events import EventManager
from conditions import setup_condition_listeners
import math
import random

class Map:
    def __init__(self, encounter):
        self.encounter = encounter
        self.encounter.map = self
        self.width, self.height = encounter.get_map_dimensions()
        self.figures = []
        self.positions = {}  # Maps figures to their (x, y) coordinates
        self.cell_contents = [[[] for _ in range(self.width)] for _ in range(self.height)]
        self.next_figure_id = 0
        self.squares = [Coords(x, y) for y in range(self.height) for x in range(self.width)]
        self.events = EventManager()

        self.encounter.setup_map(self)
        self.heroes_activated = 0
        
        # the general condition handlers
        setup_condition_listeners(self)

    def get_next_figure_id(self):
        figure_id = self.next_figure_id
        self.next_figure_id += 1
        return figure_id
    
    def nearest_empty_square(self, coords):
        visited = set()
        queue = [(coords, 0)]
        while queue:
            current, dist = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            # Check if the square is open
            if not self.cell_contents[current.y][current.x]:
                return current
            # Add neighbors to the queue
            for neighbor in self.get_horver_neighbors(current) + self.get_diag_neighbors(current):
                if neighbor not in visited:
                    # Optionally, you can check for impassible_types here if needed
                    queue.append((neighbor, dist + 1))
        return None
    
    def add_figure(self, figure, coords, on_occupied='fail'):
        figure.map = self
        figure.id = self.get_next_figure_id()
        self.figures.append(figure)
        if not self.coords_in_bounds(coords):
            raise ValueError("Coordinates out of bounds")
        current_contents = self.cell_contents[coords.y][coords.x]
        blocking = [c for c in current_contents if c.figure_type != FigureType.MARKER]
        if blocking:
            if on_occupied == 'displace':
                assert(len(blocking) == 1), "There should be at most one blocking figure in a square"
                # Displace the existing figure
                existing_figure = blocking[0]
                nearest_empty = self.nearest_empty_square(coords)
                if nearest_empty is None:
                    raise ValueError("No empty square found to displace the figure")
                self.move_figure(existing_figure, nearest_empty)
            elif on_occupied == 'replace':
                self.remove_figure(existing_figure)
            elif on_occupied == 'find_empty':
                nearest_empty = self.nearest_empty_square(coords)
                if nearest_empty is None:
                    raise ValueError("No empty square found to place the figure")
                coords = nearest_empty
            elif on_occupied == 'colocate':
                pass
            elif on_occupied == 'fail':
                raise ValueError("Square is occupied by another figure")
            else:
                raise ValueError(f"Unknown on_occupied action: {on_occupied}")


        self.cell_contents[coords.y][coords.x].append(figure)
        self.positions[figure] = coords

        if figure.figure_type == FigureType.HERO:
            for ability in figure.hero.abilities:
                if ability.setup_routine is not None:
                    ability.setup_routine(figure.hero)

        self.events.trigger("figure_added", figure=figure, coords=coords)
        
    def remove_figure(self, figure):
        if figure not in self.figures:
            raise ValueError("Figure not found on the map")
        coords = self.positions[figure]
        self.cell_contents[coords.y][coords.x].remove(figure)
        del self.positions[figure]
        self.figures.remove(figure)
        self.events.trigger("figure_removed", figure=figure, coords=Coords(x=coords.x, y=coords.y))

    def move_figure(self, figure, coords):
        if figure not in self.figures:
            raise ValueError("Figure not found on the map")
        old_coords = self.positions[figure]
        self.cell_contents[old_coords.y][old_coords.x].remove(figure)
        self.cell_contents[coords.y][coords.x].append(figure)
        self.positions[figure] = coords

    def get_figure_position(self, figure):
        return self.positions.get(figure)

    def get_square_contents(self, coords):
        return self.cell_contents[coords.y][coords.x]
    
    def get_figure_by_id(self, figure_id):
        for figure in self.figures:
            if figure.id == figure_id:
                return figure
        return None
    
    def get_figures_by_type(self, figure_type):
        return [figure for figure in self.figures if figure.figure_type == figure_type]

    def get_figures_by_name(self, name):
        return [figure for figure in self.figures if figure.name == name]

    def get_figures_within_distance(self, coords, distance, impassible_types=None):
        return [figure for figure in self.figures if self.distance_between(coords, figure.position, impassible_types=None) <= distance]

    def get_squares_within_distance(self, coords, distance, impassible_types=None):
        return [square for square in self.squares if self.distance_between(coords, square, impassible_types=impassible_types) <= distance]

    def coords_in_bounds(self, coords):
        return 0 <= coords.x < self.width and 0 <= coords.y < self.height

    def get_horver_neighbors(self, coords):
        x, y = coords.x, coords.y
        neighbors = [c for c in [
            Coords(x+1, y),
            Coords(x-1, y),
            Coords(x, y+1),
            Coords(x, y-1),
        ] if self.coords_in_bounds(c)]
        return neighbors

    def get_diag_neighbors(self, coords):
        x, y = coords.x, coords.y
        neighbors = [c for c in [
            Coords(x+1, y+1),
            Coords(x-1, y+1),
            Coords(x+1, y-1),
            Coords(x-1, y-1),
        ] if self.coords_in_bounds(c)]
        return neighbors

    def can_move_diagonal(self, from_coords, to_coords, impassible_types):
        dx = to_coords.x - from_coords.x
        dy = to_coords.y - from_coords.y
        
        assert abs(dx) == 1 and abs(dy) == 1, \
            f"can_move_diagonal called with non-diagonal coordinates: from {from_coords} to {to_coords}"
        
        adj1 = Coords(to_coords.x, from_coords.y)
        adj2 = Coords(from_coords.x, to_coords.y)
        for adj in [adj1, adj2]:
            if not self.coords_in_bounds(adj):
                return False
            if any(
                figure.figure_type in impassible_types
                for figure in self.cell_contents[adj.y][adj.x]
            ):
                return False
        return True
        
    def bfs(self, start, impassible_types=None, max_distance=None, target=None, return_paths=False):
        if impassible_types is None:
            impassible_types = set()
        visited = {}
        came_from = {}
        queue = [(start, 0)]
        while queue:
            current, cost = queue.pop(0)
            if current in visited:
                continue
            visited[current] = cost
            if max_distance is not None and cost > max_distance:
                continue
            if target is not None and current == target:
                break
            for neighbor in self.get_horver_neighbors(current):
                if (
                    neighbor not in visited
                    and (neighbor == target or not any(figure.figure_type in impassible_types for figure in self.cell_contents[neighbor.y][neighbor.x]))
                ):
                    queue.append((neighbor, cost + 1))
                    if neighbor not in came_from:
                        came_from[neighbor] = current
            for neighbor in self.get_diag_neighbors(current):
                if (
                    neighbor not in visited
                    and self.can_move_diagonal(current, neighbor, impassible_types)
                    and (neighbor == target or not any(figure.figure_type in impassible_types for figure in self.cell_contents[neighbor.y][neighbor.x]))
                ):
                    queue.append((neighbor, cost + 1.5))
                    if neighbor not in came_from:
                        came_from[neighbor] = current
        # Floor all costs to match D&D rounding
        costs = {coord: int(cost) for coord, cost in visited.items()}
        if return_paths:
            return costs, came_from
        return costs

    def squares_within_distance(self, pos1, impassible_types, distance):
        return set(self.bfs(pos1, impassible_types, max_distance=distance).keys())

    def squares_within_cone(self, origin, target, distance, impassible_types=None, angle_threshold = math.sqrt(2) / 2):
        dx = target.x - origin.x
        dy = target.y - origin.y
        hypot = math.sqrt(dx**2 + dy**2)
        dx, dy = (dx / hypot, dy / hypot)  # Normalize the direction vector

        in_range = self.squares_within_distance(origin, impassible_types, distance)
        cone_squares = set()
        for square in in_range:
            if square == origin:
                continue
            v_x, v_y = square.x - origin.x, square.y - origin.y
            hypot = math.sqrt(v_x**2 + v_y**2)
            v_x, v_y = (v_x / hypot, v_y / hypot) # should never be 0
            dot = dx * v_x + dy * v_y
            if dot >= angle_threshold:
                cone_squares.add(square)
        return cone_squares

    def distance_between(self, pos1, pos2, impassible_types=None):
        visited = self.bfs(pos1, impassible_types, target=pos2)
        return visited.get(pos2, float('inf'))
    
    def knock_back(self, figure, knockback_origin, knockback_distance):
        # Determine direction vector (dx, dy)
        dx = figure.position.x - knockback_origin.x
        dy = figure.position.y - knockback_origin.y
        if dx == 0 and dy == 0:
            raise(Exception("Cannot knock back figure from its own position"))

        remaining_distance = knockback_distance
        diagonal_move_expensive = False
        collided = False
        while remaining_distance > 0 and not collided:
            valid_knockbacks = []
            if dx != 0 and dy != 0 and (remaining_distance > 1 or (not diagonal_move_expensive)):
                valid_knockbacks.append((dx, dy))  # Diagonal move
            if abs(dx) > abs(dy) or (abs(dx) == abs(dy) and diagonal_move_expensive and remaining_distance == 1):
                valid_knockbacks.append((dx, 0))
            if abs(dy) > abs(dx) or (abs(dx) == abs(dy) and diagonal_move_expensive and remaining_distance == 1):
                valid_knockbacks.append((0, dy))

            if not valid_knockbacks:
                raise ValueError("No valid knockback directions found")
            
            knockback = random.choice(valid_knockbacks)
            knockback_dx = knockback[0]
            knockback_dy = knockback[1]


            new_x = figure.position.x + knockback_dx
            new_y = figure.position.y + knockback_dy
            new_coords = Coords(new_x, new_y)


            # Check map bounds
            if not self.coords_in_bounds(new_coords):
                collided = True

            # Check for impassible terrain or figures
            # you can move through an ally but not knockback through them
            impassible_types = {FigureType.OBSTACLE, FigureType.HERO, FigureType.BOSS, FigureType.MINION}
            if any(f.figure_type in impassible_types for f in self.cell_contents[new_y][new_x]):
                collided = True
            
            if not collided:
                self.move_figure(figure, new_coords)
                move_cost = 1
                if knockback_dx != 0 and knockback_dy != 0:
                    if diagonal_move_expensive:
                        move_cost = 2
                        diagonal_move_expensive = False
                    else:
                        diagonal_move_expensive = True
                remaining_distance -= move_cost

        # If not moved full distance, take damage for each remaining step
        figure.take_damage(physical_damage=remaining_distance, elemental_damage=0, damage_source="Knockback collision", reduce_health=True)

    def deal_damage(self, source, target, physical_damage, elemental_damage, reduce_health=True):
        damage_taken = target.take_damage(physical_damage, elemental_damage, damage_source=source, reduce_health=reduce_health)
        return damage_taken

    def begin_hero_turn(self):
        self.events.trigger("hero_turn_start")
        self.heroes_activated = 0
        for hero_figure in self.get_figures_by_type(FigureType.HERO):
            hero_figure.hero.reset_turn()
            self.events.trigger("start_figure_action", figure=hero_figure)
    
    def end_hero_turn(self):
        for hero_figure in self.get_figures_by_type(FigureType.HERO):
            self.events.trigger("end_figure_action", figure=hero_figure)
        self.events.trigger("hero_turn_end")

    def execute_boss_turn(self):
        self.events.trigger("boss_turn_start")
        for boss in self.get_figures_by_type([FigureType.BOSS, FigureType.MINION]):
            self.events.trigger("start_action", figure=boss)

        self.encounter.perform_boss_turn()

        for boss in self.get_figures_by_type([FigureType.BOSS, FigureType.MINION]):
            self.events.trigger("end_figure_action", figure=boss)
        self.events.trigger("boss_turn_end")