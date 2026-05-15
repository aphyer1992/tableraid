import { useState } from 'react'
import { api } from '../api.js'

const BOSS_DISPLAY = { sael: "Sa'el", como: 'Comorragh' }
const bossName = (id) => BOSS_DISPLAY[id] || id

export default function CampaignScreen({ campaignState, onAction, onFightStart, availableHeroes, error, loading }) {
  const { campaign } = campaignState
  const { week, boss_order, boss_index, phase, roster, week_party, log } = campaign

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', gap: 16, padding: 24, background: '#0f0f1a', color: '#eee' }}>
      <h1 style={{ fontSize: 28, letterSpacing: 3, margin: 0 }}>TABLERAID — Campaign</h1>

      {/* Week + boss progress */}
      <div style={{ fontSize: 14, color: '#aaa' }}>
        Week <strong style={{ color: '#f1c40f', fontSize: 18 }}>{week}</strong>
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        {boss_order.map((b, i) => (
          <div key={b} style={{
            padding: '5px 14px', borderRadius: 4, fontSize: 13,
            background: i < boss_index ? '#1e8449' : i === boss_index ? '#922b21' : '#2c3e50',
            color: i < boss_index ? '#adffa9' : '#fff',
            border: i === boss_index ? '1px solid #e74c3c' : '1px solid transparent',
          }}>
            {bossName(b)}{i < boss_index ? ' ✓' : ''}
          </div>
        ))}
      </div>

      {phase === 'hub' && (
        <HubPanel
          roster={roster}
          weekParty={week_party}
          onAction={onAction}
          onFightStart={onFightStart}
          availableHeroes={availableHeroes || []}
          loading={loading}
        />
      )}

      {phase === 'loot' && (
        <LootPanel
          roster={roster}
          weekParty={week_party}
          pendingLoot={campaign.pending_loot || []}
          onAssign={(assignments) => onAction('loot_assign', { assignments })}
          loading={loading}
        />
      )}

      {phase === 'finished' && (
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <div style={{ fontSize: 24, color: '#27ae60', marginBottom: 8 }}>Campaign Complete!</div>
          <div style={{ fontSize: 16, color: '#f1c40f' }}>Final Score: Week {week}</div>
          <div style={{ fontSize: 13, color: '#aaa', marginTop: 8 }}>Lower is better. Well played!</div>
        </div>
      )}

      {error && <div style={{ color: '#f66', fontSize: 13 }}>{error}</div>}

      {/* Log */}
      <div style={{ width: 520, background: '#0a0a14', borderRadius: 4, padding: '8px 12px', fontSize: 12, maxHeight: 100, overflowY: 'auto', border: '1px solid #222' }}>
        {(log || []).slice().reverse().map((m, i) => (
          <div key={i} style={{ color: '#aaa', lineHeight: 1.6 }}>{m}</div>
        ))}
      </div>

      <SaveLoadPanel loading={loading} />
    </div>
  )
}

function HubPanel({ roster, weekParty, onAction, onFightStart, availableHeroes, loading }) {
  const [selectedIds, setSelectedIds] = useState(new Set(weekParty))
  const [recruitArchetype, setRecruitArchetype] = useState(availableHeroes[0] || '')

  const toggle = (id) => setSelectedIds(prev => {
    const next = new Set(prev)
    next.has(id) ? next.delete(id) : next.add(id)
    return next
  })

  const partyConfirmed = weekParty.length > 0
  const selectionChanged = selectedIds.size !== weekParty.length ||
    [...selectedIds].some(id => !weekParty.includes(id))

  return (
    <div style={{ background: '#16213e', padding: 24, borderRadius: 8, width: 520 }}>
      <h3 style={{ margin: '0 0 12px', fontSize: 15 }}>Roster — click to select heroes for this week</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 16 }}>
        {roster.map(r => {
          const selected = selectedIds.has(r.hero_id)
          return (
            <div
              key={r.hero_id}
              onClick={() => toggle(r.hero_id)}
              style={{
                display: 'flex', alignItems: 'center', gap: 12, padding: '7px 12px',
                background: selected ? '#1a3a5c' : '#0f1a2e',
                border: selected ? '1px solid #f1c40f' : '1px solid #2c3e50',
                borderRadius: 4, cursor: 'pointer',
              }}
            >
              <span style={{ fontWeight: 700, minWidth: 90, color: selected ? '#f1c40f' : '#eee' }}>{r.display_name}</span>
              <span style={{ fontSize: 11, color: '#666' }}>({r.archetype})</span>
              <span style={{ fontSize: 11, color: '#c0392b', marginLeft: 'auto' }}>
                {r.loot.length > 0 ? `${r.loot.length} item${r.loot.length > 1 ? 's' : ''}` : ''}
              </span>            </div>
          )
        })}
      </div>

      {/* Recruit a new hero */}
      {availableHeroes.length > 0 && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 12, alignItems: 'center' }}>
          <select
            value={recruitArchetype}
            onChange={e => setRecruitArchetype(e.target.value)}
            disabled={loading}
            style={{ flex: 1, padding: '5px 8px', background: '#0f3460', color: '#eee', border: '1px solid #333', borderRadius: 4, fontSize: 13 }}
          >
            {availableHeroes.map(h => <option key={h} value={h}>{h}</option>)}
          </select>
          <button
            onClick={() => onAction('add_hero', { archetype: recruitArchetype })}
            disabled={loading}
            style={{ background: '#1a5276', color: '#fff', border: 'none', borderRadius: 4, padding: '6px 14px', fontSize: 13, cursor: 'pointer', opacity: loading ? 0.5 : 1, whiteSpace: 'nowrap' }}
          >
            + Recruit
          </button>
        </div>
      )}

      <div style={{ display: 'flex', gap: 8 }}>
        <button
          onClick={() => onAction('select_party', { hero_ids: [...selectedIds] })}
          disabled={loading || selectedIds.size === 0 || !selectionChanged}
          style={{
            flex: 1, background: selectionChanged && selectedIds.size > 0 ? '#2471a3' : '#333',
            color: '#fff', border: 'none', borderRadius: 4, padding: '9px 0', fontSize: 13, cursor: 'pointer',
            opacity: (loading || selectedIds.size === 0 || !selectionChanged) ? 0.5 : 1,
          }}
        >
          Confirm Party ({selectedIds.size})
        </button>
        <button
          onClick={onFightStart}
          disabled={loading || !partyConfirmed}
          style={{
            flex: 1, background: partyConfirmed ? '#922b21' : '#333',
            color: '#fff', border: partyConfirmed ? '1px solid #e74c3c' : '1px solid transparent',
            borderRadius: 4, padding: '9px 0', fontSize: 13, cursor: 'pointer',
            opacity: (loading || !partyConfirmed) ? 0.5 : 1,
          }}
        >
          Fight!
        </button>
      </div>
      {!partyConfirmed && (
        <div style={{ fontSize: 11, color: '#666', marginTop: 8, textAlign: 'center' }}>
          Select heroes and click Confirm Party before fighting
        </div>
      )}
    </div>
  )
}

function LootPanel({ roster, weekParty, pendingLoot, onAssign, loading }) {
  const partyRoster = roster.filter(r => weekParty.includes(r.hero_id))
  // assignment: item.id → hero_id
  const [assignments, setAssignments] = useState(() => {
    const init = {}
    pendingLoot.forEach(item => { init[item.id] = partyRoster[0]?.hero_id || '' })
    return init
  })

  const handleConfirm = () => {
    const payload = pendingLoot.map(item => ({ item_id: item.id, hero_id: assignments[item.id] }))
    onAssign(payload)
  }

  const SLOT_LABEL = { head: 'Head', neck: 'Neck', both_hands: 'Both Hands', off_hand: 'Off-Hand', body: 'Body', consumable: 'Consumable' }

  return (
    <div style={{ background: '#16213e', padding: 24, borderRadius: 8, width: 520 }}>
      <h3 style={{ margin: '0 0 4px', fontSize: 15, color: '#f1c40f' }}>Victory! — Assign Loot</h3>
      <p style={{ fontSize: 13, color: '#aaa', margin: '0 0 16px' }}>
        Choose which hero receives each item.
      </p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginBottom: 20 }}>
        {pendingLoot.map(item => (
          <div key={item.id} style={{ background: '#0f1a2e', borderRadius: 4, border: '1px solid #2c3e50', padding: '10px 14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
              <span style={{ fontWeight: 700, color: '#f1c40f', fontSize: 14 }}>{item.name}</span>
              <span style={{ fontSize: 11, color: '#555' }}>{SLOT_LABEL[item.slot] || item.slot}</span>
            </div>
            <div style={{ fontSize: 12, color: '#888', marginBottom: 10 }}>{item.description}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 12, color: '#aaa' }}>Assign to:</span>
              <select
                value={assignments[item.id] || ''}
                onChange={e => setAssignments(prev => ({ ...prev, [item.id]: e.target.value }))}
                disabled={loading}
                style={{ flex: 1, padding: '4px 8px', background: '#0f3460', color: '#eee', border: '1px solid #333', borderRadius: 4, fontSize: 13 }}
              >
                {partyRoster.map(r => (
                  <option key={r.hero_id} value={r.hero_id}>{r.display_name}</option>
                ))}
              </select>
            </div>
          </div>
        ))}
      </div>
      <button
        onClick={handleConfirm}
        disabled={loading || pendingLoot.some(item => !assignments[item.id])}
        style={{ width: '100%', background: '#27ae60', color: '#fff', border: 'none', borderRadius: 4, padding: '10px 0', fontSize: 14, cursor: 'pointer', opacity: loading ? 0.6 : 1 }}
      >
        Confirm &amp; Continue
      </button>
    </div>
  )
}

function SaveLoadPanel({ loading }) {
  const [saveStr, setSaveStr] = useState('')
  const [importStr, setImportStr] = useState('')
  const [importing, setImporting] = useState(false)

  const handleExport = async () => {
    try {
      const res = await api.campaignExport()
      setSaveStr(res.save_string)
    } catch (e) {
      console.error(e)
    }
  }

  const handleImport = async () => {
    if (!importStr) return
    setImporting(true)
    try {
      await api.campaignImport(importStr)
      window.location.reload()
    } catch (e) {
      alert('Import failed: ' + e.message)
    } finally {
      setImporting(false)
    }
  }

  return (
    <div style={{ fontSize: 12, color: '#555', textAlign: 'center' }}>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginBottom: 6 }}>
        <button
          onClick={handleExport}
          disabled={loading}
          style={{ background: '#2c3e50', color: '#aaa', border: '1px solid #444', borderRadius: 3, padding: '4px 12px', fontSize: 11, cursor: 'pointer' }}
        >
          Export Save
        </button>
      </div>
      {saveStr && (
        <input
          readOnly
          value={saveStr}
          onClick={e => e.target.select()}
          style={{ width: 400, background: '#111', color: '#aaa', border: '1px solid #333', borderRadius: 3, padding: '3px 8px', fontSize: 11, marginBottom: 6 }}
        />
      )}
      <div style={{ display: 'flex', gap: 6, justifyContent: 'center' }}>
        <input
          value={importStr}
          onChange={e => setImportStr(e.target.value)}
          placeholder="Paste save string to import…"
          style={{ width: 300, background: '#111', color: '#eee', border: '1px solid #333', borderRadius: 3, padding: '3px 8px', fontSize: 11 }}
        />
        <button
          onClick={handleImport}
          disabled={importing || !importStr}
          style={{ background: '#1a5276', color: '#fff', border: 'none', borderRadius: 3, padding: '4px 10px', fontSize: 11, cursor: 'pointer', opacity: (!importStr || importing) ? 0.5 : 1 }}
        >
          Import
        </button>
      </div>
    </div>
  )
}
