from figure import Figure, FigureType
from game_targeting import TargetingContext
from game_events import GameEvent
from game_conditions import Condition
from encounters.enemy_ai import choose_target_hero, make_enemy_move
import random

def como_hellfire_listener(figure, damage_taken, **kwargs):
    """Hellfire passive: Heroes taking 3+ elemental damage suffer Burning 3"""
    if figure.figure_type == FigureType.HERO and damage_taken['elemental_damage_taken'] >= 3:
        figure.add_condition(Condition.BURN, 3, incremental=True)
        print(f"{figure.name} suffers Burning 3 from Hellfire!")

def como_basic_action(map, como, encounter=None):
    """Comorragh's basic action - changes based on current form"""
    if encounter and encounter.current_form == 'champion':
        como_form_champion_attack(map, como)
    elif encounter and encounter.current_form == 'inferno':
        como_form_inferno_attack(map, como)
    else:
        # Default form - standard basic action
        from encounters.enemy_ai import basic_action
        basic_action(map, como)

def como_meteor_falls_listener(map, encounter):
    """Handle meteor impacts when they fall"""
    markers = map.get_figures_by_name("Incoming Meteor")
    
    # If no markers exist, another listener already processed them
    if not markers:
        return
    
    for marker in markers:
        for hero in map.get_figures_by_type(FigureType.HERO, {TargetingContext.AOE_ABILITY_HITTABLE: True}):
            if hero.position == marker.position:
                map.deal_damage(marker, hero, physical_damage=3, elemental_damage=3)
            if map.distance_between(marker.position, hero.position) == 1:
                map.deal_damage(marker, hero, physical_damage=0, elemental_damage=1)

    for marker in markers:
        lava_tile = Figure("LAVA", FigureType.MARKER, cell_color="#ff4500", hazard_damage=1)
        map.add_figure(lava_tile, marker.position, on_occupied='colocate')
        
        # Spawn Doomguard if Call of the Legion was used
        if encounter.spawn_doomguard_on_meteor:
            doomguard = Figure("Doomguard", FigureType.MINION, 
                             health=6, physical_def=4, elemental_def=4, 
                             move=1, physical_dmg=2, elemental_dmg=0, attack_range=1)
            map.add_figure(doomguard, marker.position, on_occupied='colocate')
            print(f"A Doomguard spawns at {marker.position}!")
            encounter.spawn_doomguard_on_meteor = False  # Reset flag after spawning
        
        map.remove_figure(marker)

def como_aim_meteor(map, encounter):
    """Aim a meteor at one random targetable hero"""
    target_heroes = map.get_figures_by_type(FigureType.HERO, {TargetingContext.ENEMY_TARGETABLE: True})
    if not target_heroes:
        return
    
    # Filter out heroes who already have a meteor aimed at them
    heroes_without_meteors = []
    for hero in target_heroes:
        figures_at_position = map.get_square_contents(hero.position)
        has_meteor = any(fig.name == "Incoming Meteor" for fig in figures_at_position)
        if not has_meteor:
            heroes_without_meteors.append(hero)
    
    # Choose from heroes without meteors if possible, otherwise any hero
    if heroes_without_meteors:
        hero = random.choice(heroes_without_meteors)
    else:
        hero = random.choice(target_heroes)
    
    incoming_meteor = Figure("Incoming Meteor", FigureType.MARKER, cell_color="#FFD700")
    map.add_figure(incoming_meteor, hero.position, on_occupied='colocate')

# Basic Cards

def como_call(map):
    """Call of the Legion - Next meteor spawns a Doomguard"""
    como = map.get_figures_by_type(FigureType.BOSS)[0]
    como_basic_action(map, como, map.encounter)
    
    # Set flag so next meteor spawns a Doomguard
    map.encounter.spawn_doomguard_on_meteor = True
    print("Call of the Legion: The next meteor will spawn a Doomguard!")

def como_flames_of_the_pit(map):
    """Flames of the Pit - Heroes take 1 elemental damage per nearby lava tile"""
    como = map.get_figures_by_type(FigureType.BOSS)[0]
    como_basic_action(map, como, map.encounter)
    
    lava_tiles = map.get_figures_by_name("LAVA")
    heroes = map.get_figures_by_type(FigureType.HERO, {TargetingContext.AOE_ABILITY_HITTABLE: True})
    
    for hero in heroes:
        damage_count = 0
        for lava in lava_tiles:
            if map.distance_between(hero.position, lava.position) <= 1:
                damage_count += 1
        
        if damage_count > 0:
            map.deal_damage(map.get_figures_by_type(FigureType.BOSS)[0], hero, 
                          physical_damage=0, elemental_damage=damage_count)

# Special Cards

def como_meteor_shower(map):
    """Meteor Shower - Summon 2 additional meteors this turn"""
    como = map.get_figures_by_type(FigureType.BOSS)[0]
    como_basic_action(map, como, map.encounter)
    
    # Aim 2 extra meteors (in addition to the one aimed at end of turn)
    for _ in range(2):
        como_aim_meteor(map, map.encounter)

def como_visage(map):
    """Visage of Terror - Heroes must flee 3 spaces or take damage"""
    como = map.get_figures_by_type(FigureType.BOSS)[0]
    como_basic_action(map, como, map.encounter)
    
    # Mark that we need to aim meteor after fleeing completes
    map.visage_needs_meteor_aim = True
    
    # Get all heroes and sort by distance from Comorragh (furthest first)
    heroes = map.get_figures_by_type(FigureType.HERO, {TargetingContext.ENEMY_TARGETABLE: True})
    heroes_with_distance = [(hero, map.distance_between(hero.position, como.position)) for hero in heroes]
    heroes_with_distance.sort(key=lambda x: x[1], reverse=True)
    
    # Store flee data for processing
    if not hasattr(map, 'visage_flee_queue'):
        map.visage_flee_queue = []
    
    # Process each hero and determine flee options
    for hero, _ in heroes_with_distance:
        # Get all valid flee squares with path info
        flee_info = map.move_away_squares(hero, como)
        
        if not flee_info:
            # Can't flee at all - take 3 damage
            hero.lose_health(3, source=como)
            print(f"{hero.name} cannot flee and takes 3 damage!")
            continue
        
        # Find maximum distance achievable within hero's movement
        max_flee_distance = 0
        for coords, info in flee_info.items():
            if info['move_cost'] <= hero.move:
                max_flee_distance = max(max_flee_distance, info['move_cost'])
        
        # Determine damage and valid destinations
        if max_flee_distance >= 3:
            # Can flee full 3 spaces - no damage
            damage = 0
            valid_destinations = {coords: info for coords, info in flee_info.items() if info['move_cost'] == 3}
        else:
            # Can't flee full 3 spaces - take damage for difference
            damage = int(3 - max_flee_distance)
            valid_destinations = {coords: info for coords, info in flee_info.items() if info['move_cost'] == max_flee_distance}
        
        if damage > 0:
            hero.lose_health(damage, source=como)
            print(f"{hero.name} can only flee {max_flee_distance} spaces and takes {damage} damage!")
        
        # Store flee data for UI to process
        if valid_destinations:
            map.visage_flee_queue.append({
                'hero': hero,
                'destinations': valid_destinations
            })
    
    # Process the flee queue via UI
    como_visage_process_next_flee(map)

def como_visage_process_next_flee(map):
    """Process the next hero in the Visage of Terror flee queue"""
    if not hasattr(map, 'visage_flee_queue') or not map.visage_flee_queue:
        # Queue is empty, cleanup and continue
        if hasattr(map, 'visage_flee_queue'):
            delattr(map, 'visage_flee_queue')
        
        # Now that all heroes have fled, aim the meteor at their new positions
        if hasattr(map, 'visage_needs_meteor_aim') and map.visage_needs_meteor_aim:
            como_aim_meteor(map, map.encounter)
            map.visage_needs_meteor_aim = False
        return
    
    # Get next hero to flee
    flee_data = map.visage_flee_queue.pop(0)
    hero_figure = flee_data['hero']
    valid_destinations = flee_data['destinations']  # Dict with path info
    
    # Get UI reference from map (needs to be set when UI is created)
    if not hasattr(map, 'ui'):
        print("Warning: Map doesn't have UI reference, cannot process Visage flee movement")
        return
    
    ui = map.ui
    
    # Create a custom callback that processes the next hero after this one moves
    def flee_move_callback(coords):
        # Execute the movement with path
        if coords != hero_figure.position:
            path = valid_destinations[coords]['path']
            map.move_figure(hero_figure, coords, path=path)
        ui.select_mode = None
        ui.move_paths = None
        ui.draw_map()
        ui.draw_hero_panel()
        
        # Process next hero in queue
        como_visage_process_next_flee(map)
    
    # Set up the UI for flee movement
    ui.select_mode = 'visage_flee'
    ui.valid_choices = list(valid_destinations.keys())
    ui.move_paths = valid_destinations  # Store path info for potential display
    ui.select_message = f"Visage of Terror: {hero_figure.hero.name} must flee 3 spaces from Comorragh or take 3 damage"
    ui.select_color = "lightgreen"
    ui.select_cmd = flee_move_callback
    ui.draw_map()
    print(f"{hero_figure.name} must choose a flee destination!")

def como_rite(map):
    """Rite of Flame - Move to furthest lava, gain shields, heal while shielded"""
    como = map.get_figures_by_type(FigureType.BOSS)[0]
    como_basic_action(map, como, map.encounter)
    
    # Find lava tile furthest from any hero
    lava_tiles = map.get_figures_by_name("LAVA")
    heroes = map.get_figures_by_type(FigureType.HERO)
    
    if lava_tiles and heroes:
        best_lava = None
        max_min_distance = -1
        
        for lava in lava_tiles:
            # Find minimum distance from this lava to any hero
            min_distance = min(map.distance_between(lava.position, hero.position) for hero in heroes)
            if min_distance > max_min_distance:
                max_min_distance = min_distance
                best_lava = lava
        
        if best_lava:
            map.move_figure(como, best_lava.position)
    
    # Gain 10 shield counters
    como.add_condition(Condition.SHIELDED, 10, incremental=True)
    
    # Set up healing listener
    listener_id = None  # placeholder
    
    def rite_heal_listener():
        shield_count = como.get_condition(Condition.SHIELDED)
        if shield_count:
            heal_amount = shield_count // 2
            if heal_amount > 0:
                como.heal(heal_amount, source=como)
        else:
            # No more shields, deregister
            map.events.deregister(GameEvent.BOSS_TURN_START, listener_id)
    
    listener_id = map.events.register(GameEvent.BOSS_TURN_START, rite_heal_listener)

# Form abilities - these switch forms and apply defense changes

def como_form_champion(map):
    """Enter Form of the Champion - Changes basic attack to line attack"""
    como = map.get_figures_by_type(FigureType.BOSS)[0]
    encounter = map.encounter
    
    # Remove old form bonuses if any
    if encounter.current_form == 'inferno':
        como.physical_def += 1  # Remove inferno penalty
        como.elemental_def -= 1  # Remove inferno bonus
    
    # Apply champion bonuses
    encounter.current_form = 'champion'
    como.physical_def -= 1  # +1 becomes lower threshold
    como.elemental_def += 1  # -1 becomes higher threshold
    print(f"Comorragh enters Form of the Champion! Physical Def: {como.physical_def}, Elemental Def: {como.elemental_def}")

def como_form_champion_attack(map, como):
    """Attack while in Form of the Champion - 5 physical damage in a line"""
    target_hero = choose_target_hero(map, como)
    if not target_hero:
        return
    
    make_enemy_move(map, enemy=como, player=target_hero)
    
    if map.distance_between(como.position, target_hero.position) <= como.attack_range:
        # Deal damage to primary target
        map.deal_damage(como, target_hero, physical_damage=5, elemental_damage=0)
        
        # Hit targets in a line behind the primary target
        # Get squares in a narrow cone (10 degrees = very tight line) behind target
        # angle_threshold = cos(10°) ≈ 0.985
        target_area = map.squares_within_cone(
            origin=como.position, 
            target=target_hero.position, 
            distance=4, 
            angle_threshold=0.995
        )
        
        for hero in map.get_figures_by_type(FigureType.HERO, {TargetingContext.AOE_ABILITY_HITTABLE: True}):
            if hero != target_hero and hero.position in target_area:
                map.deal_damage(como, hero, physical_damage=5, elemental_damage=0)

def como_form_inferno(map):
    """Enter Form of the Inferno - Changes basic attack to AOE attack"""
    como = map.get_figures_by_type(FigureType.BOSS)[0]
    encounter = map.encounter
    
    # Remove old form bonuses if any
    if encounter.current_form == 'champion':
        como.physical_def += 1  # Remove champion bonus
        como.elemental_def -= 1  # Remove champion penalty
    
    # Apply inferno bonuses
    encounter.current_form = 'inferno'
    como.physical_def += 1  # -1 becomes higher threshold
    como.elemental_def -= 1  # +1 becomes lower threshold
    print(f"Comorragh enters Form of the Inferno! Physical Def: {como.physical_def}, Elemental Def: {como.elemental_def}")

def como_form_inferno_attack(map, como):
    """Attack while in Form of the Inferno - 2/2 damage plus AOE splash"""
    target_hero = choose_target_hero(map, como)
    if not target_hero:
        return
    
    make_enemy_move(map, enemy=como, player=target_hero)
    
    if map.distance_between(como.position, target_hero.position) <= como.attack_range:
        # Deal damage to primary target
        map.deal_damage(como, target_hero, physical_damage=2, elemental_damage=2)
        
        # Deal 1 elemental to other heroes within range 1 of target
        for hero in map.get_figures_by_type(FigureType.HERO, {TargetingContext.AOE_ABILITY_HITTABLE: True}):
            if hero != target_hero and map.distance_between(target_hero.position, hero.position) <= 1:
                map.deal_damage(como, hero, physical_damage=0, elemental_damage=1)

def como_form_swap(map):
    """Swap Forms between Champion and Inferno"""
    como = map.get_figures_by_type(FigureType.BOSS)[0]
    encounter = map.encounter
    
    if encounter.current_form == 'champion':
        como_form_inferno(map)
    else:
        como_form_champion(map)