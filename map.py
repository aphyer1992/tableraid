from coords import Coords
from figure import FigureType
from events import EventManager
from game_events import GameEvent
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
        self.current_round = 1
        
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
                assert(len(blocking) == 1), "There should be at most one blocking figure in a square"
                existing_figure = blocking[0]
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

        self.events.trigger(GameEvent.FIGURE_ADDED, figure=figure, coords=coords)
        
    def remove_figure(self, figure):
        if figure not in self.figures:
            raise ValueError("Figure not found on the map")
        coords = self.positions[figure]
        self.cell_contents[coords.y][coords.x].remove(figure)
        del self.positions[figure]
        self.figures.remove(figure)
        self.events.trigger(GameEvent.FIGURE_REMOVED, figure=figure, coords=Coords(x=coords.x, y=coords.y))

    def move_figure(self, figure, coords, path=None):
        """
        Move a figure to new coordinates, optionally along a specified path.
        
        Args:
            figure: The figure to move
            coords: Destination coordinates
            path: Optional list of coordinates representing the path (includes start and end)
                  If provided, figure will take hazard damage along the path
        """
        if figure not in self.figures:
            raise ValueError("Figure not found on the map")
        old_coords = self.positions[figure]
        
        # DEBUG: Print path info
        print(f"DEBUG: move_figure called for {figure.name} from {old_coords} to {coords}, path={path}")
        
        # If a path is provided, apply hazard damage
        if path is not None:
            total_hazard_damage = 0
            # Skip the starting position, check damage on all squares moved through
            for step in path[1:]:
                hazard_damage = self._get_hazard_damage(step, figure)
                print(f"DEBUG: Checking hazard at {step}: {hazard_damage}")
                if hazard_damage > 0:
                    total_hazard_damage += hazard_damage
            
            # Apply accumulated hazard damage as elemental damage with defense rolls
            if total_hazard_damage > 0:
                # Use a generic hazard source (first hazard figure found, or None)
                hazard_source = None
                for step in path[1:]:
                    for fig in self.cell_contents[step.y][step.x]:
                        if fig.hazard_damage > 0:
                            hazard_source = fig
                            break
                    if hazard_source:
                        break
                
                damage_dealt = self.deal_damage(hazard_source, figure, physical_damage=0, elemental_damage=total_hazard_damage)
                if damage_dealt > 0:
                    print(f"{figure.name} takes {damage_dealt} elemental damage from hazards!")
        
        # Execute the movement
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
    
    def get_figures_by_type(self, figure_type, targeting_filters=None):
        """
        Get figures by type, optionally filtered by targeting parameters.
        
        Args:
            figure_type: FigureType or list of FigureTypes to filter by
            targeting_filters: Dict of {TargetingContext: expected_value} to filter by
                              Only figures where ALL filters match will be returned
        
        Returns:
            List of figures matching the criteria
        """
        # Handle both single type and list of types
        if isinstance(figure_type, list):
            figures = [figure for figure in self.figures if figure.figure_type in figure_type]
        else:
            figures = [figure for figure in self.figures if figure.figure_type == figure_type]
        
        # Apply targeting parameter filters if provided
        if targeting_filters:
            filtered_figures = []
            for figure in figures:
                matches_all_filters = True
                for context, expected_value in targeting_filters.items():
                    if figure.targeting_parameters[context] != expected_value:
                        matches_all_filters = False
                        break
                if matches_all_filters:
                    filtered_figures.append(figure)
            return filtered_figures
        
        return figures

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
        
        # Check if at least one adjacent square is passable
        if not any(figure.figure_type in impassible_types for figure in self.cell_contents[adj1.y][adj1.x]):
            return True
        if not any(figure.figure_type in impassible_types for figure in self.cell_contents[adj2.y][adj2.x]):
            return True
        return False

    def bfs(self, start, impassible_types=None, max_distance=None, target=None, return_paths=False, tiebreaker_target=None):
        if impassible_types is None:
            impassible_types = set()
        visited = {}
        came_from = {}
        queue = [(start, 0.0)]
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
                    elif tiebreaker_target is not None:
                        # Use pythagorean distance as tiebreaker
                        current_parent = came_from[neighbor]
                        current_dist = math.sqrt((current_parent.x - tiebreaker_target.x) ** 2 + (current_parent.y - tiebreaker_target.y) ** 2)
                        new_dist = math.sqrt((current.x - tiebreaker_target.x) ** 2 + (current.y - tiebreaker_target.y) ** 2)
                        if new_dist < current_dist:
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
                    elif tiebreaker_target is not None:
                        # Use pythagorean distance as tiebreaker
                        current_parent = came_from[neighbor]
                        current_dist = math.sqrt((current_parent.x - tiebreaker_target.x) ** 2 + (current_parent.y - tiebreaker_target.y) ** 2)
                        new_dist = math.sqrt((current.x - tiebreaker_target.x) ** 2 + (current.y - tiebreaker_target.y) ** 2)
                        if new_dist < current_dist:
                            came_from[neighbor] = current
        # Floor all costs to match D&D rounding
        costs = {coord: int(cost) for coord, cost in visited.items()}
        if return_paths:
            return costs, came_from
        return costs

    def bfs_with_hazards(self, start, impassible_types=None, max_distance=None, figure=None):
        """
        Enhanced BFS that tracks optimal paths considering both movement cost and hazard damage.
        
        Args:
            start: Starting coordinates
            impassible_types: Set of FigureTypes that block movement
            max_distance: Maximum movement distance
            figure: The figure moving (used to determine hazard damage)
            
        Returns:
            dict mapping each reachable coord to:
            {
                'move_cost': int,        # Movement points needed
                'hazard_damage': int,    # Elemental damage from hazards (e.g., lava)
                'path': [Coords],        # List of coordinates from start to destination (inclusive)
            }
        """
        if impassible_types is None:
            impassible_types = set()
        
        # Track best path to each square: (move_cost, hazard_damage, path)
        best_paths = {}
        
        # Priority queue: (hazard_damage, move_cost, counter, current_pos, path)
        # Prioritize by hazard_damage first (minimize), then move_cost (minimize)
        # counter is used as tiebreaker to avoid comparing Coords objects
        import heapq
        counter = 0
        queue = [(0, 0.0, counter, start, [start])]
        
        while queue:
            current_hazard, current_cost, _, current, path = heapq.heappop(queue)
            
            # Skip if we've already found a better path to this square
            if current in best_paths:
                existing = best_paths[current]
                # Better = less hazard damage, or same hazard but less movement
                if (existing['hazard_damage'] < current_hazard or 
                    (existing['hazard_damage'] == current_hazard and existing['move_cost'] <= current_cost)):
                    continue
            
            # Skip if this destination exceeds max distance
            if max_distance is not None and current_cost > max_distance:
                continue
            
            # Record this path
            best_paths[current] = {
                'move_cost': int(current_cost),
                'hazard_damage': current_hazard,
                'path': path.copy()
            }
            
            # Don't expand further if we've hit max distance
            if max_distance is not None and current_cost >= max_distance:
                continue
            
            # Explore neighbors
            for neighbor in self.get_horver_neighbors(current):
                if not any(fig.figure_type in impassible_types for fig in self.cell_contents[neighbor.y][neighbor.x]):
                    new_cost = current_cost + 1
                    new_hazard = current_hazard + self._get_hazard_damage(neighbor, figure)
                    new_path = path + [neighbor]
                    counter += 1
                    heapq.heappush(queue, (new_hazard, new_cost, counter, neighbor, new_path))
            
            for neighbor in self.get_diag_neighbors(current):
                if (self.can_move_diagonal(current, neighbor, impassible_types) and
                    not any(fig.figure_type in impassible_types for fig in self.cell_contents[neighbor.y][neighbor.x])):
                    new_cost = current_cost + 1.5
                    new_hazard = current_hazard + self._get_hazard_damage(neighbor, figure)
                    new_path = path + [neighbor]
                    counter += 1
                    heapq.heappush(queue, (new_hazard, new_cost, counter, neighbor, new_path))
        
        return best_paths
    
    def _get_hazard_damage(self, coords, figure):
        """
        Calculate hazard damage for a figure moving into a square.
        Checks all figures in the square for their hazard_damage property.
        """
        total_damage = 0
        for fig in self.cell_contents[coords.y][coords.x]:
            total_damage += fig.hazard_damage
        return total_damage

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
    
    def move_away_squares(self, fleeing_figure, threat_figure):
        """
        Returns all squares where fleeing_figure can move while fleeing from threat_figure.
        
        Fleeing logic: You can flee along any horizontal/vertical/diagonal direction within 
        45 degrees of 'directly away from the threat'. This gives 2-3 valid directions 
        depending on whether you're on a cardinal/diagonal line or not.
        
        Args:
            fleeing_figure: The figure trying to flee
            threat_figure: The figure being fled from
            
        Returns:
            dict mapping Coords to path info (same format as bfs_with_hazards):
            {
                coords: {
                    'move_cost': int,
                    'hazard_damage': int,
                    'path': [Coords]
                }
            }
        """
        flee_pos = fleeing_figure.position
        threat_pos = threat_figure.position
        
        # Calculate direction vector from threat to fleeing figure
        dx = flee_pos.x - threat_pos.x
        dy = flee_pos.y - threat_pos.y
        
        if dx == 0 and dy == 0:
            return {}  # Can't flee if on same square
        
        # The 8 possible movement directions (dx, dy)
        directions = [
            (1, 0),   # E
            (1, 1),   # NE
            (0, 1),   # N
            (-1, 1),  # NW
            (-1, 0),  # W
            (-1, -1), # SW
            (0, -1),  # S
            (1, -1)   # SE
        ]
        
        # Calculate which directions are valid for fleeing
        valid_directions = []
        for dir_dx, dir_dy in directions:
            dot_product = dir_dx * dx + dir_dy * dy
            
            if dot_product > 0:
                away_magnitude = math.sqrt(dx*dx + dy*dy)
                dir_magnitude = math.sqrt(dir_dx*dir_dx + dir_dy*dir_dy)
                cos_angle = dot_product / (away_magnitude * dir_magnitude)
                
                # cos(45°) ≈ 0.707, so accept directions within 45 degrees
                if cos_angle >= 0.707:
                    valid_directions.append((dir_dx, dir_dy))
        
        # Use hazard-aware BFS but only allow movement in valid flee directions
        max_move = fleeing_figure.move
        best_paths = {}
        
        import heapq
        counter = 0
        queue = [(0, 0.0, counter, flee_pos, [flee_pos])]
        
        while queue:
            current_hazard, current_cost, _, current, path = heapq.heappop(queue)
            
            # Skip if we've already found a better path to this square
            if current in best_paths:
                existing = best_paths[current]
                if (existing['hazard_damage'] < current_hazard or 
                    (existing['hazard_damage'] == current_hazard and existing['move_cost'] <= current_cost)):
                    continue
            
            # Record this path
            best_paths[current] = {
                'move_cost': int(current_cost),
                'hazard_damage': current_hazard,
                'path': path.copy()
            }
            
            # Don't expand if we've hit max distance
            if current_cost >= max_move:
                continue
            
            # Only explore neighbors in valid flee directions
            for dir_dx, dir_dy in valid_directions:
                neighbor = Coords(current.x + dir_dx, current.y + dir_dy)
                
                if not self.coords_in_bounds(neighbor):
                    continue
                
                # Check if passable
                blocking = [f for f in self.cell_contents[neighbor.y][neighbor.x] 
                           if f.figure_type != FigureType.MARKER]
                if blocking:
                    continue
                
                # Calculate movement cost (diagonal vs orthogonal)
                is_diagonal = (dir_dx != 0 and dir_dy != 0)
                move_cost = 1.5 if is_diagonal else 1.0
                
                new_cost = current_cost + move_cost
                new_hazard = current_hazard + self._get_hazard_damage(neighbor, fleeing_figure)
                new_path = path + [neighbor]
                counter += 1
                heapq.heappush(queue, (new_hazard, new_cost, counter, neighbor, new_path))
        
        # Remove starting position from results
        if flee_pos in best_paths:
            del best_paths[flee_pos]
        
        return best_paths
    
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
                valid_knockbacks.append((1 if dx > 0 else -1, 1 if dy > 0 else -1))  # Diagonal move
            if abs(dx) > abs(dy) or (abs(dx) == abs(dy) and diagonal_move_expensive and remaining_distance == 1):
                valid_knockbacks.append((1 if dx > 0 else -1, 0))
            if abs(dy) > abs(dx) or (abs(dx) == abs(dy) and diagonal_move_expensive and remaining_distance == 1):
                valid_knockbacks.append((0, 1 if dy > 0 else -1))
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
            else:
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
        if remaining_distance > 0:
            figure.take_damage(physical_damage=remaining_distance, elemental_damage=0, damage_source="Knockback collision")

    def deal_damage(self, source, target, physical_damage, elemental_damage, reduce_health=True):
        damage_taken = target.take_damage(physical_damage, elemental_damage, damage_source=source, reduce_health=reduce_health)
        return damage_taken

    def begin_hero_turn(self):
        self.events.trigger(GameEvent.HERO_TURN_START)
        self.heroes_activated = 0
        for hero_figure in self.get_figures_by_type(FigureType.HERO):
            hero_figure.hero.reset_turn()
            self.events.trigger(GameEvent.START_FIGURE_ACTION, figure=hero_figure)
    
    def end_hero_turn(self):
        for hero_figure in self.get_figures_by_type(FigureType.HERO):
            self.events.trigger(GameEvent.END_FIGURE_ACTION, figure=hero_figure)
        self.events.trigger(GameEvent.HERO_TURN_END)

    def execute_boss_turn(self):
        self.events.trigger(GameEvent.BOSS_TURN_START)
        for figure in self.get_figures_by_type([FigureType.BOSS, FigureType.MINION]):
            self.events.trigger(GameEvent.START_FIGURE_ACTION, figure=figure)

        self.encounter.perform_boss_turn()

        for figure in self.get_figures_by_type([FigureType.BOSS, FigureType.MINION]):
            self.events.trigger(GameEvent.END_FIGURE_ACTION, figure=figure)
        self.events.trigger(GameEvent.BOSS_TURN_END)
        
        # Increment round counter at the end of boss turn
        self.current_round += 1