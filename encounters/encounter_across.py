from encounters.encounter_base import EncounterBase
from encounters.card_effects_across import (
    across_suffering,
    across_inferno,
    across_ignite_arrows,
    across_riposte,
    across_pin_down,
    across_whirling_axe,
    across_hamstring,
    across_whirling_defense,
    across_faintheartedness,
    across_bestial_force,
    across_shieldwall,
    across_phoenix_fire,
    boss_firestorm,
    boss_incendiary_bonds,
    boss_legion_commander,
    boss_conjure_flame,
)
from figure import Figure, FigureType
import random
from coords import Coords
from encounters.enemy_ai import basic_action
from game_targeting import TargetingContext
from game_events import GameEvent
from game_conditions import Condition
from combat_helpers import aoe_attack_adjacent, aoe_attack_all_heroes
from enum import Enum
from encounters import minions_across

class CharrMinionType(Enum):
    """Minion types for the Across the Wall encounter"""
    BLADE_STORM = "blade_storm"
    AXE_FIEND = "axe_fiend"
    ASH_WALKER = "ash_walker"
    FLAMECALLER = "flamecaller"
    STALKER = "stalker"
    SCOUT = "scout"
    
    def __str__(self):
        return self.value

# Minion type definitions with stats and activation functions
MINION_CONFIGS = {
    CharrMinionType.BLADE_STORM: {
        'name': 'Charr Blade Storm',
        'prefix': 'BS',
        'description': 'Melee attacker with bleed on low HP targets',
        'stats': {'health': 10, 'physical_def': 3, 'elemental_def': 5, 'move': 1,
                  'physical_dmg': 2, 'elemental_dmg': 0, 'attack_range': 1},
        'activate': minions_across.activate_blade_storms
    },
    CharrMinionType.AXE_FIEND: {
        'name': 'Charr Axe Fiend',
        'prefix': 'AF',
        'description': 'AOE melee attacker',
        'stats': {'health': 10, 'physical_def': 4, 'elemental_def': 4, 'move': 1,
                  'physical_dmg': 2, 'elemental_dmg': 0, 'attack_range': 1},
        'activate': minions_across.activate_axe_fiends
    },
    CharrMinionType.ASH_WALKER: {
        'name': 'Charr Ash Walker',
        'prefix': 'AW',
        'description': 'Ranged attacker, changes behavior when damaged',
        'stats': {'health': 8, 'physical_def': 5, 'elemental_def': 4, 'move': 1,
                  'physical_dmg': 0, 'elemental_dmg': 3, 'attack_range': 3},
        'activate': minions_across.activate_ash_walkers
    },
    CharrMinionType.FLAMECALLER: {
        'name': 'Charr Flamecaller',
        'prefix': 'FC',
        'description': 'Charges power, then AOE damage',
        'stats': {'health': 8, 'physical_def': 5, 'elemental_def': 4, 'move': 1,
                  'physical_dmg': 0, 'elemental_dmg': 1, 'attack_range': 1},
        'activate': minions_across.activate_flamecallers
    },
    CharrMinionType.STALKER: {
        'name': 'Charr Stalker',
        'prefix': 'St',
        'description': 'Long-range physical attacker',
        'stats': {'health': 8, 'physical_def': 4, 'elemental_def': 4, 'move': 1,
                  'physical_dmg': 1, 'elemental_dmg': 0, 'attack_range': 4},
        'activate': minions_across.activate_stalkers
    },
    CharrMinionType.SCOUT: {
        'name': 'Charr Scout',
        'prefix': 'Sc',
        'description': 'Runs to opposite edge, marks heroes',
        'stats': {'health': 8, 'physical_def': 4, 'elemental_def': 4, 'move': 2,
                  'physical_dmg': 0, 'elemental_dmg': 0, 'attack_range': 0},
        'activate': minions_across.activate_scouts
    }
}

def blade_storm_bleed_listener(figure, damage_taken, damage_source, **kwargs):
    """Blade Storm passive: Apply Bleed 3 if attack brings target below half HP"""
    # Only trigger if damage source is a Blade Storm
    if (damage_source and 
        hasattr(damage_source, 'figure_type') and
        damage_source.figure_type == FigureType.MINION and
        damage_source.get_effect('minion_type') == CharrMinionType.BLADE_STORM.value):
        
        # Check if target took damage and is now below half HP
        total_damage = damage_taken.get('physical_damage_taken', 0) + damage_taken.get('elemental_damage_taken', 0)
        if total_damage > 0 and figure.current_health < figure.max_health / 2:
            print(f"{damage_source.name} cuts deep! {figure.name} is now bleeding!")
            figure.add_condition(Condition.BLEED, 3, incremental=True)

across_cards = [
    {
        "id": 1,
        "name": "Suffering",
        "text": "This turn, the attacks of Charr Ash Walkers also target all heroes within 2 spaces of the target.",
        "function": across_suffering,
        "spawn": "blade_storm"
    },
    {
        "id": 2,
        "name": "Inferno",
        "text": "Each Charr Flamecaller deals 3 Elemental Damage to each adjacent hero.",
        "function": across_inferno,
        "spawn": "blade_storm"
    },
    {
        "id": 3,
        "name": "Ignite Arrows",
        "text": "Before enemy activations, place a power counter on each Charr Stalker. While those Stalkers live, their attacks deal 1 Elemental Damage to the target and all heroes adjacent to them.",
        "function": across_ignite_arrows,
        "spawn": "axe_fiend"
    },
    {
        "id": 4,
        "name": "Riposte",
        "text": "This turn, any hero who attacks an adjacent Charr Blade Storm takes 1 Physical Damage.",
        "pending_function": across_riposte,
        "function": None,
        "spawn": "axe_fiend"
    },
    {
        "id": 5,
        "name": "Pin Down",
        "text": "Any hero damaged by a Charr Stalker this round is Slowed.",
        "function": across_pin_down,
        "spawn": "ash_walker"
    },
    {
        "id": 6,
        "name": "Whirling Axe",
        "text": "This turn, Charr Axe Fiends attack all heroes within 2 spaces.",
        "function": across_whirling_axe,
        "spawn": "ash_walker"
    },
    {
        "id": 7,
        "name": "Hamstring",
        "text": "Any hero damaged by a Charr Blade Storm or Charr Axe Fiend this round is Slowed.",
        "function": across_hamstring,
        "spawn": "flamecaller"
    },
    {
        "id": 8,
        "name": "Whirling Defense",
        "text": "During the Hero turn this is the pending card, Charr Stalkers get +2 to defenses against ranged attacks.",
        "pending_function": across_whirling_defense,
        "function": None,
        "spawn": "flamecaller"
    },
    {
        "id": 9,
        "name": "Faintheartedness",
        "text": "Any hero damaged by a Charr Ash Walker this round is Slowed.",
        "function": across_faintheartedness,
        "spawn": "stalker"
    },
    {
        "id": 10,
        "name": "Bestial Force",
        "text": "Any hero damaged by any Charr this round is knocked back a number of spaces equal to the damage done.",
        "function": across_bestial_force,
        "spawn": "stalker"
    },
    {
        "id": 11,
        "name": "Shieldwall",
        "text": "During the Hero turn this is the pending card, Charr Blade Storms and Charr Axe Fiends get +2 to all defenses. They do not move in the Enemy phase.",
        "pending_function": across_shieldwall,
        "function": None,
        "spawn": "scout_left"
    },
    {
        "id": 12,
        "name": "Phoenix Fire",
        "text": "All Charr Flamecallers heal to full health.",
        "function": across_phoenix_fire,
        "spawn": "scout_right"
    },
]

boss_ability_cards = [
    {
        "id": 1,
        "name": "Firestorm",
        "text": "Place a marker in each heroes' locations. At the start of the next boss turn, each marker deals 2 Elemental Damage to each hero in that square and 1 Elemental Damage to each hero adjacent.",
        "function": boss_firestorm
    },
    {
        "id": 2,
        "name": "Incendiary Bonds",
        "text": "Attach Incendiary Bonds to a random hero. At the start of the next boss turn, that hero and all other heroes within Range 2 of them take 3 Elemental Damage and Burning 3.",
        "function": boss_incendiary_bonds
    },
    {
        "id": 3,
        "name": "Legion Commander",
        "text": "Place a Hunter's Mark on a random hero (prioritizing unmarked ones). Then each Marked hero takes 1 Physical Damage.",
        "function": boss_legion_commander
    },
    {
        "id": 4,
        "name": "Conjure Flame",
        "text": "This turn, the boss's basic attack deals +3 Elemental Damage and knocks its target back equal to the health loss.",
        "function": boss_conjure_flame
    },
]

class EncounterAcross(EncounterBase):
    def __init__(self):
        super().__init__()
        self.name = "Across the Wall"
        self.card_list = across_cards
        self.boss_ability_list = boss_ability_cards
        self.phase = 'GAUNTLET'
        self.cards_drawn = 0
        self.shuffle_deck()
        # Note: get_next_card() is called in setup_map() after map is initialized

    def shuffle_deck(self):
        most_cards = [c for c in self.card_list if c["id"] != 10]
        random.shuffle(most_cards)
        self.deck = most_cards + [c for c in self.card_list if c["id"] == 10]
    
    def get_next_card(self):
        if len(self.deck) == 0:
            self.shuffle_deck()

        self.next_card = self.deck.pop(0)
        self.cards_drawn += 1
        
        # Spawn boss after 12 gauntlet cards
        if self.phase == 'GAUNTLET' and self.cards_drawn >= 12:
            print("\n=== THE GAUNTLET IS COMPLETE ===")
            print("Bonfazz Burntfur, the Charr Legion Commander, enters the battle!\n")
            self.spawn_boss(self.map)
            self.shuffle_boss_deck()
            self.get_next_boss_card()
        
        # Call pending_function immediately when card is revealed (before hero turn)
        if self.next_card.get('pending_function'):
            self.next_card['pending_function'](self.map)
    
    def get_deployment_zone(self):
        zone = []
        for x in range(2, 9):
            zone.append((x, 1))
            zone.append((x, 2))
            zone.append((x, 3))
        
        return zone
    
    def shuffle_boss_deck(self):
        """Shuffle the boss ability deck"""
        self.boss_deck = self.boss_ability_list.copy()
        random.shuffle(self.boss_deck)
    
    def get_next_boss_card(self):
        """Draw next boss ability card"""
        if len(self.boss_deck) == 0:
            self.shuffle_boss_deck()
        
        self.next_boss_card = self.boss_deck.pop(0)

    def setup_map(self, map):
        # Register Blade Storm bleed listener
        map.events.register(GameEvent.DAMAGE_TAKEN, blade_storm_bleed_listener)
        
        # Initial enemy spawns for the gauntlet phase
        # Top row (y=10)
        self.spawn_minion(map, CharrMinionType.STALKER, Coords(3, 10))      # Fourth from left
        self.spawn_minion(map, CharrMinionType.ASH_WALKER, Coords(7, 10))   # Fourth from right
        
        # Second-from-top row (y=9)
        self.spawn_minion(map, CharrMinionType.FLAMECALLER, Coords(5, 9))   # Center
        
        # Third-from-top row (y=8)
        self.spawn_minion(map, CharrMinionType.BLADE_STORM, Coords(1, 8))   # Second from left
        self.spawn_minion(map, CharrMinionType.AXE_FIEND, Coords(9, 8))     # Second from right
        
        # Draw the first card now that map is set up
        self.get_next_card()

    # Generic minion spawn function
    def spawn_minion(self, map, minion_type, coords):
        """Spawn a minion of the specified type using MINION_CONFIGS"""
        config = MINION_CONFIGS[minion_type]
        stats = config['stats']
        
        minion = Figure(
            config['name'], FigureType.MINION,
            health=stats['health'],
            physical_def=stats['physical_def'],
            elemental_def=stats['elemental_def'],
            move=stats['move'],
            physical_dmg=stats['physical_dmg'],
            elemental_dmg=stats['elemental_dmg'],
            attack_range=stats['attack_range']
        )
        minion.add_effect('minion_type', minion_type.value)
        minion.add_effect('prefix', config['prefix'])
        
        # Special case: Flamecallers start with 0 power counters
        if minion_type == CharrMinionType.FLAMECALLER:
            minion.add_effect('power_counters', 0)
        
        # Special case: Scouts track their direction (needed for movement)
        if minion_type == CharrMinionType.SCOUT:
            # Determine direction based on spawn position (left half = right, right half = left)
            if coords.x <= 5:
                minion.add_effect('scout_direction', 'right')  # Moving towards right edge (x=10)
            else:
                minion.add_effect('scout_direction', 'left')   # Moving towards left edge (x=0)
        
        map.add_figure(minion, coords, on_occupied='find_empty')
        return minion
    
    def spawn_boss(self, map): #after the gauntlet phase ends
        boss = Figure(
            "Bonfazz Burntfur", FigureType.BOSS, 
            health=50, physical_def=4, elemental_def=4, move=3, physical_dmg=3, elemental_dmg=0, attack_range=1
        )
        map.add_figure(boss, Coords(10, 5))
        self.phase = 'BOSS_FIGHT'

    def perform_boss_turn(self):
        # Execute minion card function if it exists
        if self.next_card.get('function'):
            print(f"Charr use their ability: {self.next_card['name']}")
            self.next_card['function'](self.map)
        
        if self.phase == 'BOSS_FIGHT':
            # Boss phase: Execute boss ability and basic action
            boss = self.map.get_figures_by_type(FigureType.BOSS)[0]
            print(f"Boss uses: {self.next_boss_card['name']}")
            self.next_boss_card['function'](self.map, boss)
            self.boss_action()
        
        # Activate all minion types (happens in both phases)
        for minion_type in CharrMinionType:
            self.activate_minions(minion_type)
        
        # Handle minion spawn AFTER activation (so new minions don't act this round)
        if self.next_card.get('spawn'):
            spawn_type_str = self.next_card['spawn']
            # Convert string to CharrMinionType enum
            if spawn_type_str == 'scout_left':
                minion_type = CharrMinionType.SCOUT
                spawn_coords = Coords(0, 10)  # Left edge, top
            elif spawn_type_str == 'scout_right':
                minion_type = CharrMinionType.SCOUT
                spawn_coords = Coords(10, 10)  # Right edge, top
            else:
                # Convert string to enum (e.g., 'blade_storm' -> CharrMinionType.BLADE_STORM)
                minion_type = CharrMinionType[spawn_type_str.upper()]
                # random spawn along top row
                if self.phase == 'GAUNTLET':
                    spawn_coords = Coords(random.randint(0, 10), 10)
                else:
                    # Boss phase: spawn on random board edge
                    edge = random.choice(['top', 'bottom', 'left', 'right'])
                    if edge == 'top':
                        spawn_coords = Coords(random.randint(0, 10), 10)
                    elif edge == 'bottom':
                        spawn_coords = Coords(random.randint(0, 10), 0)
                    elif edge == 'left':
                        spawn_coords = Coords(0, random.randint(0, 10))
                    else:  # right
                        spawn_coords = Coords(10, random.randint(0, 10))
            
            print(f"A {MINION_CONFIGS[minion_type]['name']} spawns!")
            self.spawn_minion(self.map, minion_type, spawn_coords)
        
        if self.phase == 'GAUNTLET':
            # Gauntlet-specific: move the map
            self.move_map()
        
        # Get next card(s) for the following round
        self.get_next_card()
        if self.phase == 'BOSS_FIGHT':
            self.get_next_boss_card()
    
    def boss_action(self):
        """Boss basic action"""
        from encounters.enemy_ai import choose_target_hero, make_enemy_move
        
        boss = self.map.get_figures_by_type(FigureType.BOSS)[0]
        target_hero = choose_target_hero(self.map, boss)
        
        if not target_hero:
            return
        
        make_enemy_move(self.map, enemy=boss, player=target_hero)
        
        # Check if in range to attack
        if self.map.distance_between(boss.position, target_hero.position) <= boss.attack_range:
            # Check for Conjure Flame bonus
            elemental_bonus = 3 if boss.get_effect('conjure_flame') else 0
            
            print(f"{boss.name} attacks {target_hero.name}!")
            self.map.deal_damage(boss, target_hero, 
                               physical_damage=boss.physical_dmg, 
                               elemental_damage=boss.elemental_dmg + elemental_bonus)
    
    # Generic activation dispatcher
    def activate_minions(self, minion_type):
        """Activate all minions of a specific type using config"""
        config = MINION_CONFIGS[minion_type]
        config['activate'](self, self.map, minion_type.value)
    
    def mark_hero(self, hero):
        """Mark a hero for falling behind. If already marked, deal heavy damage instead."""
        if hero.get_effect('marked'):
            # Hero is already marked - deal heavy damage
            print(f"{hero.name} is caught by pursuing enemies while Marked! Takes 10 physical damage!")
            hero.lose_health(10, source=None)
        else:
            # Hero is not marked yet - apply mark
            print(f"{hero.name} falls behind and is Marked by pursuing enemies!")
            hero.add_effect('marked', True)
    
    def move_map(self):
        """Shift all figures downward by 1 space, simulating forward movement in the gauntlet"""
        # Get all figures and their current positions
        figures_and_positions = [(fig, self.map.get_figure_position(fig)) for fig in self.map.figures]
        
        # Sort by Y coordinate (ascending) - process from bottom to top
        figures_and_positions.sort(key=lambda x: x[1].y)
        
        # Move each figure down by 1 (y -= 1)
        for figure, current_pos in figures_and_positions:
            new_y = current_pos.y - 1
            
            # Check if figure would fall off the bottom (y < 0)
            if new_y < 0:
                # Figure stays on the bottom row
                print(f"{figure.name} at the bottom edge of the map!")
                
                # If it's a hero, they get marked (or take heavy damage if already marked)
                if figure.figure_type == FigureType.HERO:
                    self.mark_hero(figure)
                # Don't move the figure (stays at y=0)
            else:
                # Try to move down, but check for blocking figures
                target_pos = Coords(current_pos.x, new_y)
                
                # Check if the space directly below has blocking figures
                square_contents = self.map.get_square_contents(target_pos)
                blocking_figures = [f for f in square_contents if f.figure_type != FigureType.MARKER]
                
                if blocking_figures:
                    # Space is blocked - try diagonal moves
                    diagonal_options = [
                        Coords(current_pos.x - 1, new_y),  # Down-left
                        Coords(current_pos.x + 1, new_y),  # Down-right
                    ]
                    
                    # Find first available diagonal space
                    moved = False
                    for diag_pos in diagonal_options:
                        # Check if diagonal is in bounds and has no blocking figures
                        if 0 <= diag_pos.x < self.map.width:
                            diag_contents = self.map.get_square_contents(diag_pos)
                            diag_blocking = [f for f in diag_contents if f.figure_type != FigureType.MARKER]
                            if not diag_blocking:
                                self.map.move_figure(figure, diag_pos)
                                print(f"{figure.name} moves diagonally to avoid collision")
                                moved = True
                                break
                    
                    # If no diagonal available, don't move
                    if not moved:
                        print(f"{figure.name} blocked - cannot move down")
                else:
                    # Space is clear, move down normally
                    self.map.move_figure(figure, target_pos)