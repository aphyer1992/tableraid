const BASE = '/api'

// Unique ID for this browser tab, cleared when the tab is closed.
function getSessionId() {
  let id = sessionStorage.getItem('tableraid_session_id')
  if (!id) {
    id = crypto.randomUUID()
    sessionStorage.setItem('tableraid_session_id', id)
  }
  return id
}

async function request(path, options = {}) {
  const sid = getSessionId()
  // Append session_id as a query param so GET requests can carry it too
  const url = BASE + path + (path.includes('?') ? '&' : '?') + 'session_id=' + sid
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  getMeta: () => request('/meta'),
  getState: () => request('/state'),
  start: (encounter, heroes) =>
    request('/start', { method: 'POST', body: JSON.stringify({ encounter, heroes }) }),
  action: (type, extra = {}) =>
    request('/action', { method: 'POST', body: JSON.stringify({ type, ...extra }) }),
}
