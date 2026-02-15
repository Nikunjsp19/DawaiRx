import { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import {
  DataTable,
  LoadingState,
  AppToast,
  ConfirmDialog,
} from '../components/ui'
import { listRuns, deleteRun, downloadFile } from '../api/client'

const ITEMS_PER_PAGE = 10

export default function Dashboard() {
  const [runs, setRuns] = useState([])
  const [totalRuns, setTotalRuns] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [toast, setToast] = useState(null)
  const [deleteConfirmRunId, setDeleteConfirmRunId] = useState(null)
  const navigate = useNavigate()

  const loadRuns = useCallback(async (page = 1) => {
    setLoading(true)
    setError(null)
    const offset = (page - 1) * ITEMS_PER_PAGE
    const timeoutMs = 8000
    const withTimeout = (promise) =>
      Promise.race([
        promise,
        new Promise((_, reject) =>
          setTimeout(
            () =>
              reject(
                new Error(
                  'Request timed out. The database connection may be slow. Please try again or check your internet connection.'
                )
              ),
            timeoutMs
          )
        ),
      ])
    try {
      const data = await withTimeout(listRuns(ITEMS_PER_PAGE, offset))
      let total = data.total ?? 0
      if (total === 0 && data.runs?.length > 0) {
        total =
          data.runs.length < ITEMS_PER_PAGE
            ? offset + data.runs.length
            : Math.max(total, data.runs.length)
      }
      setRuns(data.runs || [])
      setTotalRuns(total)
      setCurrentPage(page)
    } catch (err) {
      setError(err.message || 'Unknown error occurred')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadRuns(1)
  }, [loadRuns])

  const totalPages = Math.max(1, Math.ceil(totalRuns / ITEMS_PER_PAGE))
  const offset = (currentPage - 1) * ITEMS_PER_PAGE
  const showingFrom = totalRuns === 0 ? 0 : offset + 1
  const showingTo = offset + runs.length

  const changePage = (delta) => {
    const newPage = currentPage + delta
    if (newPage >= 1 && newPage <= totalPages) {
      loadRuns(newPage)
    }
  }

  const viewRun = (run) => {
    const runId = run.run_id || run.id || 'N/A'
    if (runId !== 'N/A') navigate(`/runs/${encodeURIComponent(runId)}`)
  }

  const handleDownload = async (e, runId, fileType = 'inventory_report') => {
    e.stopPropagation()
    try {
      await downloadFile(runId, fileType)
      setToast({ type: 'success', message: 'Download started' })
      setTimeout(() => setToast(null), 3000)
    } catch (err) {
      setToast({ type: 'error', message: err.message || 'Download failed' })
      setTimeout(() => setToast(null), 5000)
    }
  }

  const handleDeleteClick = (e, runId) => {
    e.stopPropagation()
    setDeleteConfirmRunId(runId)
  }

  const handleDeleteConfirm = async () => {
    const runId = deleteConfirmRunId
    setDeleteConfirmRunId(null)
    if (!runId) return
    try {
      await deleteRun(runId)
      setToast({ type: 'success', message: 'Report deleted successfully' })
      setTimeout(() => setToast(null), 3000)
      loadRuns(currentPage)
    } catch (err) {
      setToast({ type: 'error', message: `Failed to delete report: ${err.message || 'Unknown error'}` })
      setTimeout(() => setToast(null), 5000)
    }
  }

  const formatCreated = (raw) => {
    if (!raw) return '—'
    try {
      const d = new Date(raw)
      if (isNaN(d.getTime())) return '—'
      return d.toLocaleString()
    } catch {
      return '—'
    }
  }

  const columns = [
    {
      key: 'run_id',
      label: 'Run ID',
      render: (r) => {
        const runId = r.run_id || r.id || 'N/A'
        const created = formatCreated(r.created_at)
        return (
          <div className="flex items-center gap-2">
            <div className="size-7 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-primary text-xs font-semibold">
              R
            </div>
            <div>
              <p className="font-medium text-[#110c1d] dark:text-white text-sm">{runId}</p>
              <p className="text-xs text-gray-500">{created}</p>
            </div>
          </div>
        )
      },
    },
    {
      key: 'created',
      label: 'Created',
      render: (r) => (
        <span className="text-gray-600 dark:text-gray-400 text-sm">{formatCreated(r.created_at)}</span>
      ),
    },
    {
      key: 'medicines',
      label: 'Medicines',
      align: 'right',
      render: (r) => (
        <span className="text-gray-700 dark:text-gray-300 text-sm">
          {(r.stats?.total_medicines ?? 0).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'ordered',
      label: 'Ordered',
      align: 'right',
      render: (r) => (
        <span className="text-gray-700 dark:text-gray-300 text-sm">
          {(r.stats?.total_ordered ?? 0).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'sold',
      label: 'Sold',
      align: 'right',
      render: (r) => (
        <span className="text-gray-700 dark:text-gray-300 text-sm">
          {(r.stats?.total_sold ?? 0).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'issues',
      label: 'Issues',
      align: 'right',
      render: (r) => {
        const issues = r.stats?.total_issues ?? 0
        return issues > 0 ? (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300">
            {issues}
          </span>
        ) : (
          <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">
            0
          </span>
        )
      },
    },
    {
      key: 'action',
      label: 'Action',
      align: 'right',
      cellClassName: 'text-right',
      render: (r) => {
        const runId = r.run_id || r.id || 'N/A'
        return (
          <div
            className="flex items-center justify-end gap-2"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              onClick={(e) => handleDownload(e, runId, 'inventory_report')}
              className="text-primary font-medium text-sm hover:underline flex items-center gap-1.5 px-2 py-1.5 rounded hover:bg-primary/10 transition-colors"
              title="Download Report"
            >
              <span className="material-symbols-outlined text-base align-middle">download</span>
            </button>
            <button
              type="button"
              onClick={(e) => handleDeleteClick(e, runId)}
              className="text-red-600 dark:text-red-400 font-medium text-sm hover:underline flex items-center gap-1.5 px-2 py-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              title="Delete Report"
            >
              <span className="material-symbols-outlined text-base align-middle">delete</span>
            </button>
          </div>
        )
      },
    },
  ]

  return (
    <Layout>
      {/* Page Header - same as Python: only title + subtitle, no buttons */}
      <div className="mb-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-[#110c1d] dark:text-white">
            Report History
          </h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm max-w-2xl">
            View and manage your reconciliation reports.
          </p>
        </div>
      </div>

      {/* Your Reports card - spec: bg-surface-light, rounded-lg, border border-gray-100/50 */}
      <div className="flex flex-col bg-surface-light dark:bg-surface-dark rounded-lg border border-gray-100/50 dark:border-gray-800/50 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-800">
          <h2 className="text-base font-semibold text-[#110c1d] dark:text-white flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-base">description</span>
            Your Reports
          </h2>
        </div>

        {/* Loading State - legacy exact (Lottie 200x250, text) */}
        {loading && (
          <LoadingState
            message="Loading reports...."
            subMessage="Analyzing inventory data"
            useLottie
          />
        )}

        {/* Error State - legacy exact */}
        {!loading && error && (
          <div className="p-6 text-center">
            <div className="inline-flex items-center justify-center size-12 rounded-full bg-red-100 text-red-600 mb-4">
              <span className="material-symbols-outlined">error</span>
            </div>
            <p className="text-red-600 dark:text-red-400 font-semibold">Error loading reports</p>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">{error}</p>
            <button
              type="button"
              onClick={() => loadRuns(1)}
              className="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {/* Empty State - legacy exact */}
        {!loading && !error && runs.length === 0 && (
          <div className="p-6 text-center">
            <div className="inline-flex items-center justify-center size-10 rounded-full bg-primary/10 text-primary mb-2">
              <span className="material-symbols-outlined text-xl">description</span>
            </div>
            <h3 className="text-base font-semibold text-[#110c1d] dark:text-white mb-1">No reports yet</h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4 text-sm">
              Get started by creating your first reconciliation report
            </p>
            <Link
              to="/new-report"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-primary hover:bg-primary-dark text-white text-sm font-semibold transition-all"
            >
              <span className="material-symbols-outlined text-base">add</span>
              Start New Report
            </Link>
          </div>
        )}

        {/* Table - legacy columns and structure */}
        {!loading && !error && runs.length > 0 && (
          <>
            <div className="overflow-x-auto">
              <DataTable
                caption="Report history"
                columns={columns}
                rows={runs}
                getRowKey={(r) => r.run_id || r.id}
                onRowClick={viewRun}
              />
            </div>

            {/* Pagination - legacy exact */}
            <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-800 flex flex-col sm:flex-row items-center justify-between gap-3">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Showing <span className="font-medium text-[#110c1d] dark:text-white">{showingFrom}</span> to{' '}
                <span className="font-medium text-[#110c1d] dark:text-white">{showingTo}</span> of{' '}
                <span className="font-medium text-[#110c1d] dark:text-white">{totalRuns}</span> results
              </p>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => changePage(-1)}
                  disabled={currentPage <= 1}
                  className="flex items-center gap-2 px-4 py-2 rounded-md border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
                  aria-label="Previous page"
                >
                  <span className="material-symbols-outlined text-base">chevron_left</span>
                  <span>Prev</span>
                </button>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 text-sm font-medium text-[#110c1d] dark:text-white">
                    {currentPage}
                  </span>
                  <span className="text-sm text-gray-500 dark:text-gray-400">of</span>
                  <span className="px-3 py-1 text-sm font-medium text-[#110c1d] dark:text-white">
                    {totalPages}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => changePage(1)}
                  disabled={currentPage >= totalPages || showingTo >= totalRuns}
                  className="flex items-center gap-2 px-4 py-2 rounded-md border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
                  aria-label="Next page"
                >
                  <span>Next</span>
                  <span className="material-symbols-outlined text-sm">chevron_right</span>
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      <AppToast toast={toast} onDismiss={() => setToast(null)} />

      <ConfirmDialog
        open={!!deleteConfirmRunId}
        title="Delete report"
        message={`Are you sure you want to delete report "${deleteConfirmRunId}"? This action cannot be undone.`}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteConfirmRunId(null)}
      />
    </Layout>
  )
}
