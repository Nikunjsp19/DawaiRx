import { useEffect, useMemo, useState } from 'react'
import Layout from '../components/Layout'
import { useAuth } from '../context/AuthContext'
import { approveRequest, disableAdminUser, enableAdminUser, isAdmin, listAdminRequests, listAdminReportStats, listAdminUsers, rejectRequest } from '../api/client'

const SECTION_USERS = 'users'
const SECTION_REPORTS = 'reports'
const SECTION_REQUESTS = 'requests'

const SECTIONS = [
  { id: SECTION_USERS, label: 'User page', icon: 'group' },
  { id: SECTION_REPORTS, label: 'Report generation', icon: 'assessment' },
  { id: SECTION_REQUESTS, label: 'Registration requests', icon: 'person_add' },
]

const REPORT_DAYS_OPTIONS = [7, 30, 90]

const FILTERS = ['all', 'pending', 'approved', 'rejected']
const REQUESTS_PAGE_SIZE = 10

function statusPillClass(status) {
  if (status === 'pending') return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
  if (status === 'approved') return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
  if (status === 'rejected') return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
  return 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300'
}

function RequestCard({ req, onApprove, onReject }) {
  const displayId = req.email || req.user_id || req.id || 'unknown'
  const requestUserId = req.user_id || req.id || 'unknown'
  const requestedStr = req.requested_at ? new Date(req.requested_at).toLocaleString() : '—'
  const reviewedStr = (req.reviewed_at || req.reviewed_by)
    ? `${req.reviewed_at ? new Date(req.reviewed_at).toLocaleString() : '—'}${req.reviewed_by ? ` by ${req.reviewed_by}` : ''}`
    : null

  return (
    <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-slate-200 dark:border-slate-700 p-4">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <div className="min-w-0 flex-1">
          <span className="text-sm font-semibold text-slate-900 dark:text-white truncate block">{displayId}</span>
          {req.company && (
            <span className="text-xs text-slate-500 dark:text-slate-400">Company: {req.company}</span>
          )}
        </div>
        <div className="text-xs text-slate-500 dark:text-slate-400 whitespace-nowrap shrink-0">
          Requested: {requestedStr}
        </div>
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium shrink-0 ${statusPillClass(req.status)}`}>
          {String(req.status || 'unknown').toUpperCase()}
        </span>
        {req.status === 'pending' && (
          <div className="flex gap-1.5 shrink-0">
            <button
              type="button"
              onClick={() => onApprove(requestUserId)}
              className="px-3 py-1.5 text-xs font-medium bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors"
            >
              Approve
            </button>
            <button
              type="button"
              onClick={() => onReject(requestUserId)}
              className="px-3 py-1.5 text-xs font-medium bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
            >
              Reject
            </button>
          </div>
        )}
      </div>
      {(req.reason || reviewedStr || req.admin_notes) && (
        <div className="mt-2 pt-2 border-t border-slate-100 dark:border-slate-700 space-y-1">
          {req.reason && (
            <p className="text-xs text-slate-600 dark:text-slate-400"><span className="font-medium">Reason:</span> {req.reason}</p>
          )}
          {reviewedStr && (
            <p className="text-xs text-slate-500 dark:text-slate-400">Reviewed: {reviewedStr}</p>
          )}
          {req.admin_notes && (
            <p className="text-xs text-slate-600 dark:text-slate-400 p-2 bg-slate-50 dark:bg-slate-800 rounded"><span className="font-medium">Admin notes:</span> {req.admin_notes}</p>
          )}
        </div>
      )}
    </div>
  )
}

export default function Admin() {
  const [activeSection, setActiveSection] = useState(SECTION_USERS)
  const [loading, setLoading] = useState(true)
  const [requests, setRequests] = useState([])
  const [requestsTotal, setRequestsTotal] = useState(0)
  const [requestsPage, setRequestsPage] = useState(1)
  const [filter, setFilter] = useState('all')
  const [statusMessage, setStatusMessage] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)

  const [reportStats, setReportStats] = useState([])
  const [reportStatsDays, setReportStatsDays] = useState(30)
  const [reportStatsFromDate, setReportStatsFromDate] = useState('')
  const [reportStatsToDate, setReportStatsToDate] = useState('')
  const [reportStatsSearch, setReportStatsSearch] = useState('')
  const [reportStatsLoading, setReportStatsLoading] = useState(false)
  const [reportStatsError, setReportStatsError] = useState(null)

  const [users, setUsers] = useState([])
  const [usersLoading, setUsersLoading] = useState(false)
  const [usersError, setUsersError] = useState(null)
  const [userActionLoading, setUserActionLoading] = useState(null) // target user_id while toggling disable
  const { userId: currentUserId } = useAuth()

  const [modalOpen, setModalOpen] = useState(false)
  const [modalAction, setModalAction] = useState('approve')
  const [modalUserId, setModalUserId] = useState('')
  const [modalDisplayId, setModalDisplayId] = useState('')
  const [adminNotes, setAdminNotes] = useState('')

  const loadRequests = async (statusFilter = 'all', page = 1) => {
    setLoading(true)
    setStatusMessage(null)
    try {
      const admin = await isAdmin()
      if (!admin?.is_admin) {
        setStatusMessage({ type: 'error', text: 'Access denied. Admin privileges required.' })
        setRequests([])
        setRequestsTotal(0)
        return
      }
      const data = await listAdminRequests(statusFilter, page, REQUESTS_PAGE_SIZE)
      setRequests(Array.isArray(data?.requests) ? data.requests : [])
      setRequestsTotal(Number(data?.total) ?? 0)
    } catch (err) {
      setStatusMessage({ type: 'error', text: err?.message || 'Failed to load requests.' })
      setRequests([])
      setRequestsTotal(0)
    } finally {
      setLoading(false)
    }
  }

  const loadReportStats = async () => {
    setReportStatsLoading(true)
    setReportStatsError(null)
    try {
      const admin = await isAdmin()
      if (!admin?.is_admin) {
        setReportStatsError('Access denied. Admin privileges required.')
        setReportStats([])
        return
      }
      const options = reportStatsFromDate && reportStatsToDate
        ? { fromDate: reportStatsFromDate, toDate: reportStatsToDate, q: reportStatsSearch || undefined }
        : { days: reportStatsDays, q: reportStatsSearch || undefined }
      const data = await listAdminReportStats(options)
      setReportStats(Array.isArray(data?.stats) ? data.stats : [])
    } catch (err) {
      setReportStatsError(err?.message || 'Failed to load report stats.')
      setReportStats([])
    } finally {
      setReportStatsLoading(false)
    }
  }

  const loadUsers = async () => {
    setUsersLoading(true)
    setUsersError(null)
    try {
      const admin = await isAdmin()
      if (!admin?.is_admin) {
        setUsersError('Access denied. Admin privileges required.')
        setUsers([])
        return
      }
      const data = await listAdminUsers()
      setUsers(Array.isArray(data?.users) ? data.users : [])
    } catch (err) {
      setUsersError(err?.message || 'Failed to load users.')
      setUsers([])
    } finally {
      setUsersLoading(false)
    }
  }

  const handleDisableUser = async (targetUserId) => {
    if (targetUserId === currentUserId) return
    setUserActionLoading(targetUserId)
    try {
      await disableAdminUser(targetUserId)
      await loadUsers()
    } catch (err) {
      setUsersError(err?.message || 'Failed to disable user.')
    } finally {
      setUserActionLoading(null)
    }
  }

  const handleEnableUser = async (targetUserId) => {
    setUserActionLoading(targetUserId)
    try {
      await enableAdminUser(targetUserId)
      await loadUsers()
    } catch (err) {
      setUsersError(err?.message || 'Failed to enable user.')
    } finally {
      setUserActionLoading(null)
    }
  }

  useEffect(() => {
    if (activeSection === SECTION_REQUESTS) {
      loadRequests(filter, requestsPage)
    }
  }, [activeSection, filter, requestsPage])

  useEffect(() => {
    if (activeSection === SECTION_REPORTS) {
      loadReportStats()
    }
  }, [activeSection])

  useEffect(() => {
    if (activeSection === SECTION_USERS) {
      loadUsers()
    }
  }, [activeSection])

  const totalPages = Math.max(1, Math.ceil(requestsTotal / REQUESTS_PAGE_SIZE))
  const requestStart = requestsTotal === 0 ? 0 : (requestsPage - 1) * REQUESTS_PAGE_SIZE + 1
  const requestEnd = requestsTotal === 0 ? 0 : Math.min((requestsPage - 1) * REQUESTS_PAGE_SIZE + requests.length, requestsTotal)

  const openActionModal = (action, userId, displayId) => {
    setModalAction(action)
    setModalUserId(userId)
    setModalDisplayId(displayId || userId)
    setAdminNotes('')
    setModalOpen(true)
  }

  const closeModal = () => {
    if (actionLoading) return
    setModalOpen(false)
    setModalUserId('')
    setModalDisplayId('')
    setAdminNotes('')
  }

  const confirmAction = async () => {
    if (!modalUserId) return
    setActionLoading(true)
    setStatusMessage(null)
    try {
      if (modalAction === 'approve') {
        await approveRequest(modalUserId, adminNotes.trim() || null)
        setStatusMessage({ type: 'success', text: `Approved request for '${modalDisplayId}'.` })
      } else {
        await rejectRequest(modalUserId, adminNotes.trim() || null)
        setStatusMessage({ type: 'success', text: `Rejected request for '${modalDisplayId}'.` })
      }
      closeModal()
      await loadRequests(filter, requestsPage)
    } catch (err) {
      setStatusMessage({ type: 'error', text: err?.message || 'Failed to process request.' })
    } finally {
      setActionLoading(false)
    }
  }

  const tabClass = (sectionId) => {
    const isActive = activeSection === sectionId
    const base = 'flex-1 flex items-center justify-center gap-2 py-3 px-4 font-medium text-sm transition-colors border-b-2 -mb-px'
    return isActive
      ? `${base} border-primary text-primary bg-primary/5 dark:bg-primary/10`
      : `${base} border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/50`
  }

  const filterBtnClass = (filterName) => {
    const active = filter === filterName
    if (active && filterName === 'all') return 'px-4 py-2 rounded-lg text-sm font-medium bg-primary text-white'
    if (active && filterName === 'pending') return 'px-4 py-2 rounded-lg text-sm font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
    if (active && filterName === 'approved') return 'px-4 py-2 rounded-lg text-sm font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
    if (active && filterName === 'rejected') return 'px-4 py-2 rounded-lg text-sm font-medium bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
    return 'px-4 py-2 rounded-lg text-sm font-medium bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600'
  }

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-1">Admin Panel</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">Manage users and registration requests</p>
      </div>

      <div className="w-full border-b border-slate-200 dark:border-slate-700 mb-6 flex">
        {SECTIONS.map((section) => (
          <button
            key={section.id}
            type="button"
            role="tab"
            aria-selected={activeSection === section.id}
            className={tabClass(section.id)}
            onClick={() => setActiveSection(section.id)}
          >
            <span className="material-symbols-outlined text-lg">{section.icon}</span>
            {section.label}
          </button>
        ))}
      </div>

      {statusMessage && (
        <div
          className={`mb-4 px-4 py-3 rounded-lg border ${
            statusMessage.type === 'success'
              ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-900/30 text-green-800 dark:text-green-300'
              : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-900/30 text-red-800 dark:text-red-300'
          }`}
        >
          <p className="text-sm">{statusMessage.text}</p>
        </div>
      )}

      {activeSection === SECTION_REQUESTS && (
        <>
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2 mb-1">
              <span className="material-symbols-outlined text-xl">person_add</span>
              Registration Requests
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Review and approve or reject registration requests. Use the status filters below to narrow the list.
            </p>
          </div>

          <div className="mb-6 flex flex-wrap gap-2">
            {FILTERS.map((filterName) => (
              <button
                key={filterName}
                type="button"
                className={filterBtnClass(filterName)}
                onClick={() => { setFilter(filterName); setRequestsPage(1) }}
              >
                {filterName.charAt(0).toUpperCase() + filterName.slice(1)}
              </button>
            ))}
          </div>

          {loading && (
            <div className="text-center py-12">
              <span className="material-symbols-outlined animate-spin text-4xl text-primary">sync</span>
              <p className="mt-4 text-slate-500 dark:text-slate-400">Loading requests...</p>
            </div>
          )}

          {!loading && requests.length === 0 && (
            <div className="text-center py-12">
              <span className="material-symbols-outlined text-6xl text-slate-300 dark:text-slate-600 mb-4">inbox</span>
              <p className="text-slate-500 dark:text-slate-400">No registration requests found</p>
            </div>
          )}

          {!loading && requests.length > 0 && (
            <div className="space-y-2">
              {requests.map((req) => (
                <RequestCard
                  key={req.id || req.user_id}
                  req={req}
                  onApprove={(id) => openActionModal('approve', id, req.email || req.user_id)}
                  onReject={(id) => openActionModal('reject', id, req.email || req.user_id)}
                />
              ))}
              <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-slate-200 dark:border-slate-700 pt-4">
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Showing {requestStart}–{requestEnd} of {requestsTotal}
                </p>
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={requestsPage <= 1}
                    onClick={() => setRequestsPage((p) => Math.max(1, p - 1))}
                    className="px-3 py-1.5 text-sm font-medium rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                  >
                    Previous
                  </button>
                  <button
                    type="button"
                    disabled={requestsPage >= totalPages}
                    onClick={() => setRequestsPage((p) => Math.min(totalPages, p + 1))}
                    className="px-3 py-1.5 text-sm font-medium rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {activeSection === SECTION_USERS && (
        <>
          {usersError && (
            <div className="mb-4 px-4 py-3 rounded-lg border bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-900/30 text-red-800 dark:text-red-300">
              <p className="text-sm">{usersError}</p>
            </div>
          )}

          {usersLoading && (
            <div className="text-center py-12">
              <span className="material-symbols-outlined animate-spin text-4xl text-primary">sync</span>
              <p className="mt-4 text-slate-500 dark:text-slate-400">Loading users...</p>
            </div>
          )}

          {!usersLoading && !usersError && users.length === 0 && (
            <div className="text-center py-12">
              <span className="material-symbols-outlined text-6xl text-slate-300 dark:text-slate-600 mb-4">group</span>
              <p className="text-slate-500 dark:text-slate-400">No users found.</p>
            </div>
          )}

          {!usersLoading && !usersError && users.length > 0 && (
            <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300">User ID</th>
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300">Email</th>
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300">Status</th>
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u, idx) => (
                    <tr key={u.user_id || idx} className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/30">
                      <td className="px-4 py-3 text-sm font-medium text-slate-900 dark:text-white">{u.user_id || '—'}</td>
                      <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-400">{u.email || '—'}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${u.disabled ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'}`}>
                          {u.disabled ? 'Disabled' : 'Active'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {u.user_id !== currentUserId && (
                          u.disabled ? (
                            <button
                              type="button"
                              disabled={userActionLoading === u.user_id}
                              onClick={() => handleEnableUser(u.user_id)}
                              className="px-3 py-1.5 text-xs font-medium bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded-md transition-colors"
                            >
                              {userActionLoading === u.user_id ? '…' : 'Enable'}
                            </button>
                          ) : (
                            <button
                              type="button"
                              disabled={userActionLoading === u.user_id}
                              onClick={() => handleDisableUser(u.user_id)}
                              className="px-3 py-1.5 text-xs font-medium bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white rounded-md transition-colors"
                            >
                              {userActionLoading === u.user_id ? '…' : 'Disable'}
                            </button>
                          )
                        )}
                        {u.user_id === currentUserId && (
                          <span className="text-xs text-slate-500 dark:text-slate-400">(you)</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {activeSection === SECTION_REPORTS && (
        <>
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Customer search</label>
            <input
              type="text"
              placeholder="Filter by user ID or email..."
              value={reportStatsSearch}
              onChange={(e) => setReportStatsSearch(e.target.value)}
              className="w-full max-w-md px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-primary focus:border-primary"
            />
          </div>

          <div className="mb-4">
            <span className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Time range</span>
            <div className="flex flex-wrap items-center gap-3">
              {REPORT_DAYS_OPTIONS.map((d) => (
                <button
                  key={d}
                  type="button"
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    !reportStatsFromDate && !reportStatsToDate && reportStatsDays === d
                      ? 'bg-primary text-white'
                      : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600'
                  }`}
                  onClick={() => {
                    setReportStatsDays(d)
                    setReportStatsFromDate('')
                    setReportStatsToDate('')
                    loadReportStats()
                  }}
                >
                  Last {d} days
                </button>
              ))}
              <span className="text-slate-500 dark:text-slate-400 text-sm mx-1">or</span>
              <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                <span>From</span>
                <input
                  type="date"
                  value={reportStatsFromDate}
                  onChange={(e) => setReportStatsFromDate(e.target.value)}
                  className="px-3 py-1.5 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                <span>To</span>
                <input
                  type="date"
                  value={reportStatsToDate}
                  onChange={(e) => setReportStatsToDate(e.target.value)}
                  className="px-3 py-1.5 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </label>
              <button
                type="button"
                onClick={loadReportStats}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-primary text-white hover:opacity-90 transition-opacity"
              >
                Apply
              </button>
            </div>
          </div>

          {reportStatsError && (
            <div className="mb-4 px-4 py-3 rounded-lg border bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-900/30 text-red-800 dark:text-red-300">
              <p className="text-sm">{reportStatsError}</p>
              {reportStatsError.includes('404') && (
                <p className="text-sm mt-2 opacity-90">
                  Ensure the backend is running (e.g. <code className="bg-red-100 dark:bg-red-900/40 px-1 rounded">mvn spring-boot:run</code> from <code className="bg-red-100 dark:bg-red-900/40 px-1 rounded">backend/</code>) and that the API base URL is correct (e.g. dev proxy to port 8080 or <code className="bg-red-100 dark:bg-red-900/40 px-1 rounded">VITE_API_URL=http://localhost:8080</code>).
                </p>
              )}
              <button
                type="button"
                onClick={loadReportStats}
                className="mt-3 px-3 py-1.5 text-sm font-medium bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
              >
                Retry
              </button>
            </div>
          )}

          {reportStatsLoading && (
            <div className="text-center py-12">
              <span className="material-symbols-outlined animate-spin text-4xl text-primary">sync</span>
              <p className="mt-4 text-slate-500 dark:text-slate-400">Loading report stats...</p>
            </div>
          )}

          {!reportStatsLoading && !reportStatsError && reportStats.length === 0 && (
            <div className="text-center py-12">
              <span className="material-symbols-outlined text-6xl text-slate-300 dark:text-slate-600 mb-4">assessment</span>
              <p className="text-slate-500 dark:text-slate-400">No report activity in the selected period.</p>
            </div>
          )}

          {!reportStatsLoading && !reportStatsError && reportStats.length > 0 && (
            <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300">User</th>
                    <th className="px-4 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300">Reports generated</th>
                  </tr>
                </thead>
                <tbody>
                  {reportStats.map((row, idx) => (
                    <tr key={row.user_id || idx} className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/30">
                      <td className="px-4 py-3 text-sm text-slate-900 dark:text-white font-medium">{row.user_id || '—'}</td>
                      <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-400 tabular-nums">{row.report_count ?? 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {modalOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
        >
          <div className="bg-surface-light dark:bg-surface-dark rounded-xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
              {modalAction === 'approve'
                ? `Approve registration request for ${modalDisplayId}?`
                : `Reject registration request for ${modalDisplayId}?`}
            </h3>

            <div className="mb-4">
              <label htmlFor="adminNotes" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Admin notes (optional)
              </label>
              <textarea
                id="adminNotes"
                rows={3}
                value={adminNotes}
                onChange={(e) => setAdminNotes(e.target.value)}
                className="w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white resize-none"
                placeholder="Add notes about this decision"
              />
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={confirmAction}
                disabled={actionLoading}
                className={`flex-1 px-4 py-2 rounded-lg text-white font-medium transition-colors ${
                  modalAction === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
                } disabled:opacity-60`}
              >
                {actionLoading ? 'Processing...' : modalAction === 'approve' ? 'Approve' : 'Reject'}
              </button>
              <button
                type="button"
                onClick={closeModal}
                disabled={actionLoading}
                className="flex-1 px-4 py-2 rounded-lg bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 font-medium"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}
