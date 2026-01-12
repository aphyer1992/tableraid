"""Activation functions for Charr minions in the Across the Wall encounter"""

import random
from coords import Coords
from figure import FigureType
from combat_helpers import aoe_attack_all_heroes, aoe_attack
from encounters.enemy_ai import basic_action, choose_target_hero, make_enemy_move


def activate_blade_storms(encounter, map, minion_type_value):
    """Activate all Blade Storm minions - Bleed applied via listener when target drops below half HP"""
    for minion in map.get_figures_by_type(FigureType.MINION):
        if minion.get_effect('minion_type') == minion_type_value:
            basic_action(map, minion)


def activate_axe_fiends(encounter, map, minion_type_value):
    """Activate all Axe Fiend minions - AOE melee attack to all adjacent heroes (or extended range if card effect active)"""
    for minion in map.get_figures_by_type(FigureType.MINION):
        if minion.get_effect('minion_type') == minion_type_value:
            # Choose target and move
            target_hero = choose_target_hero(map, minion)
            if not target_hero:
                print(f"No targetable heroes found for {minion.name}.")
                continue
            
            make_enemy_move(map, enemy=minion, player=target_hero)
            
            # Check for extended range from card effect
            attack_range = minion.get_effect('extended_range', 1)
            
            # Attack all heroes within range
            aoe_attack(minion, map, range=attack_range, physical_damage=2, target_type=FigureType.HERO)
            
            if attack_range > 1:
                print(f"{minion.name} whirls their axe, hitting all heroes within {attack_range} spaces!")
            else:
                print(f"{minion.name} swings at adjacent heroes!")


def activate_ash_walkers(encounter, map, minion_type_value):
    """Activate all Ash Walker minions - Shadow Strike at full HP, Life Siphon when damaged"""
    for minion in map.get_figures_by_type(FigureType.MINION):
        if minion.get_effect('minion_type') == minion_type_value:
            # Choose target and move
            target_hero = choose_target_hero(map, minion)
            if not target_hero:
                print(f"No targetable heroes found for {minion.name}.")
                continue
            
            make_enemy_move(map, enemy=minion, player=target_hero)
            
            # Check if in range to attack
            if map.distance_between(minion.position, target_hero.position) <= minion.attack_range:
                # Determine damage based on health
                if minion.current_health == minion.max_health:
                    # Full HP: Shadow Strike - 3 elemental damage
                    print(f"{minion.name} uses Shadow Strike!")
                    damage_amount = 3
                    is_life_siphon = False
                else:
                    # Damaged: Life Siphon - 1 elemental damage, heal for damage dealt
                    print(f"{minion.name} uses Life Siphon!")
                    damage_amount = 1
                    is_life_siphon = True
                
                # Deal damage to primary target
                damage_dealt = map.deal_damage(minion, target_hero, physical_damage=0, elemental_damage=damage_amount)
                
                # Life Siphon healing
                if is_life_siphon and damage_dealt > 0:
                    minion.heal(damage_dealt, source=minion)
                    print(f"{minion.name} heals {damage_dealt} HP from Life Siphon!")
                
                # Check for splash damage effect (from Suffering card)
                splash_range = minion.get_effect('splash_damage')
                if splash_range:
                    nearby_heroes = map.get_figures_within_distance(target_hero.position, splash_range)
                    splash_targets = [h for h in nearby_heroes if h.figure_type == FigureType.HERO and h != target_hero]
                    
                    if splash_targets:
                        print(f"{minion.name}'s attack splashes to nearby heroes!")
                        for hero in splash_targets:
                            splash_damage = map.deal_damage(minion, hero, physical_damage=0, elemental_damage=damage_amount)
                            # Life Siphon also heals from splash damage
                            if is_life_siphon and splash_damage > 0:
                                minion.heal(splash_damage, source=minion)
                                print(f"{minion.name} heals {splash_damage} HP from Life Siphon splash!")


def activate_flamecallers(encounter, map, minion_type_value):
    """Activate all Flamecaller minions - Gain counter, deal 1 elemental to all heroes at 3+"""
    for minion in map.get_figures_by_type(FigureType.MINION):
        if minion.get_effect('minion_type') == minion_type_value:
            # Gain 1 power counter
            current_counters = minion.get_effect('power_counters', 0)
            current_counters += 1
            minion.add_effect('power_counters', current_counters, overwrite=True)
            print(f"{minion.name} gains a power counter (now at {current_counters})")
            
            # If at 3+ counters, deal 1 elemental damage to all heroes
            if current_counters >= 3:
                heroes = aoe_attack_all_heroes(minion, map, elemental_damage=1)
                if heroes:
                    print(f"{minion.name} unleashes flames at all heroes!")


def activate_stalkers(encounter, map, minion_type_value):
    """Activate all Stalker minions - 1 Physical damage at Range 4"""
    for minion in map.get_figures_by_type(FigureType.MINION):
        if minion.get_effect('minion_type') == minion_type_value:
            basic_action(map, minion)


def activate_scouts(encounter, map, minion_type_value):
    """Activate all Scout minions - Move to opposite edge, mark hero and respawn"""
    scouts_to_process = [m for m in map.get_figures_by_type(FigureType.MINION)
                        if m.get_effect('minion_type') == minion_type_value]
    
    for scout in scouts_to_process:
        direction = scout.get_effect('scout_direction')
        current_pos = scout.position
        
        # Determine target edge and movement
        if direction == 'right':
            target_x = 10
            dx = 1 if current_pos.x < target_x else 0
        else:  # direction == 'left'
            target_x = 0
            dx = -1 if current_pos.x > target_x else 0
        
        # Move up to 2 spaces towards target edge
        spaces_moved = 0
        while spaces_moved < scout.move and dx != 0:
            new_pos = Coords(current_pos.x + dx, current_pos.y)
            
            # Check if new position is blocked
            blocking_figures = [f for f in map.get_square_contents(new_pos) 
                               if f.figure_type != FigureType.MARKER]
            
            if not blocking_figures:
                map.move_figure(scout, new_pos)
                current_pos = new_pos
                spaces_moved += 1
                
                # Check if reached target edge
                if current_pos.x == target_x:
                    dx = 0  # Stop moving
            else:
                break  # Blocked, stop moving
        
        # Check if scout reached the opposite edge
        if current_pos.x == target_x:
            print(f"{scout.name} reaches the opposite edge!")
            
            # Find unmarked heroes
            heroes = map.get_figures_by_type(FigureType.HERO)
            unmarked_heroes = [h for h in heroes if not h.get_effect('marked')]
            
            if unmarked_heroes:
                # Mark a random unmarked hero
                target_hero = random.choice(unmarked_heroes)
                print(f"{scout.name} places a Hunter's Mark on {target_hero.name}!")
                encounter.mark_hero(target_hero)
            else:
                print(f"{scout.name} finds no unmarked heroes to mark.")
            
            # Spawn a new scout at the edge the original one exited from (opposite edge)
            if direction == 'right':
                spawn_x = 0  # Exited right, spawn on left
            else:
                spawn_x = 10  # Exited left, spawn on right
            
            spawn_coords = Coords(spawn_x, current_pos.y)
            print(f"A new {scout.name} appears at the opposite edge!")
            
            # Import here to avoid circular dependency
            from encounters.encounter_across import CharrMinionType
            encounter.spawn_minion(map, CharrMinionType.SCOUT, spawn_coords)
            
            # Remove the original scout
            map.remove_figure(scout)
