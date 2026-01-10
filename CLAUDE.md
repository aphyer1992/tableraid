# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tableraid is a turn-based tabletop game simulation built with Python and tkinter. Heroes fight through encounters against bosses and minions on a grid-based map with D&D-style movement rules.

## Commands

```bash
# Run the game
python main.py

# Run movement/pathfinding tests
python test_movement.py

# Lint (uses .pylintrc config)
pylint *.py heroes/*.py encounters/*.py
```

## Architecture

### Core Game Loop
`main.py` creates a `Map` with an `Encounter`, spawns `Hero` instances from archetypes, and runs the `GameUI`.

### Key Components

**Map (`map.py`)** - Central game state:
- Grid of cells containing figures
- Pathfinding via `bfs()` and `bfs_with_hazards()` with D&D diagonal rules (alternating 1/2 cost)
- Combat via `deal_damage()` with defense rolls
- Turn management (`begin_hero_turn`, `execute_boss_turn`)

**Figure (`figure.py`)** - Base entity class:
- Types: `HERO`, `BOSS`, `MINION`, `OBSTACLE`, `MARKER`
- Stats: health, defenses, damage, movement
- Conditions dict (Burn, Bleed, Stunned, etc.)
- Active effects dict for temporary modifiers
- `targeting_parameters` control visibility and priority

**Hero (`heroes/hero.py`)** - Wraps Figure with:
- Energy system (spend to activate, abilities cost energy)
- Activation order affects energy cost (heroes_activated counter)
- Move/attack availability per turn
- Abilities list with castability checks

**Abilities (`heroes/ability.py`)** - Define costs and effects:
- `energy_cost`, `move_cost`, `attack_cost`
- `variable_cost` for X-cost abilities
- `setup_routine` for passive initialization
- Effects in `ability_effects.py`

### Event System

**EventManager (`events.py`)** - Observer pattern:
```python
map.events.register(GameEvent.DAMAGE_TAKEN, my_callback)
map.events.trigger(GameEvent.DAMAGE_TAKEN, figure=target, damage_taken=dmg_dict)
```

**GameEvent enum (`game_events.py`)** - Event types:
- Turn: `HERO_TURN_START/END`, `BOSS_TURN_START/END`, `START/END_FIGURE_ACTION`
- Combat: `DAMAGE_TAKEN`, `DEFENSE_ROLL`, `HEALED`
- State: `FIGURE_ADDED/REMOVED/DEATH`, `CONDITION_ADDED/REMOVED`, `GET_MOVE`

### Condition System

**Condition enum (`game_conditions.py`)** - Status effects (Burn, Bleed, Regen, Slowed, Stunned, Shielded)

**conditions.py** - Listeners that implement condition behavior:
- `condition_turn_start_listener` / `condition_turn_end_listener` - tick conditions
- `shield_listener` - damage absorption
- `slow_stun_move_listener` - movement modification via `GET_MOVE` event

### Encounters

**EncounterBase (`encounters/encounter_base.py`)** - Interface for encounters:
- `setup_map()` - spawn enemies/obstacles
- `get_boss_display_info()` - UI card display
- `perform_boss_turn()` - AI logic

Encounter-specific files contain boss cards and their effect implementations.

### UI

**GameUI (`ui.py`)** - tkinter interface:
- Selection modes: `hero_placement`, `hero_move`, `hero_attack`, `choose_friendly_target`
- `valid_choices` + `select_cmd` pattern for click handling
- `GameStateSnapshot` enables "Restart Round" functionality

## Movement Rules

- Cardinal moves cost 1
- Diagonal moves alternate: 1st costs 1, 2nd costs 2, 3rd costs 1, etc.
- Diagonal blocked if both adjacent squares contain impassible figures
- Hazard damage (lava) accumulates along path, applied as elemental damage

## Adding New Content

**New Hero**: Add archetype dict to `hero_archetypes.py`, create abilities in `ability.py` with effects in `ability_effects.py`

**New Encounter**: Subclass `EncounterBase`, implement `setup_map()` and `perform_boss_turn()`, add card effects file

**New Condition**: Add to `Condition` enum, add listener in `conditions.py`, add display config in `effects_display.py`
