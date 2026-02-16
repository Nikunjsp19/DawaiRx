const API_BASE = import.meta.env.VITE_API_URL || ''

function getAuthHeaders() {
  const token = localStorage.getItem('auth_token')
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`
  return headers
}

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`
  let res
  try {
    res = await fetch(url, { ...options, headers: { ...getAuthHeaders(), ...options.headers } })
  } catch (e) {
    if (e?.message === 'Failed to fetch' || e?.name === 'TypeError') {
      const port = (import.meta.env.VITE_API_URL || '').match(/:(\d+)/)?.[1] || '8080'
      throw new Error(`Cannot connect to the server. Is the backend running? (expected on port ${port})`)
    }
    throw e
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    const msg = Array.isArray(err.detail) ? err.detail.map((d) => d.msg || d).join(', ') : (err.detail || err.message || `HTTP ${res.status}`)
    throw new Error(typeof msg === 'string' ? msg : `HTTP ${res.status}`)
  }
  if (res.status === 204) return null
  const contentType = res.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) return res.json()
  return res.blob()
}

export async function listRuns(limit = 10, offset = 0) {
  return request(`/api/runs?limit=${limit}&offset=${offset}`)
}

export async function getRun(runId) {
  return request(`/api/runs/${encodeURIComponent(runId)}`)
}

export async function getRunItems(runId) {
  return request(`/api/runs/${encodeURIComponent(runId)}/items`)
}

export async function getMedicineDetails(runId, medicineIdentifier) {
  return request(`/api/runs/${encodeURIComponent(runId)}/medicine/${encodeURIComponent(medicineIdentifier)}`)
}

export async function getRunItemsFromCsv(runId) {
  const res = await fetch(`${API_BASE}/api/runs/${encodeURIComponent(runId)}/items/csv`, { headers: getAuthHeaders() })
  if (!res.ok) throw new Error('Failed to fetch CSV items')
  const text = await res.text()
  const lines = text.split(/\r?\n/).filter(Boolean)
  if (lines.length < 2) return []
  const headers = lines[0].split(',').map((h) => h.trim())
  return lines.slice(1).map((line) => {
    const values = line.split(',').map((v) => v.trim())
    const row = {}
    headers.forEach((h, i) => { row[h] = values[i] != null ? values[i] : '' })
    return row
  })
}

export async function deleteRun(runId) {
  return request(`/api/runs/${encodeURIComponent(runId)}`, { method: 'DELETE' })
}

export async function downloadFile(runId, fileType) {
  const token = localStorage.getItem('auth_token')
  const url = `${API_BASE}/api/download/${encodeURIComponent(runId)}/${encodeURIComponent(fileType)}`
  const res = await fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
  if (!res.ok) throw new Error('Download failed')
  const blob = await res.blob()
  const disposition = res.headers.get('Content-Disposition')
  let filename = 'download'
  if (disposition) {
    const match = disposition.match(/filename="?([^";]+)"?/)
    if (match) filename = match[1]
  }
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename
  a.click()
  URL.revokeObjectURL(a.href)
}

export async function importReportCsv(file) {
  const form = new FormData()
  form.append('file', file)
  const token = localStorage.getItem('auth_token')
  const res = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || err.message || 'Import failed')
  }
  return res.json()
}

/** Upload + run (backend does full pipeline in one request; can take minutes for large files).
 *  Optional signal for cancel/timeout. Returns { run_id, ... }. */
export const UPLOAD_TIMEOUT_MS = 10 * 60 * 1000 // 10 minutes

export async function uploadReportFiles(orderedFiles, soldFile, mappingFile = null, dateFrom = null, dateTo = null, reportName = null, signal = null) {
  const form = new FormData()
  const ordered = Array.isArray(orderedFiles) ? orderedFiles : orderedFiles ? [orderedFiles] : []
  ordered.forEach((f) => form.append('ordered_files', f))
  if (soldFile) form.append('sold_file', soldFile)
  if (mappingFile) form.append('mapping_file', mappingFile)
  if (dateFrom) form.append('date_from', dateFrom)
  if (dateTo) form.append('date_to', dateTo)
  if (reportName) form.append('report_name', reportName)
  const token = localStorage.getItem('auth_token')
  const res = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
    signal: signal ?? undefined,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    const detail = Array.isArray(err.detail) ? err.detail.map((d) => d.msg || d).join(', ') : (err.detail || err.message)
    throw new Error(detail || 'Upload failed')
  }
  return res.json()
}

/** Run reconciliation after upload. Uses session_id from uploadReportFiles. Returns { success, run_id, ... }. */
export async function runReport(sessionId, dateFrom, dateTo, reportName) {
  const form = new FormData()
  form.append('session_id', sessionId)
  if (dateFrom) form.append('date_from', dateFrom)
  if (dateTo) form.append('date_to', dateTo)
  if (reportName) form.append('report_name', reportName)
  const token = localStorage.getItem('auth_token')
  const res = await fetch(`${API_BASE}/api/run`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    const detail = Array.isArray(err.detail) ? err.detail.map((d) => d.msg || d).join(', ') : (err.detail || err.message)
    throw new Error(detail || 'Reconciliation failed')
  }
  return res.json()
}

export async function login(userId, password) {
  const data = await request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, password }),
  })
  return data
}

export async function register({ userId, email, password }) {
  return request('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, email: email || '', password }),
  })
}

export async function requestAccess({ userId, email, company, reason }) {
  return request('/api/auth/request-access', {
    method: 'POST',
    body: JSON.stringify({
      user_id: userId,
      email: email || undefined,
      company: company || undefined,
      reason: reason || undefined,
    }),
  })
}

export async function checkRequestStatus(userId) {
  try {
    return await request(`/api/auth/check-approval/${encodeURIComponent(userId)}`)
  } catch {
    const res = await fetch(
      `${API_BASE}/api/auth/check-status?email=${encodeURIComponent(userId)}`,
      { headers: { 'Content-Type': 'application/json' } }
    )
    if (!res.ok) throw new Error('Failed to check status')
    return res.json()
  }
}

export async function updateSettings({ email, currentPassword, newPassword }) {
  const payload = {}
  if (email != null && email !== '') payload.email = email
  if (currentPassword) payload.current_password = currentPassword
  if (newPassword) payload.new_password = newPassword
  return request('/api/auth/settings', {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export async function isAdmin() {
  try {
    const data = await request('/api/admin/is-admin')
    return { is_admin: data?.is_admin === true }
  } catch {
    try {
      const data = await request('/api/auth/me')
      return { is_admin: data?.is_admin === true }
    } catch {
      return { is_admin: false }
    }
  }
}

export async function getCurrentUser() {
  try {
    const data = await request('/api/auth/me')
    return data
  } catch {
    const userId = localStorage.getItem('user_id')
    return { user_id: userId || null, email: null }
  }
}

const REQUESTS_PAGE_SIZE = 10

function normalizeRequestsResponse(data) {
  if (Array.isArray(data)) return { requests: data, total: data.length }
  if (data?.requests && data?.total !== undefined) return { requests: data.requests, total: data.total }
  if (Array.isArray(data?.requests)) return { requests: data.requests, total: data.requests.length }
  return { requests: [], total: 0 }
}

/** List registration requests (admin only). Returns { requests, total }. Supports pagination. */
export async function listAdminRequests(statusFilter = 'all', page = 1, limit = REQUESTS_PAGE_SIZE) {
  const params = new URLSearchParams()
  if (statusFilter && statusFilter !== 'all') params.set('status_filter', statusFilter)
  params.set('page', String(Math.max(1, page)))
  params.set('limit', String(Math.max(1, Math.min(100, limit))))
  const data = await request(`/api/admin/requests?${params.toString()}`)
  return normalizeRequestsResponse(data)
}

export async function approveRequest(userId, adminNotes = null) {
  try {
    return await request(`/api/admin/approve-request/${encodeURIComponent(userId)}`, {
      method: 'POST',
      body: JSON.stringify({ admin_notes: adminNotes }),
    })
  } catch {
    return request(`/api/admin/requests/${encodeURIComponent(userId)}/approve`, { method: 'POST' })
  }
}

export async function rejectRequest(userId, adminNotes = null) {
  try {
    return await request(`/api/admin/reject-request/${encodeURIComponent(userId)}`, {
      method: 'POST',
      body: JSON.stringify({ admin_notes: adminNotes }),
    })
  } catch {
    return request(`/api/admin/requests/${encodeURIComponent(userId)}/reject`, { method: 'POST' })
  }
}

/** List all users (admin only). Returns { users: [{ user_id, email, disabled }] }. */
export async function listAdminUsers() {
  const data = await request('/api/admin/users')
  const list = Array.isArray(data?.users) ? data.users : []
  return { users: list }
}

/** Disable a user (admin only). Fails if targeting self. */
export async function disableAdminUser(targetUserId) {
  return request(`/api/admin/users/${encodeURIComponent(targetUserId)}/disable`, { method: 'POST' })
}

/** Enable a user (admin only). */
export async function enableAdminUser(targetUserId) {
  return request(`/api/admin/users/${encodeURIComponent(targetUserId)}/enable`, { method: 'POST' })
}

/** Delete a user permanently (admin only). Cannot delete self or admins. */
export async function deleteAdminUser(targetUserId) {
  return request(`/api/admin/users/${encodeURIComponent(targetUserId)}`, { method: 'DELETE' })
}

/**
 * Report generation stats per user (admin only).
 * Options: { days }, or { fromDate, toDate } (YYYY-MM-DD), and optional { q } for customer search.
 * Returns { stats: [{ user_id, report_count }], days?, from_date?, to_date? }.
 */
export async function listAdminReportStats(options = {}) {
  const { days: daysOpt, fromDate, toDate, q } = options
  const params = new URLSearchParams()
  if (fromDate && toDate) {
    params.set('from_date', fromDate)
    params.set('to_date', toDate)
  } else {
    const d = Math.max(1, Math.min(365, Number(daysOpt) ?? 30))
    params.set('days', String(d))
  }
  if (q != null && String(q).trim()) params.set('q', String(q).trim())
  const query = params.toString()
  const path = `/api/admin/report-stats${query ? `?${query}` : ''}`
  try {
    return await request(path)
  } catch (e) {
    if (e?.message?.includes('404')) {
      const pathAlt = `/api/admin/report_stats${query ? `?${query}` : ''}`
      return await request(pathAlt)
    }
    throw e
  }
}

export async function canSelfRegister(userId) {
  const status = await checkRequestStatus(userId)
  const approved = status?.approved === true || status?.status === 'approved'
  return { approved, status }
}

export async function getHealth() {
  try {
    return await request('/health')
  } catch {
    return { status: 'unknown' }
  }
}
