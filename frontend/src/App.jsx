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
  const [cursorPos, setCursorPos] = useState({ x: 0, y: 0 })
  const [xCostPrimed, setXCostPrimed] = useState(null) // { heroName, abilityIdx, abilityName, energy, minEnergy, maxEnergy }
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
      // Resync with server after any error — if the session was reset (server restart,
      // etc.) this will return phase='idle' and the app will return to the setup screen.
      try { setGameState(await api.getState()) } catch { /* leave existing state */ }
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

  // Keyboard cursor navigation + ability hotkeys
  useEffect(() => {
    const onKey = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return
      const mapW = gameState?.map?.width ?? 11
      const mapH = gameState?.map?.height ?? 11
      const pending = gameState?.pending_interaction

      // When an X-cost ability is primed, intercept energy-adjustment keys
      if (xCostPrimed) {
        if (e.key === '+' || e.key === '=') {
          e.preventDefault()
          setXCostPrimed(p => ({ ...p, energy: Math.min(p.maxEnergy, p.energy + 1) }))
          return
        }
        if (e.key === '-') {
          e.preventDefault()
          setXCostPrimed(p => ({ ...p, energy: Math.max(p.minEnergy, p.energy - 1) }))
          return
        }
        const num = parseInt(e.key)
        if (!isNaN(num) && num >= xCostPrimed.minEnergy && num <= xCostPrimed.maxEnergy) {
          setXCostPrimed(p => ({ ...p, energy: num }))
          return
        }
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          const hero = gameState?.heroes?.find(h => h.name === xCostPrimed.heroName)
          if (hero?.position) setCursorPos(hero.position)
          dispatch('cast_ability', { hero: xCostPrimed.heroName, ability_index: xCostPrimed.abilityIdx, energy: xCostPrimed.energy })
          setXCostPrimed(null)
          return
        }
        if (e.key === 'Escape') { setXCostPrimed(null); return }
        // Arrow keys fall through
      }

      if (e.key === 'ArrowLeft')  { e.preventDefault(); setCursorPos(p => ({ ...p, x: Math.max(0, p.x - 1) })); return }
      if (e.key === 'ArrowRight') { e.preventDefault(); setCursorPos(p => ({ ...p, x: Math.min(mapW - 1, p.x + 1) })); return }
      if (e.key === 'ArrowUp')    { e.preventDefault(); setCursorPos(p => ({ ...p, y: Math.min(mapH - 1, p.y + 1) })); return }
      if (e.key === 'ArrowDown')  { e.preventDefault(); setCursorPos(p => ({ ...p, y: Math.max(0, p.y - 1) })); return }

      if (e.key === 'Escape') { dispatch('cancel'); return }

      const heroAtCursor = gameState?.heroes?.find(
        h => h.position?.x === cursorPos.x && h.position?.y === cursorPos.y
      )

      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        if (pending) {
          const isValid = pending.valid_choices?.some(c => c.x === cursorPos.x && c.y === cursorPos.y)
          if (isValid) {
            if (pending.type !== 'hero_move') {
              const hero = gameState?.heroes?.find(h => h.name === pending.hero_name)
              if (hero?.position) setCursorPos(hero.position)
            }
            dispatch('select', { x: cursorPos.x, y: cursorPos.y })
          }
        } else if (gameState?.phase === 'hero_turn' && heroAtCursor && !heroAtCursor.activated) {
          dispatch('activate', { hero: heroAtCursor.name })
        }
        return
      }
      if ((e.key === 'm' || e.key === 'M') && !pending) {
        if (heroAtCursor?.activated && heroAtCursor?.move_available && !loading)
          dispatch('move', { hero: heroAtCursor.name })
        return
      }
      if ((e.key === 'a' || e.key === 'A') && !pending) {
        if (heroAtCursor?.activated && heroAtCursor?.attack_available && !loading)
          dispatch('attack', { hero: heroAtCursor.name })
        return
      }

      // Ability hotkeys
      if (!pending && !loading && heroAtCursor) {
        const hotkey = e.key.toLowerCase()
        const abilityIdx = heroAtCursor.abilities?.findIndex(a => a.hotkey === hotkey && a.is_castable)
        if (abilityIdx != null && abilityIdx >= 0) {
          const ability = heroAtCursor.abilities[abilityIdx]
          if (ability.variable_cost) {
            setXCostPrimed({
              heroName: heroAtCursor.name,
              abilityIdx,
              abilityName: ability.name,
              energy: ability.energy_cost,
              minEnergy: ability.energy_cost,
              maxEnergy: heroAtCursor.current_energy,
            })
          } else {
            dispatch('cast_ability', { hero: heroAtCursor.name, ability_index: abilityIdx, energy: ability.energy_cost })
          }
        }
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [gameState, cursorPos, xCostPrimed, loading, dispatch])

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

  const heroAttackMap = {}
  if (gameState.heroes) {
    for (const h of gameState.heroes) {
      if (h.activated && h.attack_available && h.position) {
        heroAttackMap[`${h.position.x},${h.position.y}`] = h.name
      }
    }
  }

  const handleCellAttack = (x, y) => {
    const heroName = heroAttackMap[`${x},${y}`]
    if (heroName && !pending && !loading) dispatch('attack', { hero: heroName })
  }

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
        {xCostPrimed && (
          <div style={{ background: '#2d1e5f', padding: '6px 12px', fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>Cast <strong>{xCostPrimed.abilityName}</strong> with</span>
            <button
              onClick={() => setXCostPrimed(p => ({ ...p, energy: Math.max(p.minEnergy, p.energy - 1) }))}
              style={{ background: '#444', color: '#fff', fontSize: 12, padding: '1px 6px', borderRadius: 3 }}
            >−</button>
            <strong style={{ color: '#f1c40f', minWidth: 14, textAlign: 'center' }}>{xCostPrimed.energy}</strong>
            <button
              onClick={() => setXCostPrimed(p => ({ ...p, energy: Math.min(p.maxEnergy, p.energy + 1) }))}
              style={{ background: '#444', color: '#fff', fontSize: 12, padding: '1px 6px', borderRadius: 3 }}
            >+</button>
            <span style={{ color: '#f1c40f' }}>⚡</span>
            <span style={{ flex: 1, color: '#aaa', fontSize: 11 }}>— Enter to confirm, Esc to cancel</span>
            <button
              onClick={() => { dispatch('cast_ability', { hero: xCostPrimed.heroName, ability_index: xCostPrimed.abilityIdx, energy: xCostPrimed.energy }); setXCostPrimed(null) }}
              disabled={loading}
              style={{ background: '#6c3483', color: '#fff', fontSize: 11, padding: '2px 8px', borderRadius: 3 }}
            >Cast</button>
            <button
              onClick={() => setXCostPrimed(null)}
              style={{ background: '#7f1d1d', color: '#fff', fontSize: 11, padding: '2px 8px', borderRadius: 3 }}
            >Cancel</button>
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
              cursorPos={cursorPos}
              heroAttackMap={heroAttackMap}
              onCellAttack={handleCellAttack}
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
