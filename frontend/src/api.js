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

  // Campaign
  campaignCreate: (roster) =>
    request('/campaign/create', { method: 'POST', body: JSON.stringify({ roster }) }),
  campaignState: () => request('/campaign/state'),
  campaignParty: (hero_ids) =>
    request('/campaign/party', { method: 'POST', body: JSON.stringify({ hero_ids }) }),
  campaignFightStart: () =>
    request('/campaign/fight/start', { method: 'POST', body: JSON.stringify({}) }),
  campaignFightAction: (type, extra = {}) =>
    request('/campaign/fight/action', { method: 'POST', body: JSON.stringify({ type, ...extra }) }),
  campaignLootAssign: (assignments) =>
    request('/campaign/loot/assign', { method: 'POST', body: JSON.stringify({ assignments }) }),
  campaignFightResign: () =>
    request('/campaign/fight/resign', { method: 'POST', body: JSON.stringify({}) }),
  campaignRosterAdd: (archetype) =>
    request('/campaign/roster/add', { method: 'POST', body: JSON.stringify({ archetype }) }),
  campaignExport: () => request('/campaign/export'),
  campaignImport: (save_string) =>
    request('/campaign/import', { method: 'POST', body: JSON.stringify({ save_string }) }),
}
