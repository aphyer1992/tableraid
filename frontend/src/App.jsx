import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from './api.js'
import GameBoard from './components/GameBoard.jsx'
import HeroPanel from './components/HeroPanel.jsx'
import BossPanel from './components/BossPanel.jsx'
import SetupScreen from './components/SetupScreen.jsx'
import HomeScreen from './components/HomeScreen.jsx'
import CampaignSetupScreen from './components/CampaignSetupScreen.jsx'
import CampaignScreen from './components/CampaignScreen.jsx'

const BOSS_DISPLAY = { sael: "Sa'el", como: 'Comorragh' }
const bossName = (id) => BOSS_DISPLAY[id] || id

export default function App() {
  const [mode, setMode] = useState('home')
  const [gameState, setGameState] = useState(null)
  const [campaignState, setCampaignState] = useState(null)
  const [error, setError] = useState(null)
  const [meta, setMeta] = useState(null)
  const [loading, setLoading] = useState(false)
  const [cursorPos, setCursorPos] = useState({ x: 0, y: 0 })
  const [xCostPrimed, setXCostPrimed] = useState(null) // { heroName, abilityIdx, abilityName, energy, minEnergy, maxEnergy }
  const isDraggingRef = useRef(false)
  const dragDestRef = useRef(null)   // mouseup coords if fired before 'move' response
  const dragStartRef = useRef(null)  // cell where drag began (click on same cell = cancel)
  const pendingRef = useRef(null)    // pending_interaction set by 'move' response (avoids stale closure)

  // Load available encounters + heroes on mount; also try to restore an existing campaign
  useEffect(() => {
    api.getMeta().then(setMeta).catch(console.error)
    api.getState().then(setGameState).catch(console.error)
    api.campaignState().then(cs => {
      if (cs?.campaign) {
        setCampaignState(cs)
        const phase = cs.campaign.phase
        setMode(phase === 'fight' ? 'campaign_fight' : `campaign_${phase}`)
      }
    }).catch(() => {})
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
      setMode('single_game')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // Campaign handlers
  const handleCampaignStart = useCallback(async (roster) => {
    setError(null)
    setLoading(true)
    try {
      const cs = await api.campaignCreate(roster)
      setCampaignState(cs)
      setMode('campaign_hub')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const handleCampaignAction = useCallback(async (actionName, payload = {}) => {
    setError(null)
    setLoading(true)
    try {
      let cs
      if (actionName === 'select_party') {
        cs = await api.campaignParty(payload.hero_ids)
      } else if (actionName === 'loot_assign') {
        cs = await api.campaignLootAssign(payload.assignments)
      } else if (actionName === 'add_hero') {
        cs = await api.campaignRosterAdd(payload.archetype)
      } else {
        throw new Error(`Unknown campaign action: ${actionName}`)
      }
      setCampaignState(cs)
      const phase = cs.campaign.phase
      setMode(phase === 'fight' ? 'campaign_fight' : `campaign_${phase}`)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const handleCampaignFightStart = useCallback(async () => {
    setError(null)
    setLoading(true)
    try {
      const cs = await api.campaignFightStart()
      setCampaignState(cs)
      setMode('campaign_fight')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const handleCampaignResign = useCallback(async () => {
    if (!window.confirm('Resign this fight? You will lose this week and reset to the first boss.')) return
    setError(null)
    setLoading(true)
    try {
      const cs = await api.campaignFightResign()
      setCampaignState(cs)
      setMode('campaign_hub')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const campaignDispatch = useCallback(async (type, extra = {}) => {
    setError(null)
    setLoading(true)
    try {
      const cs = await api.campaignFightAction(type, extra)
      setCampaignState(cs)
      const phase = cs.campaign.phase
      if (phase !== 'fight') {
        setMode(`campaign_${phase}`)
      }
      // Handle drag-to-move for campaign fight: mirror single-game drag logic
      if (type === 'move' && isDraggingRef.current) {
        const dest = dragDestRef.current
        dragDestRef.current = null
        if (dest !== null) {
          isDraggingRef.current = false
          const valid = cs.fight?.pending_interaction?.valid_choices || []
          const isSameCell = dragStartRef.current && dest.x === dragStartRef.current.x && dest.y === dragStartRef.current.y
          if (!isSameCell && valid.some(c => c.x === dest.x && c.y === dest.y)) {
            const cs2 = await api.campaignFightAction('select', dest)
            setCampaignState(cs2)
          } else {
            const cs2 = await api.campaignFightAction('cancel', {})
            setCampaignState(cs2)
          }
        } else {
          pendingRef.current = cs.fight?.pending_interaction
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

  // Active fight state — either single game or campaign fight
  const activeFight = mode === 'campaign_fight' ? campaignState?.fight : gameState
  const activeDispatch = mode === 'campaign_fight' ? campaignDispatch : dispatch

  // Clicks resolve pending interactions during hero turn (placement handled by mousedown)
  const handleCellClick = useCallback((x, y) => {
    if (!activeFight) return
    if (activeFight.pending_interaction) {
      const valid = activeFight.pending_interaction.valid_choices || []
      if (valid.some(c => c.x === x && c.y === y)) {
        activeDispatch('select', { x, y })
      }
    }
  }, [activeFight, activeDispatch])

  // Drag-to-move: mousedown on an activated hero tile with move_available initiates move.
  // Also handles placement: mousedown on a valid placement zone cell places the next hero.
  const handleCellMouseDown = useCallback((x, y) => {
    if (!activeFight) return

    // Placement phase: mousedown on valid zone cell places the next hero
    if (activeFight.phase === 'placement') {
      const zone = activeFight.placement_zone || []
      if (zone.some(c => c.x === x && c.y === y)) {
        activeDispatch('place_hero', { x, y })
      }
      return
    }

    if (activeFight.phase !== 'hero_turn' || activeFight.pending_interaction) return
    const hero = activeFight.heroes.find(h =>
      h.activated && h.move_available && h.position?.x === x && h.position?.y === y
    )
    if (!hero) return
    isDraggingRef.current = true
    dragDestRef.current = null
    dragStartRef.current = { x, y }
    pendingRef.current = null
    activeDispatch('move', { hero: hero.name })
  }, [activeFight, activeDispatch])

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
        activeDispatch('select', { x, y })
      } else {
        activeDispatch('cancel')
      }
    } else {
      // Case B: API still in flight — store dest; dispatch will resolve after response
      dragDestRef.current = { x, y }
    }
  }, [activeDispatch])

  // Keyboard cursor navigation + ability hotkeys
  useEffect(() => {
    const onKey = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return
      const mapW = activeFight?.map?.width ?? 11
      const mapH = activeFight?.map?.height ?? 11
      const pending = activeFight?.pending_interaction

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
          const hero = activeFight?.heroes?.find(h => h.name === xCostPrimed.heroName)
          if (hero?.position) setCursorPos(hero.position)
          activeDispatch('cast_ability', { hero: xCostPrimed.heroName, ability_index: xCostPrimed.abilityIdx, energy: xCostPrimed.energy })
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

      if (e.key === 'Escape') { activeDispatch('cancel'); return }

      const heroAtCursor = activeFight?.heroes?.find(
        h => h.position?.x === cursorPos.x && h.position?.y === cursorPos.y
      )

      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        if (pending) {
          const isValid = pending.valid_choices?.some(c => c.x === cursorPos.x && c.y === cursorPos.y)
          if (isValid) {
            if (pending.type !== 'hero_move') {
              const hero = activeFight?.heroes?.find(h => h.name === pending.hero_name)
              if (hero?.position) setCursorPos(hero.position)
            }
            activeDispatch('select', { x: cursorPos.x, y: cursorPos.y })
          }
        } else if (activeFight?.phase === 'hero_turn' && heroAtCursor && !heroAtCursor.activated) {
          activeDispatch('activate', { hero: heroAtCursor.name })
        }
        return
      }
      if ((e.key === 'm' || e.key === 'M') && !pending) {
        if (heroAtCursor?.activated && heroAtCursor?.move_available && !loading)
          activeDispatch('move', { hero: heroAtCursor.name })
        return
      }
      if ((e.key === 'a' || e.key === 'A') && !pending) {
        if (heroAtCursor?.activated && heroAtCursor?.attack_available && !loading)
          activeDispatch('attack', { hero: heroAtCursor.name })
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
            activeDispatch('cast_ability', { hero: heroAtCursor.name, ability_index: abilityIdx, energy: ability.energy_cost })
          }
        }
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [activeFight, cursorPos, xCostPrimed, loading, activeDispatch])

  if (!meta) {
    return <div style={{ padding: 40 }}>Loading...</div>
  }

  if (mode === 'home') {
    return (
      <HomeScreen
        onSingle={() => { setError(null); setMode('single_setup') }}
        onCampaign={() => { setError(null); setMode('campaign_setup') }}
      />
    )
  }

  if (mode === 'single_setup') {
    return (
      <SetupScreen
        meta={meta}
        onStart={handleStart}
        onBack={() => setMode('home')}
        error={error}
        loading={loading}
      />
    )
  }

  if (mode === 'campaign_setup') {
    return (
      <CampaignSetupScreen
        meta={meta}
        onStart={handleCampaignStart}
        onBack={() => setMode('home')}
        error={error}
        loading={loading}
      />
    )
  }

  if (mode === 'campaign_hub' || mode === 'campaign_loot' || mode === 'campaign_finished') {
    return (
      <CampaignScreen
        campaignState={campaignState}
        onAction={handleCampaignAction}
        onFightStart={handleCampaignFightStart}
        availableHeroes={meta.heroes}
        error={error}
        loading={loading}
      />
    )
  }

  // Single game idle — shouldn't normally reach here since we route to setup, but handle gracefully
  if (mode === 'single_game' && (!gameState || gameState.phase === 'idle')) {
    return (
      <SetupScreen
        meta={meta}
        onStart={handleStart}
        onBack={() => setMode('home')}
        error={error}
        loading={loading}
      />
    )
  }

  const pending = activeFight?.pending_interaction
  const validCoords = new Set(
    (activeFight?.phase === 'placement'
      ? activeFight.placement_zone
      : pending?.valid_choices || []
    ).map(c => `${c.x},${c.y}`)
  )

  const heroAttackMap = {}
  if (activeFight?.heroes) {
    for (const h of activeFight.heroes) {
      if (h.activated && h.attack_available && h.position) {
        heroAttackMap[`${h.position.x},${h.position.y}`] = h.name
      }
    }
  }

  const handleCellAttack = (x, y) => {
    const heroName = heroAttackMap[`${x},${y}`]
    if (heroName && !pending && !loading) activeDispatch('attack', { hero: heroName })
  }

  // Campaign fight header strip
  const campaignFightHeader = mode === 'campaign_fight' && campaignState ? (
    <div style={{ background: '#0a0a14', borderBottom: '1px solid #333', padding: '4px 16px', display: 'flex', gap: 24, alignItems: 'center', fontSize: 13 }}>
      <span style={{ color: '#f1c40f' }}>Week <strong>{campaignState.campaign.week}</strong></span>
      <span style={{ color: '#aaa' }}>vs <strong style={{ color: '#e74c3c' }}>{bossName(campaignState.campaign.current_boss) || 'Boss'}</strong></span>
      <button
        onClick={handleCampaignResign}
        disabled={loading}
        style={{ marginLeft: 'auto', background: '#5d1a1a', color: '#f66', border: '1px solid #7f1d1d', borderRadius: 3, padding: '2px 10px', fontSize: 11, cursor: 'pointer', opacity: loading ? 0.5 : 1 }}
      >
        Resign Week
      </button>
    </div>
  ) : null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {campaignFightHeader}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
      {/* Left: hero panel */}
      <div style={{ width: 220, overflowY: 'auto', background: '#16213e', borderRight: '1px solid #333' }}>
        <HeroPanel
          heroes={activeFight?.heroes}
          phase={activeFight?.phase}
          pending={pending}
          dispatch={activeDispatch}
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
        {activeFight?.phase === 'placement' && (
          <div style={{ background: '#1e3a5f', padding: '6px 12px', fontSize: 13 }}>
            Placing: <strong>{activeFight.placement_next_hero}</strong> — click a blue cell
          </div>
        )}
        {pending && (
          <div style={{ background: '#1e3a5f', padding: '6px 12px', fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ flex: 1 }}>{interactionLabel(pending)} — click a highlighted cell</span>
            <button
              onClick={() => activeDispatch('cancel')}
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
              onClick={() => { activeDispatch('cast_ability', { hero: xCostPrimed.heroName, ability_index: xCostPrimed.abilityIdx, energy: xCostPrimed.energy }); setXCostPrimed(null) }}
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
          {activeFight?.map && (
            <GameBoard
              mapData={activeFight.map}
              validCoords={validCoords}
              pendingType={pending?.type || (activeFight.phase === 'placement' ? 'placement' : null)}
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
          {(activeFight?.log || []).slice().reverse().map((msg, i) => (
            <div key={i} style={{ color: '#aaa', lineHeight: 1.6 }}>{msg}</div>
          ))}
        </div>
      </div>

      {/* Right: boss panel */}
      <div style={{ width: 220, overflowY: 'auto', background: '#16213e', borderLeft: '1px solid #333' }}>
        <BossPanel
          bossDisplay={activeFight?.boss_display}
          phase={activeFight?.phase}
          pending={pending}
          dispatch={activeDispatch}
          loading={loading}
          mapRound={activeFight?.map?.current_round}
        />
      </div>
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
