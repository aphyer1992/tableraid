import random
from game_events import GameEvent
from game_conditions import Condition
from game_targeting import TargetingContext
from figure import FigureType
from items.item_base import Item
from heroes.ability import Ability


# ---------------------------------------------------------------------------
# Frozen Crown — Head
# ---------------------------------------------------------------------------

class FrozenCrown(Item):
    def __init__(self):
        super().__init__(
            id='frozen_crown',
            name='Frozen Crown',
            slot='head',
            description="At the end of a round, if you spent 4 or more energy on abilities this turn, regain 1 energy.",
        )

    def apply(self, hero, fight_map):
        def listener(**kwargs):
            if hero.energy_spent_abilities >= 4:
                hero.gain_energy(1)
                print(f"{hero.name}: Frozen Crown — regained 1 energy.")
        fight_map.events.register(GameEvent.HERO_TURN_END, listener)


# ---------------------------------------------------------------------------
# Storm's Eye — Neck
# ---------------------------------------------------------------------------

class StormsEye(Item):
    def __init__(self):
        super().__init__(
            id='storms_eye',
            name="Storm's Eye",
            slot='neck',
            description="Move: deal 1 Elemental damage to all adjacent enemies.",
        )

    def apply(self, hero, fight_map):
        def listener(**kwargs):
            figure = kwargs.get('figure')
            if figure != hero.figure:
                return
            # Deal 1 elemental damage to all adjacent enemies
            adjacent = fight_map.get_figures_within_distance(figure.position, 1)
            for target in adjacent:
                if target.targeting_parameters.get(TargetingContext.ENEMY_TARGETABLE, False) and target.figure_type in (FigureType.BOSS, FigureType.MINION):
                    fight_map.deal_damage(figure, target, physical_damage=0, elemental_damage=1)
                    print(f"{hero.name}: Storm's Eye — dealt 1 elemental to {target.name}.")
        fight_map.events.register(GameEvent.FIGURE_MOVED, listener)


# ---------------------------------------------------------------------------
# Icicle Shards — Both hands
# ---------------------------------------------------------------------------

class IcicleShards(Item):
    def __init__(self):
        super().__init__(
            id='icicle_shards',
            name='Icicle Shards',
            slot='both_hands',
            description="Whenever an enemy rolls 2 or more 1s against physical damage dealt by you, apply Bleed 5 to that enemy.",
        )

    def apply(self, hero, fight_map):
        one_count = [0]

        def defense_listener(**kwargs):
            if kwargs.get('damage_source') != hero.figure:
                return
            if kwargs.get('damage_type') != 'Physical':
                return
            if kwargs['roll_data']['value'] == 1:
                one_count[0] += 1

        def damage_listener(**kwargs):
            if kwargs.get('damage_source') != hero.figure:
                return
            target = kwargs.get('figure')
            if one_count[0] >= 2 and target is not None:
                target.add_condition(Condition.BLEED, 5)
                print(f"{hero.name}: Icicle Shards — applied Bleed 5 to {target.name}.")
            one_count[0] = 0

        fight_map.events.register(GameEvent.DEFENSE_ROLL, defense_listener)
        fight_map.events.register(GameEvent.DAMAGE_TAKEN, damage_listener)


# ---------------------------------------------------------------------------
# Glacial Bulwark — Off-hand
# ---------------------------------------------------------------------------

class GlacialBulwark(Item):
    def __init__(self):
        super().__init__(
            id='glacial_bulwark',
            name='Glacial Bulwark',
            slot='off_hand',
            description="Fight start: 1 charge. On a failed physical defense roll, lose 1 charge and re-roll. On activate, replace the charge.",
        )

    def apply(self, hero, fight_map):
        hero.figure.add_effect('gb_charges', 1, overwrite=True)

        def defense_listener(**kwargs):
            if kwargs.get('figure') != hero.figure:
                return
            if kwargs.get('damage_type') != 'Physical':
                return
            roll_data = kwargs['roll_data']
            if roll_data['value'] < hero.figure.physical_def:
                charges = hero.figure.get_effect('gb_charges') or 0
                if charges > 0:
                    hero.figure.add_effect('gb_charges', charges - 1, overwrite=True)
                    roll_data['value'] = random.randint(1, 6)
                    print(f"{hero.name}: Glacial Bulwark — re-rolled defense ({roll_data['value']}).")

        def activated_listener(**kwargs):
            if kwargs.get('figure') != hero.figure:
                return
            hero.figure.add_effect('gb_charges', 1, overwrite=True)

        fight_map.events.register(GameEvent.DEFENSE_ROLL, defense_listener)
        fight_map.events.register(GameEvent.HERO_ACTIVATED, activated_listener)


# ---------------------------------------------------------------------------
# Robes of True Ice — Body
# ---------------------------------------------------------------------------

class RobesOfTrueIce(Item):
    def __init__(self):
        super().__init__(
            id='robes_of_true_ice',
            name='Robes of True Ice',
            slot='body',
            description="+1 Max Energy, +1 Elemental Defense, -1 Physical Defense.",
        )

    def apply(self, hero, fight_map):
        hero.max_energy += 1
        hero.current_energy = min(hero.current_energy + 1, hero.max_energy)
        hero.figure.elemental_def += 1
        hero.figure.physical_def -= 1


# ---------------------------------------------------------------------------
# Mana Storm Potion — Consumable
# ---------------------------------------------------------------------------

class ManaStormPotion(Item):
    def __init__(self):
        super().__init__(
            id='mana_storm_potion',
            name='Mana Storm Potion',
            slot='consumable',
            description="Use once per fight. For this round, all your abilities cost 1 less energy (minimum 0).",
        )

    def apply(self, hero, fight_map):
        listener_id_holder = [None]

        def effect_fn(figure, energy_spent, ui=None):
            # figure is hero.figure (Figure object); caster is the hero
            caster = figure.hero
            caster.ability_cost_modifier = -1
            caster.abilities[-1].per_fight_used = True  # mark the potion itself as used

            def reset_listener(**kwargs):
                caster.ability_cost_modifier = 0
                if listener_id_holder[0] is not None:
                    fight_map.events.deregister(GameEvent.HERO_TURN_START, listener_id_holder[0])
                    listener_id_holder[0] = None

            lid = fight_map.events.register(GameEvent.HERO_TURN_START, reset_listener)
            listener_id_holder[0] = lid
            print(f"{hero.name}: Mana Storm Potion — abilities cost 1 less this round.")

        potion_ability = Ability(
            name='Mana Storm Potion',
            description="Once per fight: all your abilities cost 1 less energy this round (minimum 0).",
            effect_fn=effect_fn,
            energy_cost=0,
            hotkey=None,
        )
        potion_ability.hero = hero
        hero.abilities.append(potion_ability)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ALL_ITEMS = [
    FrozenCrown(),
    StormsEye(),
    IcicleShards(),
    GlacialBulwark(),
    RobesOfTrueIce(),
    ManaStormPotion(),
]
