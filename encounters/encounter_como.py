from encounters.encounter_base import EncounterBase
from figure import Figure, FigureType
import random
from coords import Coords
from encounters.enemy_ai import basic_action
from game_targeting import TargetingContext
from game_events import GameEvent
from game_conditions import Condition
from encounters.card_effects_como import (
    como_aim_meteor,
    como_call,
    como_flames_of_the_pit,
    como_meteor_shower,
    como_visage,
    como_rite,
    como_form_champion,
    como_form_inferno,
    como_basic_action,
    como_form_swap,
    como_hellfire_listener
)

como_basic_cards = [
    {   
        "id" : 1,
        "name": "Call of the Legion",
        "text" : "When the meteor Comorragh summons this round lands, it spawns a Doomguard at its location.  A Doomguard has 6HP, Move 1, Attack 2 Physical.",
        "function" : como_call,
    },
    {
        "id" : 2,
        "name": "Flames of the Pit",
        "text" : "Each hero takes 1 Elemental damage for every lava tile within 1 space of them.",
        "function" : como_flames_of_the_pit,
    }
]

como_special_cards = [
    {
        "id" : 101,
        "name": "Meteor Shower",
        "text" : "Comorragh summons 2 additional Meteors this turn",
        "function" : como_meteor_shower,
    },
    {
        "id" : 102,
        "name": "Visage of Terror",
        "text" : "All heroes must move 3 spaces away from Comorragh.  Any hero unable to move the full distance loses 1 health per unspent move.",
        "function" : como_visage,
    },
    {
        "id" : 103,
        "name": "Rite of Flame",
        "text" : "Comorragh moves to the lava tile furthest from any hero and gains 10 Shield Counters.  While the shield holds, at the start of each of his turns Comorragh heals 1 HP per 2 Shield Counters.",
        "function" : como_rite,
    }
]

como_forms = [
    {
        'id' : 1,
        'form': 'champion',
        'name' : 'Form of the Champion',
        'text': 'While in the Form of the Champion, Comorragh gains +1 Physical Defense but -1 Elemental Defense.  His attacks deal 5 Physical damage and also hit any target within Range 3 in a straight line behind his target.',
        'function': como_form_champion,
    },
    {
        'id' : 2,
        'form': 'inferno',
        'name' : 'Form of the Inferno',
        'text': 'While in the Form of the Inferno, Comorragh gains +1 Elemental Defense but -1 Physical Defense.  His attacks deal 2 Physical and 2 Elemental damage and also deal 1 Elemental damage to all other heroes within Range 1 of his target.',
        'function': como_form_inferno,
    }
]

class EncounterComo(EncounterBase):
    def __init__(self):
        super().__init__()
        self.name = "Comorragh"
        self.current_form = None  # Can be 'champion' or 'inferno'
        self.spawn_doomguard_on_meteor = False  # Set by Call of the Legion
        self.cards_since_form_swap = 0  # Track cards to swap form every 3
        self.initial_lava_coords = [Coords(1,5), Coords(9,5), Coords(5,1), Coords(5,9), Coords(2,2), Coords(8,2), Coords(2,8), Coords(8,8)]
        self.build_deck()
        self.get_next_card()
    
    def build_deck(self):
        self.deck = []
        for s in como_special_cards:
            for c in como_basic_cards:
                self.deck.append(c)
            self.deck.append(s)

    def get_next_card(self):
        if len(self.deck) == 0:
            self.build_deck()

        self.next_card = self.deck.pop(0)
    
    def get_boss_display_info(self):
        """Return display items for boss panel: current form and next card"""
        display_items = []
        
        # Show current form using the card definition text
        if self.current_form:
            form_card = next((card for card in como_form_cards if card['form'] == self.current_form), None)
            if form_card:
                display_items.append(form_card)
        
        # Show next card
        display_items.append(self.next_card)
        
        return display_items
    
    def get_deployment_zone(self):
        zone = []
        for x in range(0, 11):
            zone.append((x, 0))
        
        return zone

    def setup_map(self, map):
        como = Figure(
            "Comorragh, Hellfire Prince", FigureType.BOSS, 
            health=100, physical_def=4, elemental_def=4, move=3, physical_dmg=4, elemental_dmg=0, attack_range=1
        )
        # como starts in the middle
        map.add_figure(como, Coords(5,5))
        
        # Create actual LAVA figures at the initial lava tile locations
        for lava_coord in self.initial_lava_coords:
            lava_tile = Figure("LAVA", FigureType.MARKER, cell_color="#ff4500", hazard_damage=1)
            map.add_figure(lava_tile, lava_coord, on_occupied='colocate')
        
        # Start in champion form
        self.current_form = 'champion'
        como.physical_def -= 1  # +1 Physical Defense bonus
        como.elemental_def += 1  # -1 Elemental Defense penalty
        print(f"Comorragh begins in Form of the Champion! Physical Def: {como.physical_def}, Elemental Def: {como.elemental_def}")
        
        # Set up Hellfire passive effect
        map.events.register(GameEvent.DAMAGE_TAKEN, como_hellfire_listener)
    

    def activate_doomguards(self):
        doomguards = self.map.get_figures_by_name("Doomguard")
        for doomguard in doomguards:
            print('Activating Doomguard at {}'.format(doomguard.position))
            basic_action(self.map, doomguard)

    def activate_boss(self):
        print("Comorragh is activating his next card: {}".format(self.next_card['name']))
        self.next_card['function'](self.map)
        self.get_next_card()
        
        # Swap forms every 3 cards (after each special card)
        self.cards_since_form_swap += 1
        if self.cards_since_form_swap >= 3:
            self.cards_since_form_swap = 0
            como_form_swap(self.map)

    def lava_heal(self):
        """Heal all Boss and Minion figures standing in lava by 1 HP"""
        # Find all lava tiles by getting LAVA figures
        lava_tiles = self.map.get_figures_by_name("LAVA")
        lava_coords = [lava.position for lava in lava_tiles]
        
        # Get all Boss and Minion figures
        bosses_and_minions = self.map.get_figures_by_type([FigureType.BOSS, FigureType.MINION])
        
        for figure in bosses_and_minions:
            if figure.position in lava_coords and figure.current_health < figure.max_health:
                figure.heal(1, source=figure)
                print(f"{figure.name} heals 1 HP from standing in lava! (now at {figure.current_health}/{figure.max_health})")

    def process_meteor_impacts(self):
        """Process any meteors that impact this turn (called after boss activates)"""
        from encounters.card_effects_como import como_meteor_falls_listener
        como_meteor_falls_listener(self.map, self)

    def perform_boss_turn(self):
        self.activate_doomguards()
        self.process_meteor_impacts()  # Meteors land after boss acts, so new Doomguards don't activate this turn
        self.activate_boss()
        como_aim_meteor(self.map, self)  # Aim new meteor for next turn
        self.lava_heal()