from game_events import GameEvent

tick_down_at_start = ['"Regen"', '"Shielded"']  # conditions that tick down at start of turn
tick_down_at_end = ['"Burn"', '"Bleed"']  # conditions that tick down at end of turn

def condition_turn_end_listener(figure):
    for condition, duration in figure.conditions.items():
        if condition == "Burn":
            figure.map.deal_damage("Burning condition", figure, physical_damage=0, elemental_damage=1)
        elif condition == "Bleed":
            figure.map.deal_damage("Bleeding condition", figure, physical_damage=1, elemental_damage=0)
        
        if condition in tick_down_at_end: # e.g. shield does not tick down at end of turn by default
            figure.conditions[condition] = duration - 1
            print(f"DEBUG: Condition {condition} on {figure.name} ticks down to {figure.conditions[condition]}")
    
    # remove any that have timed out.
    figure.conditions = {k: v for k, v in figure.conditions.items() if v > 0}

def condition_turn_start_listener(figure):
    for condition, duration in figure.conditions.items():
        if condition == "Regen":
            figure.heal(1)
        
        if condition in tick_down_at_start:
            figure.conditions[condition] = duration - 1
            print(f"DEBUG: Condition {condition} on {figure.name} ticks down to {figure.conditions[condition]}")

    # remove any that have timed out.
    figure.conditions = {k: v for k, v in figure.conditions.items() if v > 0}

def slow_listener(figure, move_data):
    if "Slowed" in figure.conditions:
        move_data["value"] = min(move_data["value"], 1)

def shield_listener(figure, damage_taken, **kwargs):
    if "Shielded" in figure.conditions:
        shield_amount = figure.conditions["Shielded"]
        physical_blocked = min(shield_amount, damage_taken["physical_damage_taken"])
        elemental_blocked = min(shield_amount - physical_blocked, damage_taken["elemental_damage_taken"])
        damage_taken["physical_damage_taken"] -= physical_blocked
        damage_taken["elemental_damage_taken"] -= elemental_blocked
        figure.conditions["Shielded"] -= (physical_blocked + elemental_blocked)
        if figure.conditions["Shielded"] <= 0:
            del figure.conditions["Shielded"]

def setup_condition_listeners(map):
    map.events.register(GameEvent.START_FIGURE_ACTION, condition_turn_start_listener)
    map.events.register(GameEvent.END_FIGURE_ACTION, condition_turn_end_listener)
    map.events.register(GameEvent.GET_MOVE, slow_listener)
    map.events.register(GameEvent.DAMAGE_TAKEN, shield_listener)