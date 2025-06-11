def condition_listener(figure):
    for condition, duration in figure.conditions.items():
        if condition == "Burn":
            figure.map.deal_damage("Burning condition", figure, 1, 'Elemental')
        elif condition == "Bleed":
            figure.map.deal_damage("Bleeding condition", figure, 1, 'Physical')
        elif condition == "Regen":
            figure.heal(1)

        if duration > 1:
            figure.conditions[condition] -= 1
        else:
            del figure.conditions[condition]

def slow_listener(figure, move_data):
    if "Slowed" in figure.conditions:
        move_data["value"] = min(move_data["value"], 1)