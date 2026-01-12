from figure import Figure, FigureType
from game_conditions import Condition
from game_events import GameEvent
from game_targeting import TargetingContext
from event_helpers import register_temporary_listener, schedule_callback, modify_stat_temporarily
from combat_helpers import aoe_attack_adjacent
from coords import Coords
import random

def create_slow_on_damage_listener(minion_types):
    """Create a listener that slows heroes damaged by specified minion types
    
    Args:
        minion_types: String or list of strings of minion type values to check
    """
    if isinstance(minion_types, str):
        minion_types = [minion_types]
    
    def listener(figure, damage_taken, damage_source, **kwargs):
        if (damage_source and 
            damage_source.figure_type == FigureType.MINION and
            damage_source.get_effect('minion_type') in minion_types and
            figure.figure_type == FigureType.HERO):
            
            total_damage = damage_taken.get('physical_damage_taken', 0) + damage_taken.get('elemental_damage_taken', 0)
            if total_damage > 0:
                print(f"{figure.name} is Slowed by {damage_source.name}!")
                figure.add_condition(Condition.SLOWED, 1)
    
    return listener

def across_suffering(map):
    """Suffering - Ash Walker attacks splash to heroes within 2 spaces"""
    from encounters.encounter_across import CharrMinionType
    
    # Set splash effect on all Ash Walkers
    ash_walkers = []
    for minion in map.get_figures_by_type(FigureType.MINION):
        if minion.get_effect('minion_type') == CharrMinionType.ASH_WALKER.value:
            minion.add_effect('splash_damage', 2, overwrite=True)  # Splash range of 2
            ash_walkers.append(minion)
    
    # Clear the effect at end of boss turn
    def cleanup_splash(**kwargs):
        for walker in ash_walkers:
            if walker.current_health > 0:
                walker.add_effect('splash_damage', None, overwrite=True)
    
    schedule_callback(map, GameEvent.BOSS_TURN_END, cleanup_splash)

def across_inferno(map):
    """Inferno - Flamecallers deal 3 elemental to adjacent heroes"""
    from encounters.encounter_across import CharrMinionType
    
    for minion in map.get_figures_by_type(FigureType.MINION):
        if minion.get_effect('minion_type') == CharrMinionType.FLAMECALLER.value:
            print(f"{minion.name} unleashes an inferno!")
            aoe_attack_adjacent(minion, map, elemental_damage=3, target_type=FigureType.HERO)

def across_ignite_arrows(map):
    """Ignite Arrows - Stalkers get counters and splash damage"""
    from encounters.encounter_across import CharrMinionType
    
    # Add power counter to each Stalker and mark them with ignite_arrows effect
    stalkers_with_ignite = []
    for minion in map.get_figures_by_type(FigureType.MINION):
        if minion.get_effect('minion_type') == CharrMinionType.STALKER.value:
            # Add power counter
            current_counters = minion.get_effect('power_counters', 0)
            minion.add_effect('power_counters', current_counters + 1, overwrite=True)
            print(f"{minion.name} gains a power counter from Ignite Arrows!")
            
            # Mark with ignite_arrows - this persists until death
            minion.add_effect('ignite_arrows', True, overwrite=True)
            stalkers_with_ignite.append(minion)
    
    # Create a damage listener that applies splash damage when Stalkers attack
    def ignite_arrows_listener(attacker, target, damage_taken, **kwargs):
        # Only trigger for Stalkers with ignite_arrows effect
        if (attacker and 
            attacker.figure_type == FigureType.MINION and
            attacker.get_effect('minion_type') == CharrMinionType.STALKER.value and
            attacker.get_effect('ignite_arrows') and
            target.figure_type == FigureType.HERO):
            
            # Find heroes adjacent to the target
            adjacent_positions = (map.get_horver_neighbors(target.position) + 
                                map.get_diag_neighbors(target.position))
            
            for pos in adjacent_positions:
                for figure in map.get_square_contents(pos):
                    if figure.figure_type == FigureType.HERO and figure != target:
                        print(f"{attacker.name}'s ignited arrow splashes to {figure.name}!")
                        map.deal_damage(attacker, figure, physical_damage=0, elemental_damage=1)
    
    # Register the listener (persists beyond this turn)
    map.events.register(GameEvent.DAMAGE_TAKEN, ignite_arrows_listener)

def across_riposte(map):
    """Riposte - Heroes attacking adjacent Blade Storms take 1 physical damage"""
    from encounters.encounter_across import CharrMinionType
    
    def riposte_listener(attacker, target, damage_taken, **kwargs):
        # Check if a hero attacked an adjacent Blade Storm
        if (attacker and target and
            attacker.figure_type == FigureType.HERO and
            target.figure_type == FigureType.MINION and
            target.get_effect('minion_type') == CharrMinionType.BLADE_STORM.value and
            map.distance_between(attacker.position, target.position) <= 1):
            
            print(f"{target.name} ripostes against {attacker.name}!")
            map.deal_damage(target, attacker, physical_damage=1, elemental_damage=0)
    
    # Active during hero turn only
    register_temporary_listener(map, GameEvent.DAMAGE_TAKEN, riposte_listener, GameEvent.HERO_TURN_END)

def across_pin_down(map):
    """Pin Down - Heroes damaged by Stalkers are Slowed"""
    listener = create_slow_on_damage_listener('stalker')
    register_temporary_listener(map, GameEvent.DAMAGE_TAKEN, listener, GameEvent.BOSS_TURN_END)

def across_whirling_axe(map):
    """Whirling Axe - Axe Fiends attack all heroes within 2 spaces"""
    from encounters.encounter_across import CharrMinionType
    
    # Set extended range on all Axe Fiends
    axe_fiends = []
    for minion in map.get_figures_by_type(FigureType.MINION):
        if minion.get_effect('minion_type') == CharrMinionType.AXE_FIEND.value:
            minion.add_effect('extended_range', 2, overwrite=True)
            axe_fiends.append(minion)
    
    # Clear the effect at end of boss turn
    def cleanup_extended_range(**kwargs):
        for fiend in axe_fiends:
            if fiend.current_health > 0:  # Only if still alive
                fiend.add_effect('extended_range', None, overwrite=True)
    
    schedule_callback(map, GameEvent.BOSS_TURN_END, cleanup_extended_range)

def across_hamstring(map):
    """Hamstring - Heroes damaged by Blade Storm or Axe Fiend are Slowed"""
    listener = create_slow_on_damage_listener(['blade_storm', 'axe_fiend'])
    register_temporary_listener(map, GameEvent.DAMAGE_TAKEN, listener, GameEvent.BOSS_TURN_END)

def across_whirling_defense(map):
    """Whirling Defense - Stalkers get +2 defense against ranged attacks during hero turn"""
    from encounters.encounter_across import CharrMinionType
    
    def defense_boost_listener(figure, roll_data, damage_type, damage_source, **kwargs):
        # Check if a Stalker is defending against a non-adjacent attack
        if (figure and damage_source and
            figure.figure_type == FigureType.MINION and
            figure.get_effect('minion_type') == CharrMinionType.STALKER.value and
            damage_source.figure_type == FigureType.HERO and
            map.distance_between(figure.position, damage_source.position) > 1):
            
            # Boost defense roll by 2
            original_defense = figure.physical_def if damage_type == 'Physical' else figure.elemental_def
            roll_data["defense_value"] = original_defense + 2
            print(f"{figure.name} whirls defensively! (+2 defense against ranged attack)")
    
    # Active during hero turn only
    register_temporary_listener(map, GameEvent.DEFENSE_ROLL, defense_boost_listener, GameEvent.HERO_TURN_END)

def across_faintheartedness(map):
    """Faintheartedness - Heroes damaged by Ash Walkers are Slowed"""
    listener = create_slow_on_damage_listener('ash_walker')
    register_temporary_listener(map, GameEvent.DAMAGE_TAKEN, listener, GameEvent.BOSS_TURN_END)

def across_bestial_force(map):
    """Bestial Force - Heroes damaged are knocked back by damage amount"""
    
    def knockback_listener(figure, damage_taken, damage_source, **kwargs):
        # Check if a hero was damaged by a Charr enemy
        if (figure.figure_type == FigureType.HERO and 
            isinstance(damage_source, Figure) and
            damage_source.figure_type in [FigureType.MINION, FigureType.BOSS]):
            
            # Calculate total damage
            total_damage = damage_taken.get('physical_damage_taken', 0) + damage_taken.get('elemental_damage_taken', 0)
            
            if total_damage > 0:
                print(f"{figure.name} is knocked back {total_damage} spaces by {damage_source.name}!")
                map.knock_back(figure, damage_source.position, total_damage)
    
    # Active for boss turn only
    register_temporary_listener(map, GameEvent.DAMAGE_TAKEN, knockback_listener, GameEvent.BOSS_TURN_END)

def across_shieldwall(map):
    """Shieldwall - Blade Storms and Axe Fiends get +2 defense, don't move"""
    from encounters.encounter_across import CharrMinionType
    
    shieldwall_minions = []
    for minion in map.get_figures_by_type(FigureType.MINION):
        if minion.get_effect('minion_type') in [CharrMinionType.BLADE_STORM.value, CharrMinionType.AXE_FIEND.value]:
            # Boost defenses during hero turn
            modify_stat_temporarily(minion, {
                'physical_def': 2,
                'elemental_def': 2
            }, revert_event=GameEvent.HERO_TURN_END)
            
            # Prevent movement during boss turn by setting move to 0
            modify_stat_temporarily(minion, {
                'move': -minion.move  # Reduces move to 0
            }, revert_event=GameEvent.BOSS_TURN_END)
            
            shieldwall_minions.append(minion)
            print(f"{minion.name} forms a shieldwall! (+2 defenses, cannot move)")

def across_phoenix_fire(map):
    """Phoenix Fire - All Flamecallers heal to full health"""
    from encounters.encounter_across import CharrMinionType
    
    for minion in map.get_figures_by_type(FigureType.MINION):
        if minion.get_effect('minion_type') == CharrMinionType.FLAMECALLER.value:
            if minion.current_health < minion.max_health:
                healing = minion.max_health - minion.current_health
                minion.heal(healing, source=minion)
                print(f"{minion.name} is rejuvenated by Phoenix Fire! (healed {healing} HP)")


# ============================================================================
# BOSS ABILITY CARDS
# ============================================================================

def boss_firestorm(map, boss):
    """Firestorm - Mark hero locations, detonate next turn"""
    heroes = map.get_figures_by_type(FigureType.HERO)
    
    for hero in heroes:
        marker = Figure("Firestorm Marker", FigureType.MARKER, cell_color="#FF4500")
        map.add_figure(marker, hero.position, on_occupied='colocate')
        print(f"Firestorm marker placed at {hero.position}")
    
    # Detonate on next boss turn start
    def detonate_firestorm(**kwargs):
        markers = map.get_figures_by_name("Firestorm Marker")
        if not markers:
            return
        
        for marker in markers:
            # Deal 2 damage to heroes on marker position
            for figure in map.get_square_contents(marker.position):
                if figure.figure_type == FigureType.HERO:
                    print(f"Firestorm detonates on {figure.name}!")
                    map.deal_damage(marker, figure, physical_damage=0, elemental_damage=2)
            
            # Deal 1 damage to adjacent heroes
            adjacent_positions = map.get_horver_neighbors(marker.position) + map.get_diag_neighbors(marker.position)
            for pos in adjacent_positions:
                for figure in map.get_square_contents(pos):
                    if figure.figure_type == FigureType.HERO:
                        map.deal_damage(marker, figure, physical_damage=0, elemental_damage=1)
        
        # Remove markers
        for marker in markers:
            map.remove_figure(marker)
    
    schedule_callback(map, GameEvent.BOSS_TURN_START, detonate_firestorm)

def boss_incendiary_bonds(map, boss):
    """Incendiary Bonds - Attach to random hero, detonate next turn"""
    heroes = map.get_figures_by_type(FigureType.HERO, {TargetingContext.ENEMY_TARGETABLE: True})
    if not heroes:
        return
    
    target = random.choice(heroes)
    target.add_effect('incendiary_bonds', True, overwrite=True)
    print(f"{target.name} is bound by Incendiary Bonds!")
    
    # Detonate on next boss turn start
    def detonate_bonds(**kwargs):
        if target.current_health <= 0 or not target.get_effect('incendiary_bonds'):
            return
        
        # Clear effect
        target.add_effect('incendiary_bonds', None, overwrite=True)
        
        # Damage all heroes within range 2
        all_heroes = map.get_figures_by_type(FigureType.HERO)
        for hero in all_heroes:
            if map.distance_between(target.position, hero.position) <= 2:
                print(f"Incendiary Bonds detonate on {hero.name}!")
                map.deal_damage(boss, hero, physical_damage=0, elemental_damage=3)
                hero.add_condition(Condition.BURN, 3, incremental=False)
    
    schedule_callback(map, GameEvent.BOSS_TURN_START, detonate_bonds)

def boss_legion_commander(map, boss):
    """Legion Commander - Mark heroes and damage marked ones"""
    heroes = map.get_figures_by_type(FigureType.HERO, {TargetingContext.ENEMY_TARGETABLE: True})
    if not heroes:
        return
    
    # Prioritize unmarked heroes
    unmarked = [h for h in heroes if not h.get_effect('hunters_mark')]
    if unmarked:
        target = random.choice(unmarked)
    else:
        target = random.choice(heroes)
    
    target.add_effect('hunters_mark', True, overwrite=True)
    print(f"{target.name} receives a Hunter's Mark!")
    
    # Damage all marked heroes
    for hero in heroes:
        if hero.get_effect('hunters_mark'):
            print(f"{hero.name} takes damage from their Hunter's Mark!")
            map.deal_damage(boss, hero, physical_damage=1, elemental_damage=0)

def boss_conjure_flame(map, boss):
    """Conjure Flame - Boss's basic attack this turn gets +3 elemental and knockback"""
    
    # Set temporary effect on boss
    boss.add_effect('conjure_flame', True, overwrite=True)
    print(f"{boss.name} conjures flames for their next attack!")
    
    # Create knockback listener for this turn
    def conjure_flame_listener(figure, damage_taken, damage_source, **kwargs):
        if (damage_source == boss and 
            boss.get_effect('conjure_flame') and
            figure.figure_type == FigureType.HERO):
            
            total_damage = damage_taken.get('physical_damage_taken', 0) + damage_taken.get('elemental_damage_taken', 0)
            if total_damage > 0:
                print(f"{figure.name} is knocked back by conjured flames!")
                map.knock_back(figure, boss.position, total_damage)
    
    register_temporary_listener(map, GameEvent.DAMAGE_TAKEN, conjure_flame_listener, GameEvent.BOSS_TURN_END)
    
    # Clear effect at end of turn
    def clear_conjure_flame(**kwargs):
        boss.add_effect('conjure_flame', None, overwrite=True)
    
    schedule_callback(map, GameEvent.BOSS_TURN_END, clear_conjure_flame)
