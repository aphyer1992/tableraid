"""
FastAPI application for Tableraid.

Run with:  uvicorn api.main:app --reload  (from Tableraid/ directory)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

from api.game_session import GameSession
from api.serializers import serialize_session
from api.campaign_session import CampaignSession
from api.campaign_serializer import serialize_campaign_response

app = FastAPI(title="Tableraid API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Per-browser-tab sessions, keyed by client-generated UUID
sessions: dict[str, GameSession] = {}
campaign_sessions: dict[str, CampaignSession] = {}


def get_session(session_id: str) -> GameSession:
    if session_id not in sessions:
        sessions[session_id] = GameSession()
    return sessions[session_id]


def get_campaign(session_id: str) -> CampaignSession:
    if session_id not in campaign_sessions:
        campaign_sessions[session_id] = CampaignSession()
    return campaign_sessions[session_id]


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class StartRequest(BaseModel):
    encounter: str
    heroes: list[str]


class ActionRequest(BaseModel):
    type: str
    hero: Optional[str] = None
    ability_index: Optional[int] = None
    energy: Optional[int] = None
    x: Optional[int] = None
    y: Optional[int] = None


class CampaignCreateRequest(BaseModel):
    roster: list[str]


class CampaignPartyRequest(BaseModel):
    hero_ids: list[str]


class CampaignImportRequest(BaseModel):
    save_string: str


class CampaignRosterAddRequest(BaseModel):
    archetype: str


class CampaignLootAssignRequest(BaseModel):
    assignments: list[dict]   # [{'item_id': str, 'hero_id': str}, ...]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/meta")
def get_meta():
    """Return available encounters and hero names (not session-specific)."""
    tmp = GameSession()
    return {
        'encounters': tmp.get_encounters(),
        'heroes': tmp.get_hero_archetypes(),
    }


@app.get("/api/state")
def get_state(session_id: str = Query(...)):
    """Return the full current game state for this session."""
    return serialize_session(get_session(session_id))


@app.post("/api/start")
def start_game(req: StartRequest, session_id: str = Query(...)):
    """Start (or restart) a game with a given encounter and hero roster."""
    sessions[session_id] = GameSession()
    session = sessions[session_id]
    try:
        session.start_simple(req.encounter, req.heroes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return serialize_session(session)


@app.post("/api/action")
def submit_action(req: ActionRequest, session_id: str = Query(...)):
    """Submit a player action."""
    session = get_session(session_id)
    # Server-side action log
    parts = [req.type]
    if req.hero:
        parts.append(req.hero)
    if req.ability_index is not None:
        parts.append(f"ability#{req.ability_index}")
    if req.x is not None:
        parts.append(f"({req.x},{req.y})")
    print(f"  >> {' '.join(parts)}")
    try:
        _dispatch_game_action(session, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return serialize_session(session)


# ---------------------------------------------------------------------------
# Campaign routes
# ---------------------------------------------------------------------------

def _dispatch_game_action(session: GameSession, req: ActionRequest):
    """Shared action dispatch logic used by both single-game and campaign fight routes."""
    match req.type:
        case "place_hero":
            session.action_place_hero(req.x, req.y)
        case "activate":
            session.action_activate_hero(req.hero)
        case "move":
            session.action_basic_move(req.hero)
        case "attack":
            session.action_basic_attack(req.hero)
        case "cast_ability":
            session.action_cast_ability(req.hero, req.ability_index, req.energy)
        case "select":
            session.action_select(req.x, req.y)
        case "end_turn":
            session.action_end_turn()
        case "restart_round":
            session.action_restart_round()
        case "cancel":
            session.action_cancel()
        case _:
            raise ValueError(f"Unknown action type: {req.type}")


@app.post("/api/campaign/create")
def campaign_create(req: CampaignCreateRequest, session_id: str = Query(...)):
    cs = CampaignSession()
    campaign_sessions[session_id] = cs
    try:
        cs.create(req.roster)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return serialize_campaign_response(cs)


@app.get("/api/campaign/state")
def campaign_state(session_id: str = Query(...)):
    cs = campaign_sessions.get(session_id)
    if cs is None:
        raise HTTPException(404, "No campaign session found")
    return serialize_campaign_response(cs)


@app.post("/api/campaign/party")
def campaign_party(req: CampaignPartyRequest, session_id: str = Query(...)):
    cs = campaign_sessions.get(session_id)
    if cs is None:
        raise HTTPException(404, "No campaign session found")
    try:
        cs.select_party(req.hero_ids)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return serialize_campaign_response(cs)


@app.post("/api/campaign/fight/start")
def campaign_fight_start(session_id: str = Query(...)):
    cs = campaign_sessions.get(session_id)
    if cs is None:
        raise HTTPException(404, "No campaign session found")
    try:
        cs.start_fight()
    except ValueError as e:
        raise HTTPException(400, str(e))
    return serialize_campaign_response(cs)


@app.post("/api/campaign/fight/action")
def campaign_fight_action(req: ActionRequest, session_id: str = Query(...)):
    cs = campaign_sessions.get(session_id)
    if cs is None or cs.current_fight is None:
        raise HTTPException(400, "No active campaign fight")
    parts = [req.type]
    if req.hero:
        parts.append(req.hero)
    if req.ability_index is not None:
        parts.append(f"ability#{req.ability_index}")
    if req.x is not None:
        parts.append(f"({req.x},{req.y})")
    print(f"  >> [campaign] {' '.join(parts)}")
    try:
        _dispatch_game_action(cs.current_fight, req)
        if cs.current_fight.phase == 'game_over':
            cs.handle_fight_outcome()
    except ValueError as e:
        raise HTTPException(400, str(e))
    return serialize_campaign_response(cs)


@app.post("/api/campaign/loot/assign")
def campaign_loot_assign(req: CampaignLootAssignRequest, session_id: str = Query(...)):
    cs = campaign_sessions.get(session_id)
    if cs is None:
        raise HTTPException(404, "No campaign session found")
    try:
        cs.assign_loot(req.assignments)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return serialize_campaign_response(cs)


@app.post("/api/campaign/fight/resign")
def campaign_fight_resign(session_id: str = Query(...)):
    cs = campaign_sessions.get(session_id)
    if cs is None:
        raise HTTPException(404, "No campaign session found")
    try:
        cs.resign_fight()
    except ValueError as e:
        raise HTTPException(400, str(e))
    return serialize_campaign_response(cs)


@app.post("/api/campaign/roster/add")
def campaign_roster_add(req: CampaignRosterAddRequest, session_id: str = Query(...)):
    cs = campaign_sessions.get(session_id)
    if cs is None:
        raise HTTPException(404, "No campaign session found")
    try:
        cs.add_roster_hero(req.archetype)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return serialize_campaign_response(cs)


@app.get("/api/campaign/export")
def campaign_export(session_id: str = Query(...)):
    cs = campaign_sessions.get(session_id)
    if cs is None:
        raise HTTPException(404, "No campaign session found")
    return {'save_string': cs.export_save()}


@app.post("/api/campaign/import")
def campaign_import(req: CampaignImportRequest, session_id: str = Query(...)):
    try:
        cs = CampaignSession.from_save(req.save_string)
    except ValueError as e:
        raise HTTPException(400, str(e))
    campaign_sessions[session_id] = cs
    return serialize_campaign_response(cs)


# ---------------------------------------------------------------------------
# Serve React frontend (after `npm run build` → frontend/dist/)
# ---------------------------------------------------------------------------

_frontend_dist = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')
if os.path.isdir(_frontend_dist):
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")