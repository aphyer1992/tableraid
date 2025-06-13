from figure import Figure, FigureType
from coords import Coords
from .enemy_ai import basic_action, choose_target_hero, make_enemy_move
import random

def sael_biting_cold_listener(figure, roll, damage_type, map):
    counters = map.encounter.biting_cold_counters
    if damage_type == 'Elemental' and figure.figure_type == FigureType.HERO and roll <= counters:
        figure.current_health -= 1
        figure.add_condition("Slowed", 1)

def sael_avalanche_knockback_listener(figure, damage_taken, damage_type, damage_source, map):
    if damage_type == 'Physical' and figure.figure_type == FigureType.HERO and damage_source.figure_type == FigureType.BOSS:
        map.knock_back(figure, damage_source.position, damage_taken)


def sael_avalanche_crush(map, sael):
    listener_id = map.events.register(
        "damage_taken", 
        lambda figure, damage_taken, damage_type, damage_source: sael_avalanche_knockback_listener(figure, damage_taken, damage_type, damage_source, map)
    )
    
    for i in range(3):
        basic_action(map, sael)
    
    map.events.deregister("damage_taken", listener_id)

def sael_frozen_servants(map, sael):
    basic_action(map, sael)

    map.add_figure(Figure("Frost Elemental", FigureType.MINION, health=5, physical_def=5, elemental_def=4), Coords(0,2)) 
    map.add_figure(Figure("Frost Elemental", FigureType.MINION, health=5, physical_def=5, elemental_def=4), Coords(10,2)) 
    


def storm_shield_pulse(map, sael):
    heroes = map.get_figures_by_type(FigureType.HERO)
    for hero in heroes:
        map.deal_damage(sael, hero, physical_damage=0, elemental_damage=1, reduce_hp=True)

def storm_shield_listener(map, sael, listener):
    if sael.get_condition("Shielded"):
        storm_shield_pulse(map)
    else:
        map.events.deregister("boss_turn_start", listener)

def sael_storm_shield(map, sael):
    basic_action(map, sael)
    sael.add_condition("Shielded", 10, incremental=True)
    storm_shield_pulse(map, sael)

    listener_id = None  # placeholder

    def shield_listener():
        if sael.get_condition("Shielded"):
            storm_shield_pulse(map, sael)
        else:
            map.events.deregister("boss_turn_start", listener_id)

    listener_id = map.events.register("boss_turn_start", shield_listener)
    
def sael_icicle_shards(map, sael):
    basic_action(map, sael)

    heroes = map.get_figures_by_type(FigureType.HERO)
    print(heroes)
    for hero in heroes:
        dmg_dealt = map.deal_damage(sael, hero, physical_damage=1, elemental_damage=0)
        if dmg_dealt > 0:
            hero.add_condition("Bleed", hero.max_health - hero.current_health)

def sael_chilling_winds(map, sael):
    basic_action(map, sael)

    heroes = map.get_figures_by_type(FigureType.HERO)
    for hero in heroes:
        dmg_dealt = map.deal_damage(sael, hero, physical_damage=0, elemental_damage=1)
        if dmg_dealt > 0:
            hero.add_condition("Slowed", 1)

def sael_frost_tomb(map, sael):
    basic_action(map, sael)
    target_hero = random.choice(map.get_figures_by_type(FigureType.HERO))
    tomb = Figure("Frost Tomb", FigureType.MARKER, health=5, physical_def=5, elemental_def=4, move=0)
    map.add_figure(tomb, target_hero.position, on_occupied='colocate')
    target_hero.targetable = False
    target_hero.add_condition("Stunned", 99)

    def tomb_damage_listener(figure):
        if figure == target_hero:
            map.deal_damage(tomb, target_hero, physical_damage=0, elemental_damage=1)

    def tomb_freedom_listener(figure):
        if figure == tomb:
            target_hero.targetable = True
            target_hero.remove_condition("Stunned")
            map.events.deregister("figure_death", listener_id)

    # tomb regularly damages, you are freed when it dies
    map.events.register("start_turn", lambda figure: tomb_damage_listener(figure))
    map.events.register("end_turn", lambda figure: tomb_damage_listener(figure))
    listener_id = map.events.register("figure_death", lambda figure: tomb_freedom_listener(figure))

def sael_whirlwind(map, sael):
    target_hero = choose_target_hero(map, sael)
    make_enemy_move(map, sael, target_hero, sael.move)
    for hero in map.get_figures_by_type(FigureType.HERO):
        if map.distance_between(sael.position, hero.position) <= 2:
            map.deal_damage(sael, hero, physical_damage=sael.physical_dmg, elemental_damage=sael.elemental_dmg + 1)

def sael_frost_breath(map, sael):
    target_hero = choose_target_hero(map, sael)
    make_enemy_move(map, sael, target_hero, sael.move)

    if map.distance_between(sael.position, target_hero.position) <= sael.attack_range:
        target_area = map.get_cone(sael.position, target_hero.position, sael.attack_range)

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
        map.remove_figure(marker)
        map.add_figure(Figure("Fallen Ice", FigureType.OBSTACLE), marker.position, on_occupied='displace')
    map.events.deregister("boss_turn_start", sael_ice_collapse_listener)

def sael_ice_collapse(map, sael):
    basic_action(map, sael)
    target_heroes = random.sample(map.get_figures_by_type(FigureType.HERO), 2)
    for hero in target_heroes:
        map.add_figure(Figure("Incoming Ice", FigureType.MARKER), hero.position)
    map.events.register("boss_turn_start", lambda: sael_ice_collapse_listener(map))

# When Biting Cold is applied:

def sael_eye_of_the_storm(map, sael):
    basic_action(map, sael)

    # not sure where this lives, pending figuring out how that affects elemental damage
    map.encounter.biting_cold_counters += 1
    
    heroes = map.get_figures_by_type(FigureType.HERO)
    heroes.sort(key=lambda h: map.get_distance(sael.position, h.position), reverse=True)  # from furthest to closest
    for hero in heroes:
        # doesn't actually deal damage, just knocks back.
        dmg_dealt = map.deal_damage(sael, hero, physical_damage=0, elemental_damage=3, reduce_hp=False)
        if dmg_dealt > 0:
            map.knock_back(hero, dmg_dealt)