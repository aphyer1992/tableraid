"""Helper functions for combat actions shared between heroes, enemies, and card effects"""

from figure import FigureType
from game_targeting import TargetingContext


def aoe_attack(attacker, ui_or_map, range, physical_damage=0, elemental_damage=0, 
               target_type=None, after_attack_callback=None):
    """Execute an attack against all valid targets within range
    
    Args:
        attacker: The attacking figure
        ui_or_map: UI object (for heroes) or map object (for enemies/cards)
        range: Maximum distance for targets
        physical_damage: Physical damage to deal (default: 0)
        elemental_damage: Elemental damage to deal (default: 0)
        target_type: FigureType to target (default: enemies for heroes, heroes for enemies)
        after_attack_callback: Optional callback(attacker, target, damage_dealt, ui) to run after each attack
    
    Examples:
        # Hero ability: Deal 2 elemental damage to all enemies within range 3
        aoe_attack(figure, ui, range=3, elemental_damage=2)
        
        # Enemy ability: Deal 3 elemental to all heroes within range 1
        aoe_attack(minion, map, range=1, elemental_damage=3, target_type=FigureType.HERO)
    """
    # Determine if we have a UI or map object
    has_ui = hasattr(ui_or_map, 'execute_attack')
    map_obj = ui_or_map if not has_ui else attacker.map
    
    # Determine target type if not specified
    if target_type is None:
        if attacker.figure_type == FigureType.HERO:
            # Heroes target enemies (BOSS/MINION)
            target_types = [FigureType.BOSS, FigureType.MINION]
        else:
            # Enemies target heroes
            target_types = [FigureType.HERO]
    else:
        target_types = [target_type] if not isinstance(target_type, list) else target_type
    
    # Get figures in range
    in_range = map_obj.get_figures_within_distance(attacker.position, range)
    
    # Filter targets
    targets = []
    for f in in_range:
        if f.figure_type in target_types:
            # For hero abilities, also check AOE_ABILITY_HITTABLE
            if has_ui and f.targeting_parameters.get(TargetingContext.AOE_ABILITY_HITTABLE, True):
                targets.append(f)
            elif not has_ui:
                targets.append(f)
    
    # Execute attacks
    for target in targets:
        if has_ui:
            ui_or_map.execute_attack(
                attacker, 
                target, 
                physical_damage=physical_damage, 
                elemental_damage=elemental_damage,
                after_attack_callback=after_attack_callback
            )
        else:
            map_obj.deal_damage(
                attacker,
                target,
                physical_damage=physical_damage,
                elemental_damage=elemental_damage
            )


def aoe_attack_adjacent(attacker, map, physical_damage=0, elemental_damage=0, 
                        target_type=None, diagonal=True):
    """Attack all adjacent targets (convenience wrapper for aoe_attack with range=1)
    
    Args:
        attacker: The attacking figure
        map: The game map
        physical_damage: Physical damage to deal (default: 0)
        elemental_damage: Elemental damage to deal (default: 0)
        target_type: FigureType to target (default: HERO for enemies, BOSS/MINION for heroes)
        diagonal: Include diagonal neighbors (default: True, currently unused - D&D distance includes all 8 neighbors at range 1)
    
    Examples:
        # Enemy hits all adjacent heroes for 2 physical damage
        aoe_attack_adjacent(axe_fiend, map, physical_damage=2)
        
        # Card effect: Flamecallers deal 3 elemental to adjacent heroes
        aoe_attack_adjacent(flamecaller, map, elemental_damage=3, target_type=FigureType.HERO)
    """
    aoe_attack(attacker, map, range=1, physical_damage=physical_damage, 
               elemental_damage=elemental_damage, target_type=target_type)


def aoe_attack_all_heroes(attacker, map, physical_damage=0, elemental_damage=0):
    """Attack ALL heroes on the map (common for global effects)
    
    Args:
        attacker: The attacking figure
        map: The game map  
        physical_damage: Physical damage to deal (default: 0)
        elemental_damage: Elemental damage to deal (default: 0)
    
    Example:
        # Flamecaller at 3+ counters damages all heroes
        aoe_attack_all_heroes(flamecaller, map, elemental_damage=1)
    """
    heroes = map.get_figures_by_type(FigureType.HERO)
    for hero in heroes:
        map.deal_damage(attacker, hero, physical_damage=physical_damage, elemental_damage=elemental_damage)
    
    return heroes
