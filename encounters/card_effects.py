from figure import Figure, FigureType
from coords import Coords
from encounters.enemy_ai import basic_action, choose_target_hero, make_enemy_move
import figure
from game_events import GameEvent
import random
from game_conditions import Condition

def sael_biting_cold_listener(figure, roll, damage_type, map):
    counters = map.encounter.biting_cold_counters
    if damage_type == 'Elemental' and figure.figure_type == FigureType.HERO and roll <= counters:
        figure.current_health -= 1
        figure.add_condition(Condition.SLOWED, 1)

def sael_avalanche_knockback_listener(figure, damage_taken, damage_source, map):
    if figure.figure_type == FigureType.HERO and isinstance(damage_source, Figure) and damage_source.figure_type == FigureType.BOSS:
        map.knock_back(figure, damage_source.position, damage_taken['physical_damage_taken'])


def sael_avalanche_crush(map, sael):
    listener_id = map.events.register(
        GameEvent.DAMAGE_TAKEN, 
        lambda figure, damage_taken, damage_source, **kwargs: sael_avalanche_knockback_listener(figure, damage_taken, damage_source, map)
    )
    
    for _ in range(3):
        basic_action(map, sael)
    
    map.events.deregister(GameEvent.DAMAGE_TAKEN, listener_id)

def sael_frozen_servants(map, sael):
    basic_action(map, sael)

    map.add_figure(Figure("Frost Elemental", FigureType.MINION, health=5, physical_def=5, elemental_def=4, move=1), Coords(0,2)) 
    map.add_figure(Figure("Frost Elemental", FigureType.MINION, health=5, physical_def=5, elemental_def=4, move=1), Coords(10,2)) 
    
def storm_shield_pulse(map, sael):
    print('Storm Shield pulse from Sa\'el!')
    heroes = map.get_figures_by_type(FigureType.HERO)
    for hero in heroes:
        map.deal_damage(sael, hero, physical_damage=0, elemental_damage=1)

def sael_storm_shield(map, sael):
    basic_action(map, sael)
    sael.add_condition(Condition.SHIELDED, 10, incremental=True)
    storm_shield_pulse(map, sael)

    listener_id = None  # placeholder

    def shield_listener():
        if sael.get_condition(Condition.SHIELDED):
            storm_shield_pulse(map, sael)
        else:
            map.events.deregister(GameEvent.BOSS_TURN_START, listener_id)

    listener_id = map.events.register(GameEvent.BOSS_TURN_START, shield_listener)
    
def sael_icicle_shards(map, sael):
    basic_action(map, sael)

    heroes = map.get_figures_by_type(FigureType.HERO)
    print(heroes)
    for hero in heroes:
        dmg_dealt = map.deal_damage(sael, hero, physical_damage=1, elemental_damage=0)
        if dmg_dealt > 0:
            hero.add_condition(Condition.BLEED, hero.max_health - hero.current_health)

def sael_chilling_winds(map, sael):
    basic_action(map, sael)

    heroes = map.get_figures_by_type(FigureType.HERO)
    for hero in heroes:
        dmg_dealt = map.deal_damage(sael, hero, physical_damage=0, elemental_damage=1)
        if dmg_dealt > 0:
            hero.add_condition(Condition.SLOWED, 1)

def sael_frost_tomb(map, sael):
    basic_action(map, sael)
    target_hero = random.choice(map.get_figures_by_type(FigureType.HERO))
    tomb = Figure("Frost Tomb", FigureType.MINION, health=5, physical_def=5, elemental_def=4, move=0, cell_color="#0D126B")
    map.add_figure(tomb, target_hero.position, on_occupied='colocate')
    target_hero.targetable = False
    target_hero.add_condition(Condition.STUNNED, 99)

    def tomb_damage_listener():
        map.deal_damage(tomb, target_hero, physical_damage=0, elemental_damage=1)

    def tomb_freedom_listener(figure):
        if figure == tomb:
            target_hero.targetable = True
            target_hero.remove_condition(Condition.STUNNED)
            map.events.deregister("figure_death", listener_id)

    # tomb regularly damages, you are freed when it dies
    map.events.register(GameEvent.HERO_TURN_START, lambda: tomb_damage_listener())
    map.events.register(GameEvent.BOSS_TURN_START, lambda: tomb_damage_listener())
    listener_id = map.events.register(GameEvent.FIGURE_DEATH, lambda figure: tomb_freedom_listener(figure))

def sael_whirlwind(map, sael):
    target_hero = choose_target_hero(map, sael)
    make_enemy_move(map, enemy=sael, player=target_hero)
    for hero in map.get_figures_by_type(FigureType.HERO):
        if map.distance_between(sael.position, hero.position) <= 2:
            map.deal_damage(sael, hero, physical_damage=sael.physical_dmg, elemental_damage=sael.elemental_dmg + 1)

def sael_frost_breath(map, sael):
    target_hero = choose_target_hero(map, sael)
    make_enemy_move(map, enemy=sael, player=target_hero)

    if map.distance_between(sael.position, target_hero.position) <= sael.attack_range:
        target_area = map.squares_within_cone(origin=sael.position, target=target_hero.position, distance=4)
    else:
        target_area = []

    for hero in map.get_figures_by_type(FigureType.HERO):
        if hero.position in target_area:
            map.deal_damage(sael, hero, physical_damage=0, elemental_damage=3)
    return

def sael_ice_collapse_listener(map):
    markers = map.get_figures_by_name("Incoming Ice")
    assert(len(markers) == 2), "There should be exactly two Incoming Ice markers"
    for marker in markers:
        for hero in map.get_figures_by_type(FigureType.HERO):
            if hero.position == marker.position:
                map.deal_damage(marker, hero, physical_damage=4, elemental_damage=4)
            if map.distance_between(marker.position, hero.position) == 1:
                map.deal_damage(marker, hero, physical_damage=1, elemental_damage=1)

    for marker in markers:
        fallen_ice = Figure("ICEFALL", FigureType.OBSTACLE, cell_color="#B8860B")
        map.add_figure(fallen_ice, marker.position, on_occupied='displace')
        map.remove_figure(marker)

def sael_ice_collapse(map, sael):
    basic_action(map, sael)
    target_heroes = random.sample(map.get_figures_by_type(FigureType.HERO), 2)
    for hero in target_heroes:
        incoming_ice = Figure("Incoming Ice", FigureType.MARKER, cell_color="#FFB6C1")
        map.add_figure(incoming_ice, hero.position, on_occupied='colocate')
    
    # Create a one-time listener that deregisters itself after running
    def one_time_collapse_listener():
        sael_ice_collapse_listener(map)
        map.events.deregister(GameEvent.BOSS_TURN_START, listener_id)
    
    listener_id = map.events.register(GameEvent.BOSS_TURN_START, one_time_collapse_listener)

# When Biting Cold is applied:

def sael_eye_of_the_storm(map, sael):
    basic_action(map, sael)

    # not sure where this lives, pending figuring out how that affects elemental damage
    map.encounter.biting_cold_counters += 1
    
    heroes = map.get_figures_by_type(FigureType.HERO)
    heroes.sort(key=lambda h: map.get_distance(sael.position, h.position), reverse=True)  # from furthest to closest
    for hero in heroes:
        # doesn't actually deal damage, just knocks back.
        dmg_dealt = map.deal_damage(sael, hero, physical_damage=0, elemental_damage=3, reduce_health=False)
        if dmg_dealt > 0:
            map.knock_back(hero, dmg_dealt)