export default function BossPanel({ bossDisplay, phase, pending, dispatch, loading, mapRound }) {
  return (
    <div style={{ padding: 8 }}>
      <div style={{ textAlign: 'center', fontWeight: 700, fontSize: 14, padding: '6px 0', borderBottom: '1px solid #333', marginBottom: 8 }}>
        Round {mapRound ?? '—'}
      </div>

      {(bossDisplay || []).map((item, i) => (
        <div key={i} style={{
          background: '#f8f4e3',
          color: '#222',
          borderRadius: 6,
          padding: 10,
          marginBottom: 10,
          border: '2px solid #c8a96b',
        }}>
          <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 6 }}>{item.name}</div>
          <div style={{ fontSize: 12, lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>{item.text}</div>
        </div>
      ))}
    </div>
  )
}
