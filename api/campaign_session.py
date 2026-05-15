"""
CampaignSession manages the multi-week campaign lifecycle.
It holds a roster of heroes that persist across weeks, tracks boss progress,
and owns a GameSession for the currently active fight.
"""

import uuid
import json
import base64
import random
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.game_session import GameSession, _resolve_display_names
from figure import FigureType

CAMPAIGN_BOSS_ORDER = ['sael', 'como']

BOSS_LOOT_TABLES = {
    'sael': ['frozen_crown', 'storms_eye', 'icicle_shards', 'glacial_bulwark', 'robes_of_true_ice', 'mana_storm_potion'],
}


class CampaignSession:
    def __init__(self):
        self.week = 1
        self.boss_index = 0
        # phase: 'hub' | 'fight' | 'loot' | 'finished'
        self.phase = 'hub'
        self.roster = []       # list of {hero_id, archetype, display_name, loot: [item_id]}
        self.week_party = []   # hero_ids selected for this week's fights
        self.pending_loot = [] # item_ids awaiting player assignment (during 'loot' phase)
        self.current_fight = None  # GameSession when in fight
        self.log = []

    # -------------------------------------------------------------------------
    # Campaign setup
    # -------------------------------------------------------------------------

    def create(self, roster_archetypes: list[str]):
        """Build roster from archetype names. Duplicates auto-numbered."""
        from heroes.hero_archetypes import hero_archetypes
        valid = {a['name'] for a in hero_archetypes}
        invalid = [a for a in roster_archetypes if a not in valid]
        if invalid:
            raise ValueError(f"Unknown hero class(es): {invalid}")
        if not roster_archetypes:
            raise ValueError("Roster must have at least one hero")

        specs = _resolve_display_names(roster_archetypes)
        self.roster = [
            {'hero_id': str(uuid.uuid4()), 'archetype': arch, 'display_name': disp, 'loot': []}
            for arch, disp in specs
        ]
        self.week = 1
        self.boss_index = 0
        self.phase = 'hub'
        self.week_party = []
        self.pending_loot = []
        self.current_fight = None
        self.log = ['Campaign started. Choose your party for Week 1.']

    # -------------------------------------------------------------------------
    # Hub actions
    # -------------------------------------------------------------------------

    def select_party(self, hero_ids: list[str]):
        """Select which roster heroes will fight this week."""
        if self.phase != 'hub':
            raise ValueError("Not at hub")
        roster_ids = {r['hero_id'] for r in self.roster}
        invalid = [hid for hid in hero_ids if hid not in roster_ids]
        if invalid:
            raise ValueError(f"Unknown hero ids: {invalid}")
        if not hero_ids:
            raise ValueError("Must select at least one hero")
        if len(set(hero_ids)) != len(hero_ids):
            raise ValueError("Duplicate hero ids in selection")
        self.week_party = hero_ids

    def start_fight(self):
        """Start the next fight using current boss and selected party."""
        if self.phase != 'hub':
            raise ValueError("Not at hub")
        if not self.week_party:
            raise ValueError("No party selected — call select_party first")
        if self.boss_index >= len(CAMPAIGN_BOSS_ORDER):
            raise ValueError("No more bosses")

        boss_id = CAMPAIGN_BOSS_ORDER[self.boss_index]
        party = [r for r in self.roster if r['hero_id'] in self.week_party]
        hero_specs = [(r['archetype'], r['display_name']) for r in party]

        self.current_fight = GameSession()
        self.current_fight.start(boss_id, hero_specs)

        # Apply each hero's items
        from items import get_item
        for entry in party:
            hero_obj = self.current_fight._get_hero(entry['display_name'])
            for item_id in entry['loot']:
                get_item(item_id).apply(hero_obj, self.current_fight.map)

        self.phase = 'fight'
        self.log.append(f"Week {self.week}: Fighting {boss_id.capitalize()}.")

    # -------------------------------------------------------------------------
    # Fight outcome
    # -------------------------------------------------------------------------

    def resign_fight(self):
        """Treat the current fight as a loss and return to hub for next week."""
        if self.phase != 'fight':
            raise ValueError("Not in fight")
        boss_id = CAMPAIGN_BOSS_ORDER[self.boss_index]
        self.log.append(f"Week {self.week}: Resigned fight against {boss_id.capitalize()}. Advancing to Week {self.week + 1}.")
        self.week += 1
        self.boss_index = 0
        self.week_party = []
        self.current_fight = None
        self.phase = 'hub'

    def handle_fight_outcome(self):
        """Inspect finished fight and advance campaign state."""
        if self.current_fight is None or self.current_fight.phase != 'game_over':
            raise ValueError("No finished fight to resolve")

        bosses_alive = self.current_fight.map.get_figures_by_type(FigureType.BOSS)
        victory = len(bosses_alive) == 0
        boss_id = CAMPAIGN_BOSS_ORDER[self.boss_index]

        if victory:
            self.log.append(f"Week {self.week}: {boss_id.capitalize()} defeated!")
            loot_table = BOSS_LOOT_TABLES.get(boss_id, [])
            self.pending_loot = random.sample(loot_table, min(2, len(loot_table)))
            self.phase = 'loot'
        else:
            self.log.append(f"Week {self.week}: Defeated by {boss_id.capitalize()}. Advancing to Week {self.week + 1}.")
            self.week += 1
            self.boss_index = 0
            self.week_party = []
            self.current_fight = None
            self.phase = 'hub'

    def assign_loot(self, assignments: list[dict]):
        """Assign pending loot items to heroes. assignments: [{item_id, hero_id}, ...]"""
        if self.phase != 'loot':
            raise ValueError("Not in loot phase")
        assigned_item_ids = [a['item_id'] for a in assignments]
        if sorted(assigned_item_ids) != sorted(self.pending_loot):
            raise ValueError("Assigned item IDs don't match pending loot")
        roster_by_id = {r['hero_id']: r for r in self.roster}
        for a in assignments:
            if a['hero_id'] not in roster_by_id:
                raise ValueError(f"Unknown hero id: {a['hero_id']}")
            roster_by_id[a['hero_id']]['loot'].append(a['item_id'])
        self.pending_loot = []
        self.current_fight = None
        self.boss_index += 1
        if self.boss_index >= len(CAMPAIGN_BOSS_ORDER):
            self.phase = 'finished'
            self.log.append(f"Campaign complete! Final score: Week {self.week}.")
        else:
            self.phase = 'hub'
            next_boss = CAMPAIGN_BOSS_ORDER[self.boss_index]
            self.log.append(f"Week {self.week} continues — next: {next_boss.capitalize()}.")

    # -------------------------------------------------------------------------
    # Roster management
    # -------------------------------------------------------------------------

    def add_roster_hero(self, archetype: str):
        """Add a new hero to the roster at the hub between weeks."""
        if self.phase != 'hub':
            raise ValueError("Can only add heroes at the hub")
        from heroes.hero_archetypes import hero_archetypes
        valid = {a['name'] for a in hero_archetypes}
        if archetype not in valid:
            raise ValueError(f"Unknown hero archetype: {archetype}")
        existing_display = {r['display_name'] for r in self.roster}
        candidate = archetype
        n = 1
        while candidate in existing_display:
            n += 1
            candidate = f"{archetype} {n}"
        self.roster.append({
            'hero_id': str(uuid.uuid4()),
            'archetype': archetype,
            'display_name': candidate,
            'loot': [],
        })
        self.log.append(f"Added {candidate} to roster.")

    # -------------------------------------------------------------------------
    # Save / Load
    # -------------------------------------------------------------------------

    def export_save(self) -> str:
        payload = {
            'week': self.week,
            'boss_index': self.boss_index,
            'phase': 'hub',  # never save mid-fight or loot state
            'roster': self.roster,
            'week_party': self.week_party,
            'log': self.log[-20:],
        }
        return base64.b64encode(json.dumps(payload).encode()).decode()

    @classmethod
    def from_save(cls, save_string: str) -> 'CampaignSession':
        try:
            payload = json.loads(base64.b64decode(save_string.encode()).decode())
        except Exception:
            raise ValueError("Invalid save string")
        cs = cls()
        cs.week = payload['week']
        cs.boss_index = payload['boss_index']
        cs.phase = payload.get('phase', 'hub')
        cs.roster = payload['roster']
        cs.week_party = payload.get('week_party', [])
        cs.pending_loot = payload.get('pending_loot', [])
        cs.log = payload.get('log', [])
        cs.current_fight = None
        return cs
