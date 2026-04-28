import { useState } from 'react'

const PARTY_SIZE = 6

export default function SetupScreen({ meta, onStart, error, loading }) {
  const [encounter, setEncounter] = useState(meta.encounters[0]?.id || '')
  // Party is an ordered list of 6 class names (may repeat)
  const [party, setParty] = useState(
    Array.from({ length: PARTY_SIZE }, (_, i) => meta.heroes[i % meta.heroes.length] || meta.heroes[0])
  )

  const setSlot = (idx, name) => {
    const next = [...party]
    next[idx] = name
    setParty(next)
  }

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', minHeight: '100vh', gap: 24, padding: 40,
    }}>
      <h1 style={{ fontSize: 36, letterSpacing: 2 }}>TABLERAID</h1>

      <div style={{ background: '#16213e', padding: 24, borderRadius: 8, minWidth: 380 }}>
        <h2 style={{ marginBottom: 16, fontSize: 18 }}>New Game</h2>

        {/* Encounter picker */}
        <label style={{ display: 'block', marginBottom: 16 }}>
          <span style={{ fontSize: 13, color: '#aaa', display: 'block', marginBottom: 4 }}>Encounter</span>
          <select
            value={encounter}
            onChange={e => setEncounter(e.target.value)}
            style={{ width: '100%', padding: '6px 8px', background: '#0f3460', color: '#eee', border: '1px solid #333', borderRadius: 4 }}
          >
            {meta.encounters.map(enc => (
              <option key={enc.id} value={enc.id}>{enc.name}</option>
            ))}
          </select>
        </label>

        {/* Party builder — 6 slots, each a class dropdown */}
        <div style={{ marginBottom: 16 }}>
          <span style={{ fontSize: 13, color: '#aaa', display: 'block', marginBottom: 8 }}>
            Party ({PARTY_SIZE} heroes)
          </span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {party.map((heroName, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 12, color: '#666', width: 16, textAlign: 'right' }}>{idx + 1}</span>
                <select
                  value={heroName}
                  onChange={e => setSlot(idx, e.target.value)}
                  style={{
                    flex: 1, padding: '4px 8px',
                    background: '#0f3460', color: '#eee',
                    border: '1px solid #333', borderRadius: 4, fontSize: 13,
                  }}
                >
                  {meta.heroes.map(name => (
                    <option key={name} value={name}>{name}</option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        </div>

        {error && (
          <div style={{ color: '#f66', fontSize: 13, marginBottom: 12 }}>{error}</div>
        )}

        <button
          onClick={() => onStart(encounter, party)}
          disabled={loading || !encounter}
          style={{ background: '#27ae60', color: '#fff', width: '100%', padding: '10px 0', fontSize: 15 }}
        >
          {loading ? 'Starting…' : 'Start Game'}
        </button>
      </div>
    </div>
  )
}
