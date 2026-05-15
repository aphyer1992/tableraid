export default function HomeScreen({ onSingle, onCampaign }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', gap: 24, background: '#0f0f1a', color: '#eee' }}>
      <h1 style={{ fontSize: 48, letterSpacing: 4, margin: 0 }}>TABLERAID</h1>
      <p style={{ color: '#666', fontSize: 14, margin: 0 }}>Choose a mode to begin</p>
      <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
        <button
          onClick={onSingle}
          style={{ background: '#2471a3', color: '#fff', padding: '14px 40px', fontSize: 16, borderRadius: 4, border: 'none', cursor: 'pointer' }}
        >
          Single Encounter
        </button>
        <button
          onClick={onCampaign}
          style={{ background: '#922b21', color: '#fff', padding: '14px 40px', fontSize: 16, borderRadius: 4, border: 'none', cursor: 'pointer' }}
        >
          Campaign
        </button>
      </div>
    </div>
  )
}
