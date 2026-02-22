import { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import { useAuth } from '../context/AuthContext'
import { Button, Card, Badge, Input, Label, Spinner, PageHeader, EmptyState, StatusBanner, AppToast, ConfirmDialog } from '../components/ui'
import { approveRequest, deleteAdminUser, disableAdminUser, enableAdminUser, isAdmin, listAdminRequests, listAdminReportStats, listAdminUsers, rejectRequest } from '../api/client'

const SECTION_USERS = 'users', SECTION_REPORTS = 'reports', SECTION_REQUESTS = 'requests'
const SECTIONS = [
  { id: SECTION_USERS, label: 'Users', icon: 'group' },
  { id: SECTION_REPORTS, label: 'Reports', icon: 'assessment' },
  { id: SECTION_REQUESTS, label: 'Requests', icon: 'person_add' },
]
const REPORT_DAYS = [7, 30, 90]
const FILTERS = ['all', 'pending', 'approved', 'rejected']
const PAGE_SIZE = 10

function statusVariant(s) {
  if (s === 'pending') return 'warning'
  if (s === 'approved') return 'success'
  if (s === 'rejected') return 'danger'
  return 'default'
}

function RequestCard({ req, onApprove, onReject }) {
  const displayId = req.email || req.user_id || req.id || 'unknown'
  const uid = req.user_id || req.id || 'unknown'
  const requestedStr = req.requested_at ? new Date(req.requested_at).toLocaleString() : '—'
  const reviewedStr = (req.reviewed_at || req.reviewed_by) ? `${req.reviewed_at ? new Date(req.reviewed_at).toLocaleString() : '—'}${req.reviewed_by ? ` by ${req.reviewed_by}` : ''}` : null

  return (
    <Card className="!p-4">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-[var(--color-text)] truncate">{displayId}</p>
          {req.company && <p className="text-xs text-[var(--color-text-muted)]">Company: {req.company}</p>}
        </div>
        <span className="text-xs text-[var(--color-text-muted)] whitespace-nowrap">Requested: {requestedStr}</span>
        <Badge variant={statusVariant(req.status)}>{String(req.status || 'unknown').toUpperCase()}</Badge>
        {req.status === 'pending' && (
          <div className="flex gap-1.5 shrink-0">
            <Button variant="primary" size="sm" onClick={() => onApprove(uid)} className="!bg-green-600 hover:!bg-green-700">Approve</Button>
            <Button variant="danger" size="sm" onClick={() => onReject(uid)}>Reject</Button>
          </div>
        )}
      </div>
      {(req.reason || reviewedStr || req.admin_notes) && (
        <div className="mt-3 pt-3 border-t border-[var(--color-border)] space-y-1 text-xs text-[var(--color-text-secondary)]">
          {req.reason && <p><span className="font-medium">Reason:</span> {req.reason}</p>}
          {reviewedStr && <p className="text-[var(--color-text-muted)]">Reviewed: {reviewedStr}</p>}
          {req.admin_notes && <p className="p-2 bg-gray-50 dark:bg-gray-800 rounded-[var(--radius-sm)]"><span className="font-medium">Admin notes:</span> {req.admin_notes}</p>}
        </div>
      )}
    </Card>
  )
}

export default function Admin() {
  const [section, setSection] = useState(SECTION_USERS)
  const [loading, setLoading] = useState(true)
  const [requests, setRequests] = useState([]); const [reqTotal, setReqTotal] = useState(0); const [reqPage, setReqPage] = useState(1)
  const [filter, setFilter] = useState('all')
  const [statusMsg, setStatusMsg] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)

  const [reportStats, setReportStats] = useState([]); const [reportDays, setReportDays] = useState(30)
  const [reportFrom, setReportFrom] = useState(''); const [reportTo, setReportTo] = useState('')
  const [reportSearch, setReportSearch] = useState('')
  const [reportLoading, setReportLoading] = useState(false); const [reportError, setReportError] = useState(null)

  const [users, setUsers] = useState([]); const [usersLoading, setUsersLoading] = useState(false); const [usersError, setUsersError] = useState(null)
  const [userActionTarget, setUserActionTarget] = useState(null)
  const [deleteUserTarget, setDeleteUserTarget] = useState(null)
  const { userId: currentUserId } = useAuth()

  const [modalOpen, setModalOpen] = useState(false); const [modalAction, setModalAction] = useState('approve')
  const [modalUserId, setModalUserId] = useState(''); const [modalDisplay, setModalDisplay] = useState(''); const [adminNotes, setAdminNotes] = useState('')

  const loadRequests = async (statusFilter = 'all', page = 1) => {
    setLoading(true); setStatusMsg(null)
    try {
      const admin = await isAdmin(); if (!admin?.is_admin) { setStatusMsg({ type: 'error', text: 'Access denied.' }); setRequests([]); setReqTotal(0); return }
      const data = await listAdminRequests(statusFilter, page, PAGE_SIZE)
      setRequests(Array.isArray(data?.requests) ? data.requests : []); setReqTotal(Number(data?.total) ?? 0)
    } catch (err) { setStatusMsg({ type: 'error', text: err?.message || 'Failed to load.' }); setRequests([]); setReqTotal(0) }
    finally { setLoading(false) }
  }

  const loadReportStats = async () => {
    setReportLoading(true); setReportError(null)
    try {
      const admin = await isAdmin(); if (!admin?.is_admin) { setReportError('Access denied.'); setReportStats([]); return }
      const opts = reportFrom && reportTo ? { fromDate: reportFrom, toDate: reportTo, q: reportSearch || undefined } : { days: reportDays, q: reportSearch || undefined }
      const data = await listAdminReportStats(opts); setReportStats(Array.isArray(data?.stats) ? data.stats : [])
    } catch (err) { setReportError(err?.message || 'Failed to load.'); setReportStats([]) }
    finally { setReportLoading(false) }
  }

  const loadUsers = async () => {
    setUsersLoading(true); setUsersError(null)
    try {
      const admin = await isAdmin(); if (!admin?.is_admin) { setUsersError('Access denied.'); setUsers([]); return }
      const data = await listAdminUsers(); setUsers(Array.isArray(data?.users) ? data.users : [])
    } catch (err) { setUsersError(err?.message || 'Failed to load.'); setUsers([]) }
    finally { setUsersLoading(false) }
  }

  const handleToggleUser = async (targetId, disable) => {
    if (targetId === currentUserId) return; setUserActionTarget(targetId)
    try { disable ? await disableAdminUser(targetId) : await enableAdminUser(targetId); await loadUsers() }
    catch (err) { setUsersError(err?.message || 'Failed.') }
    finally { setUserActionTarget(null) }
  }

  const handleDeleteUser = async () => {
    if (!deleteUserTarget) return
    setUserActionTarget(deleteUserTarget)
    try {
      await deleteAdminUser(deleteUserTarget)
      setDeleteUserTarget(null)
      await loadUsers()
    } catch (err) {
      setUsersError(err?.message || 'Delete failed.')
    } finally {
      setUserActionTarget(null)
    }
  }

  useEffect(() => { if (section === SECTION_REQUESTS) loadRequests(filter, reqPage) }, [section, filter, reqPage])
  useEffect(() => { if (section === SECTION_REPORTS) loadReportStats() }, [section])
  useEffect(() => { if (section === SECTION_USERS) loadUsers() }, [section])

  const totalPages = Math.max(1, Math.ceil(reqTotal / PAGE_SIZE))

  const openModal = (action, userId, display) => { setModalAction(action); setModalUserId(userId); setModalDisplay(display || userId); setAdminNotes(''); setModalOpen(true) }
  const closeModal = () => { if (actionLoading) return; setModalOpen(false) }
  const confirmAction = async () => {
    if (!modalUserId) return; setActionLoading(true); setStatusMsg(null)
    try {
      if (modalAction === 'approve') { await approveRequest(modalUserId, adminNotes.trim() || null); setStatusMsg({ type: 'success', text: `Approved '${modalDisplay}'.` }) }
      else { await rejectRequest(modalUserId, adminNotes.trim() || null); setStatusMsg({ type: 'success', text: `Rejected '${modalDisplay}'.` }) }
      closeModal(); await loadRequests(filter, reqPage)
    } catch (err) { setStatusMsg({ type: 'error', text: err?.message || 'Failed.' }) }
    finally { setActionLoading(false) }
  }

  return (
    <Layout>
      {/* Sticky header: title + tabs stay visible when scrolling (e.g. Requests with "All" filter) */}
      <div className="sticky top-0 z-10 -mx-1 -mt-1 px-1 pt-1 pb-0 bg-[var(--color-bg)] border-b-0 mb-0 overflow-visible">
        <PageHeader title="Admin Panel" description="Manage users and registration requests" />

        {/* Tabs */}
        <div className={`flex border-b border-[var(--color-border)] -mx-1 overflow-x-auto ${section === SECTION_REQUESTS ? '' : 'mb-6'}`}>
          {SECTIONS.map(s => (
            <button key={s.id} type="button" role="tab" aria-selected={section === s.id}
              className={`flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-default whitespace-nowrap ${
                section === s.id ? 'border-[var(--color-ring)] text-[var(--color-ring)]' : 'border-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-gray-50 dark:hover:bg-gray-800'
              }`}
              onClick={() => setSection(s.id)}>
              <span className="material-symbols-outlined text-lg">{s.icon}</span>{s.label}
            </button>
          ))}
        </div>
        {section === SECTION_REQUESTS && (
          <div className="pt-3 pb-3 mb-2 flex flex-wrap gap-2">
            {FILTERS.map(f => (
              <button key={f} type="button" onClick={() => { setFilter(f); setReqPage(1) }}
                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-default ${
                  filter === f ? (f === 'all' ? 'bg-[var(--color-ring)] text-white' : `${f === 'pending' ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400' : f === 'approved' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'}`) : 'bg-gray-100 dark:bg-gray-800 text-[var(--color-text-secondary)] hover:bg-gray-200 dark:hover:bg-gray-700'
                }`}>
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        )}
      </div>

      {statusMsg && <StatusBanner type={statusMsg.type === 'success' ? 'success' : 'error'} className="mb-4">{statusMsg.text}</StatusBanner>}

      {/* ── Requests ──────────────────────────────────── */}
      {section === SECTION_REQUESTS && (
        <>
          {loading ? <div className="py-12 text-center"><Spinner size="lg" className="mx-auto mb-3" /><p className="text-sm text-[var(--color-text-muted)]">Loading requests...</p></div>
           : requests.length === 0 ? <EmptyState icon="inbox" title="No requests found" />
           : (
            <div className="space-y-2">
              {requests.map(r => <RequestCard key={r.id || r.user_id} req={r} onApprove={id => openModal('approve', id, r.email || r.user_id)} onReject={id => openModal('reject', id, r.email || r.user_id)} />)}
              {reqTotal > PAGE_SIZE && (
                <div className="flex items-center justify-between pt-4 border-t border-[var(--color-border)]">
                  <p className="text-sm text-[var(--color-text-muted)]">Page {reqPage} of {totalPages}</p>
                  <div className="flex gap-2">
                    <Button variant="secondary" size="sm" disabled={reqPage <= 1} onClick={() => setReqPage(p => Math.max(1, p-1))}>Previous</Button>
                    <Button variant="secondary" size="sm" disabled={reqPage >= totalPages} onClick={() => setReqPage(p => Math.min(totalPages, p+1))}>Next</Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* ── Users ─────────────────────────────────────── */}
      {section === SECTION_USERS && (
        <>
          {usersError && <StatusBanner type="error" className="mb-4">{usersError}</StatusBanner>}
          {usersLoading ? <div className="py-12 text-center"><Spinner size="lg" className="mx-auto mb-3" /><p className="text-sm text-[var(--color-text-muted)]">Loading users...</p></div>
           : users.length === 0 ? <EmptyState icon="group" title="No users found" />
           : (
            <Card noPadding>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-900 border-b border-[var(--color-border)]">
                    <tr>
                      <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-[#5F6368] dark:text-[#9AA0A6]">User ID</th>
                      <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-[#5F6368] dark:text-[#9AA0A6]">Email</th>
                      <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-[#5F6368] dark:text-[#9AA0A6]">Status</th>
                      <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-[#5F6368] dark:text-[#9AA0A6]">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--color-border-subtle)]">
                    {users.map((u, idx) => (
                      <tr key={u.user_id || idx} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-default">
                        <td className="px-4 py-3 font-medium text-[var(--color-text)]">{u.user_id || '—'}</td>
                        <td className="px-4 py-3 text-[var(--color-text-secondary)]">{u.email || '—'}</td>
                        <td className="px-4 py-3"><Badge variant={u.disabled ? 'danger' : 'success'}>{u.disabled ? 'Disabled' : 'Active'}</Badge></td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap items-center gap-1.5">
                            {u.user_id === currentUserId
                              ? <span className="text-xs text-[var(--color-text-muted)]">(you)</span>
                              : (
                                <>
                                  {u.disabled
                                    ? <Button variant="primary" size="sm" disabled={userActionTarget === u.user_id} onClick={() => handleToggleUser(u.user_id, false)} className="!bg-green-600 hover:!bg-green-700">{userActionTarget === u.user_id ? '...' : 'Enable'}</Button>
                                    : <Button variant="secondary" size="sm" disabled={userActionTarget === u.user_id} onClick={() => handleToggleUser(u.user_id, true)} className="!bg-amber-100 !border !border-amber-400/70 !text-amber-800 hover:!bg-amber-200 dark:!bg-amber-900/40 dark:!border-amber-500/50 dark:!text-amber-200 dark:hover:!bg-amber-800/50">{userActionTarget === u.user_id ? '...' : 'Disable'}</Button>
                                  }
                                  <Button variant="danger" size="sm" disabled={userActionTarget === u.user_id} onClick={() => setDeleteUserTarget(u.user_id)}>{userActionTarget === u.user_id ? '...' : 'Delete'}</Button>
                                </>
                              )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      )}

      {/* ── Reports ───────────────────────────────────── */}
      {section === SECTION_REPORTS && (
        <>
          <div className="mb-4 space-y-3">
            <div><Label>Customer search</Label><Input placeholder="Filter by user ID or email..." value={reportSearch} onChange={e => setReportSearch(e.target.value)} className="max-w-md" /></div>
            <div>
              <Label>Time range</Label>
              <div className="flex flex-wrap items-center gap-2 mt-1">
                {REPORT_DAYS.map(d => (
                  <button key={d} type="button" onClick={() => { setReportDays(d); setReportFrom(''); setReportTo(''); loadReportStats() }}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-default ${!reportFrom && !reportTo && reportDays === d ? 'bg-[var(--color-ring)] text-white' : 'bg-gray-100 dark:bg-gray-800 text-[var(--color-text-secondary)] hover:bg-gray-200 dark:hover:bg-gray-700'}`}>
                    Last {d}d
                  </button>
                ))}
                <span className="text-xs text-[var(--color-text-muted)]">or</span>
                <input type="date" value={reportFrom} onChange={e => setReportFrom(e.target.value)} className="px-2.5 py-1.5 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] text-xs" />
                <input type="date" value={reportTo} onChange={e => setReportTo(e.target.value)} className="px-2.5 py-1.5 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] text-xs" />
                <Button size="sm" onClick={loadReportStats}>Apply</Button>
              </div>
            </div>
          </div>

          {reportError && <StatusBanner type="error" className="mb-4">{reportError}<Button size="sm" variant="danger" className="mt-2" onClick={loadReportStats}>Retry</Button></StatusBanner>}
          {reportLoading ? <div className="py-12 text-center"><Spinner size="lg" className="mx-auto mb-3" /><p className="text-sm text-[var(--color-text-muted)]">Loading stats...</p></div>
           : !reportError && reportStats.length === 0 ? <EmptyState icon="assessment" title="No activity" description="No report activity in the selected period." />
           : !reportError && reportStats.length > 0 && (
            <Card noPadding>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-900 border-b border-[var(--color-border)]">
                    <tr>
                      <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-[#5F6368] dark:text-[#9AA0A6]">User</th>
                      <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-[#5F6368] dark:text-[#9AA0A6]">Reports</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--color-border-subtle)]">
                    {reportStats.map((r, i) => (
                      <tr key={r.user_id || i} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-default">
                        <td className="px-4 py-3 font-medium text-[var(--color-text)]">{r.user_id || '—'}</td>
                        <td className="px-4 py-3 tabular-nums text-[var(--color-text-secondary)]">{r.report_count ?? 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      )}

      {/* ── Action modal ──────────────────────────────── */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-[2px] z-[200] flex items-center justify-center p-4" role="dialog" aria-modal="true">
          <Card className="max-w-md w-full">
            <h3 className="text-lg font-semibold text-[var(--color-text)] mb-4">
              {modalAction === 'approve' ? `Approve ${modalDisplay}?` : `Reject ${modalDisplay}?`}
            </h3>
            <div className="mb-4">
              <Label htmlFor="adminNotes">Admin notes (optional)</Label>
              <textarea id="adminNotes" rows={3} value={adminNotes} onChange={e => setAdminNotes(e.target.value)} placeholder="Add notes" className="w-full px-3 py-2 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] text-sm resize-none" />
            </div>
            <div className="flex gap-3">
              <Button className={`flex-1 ${modalAction === 'approve' ? '!bg-green-600 hover:!bg-green-700' : ''}`} variant={modalAction === 'approve' ? 'primary' : 'danger'} disabled={actionLoading} onClick={confirmAction}>
                {actionLoading ? 'Processing...' : modalAction === 'approve' ? 'Approve' : 'Reject'}
              </Button>
              <Button variant="secondary" className="flex-1" disabled={actionLoading} onClick={closeModal}>Cancel</Button>
            </div>
          </Card>
        </div>
      )}

      <ConfirmDialog
        open={!!deleteUserTarget}
        title="Delete user"
        message={deleteUserTarget ? `Permanently delete user "${deleteUserTarget}"? This cannot be undone.` : ''}
        confirmLabel="Delete"
        variant="danger"
        onConfirm={handleDeleteUser}
        onCancel={() => setDeleteUserTarget(null)}
      />
    </Layout>
  )
}
