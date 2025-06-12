import random
from figure import FigureType

def choose_target_hero(map, figure):
    closest_heroes = []
    closest_distance = float('inf')
    for hero_figure in map.get_figures_by_type(FigureType.HERO):
        distance = map.distance_between(figure.position, hero_figure.position, figure.impassible_types)
        if distance < closest_distance:
            closest_distance = distance
            closest_heroes = [hero_figure]
        elif distance == closest_distance:
            closest_heroes.append(hero_figure)

    if not closest_heroes:  # somehow there are no targetable heroes on the map.  Perhaps the last hero is untargetable due to an ability?
        return None

    # randomize first...
    random.shuffle(closest_heroes)
    # ...then sort by taunt level, so the one with the highest taunt is targeted first
    closest_heroes.sort(key=lambda h: h.get_effect('taunt_level', 0), reverse=True)  # positive means they are taunting, negative the reverse

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

    make_enemy_move(figure, target_hero, map, figure.move, figure.impassible_types)
    
    if map.distance_between(figure.position, target_hero.position) <= figure.attack_range:
        dmg_dealt = map.deal_damage(figure, target_hero, figure.physical_dmg, figure.elemental_dmg)
        return dmg_dealt

    return 0

def make_enemy_move(enemy, player, game_map, move_range, impassible_types):
    # Get all orthogonally adjacent squares to the player
    preferred_targets = game_map.get_horver_neighbors(player.position)
    other_targets = game_map.get_diag_neighbors(player.position)
    # Find the closest preferred target
    min_dist = float('inf')
    best_square = None
    for square in preferred_targets:
        dist = game_map.distance_between(enemy.position, square, impassible_types)
        if dist < min_dist:
            min_dist = dist
            best_square = square
    
    for square in other_targets:
        dist = game_map.distance_between(enemy.position, square, impassible_types)
        if dist < min_dist:
            min_dist = dist
            best_square = square
    
    path_costs, path_came_from = game_map.bfs(enemy.position, impassible_types, target=best_square, return_paths=True)
    while path_costs[best_square] >= move_range:
        best_square = path_came_from[best_square]
    
    path_to_walk = []
    while best_square != enemy.position:
        path_to_walk.append(best_square)
        best_square = path_came_from[best_square]
    path_to_walk.reverse()  # reverse the path to walk from start to end

    for square in path_to_walk:
        game_map.move_figure(enemy, square)
    