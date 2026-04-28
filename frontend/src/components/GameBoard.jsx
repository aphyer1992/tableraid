import Cell from './Cell.jsx'

const CELL_SIZE = 60

// Figure-type colours (fallback when figure has no cell_color)
const TYPE_COLORS = {
  hero: '#1a4a7a',
  boss: '#7a1a1a',
  minion: '#4a1a7a',
  obstacle: '#555',
  marker: 'transparent',
}

export default function GameBoard({ mapData, validCoords, pendingType, onCellClick, onCellMouseDown, onCellMouseUp }) {
  const { width, height, cells, special_tiles = {} } = mapData

  // Build special-tile lookup: "x,y" -> color
  const specialTileColors = {}
  for (const tile of Object.values(special_tiles)) {
    for (const coord of tile.coords) {
      specialTileColors[`${coord.x},${coord.y}`] = tile.color
    }
  }

  // Render rows bottom-to-top (y=0 at bottom)
  const rows = []
  for (let y = height - 1; y >= 0; y--) {
    const rowCells = []
    for (let x = 0; x < width; x++) {
      const key = `${x},${y}`
      const cellData = cells[y][x]
      const isValid = validCoords.has(key)
      const specialColor = specialTileColors[key]

      rowCells.push(
        <Cell
          key={key}
          x={x}
          y={y}
          figures={cellData.figures}
          isValid={isValid}
          pendingType={pendingType}
          specialColor={specialColor}
          cellSize={CELL_SIZE}
          onClick={() => onCellClick(x, y)}
          onMouseDown={() => onCellMouseDown?.(x, y)}
          onMouseUp={() => onCellMouseUp?.(x, y)}
        />
      )
    }
    rows.push(
      <div key={y} style={{ display: 'flex' }}>
        {rowCells}
      </div>
    )
  }

  return (
    <div style={{ border: '2px solid #444', display: 'inline-block' }}>
      {rows}
    </div>
  )
}
