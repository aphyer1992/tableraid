import { useState } from 'react'

export default function CampaignSetupScreen({ meta, onStart, onBack, error, loading }) {
  const defaultSize = Math.min(6, meta.heroes.length)
  const [roster, setRoster] = useState(
    Array.from({ length: defaultSize }, (_, i) => meta.heroes[i % meta.heroes.length])
  )

  const setSlot = (idx, name) => setRoster(r => { const n = [...r]; n[idx] = name; return n })
  const addSlot = () => roster.length < 12 && setRoster(r => [...r, meta.heroes[0]])
  const removeSlot = () => roster.length > 1 && setRoster(r => r.slice(0, -1))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', gap: 20, padding: 40, background: '#0f0f1a', color: '#eee' }}>
      <h1 style={{ fontSize: 36, letterSpacing: 3, margin: 0 }}>TABLERAID</h1>

      <div style={{ background: '#16213e', padding: 28, borderRadius: 8, width: 380 }}>
        <button
          onClick={onBack}
          style={{ background: 'none', color: '#888', border: 'none', cursor: 'pointer', fontSize: 12, padding: 0, marginBottom: 12 }}
        >
          ← Back
        </button>
        <h2 style={{ margin: '0 0 6px', fontSize: 18 }}>New Campaign — Build Roster</h2>
        <p style={{ fontSize: 12, color: '#888', margin: '0 0 16px' }}>
          Build your starting roster. You can recruit additional heroes from the hub between weeks.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 12 }}>
          {roster.map((name, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 12, color: '#555', width: 18, textAlign: 'right' }}>{idx + 1}</span>
              <select
                value={name}
                onChange={e => setSlot(idx, e.target.value)}
                style={{ flex: 1, padding: '5px 8px', background: '#0f3460', color: '#eee', border: '1px solid #333', borderRadius: 4, fontSize: 13 }}
              >
                {meta.heroes.map(h => <option key={h} value={h}>{h}</option>)}
              </select>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
          <button
            onClick={addSlot}
            disabled={roster.length >= 12}
            style={{ flex: 1, background: '#1a5276', color: '#fff', border: 'none', borderRadius: 4, padding: '5px 0', fontSize: 12, cursor: 'pointer', opacity: roster.length >= 12 ? 0.4 : 1 }}
          >
            + Add Hero
          </button>
          <button
            onClick={removeSlot}
            disabled={roster.length <= 1}
            style={{ flex: 1, background: '#444', color: '#fff', border: 'none', borderRadius: 4, padding: '5px 0', fontSize: 12, cursor: 'pointer', opacity: roster.length <= 1 ? 0.4 : 1 }}
          >
            − Remove
          </button>
        </div>

        {error && <div style={{ color: '#f66', fontSize: 13, marginBottom: 12 }}>{error}</div>}

        <button
          onClick={() => onStart(roster)}
          disabled={loading}
          style={{ background: '#27ae60', color: '#fff', width: '100%', padding: '11px 0', fontSize: 15, border: 'none', borderRadius: 4, cursor: 'pointer', opacity: loading ? 0.6 : 1 }}
        >
          {loading ? 'Starting…' : 'Start Campaign'}
        </button>
      </div>
    </div>
  )
}
