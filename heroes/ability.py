from heroes.ability_effects import (
    warrior_taunt,
    warrior_bastion,
    warrior_shield_bash,
    paladin_smite,
    paladin_holy_shield,
    paladin_healing_light,
    rogue_dual_wield,
    rogue_eviscerate,
    rogue_eviscerate_setup,
    rogue_vanish,
    ranger_power_shot,
    ranger_spirit_link,
    ranger_quick_step,
    mage_fireball,
    mage_fire_nova,
    mage_combustion_setup,
    priest_word_of_healing,
    priest_circle_of_healing,
    priest_renew
)
class Ability:
    def __init__(self, name, description, effect_fn, energy_cost=0, variable_cost=False, move_cost=False, attack_cost=False, passive=False, usable_off_turn=False, setup_routine=None, hotkey=None):
        self.name = name
        self.description = description
        self.energy_cost = energy_cost
        self.variable_cost = variable_cost
        if self.variable_cost:
            assert(energy_cost == 1) # for now we expect this
        self.move_cost = move_cost
        self.attack_cost = attack_cost
        self.effect_fn = effect_fn
        self.passive = passive
        self.usable_off_turn = usable_off_turn
        self.setup_routine = setup_routine
        self.hotkey = hotkey
        self.used = False
        self.hero = None  # This will be set when the ability is assigned to a hero

    def is_castable(self):
        if self.passive:
            return False
        if self.used:
            return False
        if not self.hero.activated and not self.usable_off_turn:
            return False
        if self.hero.current_energy < self.energy_cost:
            return False
        if self.move_cost and not self.hero.move_available:
            return False
        if self.attack_cost and not self.hero.attack_available:
            return False
        return True    

    def cast(self, map, energy_spent):
        if not self.is_castable():
            raise ValueError("Ability cannot be cast")
        if self.variable_cost:
            assert(energy_spent >= self.energy_cost)
        else:
            assert(energy_spent == self.energy_cost)
        self.hero.spend_energy(energy_spent)
        if self.move_cost:
            self.hero.move_available = False
        if self.attack_cost:
            self.hero.attack_available = False
        self.used = True
        self.effect_fn(map, self.hero, energy_spent)

taunt_ability = Ability(
    name="Taunt",
    description="Until next turn, enemies will prioritize you over equidistant heroes.",
    energy_cost=0,
    variable_cost=False,
    move_cost=False,
    attack_cost=False,
    effect_fn = warrior_taunt,
    hotkey='t'
)

bastion_ability = Ability(
    name="Bastion",
    description="Raise your shield, improving your defenses by 1 until next turn.",
    energy_cost=0,
    variable_cost=False,
    move_cost=True,
    attack_cost=False,
    effect_fn = warrior_bastion,
    hotkey='b'
)

shield_bash_ability = Ability(
    name="Shield Bash",
    description="Deal X physical damage to an adjacent enemy and gain X shield counters.",
    energy_cost=1,
    variable_cost=True,
    move_cost=False,
    attack_cost=False,
    effect_fn=warrior_shield_bash,
    hotkey='s'
)

smite_ability = Ability(
    name="Smite",
    description="Deal 5 elemental damage to an adjacent enemy.",
    energy_cost=1,
    variable_cost=False,
    move_cost=False,
    attack_cost=True,
    effect_fn=paladin_smite,
    hotkey='s'
)

holy_shield_ability = Ability(
    name="Holy Shield",
    description="Deal 1 Elemental damage to all adjacent enemies.  Raise your defenses by 1 and taunt until next turn.",
    energy_cost=1,
    variable_cost=False,
    move_cost=False,
    attack_cost=False,
    effect_fn=paladin_holy_shield,
    hotkey='h'
)

healing_light_ability = Ability(
    name="Healing Light",
    description="Heal an ally within Range 5 for 2 health per energy spent.",
    energy_cost=1,
    variable_cost=True,
    move_cost=False,
    attack_cost=False,
    effect_fn=paladin_healing_light,
    hotkey='l'
)

dual_wield_ability = Ability(
    name="Dual Wield",
    description="Deal 2 physical damage to an adjacent enemy.",
    energy_cost=0,
    variable_cost=False,
    move_cost=True,
    attack_cost=False,
    effect_fn=rogue_dual_wield,
    hotkey='d'
)

eviscerate_ability = Ability(
    name="Eviscerate",
    description="Consume all combo points to deal 2 physical damage per combo point to an adjacent enemy.  (You gain a combo point once per turn when you attack.  You lose a combo point if a turn passes without you attacking).",
    energy_cost=2,
    variable_cost=False,
    move_cost=False,
    attack_cost=False,
    effect_fn=rogue_eviscerate,
    setup_routine=rogue_eviscerate_setup,
    hotkey='e'
)

vanish_ability = Ability(
    name="Vanish",
    description="Until your next turn, enemies will deprioritize you over equidistant heroes.  If you are adjacent to an enemy, you may move up to 2 spaces away from them.",
    energy_cost=0,
    variable_cost=False,
    move_cost=False,
    attack_cost=False,
    effect_fn=rogue_vanish,
    hotkey='v'
)

power_shot_ability = Ability(
    name="Power Shot",
    description="Deal 5 physical damage to an enemy within Range 5.",
    energy_cost=1,
    variable_cost=False,
    move_cost=True,
    attack_cost=True,
    effect_fn=ranger_power_shot,
    hotkey='p'
)

spirit_link_ability = Ability(
    name="Spirit Link",
    description="Heal an ally within Range 5 for 1 health and allow them to move 1 space.",
    energy_cost=1,
    variable_cost=False,
    move_cost=False,
    attack_cost=False,
    effect_fn=ranger_spirit_link,
    hotkey='l'
)

quick_step_ability = Ability(
    name="Quick Step",
    description="Move up to 1 spaces in any direction.  This ability can be used even if you have not activated.",
    energy_cost=0,
    variable_cost=False,
    move_cost=False,
    attack_cost=False,
    usable_off_turn=True,
    effect_fn=ranger_quick_step,
    hotkey='q'
)

fireball_ability = Ability(
    name="Fireball",
    description="Deal 4 elemental damage to an enemy within Range 4 and apply Burning 5.",
    energy_cost=2,
    variable_cost=False,
    move_cost=False,
    attack_cost=True,
    effect_fn=mage_fireball,
    hotkey='f'
)

fire_nova_ability = Ability(
    name="Fire Nova",
    description="Deal X elemental damage to all enemies within Range 2.",
    energy_cost=1,
    variable_cost=True,
    move_cost=False,
    attack_cost=False,
    effect_fn=mage_fire_nova,
    hotkey='n'
)

combustion_ability = Ability(
    name="Combustion",
    description="When dealing elemental damage to burning enemies, they have -1 defense, and for every 1 they roll you regain 1 HP and 1 MP.",
    energy_cost=0,
    variable_cost=False,
    move_cost=False,
    attack_cost=False,
    passive=True,
    effect_fn=None,
    setup_routine=mage_combustion_setup
)

word_of_healing_ability = Ability(
    name="Healing Word",
    description="Heal an ally within Range 5 for 3 health.",
    energy_cost=1,
    variable_cost=False,
    move_cost=False,
    attack_cost=False,
    effect_fn=priest_word_of_healing,
    hotkey='w'
)

circle_of_healing_ability = Ability(
    name="Healing Circle",
    description="Heal all allies within Range 2 for X health.",
    energy_cost=1,
    variable_cost=True,
    move_cost=False,
    attack_cost=False,
    effect_fn=priest_circle_of_healing,
    hotkey='c'
)

renew_ability = Ability(
    name="Renew",
    description="Apply Regen 5 to an ally within Range 5.",
    energy_cost=1,
    variable_cost=False,
    move_cost=False,
    attack_cost=True,
    effect_fn=priest_renew,
    hotkey='r'
)