import { useState } from 'react'

export default function HeroPanel({ heroes, phase, pending, dispatch, loading }) {
  const isHeroTurn = phase === 'hero_turn'

  return (
    <div style={{ padding: '4px 6px' }}>
      {heroes.map(hero => (
        <HeroCard
          key={hero.name}
          hero={hero}
          isHeroTurn={isHeroTurn}
          pending={pending}
          dispatch={dispatch}
          loading={loading}
        />
      ))}

      {isHeroTurn && !pending && (
        <div style={{ display: 'flex', gap: 4, marginTop: 6 }}>
          <button
            onClick={() => dispatch('end_turn')}
            disabled={loading}
            style={{ flex: 1, background: '#c0392b', color: '#fff', padding: '5px 0', fontSize: 12 }}
          >
            End Turn
          </button>
          <button
            onClick={() => dispatch('restart_round')}
            disabled={loading}
            style={{ flex: 1, background: '#555', color: '#fff', padding: '5px 0', fontSize: 12 }}
          >
            Restart
          </button>
        </div>
      )}
    </div>
  )
}

function HeroCard({ hero, isHeroTurn, pending, dispatch, loading }) {
  const canAct = isHeroTurn && !pending && !loading
  const activationCost = hero.activation_cost ?? 0
  const hpPct = hero.max_health > 0 ? (hero.current_health / hero.max_health) * 100 : 0
  const hpColor = hpPct > 60 ? '#4caf50' : hpPct > 30 ? '#ff9800' : '#f44336'

  const conditionText = Object.entries(hero.conditions)
    .map(([k, v]) => `${k[0]}${v}`)
    .join(' ')

  // Extra effects to show in card header (e.g. combo_points)
  const extraEffects = Object.entries(hero.active_effects)
    .filter(([k]) => k === 'combo_points' && hero.active_effects[k] > 0)
    .map(([, v]) => `⚡${v}`)
    .join(' ')

  return (
    <div style={{
      background: '#0f3460',
      border: hero.activated ? '1px solid #f1c40f' : '1px solid #1a5276',
      boxShadow: hero.activated ? '0 0 6px rgba(241,196,15,0.45)' : 'none',
      borderRadius: 5,
      padding: '5px 6px',
      marginBottom: 5,
      opacity: hero.can_activate === false && !hero.activated ? 0.5 : 1,
    }}>
      {/* Row 1: name · hp · energy · extras */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 2 }}>
        <span style={{ fontWeight: 700, fontSize: 12, minWidth: 52 }}>{hero.name}</span>
        <span style={{ fontSize: 11, color: hpColor, whiteSpace: 'nowrap' }}>
          {hero.current_health}/{hero.max_health}
        </span>
        <div style={{ flex: 1, height: 3, background: '#333', borderRadius: 2 }}>
          <div style={{ width: `${hpPct}%`, height: '100%', background: hpColor, borderRadius: 2 }} />
        </div>
        <EnergyPips current={hero.current_energy} max={hero.max_energy} />
        {extraEffects && <span style={{ fontSize: 11, color: '#ffd700' }}>{extraEffects}</span>}
        {conditionText && <span style={{ fontSize: 10, color: '#aaa' }}>{conditionText}</span>}
      </div>

      {/* Row 2: action buttons */}
      <div style={{ display: 'flex', gap: 3, marginBottom: 4 }}>
        {!hero.activated ? (
          <button
            onClick={() => dispatch('activate', { hero: hero.name })}
            disabled={!canAct || hero.can_activate === false || hero.current_energy < activationCost}
            style={{ flex: 1, background: '#2471a3', color: '#fff', fontSize: 11, padding: '2px 0' }}
          >
            Activate ({activationCost}⚡)
          </button>
        ) : (
          <>
            <button
              onClick={() => dispatch('move', { hero: hero.name })}
              disabled={!canAct || !hero.move_available}
              style={{ flex: 1, background: hero.move_available ? '#1e8449' : '#333', color: '#fff', fontSize: 11, padding: '2px 0' }}
            >
              Move
            </button>
            <button
              onClick={() => dispatch('attack', { hero: hero.name })}
              disabled={!canAct || !hero.attack_available}
              style={{ flex: 1, background: hero.attack_available ? '#922b21' : '#333', color: '#fff', fontSize: 11, padding: '2px 0' }}
            >
              Atk
            </button>
          </>
        )}
      </div>

      {/* Row 3: ability pills */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        {hero.abilities.map((ability, idx) => (
          <AbilityPill
            key={ability.name}
            ability={ability}
            idx={idx}
            hero={hero}
            canAct={canAct}
            dispatch={dispatch}
          />
        ))}
      </div>
    </div>
  )
}

function EnergyPips({ current, max }) {
  return (
    <div style={{ display: 'flex', gap: 2, alignItems: 'center' }}>
      {Array.from({ length: max }, (_, i) => (
        <div key={i} style={{
          width: 6, height: 6,
          borderRadius: '50%',
          background: i < current ? '#f1c40f' : '#444',
          flexShrink: 0,
        }} />
      ))}
    </div>
  )
}

function AbilityPill({ ability, idx, hero, canAct, dispatch }) {
  const [energy, setEnergy] = useState(ability.energy_cost)
  const castable = ability.is_castable && canAct

  if (ability.passive) {
    return (
      <span style={{
        fontSize: 10, padding: '1px 5px', borderRadius: 3,
        background: '#222', color: '#666', fontStyle: 'italic',
      }} title={ability.description}>
        {ability.name}
      </span>
    )
  }

  const flags = [ability.move_cost && 'M', ability.attack_cost && 'A'].filter(Boolean).join('')
  const costLabel = ability.variable_cost
    ? 'X⚡'
    : ability.energy_cost > 0 ? `${ability.energy_cost}⚡` : ''
  const hotkeyLabel = ability.hotkey ? `[${ability.hotkey}] ` : ''
  const label = `${hotkeyLabel}${ability.name}${costLabel ? ' ' + costLabel : ''}${flags ? ' ' + flags : ''}`

  const handleCast = () => {
    dispatch('cast_ability', {
      hero: hero.name,
      ability_index: idx,
      energy: ability.variable_cost ? energy : ability.energy_cost,
    })
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
      {ability.variable_cost && castable && (
        <select
          value={energy}
          onChange={e => setEnergy(Number(e.target.value))}
          onClick={e => e.stopPropagation()}
          style={{
            fontSize: 10, width: 32, padding: '1px 2px',
            background: '#0f3460', color: '#eee', border: '1px solid #333', borderRadius: 3,
          }}
        >
          {Array.from(
            { length: Math.max(0, hero.current_energy - ability.energy_cost + 1) },
            (_, i) => ability.energy_cost + i
          ).map(v => <option key={v} value={v}>{v}</option>)}
        </select>
      )}
      <button
        onClick={handleCast}
        disabled={!castable}
        title={ability.description}
        style={{
          fontSize: 10,
          padding: '2px 5px',
          background: ability.used ? '#2a2a2a' : castable ? '#6c3483' : '#2a2a2a',
          color: castable ? '#eee' : '#666',
          borderRadius: 3,
          whiteSpace: 'nowrap',
        }}
      >
        {label}
      </button>
    </div>
  )
}
