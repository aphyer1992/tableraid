import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from './api.js'
import GameBoard from './components/GameBoard.jsx'
import HeroPanel from './components/HeroPanel.jsx'
import BossPanel from './components/BossPanel.jsx'
import SetupScreen from './components/SetupScreen.jsx'

export default function App() {
  const [gameState, setGameState] = useState(null)
  const [error, setError] = useState(null)
  const [meta, setMeta] = useState(null)
  const [loading, setLoading] = useState(false)
  const isDraggingRef = useRef(false)
  const dragDestRef = useRef(null)   // mouseup coords if fired before 'move' response
  const dragStartRef = useRef(null)  // cell where drag began (click on same cell = cancel)
  const pendingRef = useRef(null)    // pending_interaction set by 'move' response (avoids stale closure)

  // Load available encounters + heroes on mount
  useEffect(() => {
    api.getMeta().then(setMeta).catch(console.error)
    api.getState().then(setGameState).catch(console.error)
  }, [])

  const dispatch = useCallback(async (type, extra = {}) => {
    setError(null)
    setLoading(true)
    try {
      const newState = await api.action(type, extra)
      setGameState(newState)
      // Handle drag-to-move: coordinate between mousedown dispatch and mouseup handler
      if (type === 'move' && isDraggingRef.current) {
        const dest = dragDestRef.current
        dragDestRef.current = null
        if (dest !== null) {
          // Case B: mouseup already fired while API was in flight — resolve now
          isDraggingRef.current = false
          const valid = newState.pending_interaction?.valid_choices || []
          const isSameCell = dragStartRef.current && dest.x === dragStartRef.current.x && dest.y === dragStartRef.current.y
          if (!isSameCell && valid.some(c => c.x === dest.x && c.y === dest.y)) {
            const s2 = await api.action('select', dest)
            setGameState(s2)
          } else {
            const s2 = await api.action('cancel', {})
            setGameState(s2)
          }
        } else {
          // Case A: mouseup hasn't fired yet — store pending so mouseup can read it without stale closure
          pendingRef.current = newState.pending_interaction
        }
      }
    } catch (e) {
      setError(e.message)
      isDraggingRef.current = false
      dragDestRef.current = null
      dragStartRef.current = null
      pendingRef.current = null
    } finally {
      setLoading(false)
    }
  }, [])

  const handleStart = useCallback(async (encounter, heroes) => {
    setError(null)
    setLoading(true)
    try {
      const newState = await api.start(encounter, heroes)
      setGameState(newState)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // Clicks resolve pending interactions during hero turn (placement handled by mousedown)
  const handleCellClick = useCallback((x, y) => {
    if (!gameState) return
    if (gameState.pending_interaction) {
      const valid = gameState.pending_interaction.valid_choices || []
      if (valid.some(c => c.x === x && c.y === y)) {
        dispatch('select', { x, y })
      }
    }
  }, [gameState, dispatch])

  // Drag-to-move: mousedown on an activated hero tile with move_available initiates move.
  // Also handles placement: mousedown on a valid placement zone cell places the next hero.
  const handleCellMouseDown = useCallback((x, y) => {
    if (!gameState) return

    // Placement phase: mousedown on valid zone cell places the next hero
    if (gameState.phase === 'placement') {
      const zone = gameState.placement_zone || []
      if (zone.some(c => c.x === x && c.y === y)) {
        dispatch('place_hero', { x, y })
      }
      return
    }

    if (gameState.phase !== 'hero_turn' || gameState.pending_interaction) return
    const hero = gameState.heroes.find(h =>
      h.activated && h.move_available && h.position?.x === x && h.position?.y === y
    )
    if (!hero) return
    isDraggingRef.current = true
    dragDestRef.current = null
    dragStartRef.current = { x, y }
    pendingRef.current = null
    dispatch('move', { hero: hero.name })
  }, [gameState, dispatch])

  // Drag-to-move: mouseup on destination resolves the move.
  // Uses pendingRef (not gameState) to avoid stale closure when API responds before mouseup.
  const handleCellMouseUp = useCallback((x, y) => {
    if (!isDraggingRef.current) return
    const pi = pendingRef.current
    pendingRef.current = null
    const isSameCell = dragStartRef.current && x === dragStartRef.current.x && y === dragStartRef.current.y
    if (pi?.type === 'hero_move') {
      // Case A: API already responded — resolve now
      isDraggingRef.current = false
      const valid = pi.valid_choices || []
      if (!isSameCell && valid.some(c => c.x === x && c.y === y)) {
        dispatch('select', { x, y })
      } else {
        dispatch('cancel')
      }
    } else {
      // Case B: API still in flight — store dest; dispatch will resolve after response
      dragDestRef.current = { x, y }
    }
  }, [dispatch])

  if (!meta) {
    return <div style={{ padding: 40 }}>Loading...</div>
  }

  if (!gameState || gameState.phase === 'idle') {
    return (
      <SetupScreen
        meta={meta}
        onStart={handleStart}
        error={error}
        loading={loading}
      />
    )
  }

  const pending = gameState.pending_interaction
  const validCoords = new Set(
    (gameState.phase === 'placement'
      ? gameState.placement_zone
      : pending?.valid_choices || []
    ).map(c => `${c.x},${c.y}`)
  )

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Left: hero panel */}
      <div style={{ width: 220, overflowY: 'auto', background: '#16213e', borderRight: '1px solid #333' }}>
        <HeroPanel
          heroes={gameState.heroes}
          phase={gameState.phase}
          pending={pending}
          dispatch={dispatch}
          loading={loading}
        />
      </div>

      {/* Center: map + log */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {error && (
          <div style={{ background: '#7f1d1d', padding: '6px 12px', fontSize: 13 }}>
            {error}
          </div>
        )}
        {gameState.phase === 'placement' && (
          <div style={{ background: '#1e3a5f', padding: '6px 12px', fontSize: 13 }}>
            Placing: <strong>{gameState.placement_next_hero}</strong> — click a blue cell
          </div>
        )}
        {pending && (
          <div style={{ background: '#1e3a5f', padding: '6px 12px', fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ flex: 1 }}>{interactionLabel(pending)} — click a highlighted cell</span>
            <button
              onClick={() => dispatch('cancel')}
              disabled={loading}
              style={{ background: '#7f1d1d', color: '#fff', fontSize: 11, padding: '2px 8px', borderRadius: 3 }}
            >
              Cancel
            </button>
          </div>
        )}

        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
          {gameState.map && (
            <GameBoard
              mapData={gameState.map}
              validCoords={validCoords}
              pendingType={pending?.type || (gameState.phase === 'placement' ? 'placement' : null)}
              onCellClick={handleCellClick}
              onCellMouseDown={handleCellMouseDown}
              onCellMouseUp={handleCellMouseUp}
            />
          )}
        </div>

        {/* Log */}
        <div style={{ height: 80, overflowY: 'auto', background: '#0f0f1a', padding: '4px 12px', fontSize: 12, borderTop: '1px solid #333' }}>
          {(gameState.log || []).slice().reverse().map((msg, i) => (
            <div key={i} style={{ color: '#aaa', lineHeight: 1.6 }}>{msg}</div>
          ))}
        </div>
      </div>

      {/* Right: boss panel */}
      <div style={{ width: 220, overflowY: 'auto', background: '#16213e', borderLeft: '1px solid #333' }}>
        <BossPanel
          bossDisplay={gameState.boss_display}
          phase={gameState.phase}
          pending={pending}
          dispatch={dispatch}
          loading={loading}
          mapRound={gameState.map?.current_round}
        />
      </div>
    </div>
  )
}

function interactionLabel(pending) {
  switch (pending.type) {
    case 'hero_move': return `Move ${pending.hero_name}`
    case 'hero_attack': return `Attack with ${pending.hero_name}`
    case 'choose_friendly_target': return 'Choose a friendly target'
    default: return 'Select a target'
  }
}
