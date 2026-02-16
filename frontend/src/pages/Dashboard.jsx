import { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import {
  Button, Card, CardHeader, PageHeader, Spinner,
  DataTable, LoadingState, EmptyState, AppToast, ConfirmDialog, StatusBanner,
} from '../components/ui'
import { listRuns, getRun, getRunItems, deleteRun, downloadFile } from '../api/client'

const ITEMS_PER_PAGE = 10

export default function Dashboard() {
  const [runs, setRuns] = useState([])
  const [totalRuns, setTotalRuns] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [toast, setToast] = useState(null)
  const [deleteConfirmRunId, setDeleteConfirmRunId] = useState(null)
  const [medicineCounts, setMedicineCounts] = useState({})
  const navigate = useNavigate()

  const fetchMedicineCount = useCallback(async (runId) => {
    try {
      const data = await getRun(runId)
      if (Array.isArray(data?.dawairx_report)) return data.dawairx_report.length
      const items = await getRunItems(runId)
      return Array.isArray(items) ? items.length : null
    } catch { return null }
  }, [])

  const loadRuns = useCallback(async (page = 1) => {
    setLoading(true); setError(null)
    const offset = (page - 1) * ITEMS_PER_PAGE
    try {
      const data = await Promise.race([
        listRuns(ITEMS_PER_PAGE, offset),
        new Promise((_, r) => setTimeout(() => r(new Error('Request timed out. Please try again.')), 8000)),
      ])
      let total = data.total ?? 0
      if (total === 0 && data.runs?.length > 0) total = data.runs.length < ITEMS_PER_PAGE ? offset + data.runs.length : Math.max(total, data.runs.length)
      const runsList = data.runs || []
      setRuns(runsList); setTotalRuns(total); setCurrentPage(page)

      // Fetch actual medicine counts from the report data (in background)
      for (const run of runsList) {
        const id = run.run_id || run.id
        if (!id) continue
        // Check if the list response already includes dawairx_report
        if (Array.isArray(run.dawairx_report)) {
          setMedicineCounts(prev => ({ ...prev, [id]: run.dawairx_report.length }))
        } else {
          fetchMedicineCount(id).then(count => {
            if (count != null) setMedicineCounts(prev => ({ ...prev, [id]: count }))
          })
        }
      }
    } catch (err) { setError(err.message || 'Unknown error') }
    finally { setLoading(false) }
  }, [fetchMedicineCount])

  useEffect(() => { loadRuns(1) }, [loadRuns])

  const totalPages = Math.max(1, Math.ceil(totalRuns / ITEMS_PER_PAGE))
  const offset = (currentPage - 1) * ITEMS_PER_PAGE
  const showingFrom = totalRuns === 0 ? 0 : offset + 1
  const showingTo = offset + runs.length

  const changePage = (delta) => {
    const p = currentPage + delta
    if (p >= 1 && p <= totalPages) loadRuns(p)
  }

  const viewRun = (run) => {
    const id = run.run_id || run.id || 'N/A'
    if (id !== 'N/A') navigate(`/runs/${encodeURIComponent(id)}`)
  }

  const handleDownload = async (e, runId) => {
    e.stopPropagation()
    try { await downloadFile(runId, 'inventory_report'); setToast({ type: 'success', message: 'Download started' }) }
    catch (err) { setToast({ type: 'error', message: err.message || 'Download failed' }) }
    finally { setTimeout(() => setToast(null), 3000) }
  }

  const handleDeleteClick = (e, runId) => { e.stopPropagation(); setDeleteConfirmRunId(runId) }

  const handleDeleteConfirm = async () => {
    const id = deleteConfirmRunId; setDeleteConfirmRunId(null)
    if (!id) return
    try { await deleteRun(id); setToast({ type: 'success', message: 'Report deleted' }); loadRuns(currentPage) }
    catch (err) { setToast({ type: 'error', message: `Delete failed: ${err.message}` }) }
    finally { setTimeout(() => setToast(null), 4000) }
  }

  const fmtDate = (raw) => {
    if (!raw) return '—'
    try { const d = new Date(raw); return isNaN(d.getTime()) ? '—' : d.toLocaleString() } catch { return '—' }
  }

  const fmtShortDate = (raw) => {
    if (!raw) return ''
    try {
      if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
        const [y, m, d] = raw.split('-').map(Number)
        return new Date(y, m - 1, d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
      }
      const d = new Date(raw)
      return isNaN(d.getTime()) ? raw : d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    } catch { return raw }
  }

  const getDateRange = (r) => {
    const cfg = r.config_summary || {}
    const from = cfg.date_from
    const to = cfg.date_to
    if (from && to) return `${fmtShortDate(from)} – ${fmtShortDate(to)}`
    if (from) return `From ${fmtShortDate(from)}`
    if (to) return `Until ${fmtShortDate(to)}`
    return '—'
  }

  const columns = [
    {
      key: 'run_id', label: 'Report',
      render: (r) => {
        const id = r.run_id || r.id || 'N/A'
        return (
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center size-8 rounded-full bg-[var(--color-ring)]/10 text-[var(--color-ring)] text-xs font-bold shrink-0">R</div>
            <div className="min-w-0">
              <p className="font-medium text-[var(--color-text)] text-sm truncate">{id}</p>
              <p className="text-xs text-[var(--color-text-muted)]">{fmtDate(r.created_at)}</p>
            </div>
          </div>
        )
      },
    },
    {
      key: 'date_range', label: 'Date Range',
      render: (r) => <span className="text-sm text-[var(--color-text-secondary)]">{getDateRange(r)}</span>,
    },
    {
      key: 'medicines', label: 'Medicines', align: 'right',
      render: (r) => {
        const id = r.run_id || r.id
        const realCount = medicineCounts[id]
        if (realCount != null) return <span className="text-sm font-medium tabular-nums">{realCount.toLocaleString()}</span>
        return <span className="text-sm tabular-nums text-[var(--color-text-muted)]">...</span>
      },
    },
    { key: 'ordered', label: 'Ordered', align: 'right', render: (r) => <span className="text-sm tabular-nums">{(r.stats?.total_ordered ?? 0).toLocaleString()}</span> },
    { key: 'sold', label: 'Sold', align: 'right', render: (r) => <span className="text-sm tabular-nums">{(r.stats?.total_sold ?? 0).toLocaleString()}</span> },
    {
      key: 'action', label: '', align: 'right', cellClassName: 'text-right',
      render: (r) => {
        const id = r.run_id || r.id || 'N/A'
        return (
          <div className="flex items-center justify-end gap-1" onClick={(e) => e.stopPropagation()}>
            <Button variant="ghost" size="sm" onClick={(e) => handleDownload(e, id)} title="Download">
              <span className="material-symbols-outlined text-base">download</span>
            </Button>
            <Button variant="danger-ghost" size="sm" onClick={(e) => handleDeleteClick(e, id)} title="Delete">
              <span className="material-symbols-outlined text-base">delete</span>
            </Button>
          </div>
        )
      },
    },
  ]

  return (
    <Layout>
      <PageHeader title="Report History" description="View and manage your reconciliation reports." />

      <Card noPadding>
        <CardHeader icon="description" title="Your Reports" />

        {loading && <LoadingState message="Loading reports..." subMessage="Fetching data" useLottie />}

        {!loading && error && (
          <div className="p-8 text-center">
            <div className="inline-flex items-center justify-center size-12 rounded-full bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 mb-3">
              <span className="material-symbols-outlined">error</span>
            </div>
            <p className="font-medium text-red-600 dark:text-red-400 text-sm">Error loading reports</p>
            <p className="text-sm text-[var(--color-text-muted)] mt-1 max-w-md mx-auto">{error}</p>
            <Button variant="primary" size="md" className="mt-4" onClick={() => loadRuns(1)}>Retry</Button>
          </div>
        )}

        {!loading && !error && runs.length === 0 && (
          <EmptyState
            icon="description"
            title="No reports yet"
            description="Get started by creating your first reconciliation report."
            action={<Link to="/new-report"><Button size="md"><span className="material-symbols-outlined text-base">add</span>Start New Report</Button></Link>}
          />
        )}

        {!loading && !error && runs.length > 0 && (
          <>
            <DataTable caption="Report history" columns={columns} rows={runs} getRowKey={(r) => r.run_id || r.id} onRowClick={viewRun} />

            {/* Pagination */}
            <div className="px-5 py-3 border-t border-[var(--color-border)] flex flex-col sm:flex-row items-center justify-between gap-3">
              <p className="text-sm text-[var(--color-text-muted)]">
                Showing <span className="font-medium text-[var(--color-text)]">{showingFrom}</span>–<span className="font-medium text-[var(--color-text)]">{showingTo}</span> of <span className="font-medium text-[var(--color-text)]">{totalRuns}</span>
              </p>
              <div className="flex items-center gap-2">
                <Button variant="secondary" size="sm" onClick={() => changePage(-1)} disabled={currentPage <= 1} aria-label="Previous page">
                  <span className="material-symbols-outlined text-sm">chevron_left</span>Prev
                </Button>
                <span className="text-sm tabular-nums text-[var(--color-text)]">{currentPage} <span className="text-[var(--color-text-muted)]">of</span> {totalPages}</span>
                <Button variant="secondary" size="sm" onClick={() => changePage(1)} disabled={currentPage >= totalPages || showingTo >= totalRuns} aria-label="Next page">
                  Next<span className="material-symbols-outlined text-sm">chevron_right</span>
                </Button>
              </div>
            </div>
          </>
        )}
      </Card>

      <AppToast toast={toast} onDismiss={() => setToast(null)} />
      <ConfirmDialog open={!!deleteConfirmRunId} title="Delete report" message={`Are you sure you want to delete report "${deleteConfirmRunId}"? This cannot be undone.`} confirmLabel="Delete" variant="danger" onConfirm={handleDeleteConfirm} onCancel={() => setDeleteConfirmRunId(null)} />
    </Layout>
  )
}
