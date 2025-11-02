from figure import FigureType

def warrior_taunt(figure, energy_spent, ui=None):
    figure.add_effect('taunt_level', 1)

    def end_taunt_listener(figure):
        figure.remove_effect('taunt_level')
        figure.map.events.deregister("hero_turn_start", listener_id)

    listener_id = figure.map.events.register("hero_turn_start", lambda: end_taunt_listener(figure))

def warrior_bastion(figure, energy_spent, ui=None):
    assert(figure.physical_def == 3)
    assert(figure.elemental_def == 5)
    figure.physical_def = 2
    figure.elemental_def = 4

    def end_bastion_listener(figure_ending):
        if figure_ending == figure:
            figure.physical_def = 3
            figure.elemental_def = 5
            figure.map.events.deregister("hero_turn_start", listener_id)

    listener_id = figure.map.events.register("hero_turn_start", end_bastion_listener)

def warrior_shield_bash(warrior_figure, energy_spent, ui=None):
    ui.hero_attack(warrior_figure.hero, range=1, physical_damage=energy_spent, elemental_damage=0, costs_attack_action=False)
    warrior_figure.add_condition("Shielded", energy_spent, incremental=True)
    
def paladin_smite(figure, energy_spent, ui=None):
    ui.hero_attack(figure.hero, range=1, physical_damage=0, elemental_damage=5, costs_attack_action=True)

def paladin_holy_shield(figure, energy_spent, ui=None):
    assert(figure.physical_def == 4)
    assert(figure.elemental_def == 4)
    figure.physical_def = 3
    figure.elemental_def = 3
    figure.add_effect('taunt_level', 1)

    def end_holy_shield_listener(figure_ending):
        if figure_ending == figure:
            figure.physical_def = 4
            figure.elemental_def = 4
            figure.remove_effect('taunt_level')
            figure.map.events.deregister("hero_turn_start", listener_id)

    listener_id = figure.map.events.register("hero_turn_start", end_holy_shield_listener)

def paladin_healing_light(figure, energy_spent, ui=None):
    assert(energy_spent >= 1)
    callback_fn = lambda target: target.heal(2 * energy_spent, source=figure)
    ui.choose_friendly_target(figure.position, range=5, callback_fn=callback_fn)

def rogue_dual_wield(figure, energy_spent, ui=None):
    ui.hero_attack(figure.hero, range=1, physical_damage=2, elemental_damage=0, costs_attack_action=False)
    
def rogue_eviscerate_attack_listener(damage_source, hero):
    if damage_source == hero.figure:
        if not hero.figure.get_effect('gained_combo_points'):
            hero.figure.add_effect('combo_points', hero.figure.get_effect('combo_points') + 1, overwrite=True)
            hero.figure.add_effect('gained_combo_points', True, overwrite=True)

def rogue_eviscerate_turn_end_listener(hero):
    if not hero.figure.get_effect('gained_combo_points'):
        current_combo_points = hero.figure.get_effect('combo_points')
        hero.figure.add_effect('combo_points', max(0, current_combo_points - 1), overwrite=True)

    hero.figure.add_effect('gained_combo_points', False, overwrite=True)
    return

def rogue_eviscerate_setup(hero):
    hero.figure.add_effect('combo_points', 0)
    hero.figure.add_effect('gained_combo_points', False)
    hero.figure.map.events.register("damage_taken", lambda damage_source, **kwargs: rogue_eviscerate_attack_listener(damage_source, hero))
    hero.figure.map.events.register("hero_turn_end", lambda: rogue_eviscerate_turn_end_listener(hero))

def rogue_eviscerate(figure, energy_spent, ui=None):
    current_combo_points = figure.get_effect('combo_points')
    ui.hero_attack(
        figure.hero,
        physical_damage=2*current_combo_points,
        elemental_damage=0,
        range=1
    )
    figure.add_effect('combo_points', 0, overwrite=True)

def rogue_vanish(figure, energy_spent, ui=None):
    figure.add_effect('taunt_level', -1)
    def end_vanish_listener(figure_ending):
        if figure_ending == figure:
            figure.remove_effect('taunt_level')
            figure.map.events.deregister("hero_turn_start", listener_id)

    listener_id = figure.map.events.register("hero_turn_start", end_vanish_listener)

    ui.hero_move(figure.hero, move_distance=2, costs_move_action=False)

def ranger_power_shot(figure, energy_spent, ui=None):
    ui.hero_attack(figure.hero, physical_damage=5, elemental_damage=0, range=5, costs_attack_action=True)

def ranger_spirit_link_callback(figure, target, ui):
    target.heal(1, source=figure)
    ui.hero_move(target, move_distance=1, costs_move_action=False)

def ranger_spirit_link(figure, energy_spent, ui=None):
    ui.choose_friendly_target(figure.position, range=5, callback_fn=ranger_spirit_link_callback)

def ranger_quick_step(figure, energy_spent, ui=None):
    assert ui
    ui.hero_move(figure.hero, move_distance=1, costs_move_action=False)

def mage_fireball_callback(figure, target, dmg_dealt, ui):
    target.add_condition("Burn", 5, incremental=False)

def mage_fireball(figure, energy_spent, ui=None):
    ui.hero_attack(
        figure.hero,
        physical_damage=0,
        elemental_damage=4,
        range=4,
        costs_attack_action=True,
        after_attack_callback=mage_fireball_callback
    )

def mage_fire_nova(figure, energy_spent, ui=None):
    in_range = figure.map.get_figures_within_distance(figure.position, 2)
    targets = [f for f in in_range if f.targetable and f.figure_type != FigureType.HERO]
    for target in targets:
        # this jumps directly to the execute_attack because no target selection is needed.
        ui.execute_attack(figure, target, physical_damage=0, elemental_damage=energy_spent, costs_attack_action=False)

def mage_combustion_listener(mage_hero, figure, roll, damage_type, damage_source):
    if damage_source != mage_hero.figure:
        return
    if damage_type == 'Elemental' and figure.get_condition('Burn') is not None:
        if roll == 1:
            print('Mage Combustion triggered for bonus HP and Energy!')
            mage_hero.figure.heal(1, source=mage_hero.figure)
            mage_hero.gain_energy(1)
        elif roll == figure.elemental_def: # if you just barely missed
            print('Mage Combustion triggered for extra damage!')
            figure.lose_health(1, source=mage_hero.figure)

def mage_combustion_setup(hero):
    hero.figure.map.events.register(
        "defense_roll", 
        lambda figure, roll, damage_type, damage_source: mage_combustion_listener(hero, figure, roll, damage_type, damage_source)
    )
    return

def priest_word_of_healing(figure, energy_spent, ui=None):
    callback_fn = lambda target: target.heal(3, source=figure)
    ui.choose_friendly_target(figure.position, range=5, callback_fn=callback_fn)

def priest_circle_of_healing(figure, energy_spent, ui=None):
    assert(energy_spent >= 1)
    heroes = figure.map.get_figures_by_type(FigureType.HERO)
    for hero in heroes:
        if figure.map.distance_between(figure.position, hero.position) <= 2:
            hero.heal(energy_spent, source=figure)

def priest_renew(figure, energy_spent, ui=None):
    callback_fn = lambda target: target.add_condition("Regen", 5, incremental=False)
    ui.choose_friendly_target(figure.position, range=5, callback_fn=callback_fn)