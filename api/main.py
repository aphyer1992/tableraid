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


def get_session(session_id: str) -> GameSession:
    if session_id not in sessions:
        sessions[session_id] = GameSession()
    return sessions[session_id]


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
        session.start(req.encounter, req.heroes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return serialize_session(session)


@app.post("/api/action")
def submit_action(req: ActionRequest, session_id: str = Query(...)):
    """Submit a player action."""
    session = get_session(session_id)
    try:
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return serialize_session(session)


# ---------------------------------------------------------------------------
# Serve React frontend (after `npm run build` → frontend/dist/)
# ---------------------------------------------------------------------------

_frontend_dist = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')
if os.path.isdir(_frontend_dist):
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")
