const TYPE_COLORS = {
  hero: '#1b4f8a',
  boss: '#8a1b1b',
  minion: '#4a1b8a',
  obstacle: '#555',
  marker: 'transparent',
}

const VALID_COLORS = {
  placement: 'rgba(100,180,255,0.55)',
  hero_move: 'rgba(80,220,100,0.55)',
  hero_attack: 'rgba(240,60,60,0.55)',
  choose_friendly_target: 'rgba(80,220,100,0.55)',
  default: 'rgba(100,180,255,0.45)',
}

export default function Cell({ x, y, figures, isValid, pendingType, specialColor, cellSize, onClick, onMouseDown, onMouseUp }) {
  // Determine background
  let bg = '#222'
  if (specialColor) bg = specialColor

  // Pick the figure with the highest rendering_priority to display.
  // Markers have priority -1; normal figures have 0+. If a cell has only a
  // marker (e.g. the Blizzard), it still gets shown.
  const mainFigure = figures.length > 0
    ? figures.reduce((best, f) =>
        (f.rendering_priority ?? 0) >= (best.rendering_priority ?? 0) ? f : best
      )
    : null

  if (mainFigure?.cell_color) bg = mainFigure.cell_color
  else if (mainFigure) bg = TYPE_COLORS[mainFigure.type] || bg

  let overlayColor = null
  if (isValid) {
    overlayColor = VALID_COLORS[pendingType] || VALID_COLORS.default
  }

  const effects = mainFigure?.effects_display || []
  const rightEffects = effects.filter(e => e.position === 'right')
  const leftEffects = effects.filter(e => e.position === 'left')

  const style = {
    width: cellSize,
    height: cellSize,
    border: '1px solid #444',
    position: 'relative',
    cursor: isValid ? 'pointer' : 'default',
    flexShrink: 0,
    background: bg,
    userSelect: 'none',
  }

  return (
    <div style={style} onClick={isValid ? onClick : undefined} onMouseDown={onMouseDown} onMouseUp={onMouseUp}>
      {/* Valid-choice overlay */}
      {overlayColor && (
        <div style={{
          position: 'absolute', inset: 0,
          background: overlayColor,
          pointerEvents: 'none',
        }} />
      )}

      {/* Figure info */}
      {mainFigure && (
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexDirection: 'column',
          color: '#fff',
          fontSize: 11,
          fontWeight: 700,
          lineHeight: 1.2,
          textAlign: 'center',
          pointerEvents: 'none',
        }}>
          {mainFigure.fixed_representation
            ? <span style={{ fontSize: 14 }}>{mainFigure.fixed_representation}</span>
            : <>
                <span>{mainFigure.name.slice(0, 3)}</span>
                {mainFigure.max_health > 0 && (
                  <>
                    <span>{mainFigure.current_health}/{mainFigure.max_health}</span>
                    <HealthBar current={mainFigure.current_health} max={mainFigure.max_health} />
                  </>
                )}
              </>
          }
        </div>
      )}

      {/* Right effects (conditions like Burn, Bleed) */}
      {rightEffects.map((eff, i) => (
        <span key={eff.key} style={{
          position: 'absolute',
          right: 1,
          bottom: 1 + i * 13,
          fontSize: 10,
          color: eff.color,
          pointerEvents: 'none',
          lineHeight: 1,
        }}>
          {eff.icon}{eff.quantity != null ? eff.quantity : ''}
        </span>
      ))}

      {/* Left effects (Shielded, Regen, combo) */}
      {leftEffects.map((eff, i) => (
        <span key={eff.key} style={{
          position: 'absolute',
          left: 1,
          bottom: 1 + i * 13,
          fontSize: 10,
          color: eff.color,
          pointerEvents: 'none',
          lineHeight: 1,
        }}>
          {eff.icon}{eff.quantity != null ? eff.quantity : ''}
        </span>
      ))}
    </div>
  )
}

function HealthBar({ current, max }) {
  const pct = max > 0 ? (current / max) * 100 : 0
  const color = pct > 60 ? '#4caf50' : pct > 30 ? '#ff9800' : '#f44336'
  return (
    <div style={{ width: '80%', height: 3, background: '#333', borderRadius: 2, marginTop: 2 }}>
      <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 2 }} />
    </div>
  )
}
