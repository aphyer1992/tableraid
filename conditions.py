def condition_listener(figure):
    for condition, duration in figure.conditions.items():
        if condition == "Burn":
            figure.map.deal_damage("Burning condition", figure, physical_damage=0, elemental_damage=1)
        elif condition == "Bleed":
            figure.map.deal_damage("Bleeding condition", figure, physical_damage=1, elemental_damage=0)
        elif condition == "Regen":
            figure.heal(1)

        figure.conditions[condition] -= 1
    
    # remove any that have timed out.
    figure.conditions = {k: v for k, v in figure.conditions.items() if v > 0}

def slow_listener(figure, move_data):
    if "Slowed" in figure.conditions:
        move_data["value"] = min(move_data["value"], 1)