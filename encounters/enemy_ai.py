import random
import math
from figure import FigureType
from game_targeting import TargetingContext

def pythagorean_distance(pos1, pos2):
    """Calculate straight-line pythagorean distance between two positions."""
    return math.sqrt((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2)

def choose_target_hero(map, figure):
    closest_heroes = []
    closest_distance = float('inf')
    for hero_figure in map.get_figures_by_type(FigureType.HERO, {TargetingContext.ENEMY_TARGETABLE: True}):        
        distance = map.distance_between(figure.position, hero_figure.position, figure.impassible_types)
        priority = hero_figure.targeting_parameters[TargetingContext.TARGETING_PRIORITY]
        print(f"DEBUG:   {hero_figure.name} at distance {distance}, targeting priority {priority}")
        
        if distance < closest_distance:
            closest_distance = distance
            closest_heroes = [hero_figure]
        elif distance == closest_distance:
            closest_heroes.append(hero_figure)

    if not closest_heroes:  # somehow there are no targetable heroes on the map.  Perhaps the last hero is untargetable due to an ability?
        return None

    # randomize first...
    random.shuffle(closest_heroes)
    # ...then sort by targeting priority, so the one with the highest priority is targeted first
    closest_heroes.sort(key=lambda h: h.targeting_parameters[TargetingContext.TARGETING_PRIORITY], reverse=True)

    target_hero = closest_heroes[0]  
    return(target_hero)


def basic_action(map, figure):
    # make the basic decision for a figure.
    # This will in essence target the closest hero, move towards them until within range, and then attack.
    print(f"Enemy AI: {figure.name} is taking a basic action.") 
    target_hero = choose_target_hero(map, figure)
    if not target_hero:
        print(f"No targetable heroes found for {figure.name}.")
        return 0 # no targetable heroes, so do nothing
    print(f"Enemy AI: {figure.name} is targeting {target_hero.name} at position {target_hero.position}.")

    make_enemy_move(map, enemy=figure, player=target_hero)
    
    if map.distance_between(figure.position, target_hero.position) <= figure.attack_range:
        dmg_dealt = map.deal_damage(figure, target_hero, figure.physical_dmg, figure.elemental_dmg)
        return dmg_dealt

    return 0

def make_enemy_move(game_map, enemy, player, move_range=None, impassible_types=None):
    if move_range is None:
        move_range = enemy.move
    if impassible_types is None:
        impassible_types = enemy.impassible_types
    
    # Get all adjacent squares to the player
    adjacent_squares = game_map.get_horver_neighbors(player.position) + game_map.get_diag_neighbors(player.position)
    
    # Find the closest square(s) by pathfinding distance
    min_dist = float('inf')
    best_candidates = []
    
    for square in adjacent_squares:
        dist = game_map.distance_between(enemy.position, square, impassible_types)
        if dist < min_dist:
            min_dist = dist
            best_candidates = [square]
        elif dist == min_dist:
            best_candidates.append(square)
    
    # Tiebreak by pythagorean distance to player (naturally prefers orthogonal over diagonal)
    best_square = min(best_candidates, key=lambda sq: pythagorean_distance(sq, player.position))
    
    print(f"Enemy AI: {enemy.name} at {enemy.position} moving towards {best_square} near player at {player.position}.")

    # Use BFS with pythagorean distance tiebreaker to ensure predictable pathing
    path_costs, path_came_from = game_map.bfs(
        enemy.position, 
        impassible_types, 
        target=best_square, 
        return_paths=True,
        tiebreaker_target=player.position
    )
    
    # Walk backwards from best_square to find the square we can reach with our movement
    current = best_square
    while path_costs[current] > move_range:
        current = path_came_from[current]
    
    destination = current
    print(f"Enemy AI: {enemy.name} will move to {destination}.")

    # Build path from enemy position to destination
    path_to_walk = []
    current = destination
    while current != enemy.position:
        path_to_walk.append(current)
        current = path_came_from[current]
    path_to_walk.reverse()  # reverse the path to walk from start to end

    for square in path_to_walk:
        game_map.move_figure(enemy, square)
    