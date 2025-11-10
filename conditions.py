from game_events import GameEvent
from game_conditions import Condition

tick_down_at_start = [Condition.REGEN]  # conditions that tick down at start of turn
tick_down_at_start_hero = [Condition.REGEN, Condition.SHIELDED] # boss shields work differently
tick_down_at_end = [Condition.BURN, Condition.BLEED, Condition.STUNNED, Condition.SLOWED]  # conditions that tick down at end of turn

def condition_turn_end_listener(figure):
    print(f"DEBUG: condition_turn_end_listener called for {figure.name}, conditions: {figure.conditions}")
    for condition, duration in figure.conditions.items():
        if condition == Condition.BURN.value:
            print(f"DEBUG: Applying burn damage to {figure.name}")
            figure.map.deal_damage("Burning condition", figure, physical_damage=0, elemental_damage=1)
        elif condition == Condition.BLEED.value:
            print(f"DEBUG: Applying bleed damage to {figure.name}")
            figure.map.deal_damage("Bleeding condition", figure, physical_damage=1, elemental_damage=0)
        
        if any(condition == tick_condition.value for tick_condition in tick_down_at_end):
            figure.conditions[condition] = duration - 1
            print(f"DEBUG: Condition {condition} on {figure.name} ticks down to {figure.conditions[condition]}")
    
    # remove any that have timed out.
    figure.conditions = {k: v for k, v in figure.conditions.items() if v > 0}

def condition_turn_start_listener(figure):
    for condition, duration in figure.conditions.items():
        if condition == Condition.REGEN.value:
            figure.heal(1)
        
        tick_down = tick_down_at_start_hero if figure.figure_type.value == 'hero' else tick_down_at_start
        if any(condition == tick_condition.value for tick_condition in tick_down):
            figure.conditions[condition] = duration - 1
            print(f"DEBUG: Condition {condition} on {figure.name} ticks down to {figure.conditions[condition]}")

    # remove any that have timed out.
    figure.conditions = {k: v for k, v in figure.conditions.items() if v > 0}

def slow_listener(figure, move_data):
    if Condition.SLOWED.value in figure.conditions:
        move_data["value"] = min(move_data["value"], 1)

def shield_listener(figure, damage_taken, **kwargs):
    if Condition.SHIELDED.value in figure.conditions:
        shield_amount = figure.conditions[Condition.SHIELDED.value]
        physical_blocked = min(shield_amount, damage_taken["physical_damage_taken"])
        elemental_blocked = min(shield_amount - physical_blocked, damage_taken["elemental_damage_taken"])
        damage_taken["physical_damage_taken"] -= physical_blocked
        damage_taken["elemental_damage_taken"] -= elemental_blocked
        print(f"{figure.name}'s Shielded condition blocks {physical_blocked} physical and {elemental_blocked} elemental damage.")
        figure.conditions[Condition.SHIELDED.value] -= (physical_blocked + elemental_blocked)
        if figure.conditions[Condition.SHIELDED.value] <= 0:
            del figure.conditions[Condition.SHIELDED.value]

def stunned_action_listener(figure):
    """Prevent stunned heroes from taking actions by immediately disabling move/attack when they activate"""
    if Condition.STUNNED.value in figure.conditions and figure.figure_type.value == 'hero':
        print(f'{figure.name} is stunned and cannot move or attack!')
        figure.hero.move_available = False
        figure.hero.attack_available = False

def setup_condition_listeners(map):
    map.events.register(GameEvent.START_FIGURE_ACTION, condition_turn_start_listener)
    map.events.register(GameEvent.END_FIGURE_ACTION, condition_turn_end_listener)
    map.events.register(GameEvent.GET_MOVE, slow_listener)
    map.events.register(GameEvent.DAMAGE_TAKEN, shield_listener)
    map.events.register(GameEvent.START_FIGURE_ACTION, stunned_action_listener)