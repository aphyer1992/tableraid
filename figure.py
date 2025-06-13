import random
from enum import Enum
class FigureType(Enum):
    BOSS = 'boss'
    HERO = 'hero'
    MINION = 'minion'
    OBSTACLE = 'obstacle'
    MARKER = 'marker'


class Figure:
    def __init__(self, name, figure_type, health=None, physical_def=0, elemental_def=0, move=0, physical_dmg=0, elemental_dmg=0, attack_range=1, fixed_representation=None):
        self.name = name
        self.figure_type = figure_type
        self.max_health = health if health is not None else 1
        self.current_health = self.max_health
        self.physical_def = physical_def
        self.elemental_def = elemental_def
        self.base_move = move
        self.physical_dmg = physical_dmg
        self.elemental_dmg = elemental_dmg
        self.attack_range = attack_range
        self.impassible_types = [FigureType.OBSTACLE]
        if self.figure_type in [FigureType.BOSS, FigureType.MINION]:
            self.impassible_types.append(FigureType.HERO)
        elif self.figure_type == FigureType.HERO:
            self.impassible_types.append(FigureType.BOSS)
            self.impassible_types.append(FigureType.MINION)
        self.targetable = True if self.figure_type in [FigureType.HERO, FigureType.MINION, FigureType.BOSS] else False
        self.conditions = {}  # e.g. { 'Burn' : 2, 'Bleed': 1 }
        self.active_effects = {} # e.g. { 'gained_combo_points': True, 'combo_points': 0 }
        self.fixed_representation = fixed_representation

    @classmethod
    def from_hero_archetype(cls, hero_archetype):
        hero_figure = cls(
            name=hero_archetype['name'],
            figure_type=FigureType.HERO,
            health=hero_archetype['max_health'],
            physical_def=hero_archetype['physical_def'],
            elemental_def=hero_archetype['elemental_def'],
            physical_dmg=hero_archetype['physical_dmg'],
            elemental_dmg=hero_archetype['elemental_dmg'],
            attack_range=hero_archetype['attack_range'],
            move=hero_archetype['move']
        )
        return hero_figure

    @property
    def position(self):
        return self.map.get_figure_position(self)
    
    @property
    def move(self):
        move_data = {"value": self.base_move}
        self.map.events.trigger("get_move", figure=self, move_data=move_data)
        return move_data["value"]

    def get_representation_text(self):
        if self.fixed_representation:
            return self.fixed_representation
        elif self.figure_type == FigureType.HERO:
            return('{}\n{}/{}'.format(self.name[0:2], self.current_health, self.max_health))    
        elif self.figure_type == FigureType.BOSS:
            return('{}\n{}/{}'.format(self.name[0:5], self.current_health, self.max_health))
        elif self.figure_type == FigureType.MINION:
            return('{}\n{}/{}'.format(self.name[0:2], self.current_health, self.max_health))
        else:
            return(self.name[0:2])
        
    def roll_defense(self, damage_type, damage_source=None):
        if damage_type == 'Physical':
            effective_def = self.physical_def
        elif damage_type == 'Elemental':
            effective_def = self.elemental_def
        else:
            raise ValueError("Invalid damage type")
        
        roll = random.randint(1, 6)

        self.map.events.trigger("defense_roll", figure=self, roll=roll, damage_type=damage_type, damage_source=damage_source)
        print('Defense roll for {} against {} damage: {}'.format(self.name, damage_type, roll))
        if roll >= effective_def: # successful defense
            return True
        else:
            return False
    
    def take_damage(self, physical_damage, elemental_damage, damage_source=None, reduce_health=True):
        rolls = [self.roll_defense('Physical', damage_source) for _ in range(physical_damage)] + [self.roll_defense('Elemental', damage_source) for _ in range(elemental_damage)]
        damage_taken = {'damage_taken' : sum(1 for roll in rolls if not roll)} # defined this way so listeners can edit.
        self.map.events.trigger("damage_taken", figure=self, damage_taken=damage_taken, damage_source=damage_source)
        if reduce_health:
            self.lose_health(damage_taken['damage_taken'], source=damage_source)

        return(damage_taken['damage_taken'])   
    
    def lose_health(self, amount, source=None):
        if amount < 0:
            raise ValueError("Health loss amount must be positive")
        self.current_health = max(0, self.current_health - amount)
        if self.current_health == 0:
            self.map.remove_figure(self)

    def heal(self, amount, source=None):
        if amount < 0:
            raise ValueError("Healing amount must be positive")
        self.current_health = min(self.max_health, self.current_health + amount)
        self.map.events.trigger("healed", figure=self, amount=amount, source=source)

    def add_effect(self, effect_key, effect_value, overwrite=False):
        if effect_key in self.active_effects and not overwrite:
            raise ValueError(f"Effect '{effect_key}' already exists and overwrite is not allowed.")
        else:
            self.active_effects[effect_key] = effect_value

    def remove_effect(self, effect):
        self.active_effects.pop(effect, None)

    def get_effect(self, effect_key, default_value=None):
        return self.active_effects.get(effect_key, default_value)

    def add_condition(self, condition, duration, incremental=True):
        if condition in self.conditions:
            if incremental:
                self.conditions[condition] += duration
            else:
                self.conditions[condition] = max(duration, self.conditions[condition])
        else:
            self.conditions[condition] = duration
        self.map.events.trigger("condition_added", figure=self, condition=condition, duration=duration)

    def remove_condition(self, condition):
        if condition in self.conditions:
            del self.conditions[condition]
            self.map.events.trigger("condition_removed", figure=self, condition=condition)

    def get_condition(self, condition, default_value=None):
        return self.conditions.get(condition, default_value)
    
    def start_action(self):
        self.map.events.trigger("start_action", figure=self)
        
    def end_figure_action(self):
        self.map.events.trigger("end_figure_action", figure=self)