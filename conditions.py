tick_down_at_start = ['"Regen"', '"Shielded"']  # conditions that tick down at start of turn
tick_down_at_end = ['"Burn"', '"Bleed"']  # conditions that tick down at end of turn

def condition_turn_end_listener(figure):
    for condition, duration in figure.conditions.items():
        if condition == "Burn":
            figure.map.deal_damage("Burning condition", figure, physical_damage=0, elemental_damage=1)
        elif condition == "Bleed":
            figure.map.deal_damage("Bleeding condition", figure, physical_damage=1, elemental_damage=0)
        
        if condition in tick_down_at_end: # e.g. shield does not tick down at end of turn by default
            figure.conditions[condition] -= 1
    
    # remove any that have timed out.
    figure.conditions = {k: v for k, v in figure.conditions.items() if v > 0}

def condition_turn_start_listener(figure):
    for condition, duration in figure.conditions.items():
        if condition == "Regen":
            figure.heal(1)
        
        if condition in tick_down_at_start:
            figure.conditions[condition] -= 1
    
    # remove any that have timed out.
    figure.conditions = {k: v for k, v in figure.conditions.items() if v > 0}

def slow_listener(figure, move_data):
    if "Slowed" in figure.conditions:
        move_data["value"] = min(move_data["value"], 1)

def shield_listener(figure, damage_taken, **kwargs):
    if "Shielded" in figure.conditions:
        shield_amount = figure.conditions["Shielded"]
        amount_blocked = min(shield_amount, damage_taken["damage_taken"])
        damage_taken["damage_taken"] -= amount_blocked
        figure.conditions["Shielded"] -= amount_blocked
        if figure.conditions["Shielded"] <= 0:
            del figure.conditions["Shielded"]

def setup_condition_listeners(map):
    map.events.register("start_figure_action", condition_turn_start_listener)
    map.events.register("end_figure_action", condition_turn_end_listener)
    map.events.register("move", slow_listener)
    map.events.register("damage_taken", shield_listener)