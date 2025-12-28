from encounters.encounter_base import EncounterBase
from encounters.card_effects_sael import (
    sael_avalanche_crush,
    sael_storm_shield,
    sael_chilling_winds,
    sael_icicle_shards,
    sael_frozen_servants,
    sael_frost_tomb,
    sael_whirlwind,
    sael_frost_breath,
    sael_ice_collapse,
    sael_eye_of_the_storm,
    sael_biting_cold_listener
)
from figure import Figure, FigureType
import random
from coords import Coords
from encounters.enemy_ai import basic_action
from game_targeting import TargetingContext

sael_cards = [
    {   
        "id" : 1,
        "name": "Avalanche Crush",
        "text" : "Sa'el performs three basic actions this round.  Each attack knocks the target back 1 space per damage done.",
        "function" : sael_avalanche_crush,
    },
    {   
        "id" : 2,
        "name": "Storm Shield",
        "text" : "After her basic action, Sa'el gains 10 Shield and deals 1 Elemental damage to all heroes.  While the shield is active, she deals 1 Elemental Damage to all heroes at the start of each of her turns.",
        "function" : sael_storm_shield,
    },
    {   
        "id" : 3,
        "name": "Chilling Winds",
        "text" : "After her basic action, Sa'el deals 1 Elemental damage to all heroes.  Each hero that takes damage gains 1 Slowed.",
        "function" : sael_chilling_winds,
    },
    {   
        "id" : 4,
        "name": "Icicle Shards",
        "text" : "After her basic action, Sa'el deals 1 Physical damage to all heroes.  Each hero that takes damage gains Bleed equal to their missing HP.",
        "function" : sael_icicle_shards,
    },
    {   
        "id" : 5,
        "name": "Frozen Servants",
        "text" : "Sa'el summons 2 Frost Elementals at the spawn points.  Each elemental has 5HP and Physical Vulnerability 1.  On future turns, Elementals act before Sa'el, with Move 1 and Attack 1 Physical + 1 Elemental.",
        "function" : sael_frozen_servants,
    },
    {   
        "id" : 6,
        "name": "Frost Tomb",
        "text" : "After her basic action, Sa'el entombs a random hero in a Frost Tomb.  The hero is immobilized, unable to act, and takes 1 Elemental Damage at the end of each turn (hero or boss).  They can be healed, but otherwise are untargetable.  The Frost Tomb has 5HP and Physical Vulnerability 1.  If the Frost Tomb is destroyed, the hero is freed.",
        "function" : sael_frost_tomb,
    },
    {   
        "id" : 7,
        "name": "Whirlwind",
        "text" : "Sa'el's basic attack this round deals +1 Elemental Damage, and hits all heroes within 2 spaces of her.",
        "function" : sael_whirlwind,
    },
    {   
        "id" : 8,
        "name": "Frost Breath",
        "text" : "Sa'el's basic attack this round replaces its usual damage with 3 Elemental Damage, and hits all heroes within 4 spaces in a cone in front of her.",
        "function" : sael_frost_breath,
    },
    {   
        "id" : 9,
        "name": "Ice Collapse",
        "text" : "Sa'el marks two random squares containing heroes.  At the start of her next turn, place Impassible Terrain in those squares.  Any hero in a marked square takes 4 Physical and 4 Elemental Damage and is knocked back.  Any hero adjacent to a marked square takes 1 Physical and 1 Elemental Damage.",
        "function" : sael_ice_collapse,
    },
    {   
        "id" : 10,
        "name": "Eye of the Storm",
        "text" : "Sa'el gains 1 Biting Cold counter.  After her basic action, she deals 3 Elemental Damage to all heroes.  However, if a hero would lose health this way, they are instead Knocked Back that many spaces.  Reshuffle Sa'el's deck, and put this card back on the bottom.",
        "function" : sael_eye_of_the_storm,
    },
]

class EncounterSael(EncounterBase):
    def __init__(self):
        super().__init__()
        self.name = "Sael"
        self.card_list = sael_cards
        self.biting_cold_counters = 0
        self.shuffle_deck()
        self.get_next_card()
        self.setup_blizzard_path()

    def setup_blizzard_path(self):
        blizzard_tiles = []
        for x in range(2, 9):
            for y in range(2,9):
                if x in [2,8] or y in [2,8]: # only the border tiles
                    blizzard_tiles.append(Coords(x, y))
        self.special_tiles = {
            "blizzard_path": {'coords': blizzard_tiles, 'color' : "#aae9f7"}
        }

    def shuffle_deck(self):
        most_cards = [c for c in self.card_list if c["id"] != 10]
        random.shuffle(most_cards)
        self.deck = most_cards + [c for c in self.card_list if c["id"] == 10]
    
    def get_next_card(self):
        if len(self.deck) == 0:
            self.shuffle_deck()

        self.next_card = self.deck.pop(0)
    
    def get_deployment_zone(self):
        zone = []
        for x in range(0, 11):
            zone.append((x, 0))
        for y in range(1,3):
            zone.append((0, y))
            zone.append((10, y))
        
        return zone

    def setup_map(self, map):
        sael = Figure(
            "Sa'el, Frozen Queen", FigureType.BOSS, 
            health=100, physical_def=4, elemental_def=4, move=3, physical_dmg=4, elemental_dmg=0, attack_range=1
        )
        # sael starts in the middle
        map.add_figure(sael, Coords(5,5))
        # register the listener to track Biting Cold
        map.events.register(
            "defense_roll", 
            lambda figure, roll_data, damage_type, **kwargs: sael_biting_cold_listener(figure, roll_data, damage_type, map)
        )

        blizzard = Figure("Blizzard", FigureType.MARKER, fixed_representation='Z')
        map.add_figure(blizzard, Coords(5, 2), on_occupied='displace')

    def activate_blizzard(self):
        print('Blizzard is moving...')
        blizzard = self.map.get_figures_by_name("Blizzard")[0]

        if blizzard.position.y == 2 and blizzard.position.x != 2: # move left along the bottom
            self.map.move_figure(blizzard, Coords(blizzard.position.x - 1, blizzard.position.y))
        elif blizzard.position.y != 8 and blizzard.position.x == 2: # move up along the left
            self.map.move_figure(blizzard, Coords(blizzard.position.x, blizzard.position.y + 1))
        elif blizzard.position.y == 8 and blizzard.position.x != 8: # move right along the top
            self.map.move_figure(blizzard, Coords(blizzard.position.x + 1, blizzard.position.y))
        elif blizzard.position.y != 2 and blizzard.position.x == 8: # move down along the right
            self.map.move_figure(blizzard, Coords(blizzard.position.x, blizzard.position.y - 1))
        else:
            raise ValueError("Blizzard is in an unexpected position: {}".format(blizzard.position))
        
        for hero in self.map.get_figures_by_type(FigureType.HERO, {TargetingContext.AOE_ABILITY_HITTABLE: True}):
            if self.map.distance_between(blizzard.position, hero.position) <= 2:
                self.map.deal_damage(blizzard, hero, physical_damage=0, elemental_damage=1)

    def activate_elementals(self):
        elementals = self.map.get_figures_by_name("Frost Elemental")
        for elemental in elementals:
            print('Activating Frost Elemental at {}'.format(elemental.position))
            basic_action(self.map, elemental)
    
    def activate_boss(self):
        print("Sa'el is activating her next card: {}".format(self.next_card['name']))
        self.next_card['function'](self.map, self.map.get_figures_by_type(FigureType.BOSS)[0])
        self.get_next_card()

    def perform_boss_turn(self):
        self.activate_blizzard()
        self.activate_elementals()
        self.activate_boss()
        self.activate_blizzard()
