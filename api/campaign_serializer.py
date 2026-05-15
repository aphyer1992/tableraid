"""Serializer for CampaignSession → dict for frontend."""

from api.campaign_session import CAMPAIGN_BOSS_ORDER
from api.serializers import serialize_session
from items import get_item


def _serialize_roster_entry(r):
    return {
        'hero_id': r['hero_id'],
        'archetype': r['archetype'],
        'display_name': r['display_name'],
        'loot': [get_item(iid).to_dict() for iid in r['loot']],
    }


def serialize_campaign(cs):
    return {
        'week': cs.week,
        'boss_index': cs.boss_index,
        'boss_order': CAMPAIGN_BOSS_ORDER,
        'current_boss': CAMPAIGN_BOSS_ORDER[cs.boss_index] if cs.boss_index < len(CAMPAIGN_BOSS_ORDER) else None,
        'phase': cs.phase,
        'roster': [_serialize_roster_entry(r) for r in cs.roster],
        'week_party': cs.week_party,
        'pending_loot': [get_item(iid).to_dict() for iid in cs.pending_loot],
        'log': cs.log[-20:],
    }


def serialize_campaign_response(cs):
    """Standard envelope returned by all campaign endpoints."""
    return {
        'campaign': serialize_campaign(cs),
        'fight': serialize_session(cs.current_fight) if cs.current_fight is not None else None,
    }
