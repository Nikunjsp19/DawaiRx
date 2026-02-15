import { useState, useEffect, useMemo, useRef } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import MedicineDetailPanel from '../components/MedicineDetailPanel'
import { LoadingState, AppToast, ConfirmDialog } from '../components/ui'
import { getRun, getRunItems, getRunItemsFromCsv, deleteRun, downloadFile } from '../api/client'

const BASE_COLUMN_KEYS = new Set([
  'NDC', 'DRUG NAME', 'RANK', 'PKG SIZE',
  'TOTAL ORDERED-O', 'TOTAL BILLED-B', 'TOTAL SHORTAGE-S', 'HIGHEST SHORTAGE-S',
  'AMOUNT', 'COST',
  'medicine_key', 'drug_name', 'ndc', 'strength', 'manufacturer',
  'ordered_total', 'sold_total', 'ordered_qty', 'sold_qty',
  'remaining_qty', 'shortage_qty', 'leftover_qty',
])

function normalizeColKey(key) {
  return (key || '').replace(/\n/g, ' ').trim()
}

function isRequiredColumn(key) {
  const n = normalizeColKey(key).toUpperCase()
  return n === 'NDC' || n === 'DRUG NAME' || n === 'DRUG_NAME'
}

function isBaseColumn(key) {
  const n = normalizeColKey(key)
  if (BASE_COLUMN_KEYS.has(n)) return true
  if (n.includes('TOTAL ORDERED') && n.endsWith('-O')) return true
  if (n.includes('TOTAL BILLED') && n.endsWith('-B')) return true
  if (n.includes('TOTAL SHORTAGE') && n.endsWith('-S') && !n.includes('HIGHEST')) return true
  if (n.includes('HIGHEST SHORTAGE') && n.endsWith('-S')) return true
  return false
}

// Display full column names to match Python (source of truth)
function getColumnDisplayLabel(key) {
  return normalizeColKey(key) || key
}

// Parse value as number when it looks numeric (API/CSV often send strings)
function parseNumeric(value) {
  if (value === '' || value == null) return NaN
  if (typeof value === 'number' && !Number.isNaN(value)) return value
  const s = String(value).trim()
  if (s === '') return NaN
  const n = Number(value)
  return Number.isNaN(n) ? NaN : n
}

function isShortageColumn(key) {
  const n = normalizeColKey(key).toUpperCase()
  return n.includes('SHORTAGE') || key === 'shortage_qty'
}

function isAmountColumn(key) {
  const n = normalizeColKey(key).toUpperCase()
  return n === 'AMOUNT' || n === 'COST'
}

function getAllColumnKeys(items) {
  if (!items || items.length === 0) return []
  const keySet = new Set()
  for (const row of items) {
    for (const key of Object.keys(row)) {
      if (key !== 'run_id') keySet.add(key)
    }
  }
  const baseOrder = [
    'NDC', 'DRUG NAME', 'RANK', 'PKG SIZE',
    'TOTAL ORDERED-O', 'TOTAL BILLED-B', 'TOTAL SHORTAGE-S', 'HIGHEST SHORTAGE-S',
    'AMOUNT', 'COST',
    'medicine_key', 'drug_name', 'ndc', 'strength', 'manufacturer',
    'ordered_total', 'sold_total', 'ordered_qty', 'sold_qty',
    'remaining_qty', 'shortage_qty', 'leftover_qty',
  ]
  const base = []
  const rest = []
  for (const key of keySet) {
    if (isBaseColumn(key)) base.push(key)
    else rest.push(key)
  }
  base.sort((a, b) => {
    const ai = baseOrder.indexOf(normalizeColKey(a))
    const bi = baseOrder.indexOf(normalizeColKey(b))
    if (ai !== -1 && bi !== -1) return ai - bi
    if (ai !== -1) return -1
    if (bi !== -1) return 1
    return String(a).localeCompare(String(b))
  })
  rest.sort((a, b) => String(a).localeCompare(String(b)))
  return [...base, ...rest]
}

function formatDateRange(dateFrom, dateTo) {
  if (!dateFrom && !dateTo) return ''
  const fmt = (s) => {
    if (!s) return ''
    try {
      if (/^\d{4}-\d{2}-\d{2}$/.test(s)) {
        const [y, m, d] = s.split('-').map(Number)
        return new Date(y, m - 1, d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
      }
      const d = new Date(s)
      return isNaN(d.getTime()) ? s : d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    } catch {
      return s
    }
  }
  if (dateFrom && dateTo) return `${fmt(dateFrom)} - ${fmt(dateTo)}`
  if (dateFrom) return `From ${fmt(dateFrom)}`
  if (dateTo) return `Until ${fmt(dateTo)}`
  return ''
}

function getMedicineIdentifier(row, columnKeys = []) {
  if (!row || typeof row !== 'object') return ''
  const ndcKey = columnKeys.find((k) => String(k).toLowerCase().includes('ndc'))
  const drugKey = columnKeys.find((k) => String(k).toLowerCase().includes('drug') && String(k).toLowerCase().includes('name'))
  const ndc = row[ndcKey] ?? row.NDC ?? row.ndc
  const drug = row[drugKey] ?? row['DRUG NAME'] ?? row.drug_name
  const medicineKey = row.medicine_key
  return String(ndc || medicineKey || drug || '').trim()
}

export default function ReportDetail() {
  const { runId } = useParams()
  const navigate = useNavigate()
  const [run, setRun] = useState(null)
  const [items, setItems] = useState([])
  const [itemsError, setItemsError] = useState(null)
  const [retryingItems, setRetryingItems] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [toast, setToast] = useState(null)
  const [search, setSearch] = useState('')
  const [sortCol, setSortCol] = useState('RANK')
  const [sortDir, setSortDir] = useState('asc')
  const [compactView, setCompactView] = useState(false)
  const [hiddenColumnKeys, setHiddenColumnKeys] = useState([])
  const [columnFilterOpen, setColumnFilterOpen] = useState(false)
  const columnFilterRef = useRef(null)
  const tableScrollRef = useRef(null)
  const scrollbarHideTimeoutRef = useRef(null)
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
  const [medicinePanelOpen, setMedicinePanelOpen] = useState(false)
  const [medicinePanelRow, setMedicinePanelRow] = useState(null)
  const [medicineIdentifier, setMedicineIdentifier] = useState('')

  useEffect(() => {
    if (!runId) return
    let cancelled = false
    setLoading(true)
    setError(null)
    setItemsError(null)
    getRun(runId)
      .then((data) => {
        if (cancelled) return
        const runObj = data.run != null ? data.run : data
        setRun(runObj)
        if (data.hasOwnProperty('dawairx_report') && Array.isArray(data.dawairx_report)) {
          setItems(data.dawairx_report)
          return
        }
        return getRunItems(runId)
          .then((itemsData) => {
            if (!cancelled) setItems(Array.isArray(itemsData) ? itemsData : [])
          })
          .catch(() => {
            if (cancelled) return
            getRunItemsFromCsv(runId)
              .then((itemsData) => {
                if (!cancelled) setItems(Array.isArray(itemsData) ? itemsData : [])
              })
              .catch(() => {
                if (!cancelled) setItemsError('Failed to fetch run items')
              })
          })
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Failed to load report')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [runId])

  const allColumnKeys = useMemo(() => getAllColumnKeys(items), [items])
  const baseColumnKeys = useMemo(() => allColumnKeys.filter((k) => isBaseColumn(k)), [allColumnKeys])
  const displayColumnKeys = useMemo(() => {
    const source = compactView ? baseColumnKeys : allColumnKeys
    return source.filter((k) => !hiddenColumnKeys.includes(k))
  }, [allColumnKeys, baseColumnKeys, compactView, hiddenColumnKeys])

  const toggleColumnVisibility = (key) => {
    if (isRequiredColumn(key)) return
    setHiddenColumnKeys((prev) => {
      if (prev.includes(key)) return prev.filter((k) => k !== key)
      const source = compactView ? baseColumnKeys : allColumnKeys
      const visibleCount = source.filter((k) => !prev.includes(k)).length
      if (visibleCount <= 1) return prev
      return [...prev, key]
    })
  }

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (columnFilterRef.current && !columnFilterRef.current.contains(e.target)) {
        setColumnFilterOpen(false)
      }
    }
    if (columnFilterOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [columnFilterOpen])

  const SCROLLBAR_HIDE_DELAY_MS = 800
  const showScrollbar = () => {
    const el = tableScrollRef.current
    if (!el) return
    if (scrollbarHideTimeoutRef.current) {
      clearTimeout(scrollbarHideTimeoutRef.current)
      scrollbarHideTimeoutRef.current = null
    }
    el.classList.add('scrollbar-visible')
    el.classList.remove('scrollbar-hidden')
  }
  const hideScrollbarAfterDelay = () => {
    if (scrollbarHideTimeoutRef.current) clearTimeout(scrollbarHideTimeoutRef.current)
    scrollbarHideTimeoutRef.current = setTimeout(() => {
      scrollbarHideTimeoutRef.current = null
      const el = tableScrollRef.current
      if (el) {
        el.classList.remove('scrollbar-visible')
        el.classList.add('scrollbar-hidden')
      }
    }, SCROLLBAR_HIDE_DELAY_MS)
  }

  useEffect(() => {
    return () => {
      if (scrollbarHideTimeoutRef.current) clearTimeout(scrollbarHideTimeoutRef.current)
    }
  }, [])

  const effectiveSortCol = sortCol && allColumnKeys.includes(sortCol) ? sortCol : (allColumnKeys[0] || 'medicine_key')

  const filteredAndSortedItems = useMemo(() => {
    let list = items
    if (search.trim()) {
      const q = search.trim().toLowerCase()
      list = list.filter((row) => {
        const drugName = (row.drug_name ?? row['DRUG NAME'] ?? '').toString().toLowerCase()
        const ndc = (row.ndc ?? row.NDC ?? '').toString().toLowerCase()
        return drugName.includes(q) || ndc.includes(q)
      })
    }
    list = [...list].sort((a, b) => {
      const av = a[effectiveSortCol]
      const bv = b[effectiveSortCol]
      const anum = typeof av === 'number' || (av != null && String(av).trim() !== '' && !Number.isNaN(Number(av)))
      const bnum = typeof bv === 'number' || (bv != null && String(bv).trim() !== '' && !Number.isNaN(Number(bv)))
      if (anum && bnum) {
        const an = typeof av === 'number' ? av : Number(av)
        const bn = typeof bv === 'number' ? bv : Number(bv)
        return sortDir === 'asc' ? an - bn : bn - an
      }
      const as = av != null ? String(av) : ''
      const bs = bv != null ? String(bv) : ''
      return sortDir === 'asc' ? as.localeCompare(bs, undefined, { numeric: true }) : bs.localeCompare(as, undefined, { numeric: true })
    })
    return list
  }, [items, search, effectiveSortCol, sortDir])

  const handleSort = (key) => {
    if (key === sortCol) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else {
      setSortCol(key)
      setSortDir('asc')
    }
  }

  const handleDownload = async (e, type, filename) => {
    e.preventDefault()
    try {
      await downloadFile(runId, type === 'csv' ? 'inventory_report' : type === 'excel' ? 'audit_report' : 'audit_report_pdf')
      setToast({ type: 'success', message: 'Download started' })
      setTimeout(() => setToast(null), 3000)
    } catch (err) {
      setToast({ type: 'error', message: err.message || 'Download failed' })
      setTimeout(() => setToast(null), 5000)
    }
  }

  const handleDeleteClick = () => setDeleteConfirmOpen(true)
  const handleDeleteConfirm = async () => {
    setDeleteConfirmOpen(false)
    try {
      await deleteRun(runId)
      setToast({ type: 'success', message: 'Report deleted' })
      setTimeout(() => setToast(null), 3000)
      navigate('/')
    } catch (err) {
      setToast({ type: 'error', message: err.message || 'Delete failed' })
      setTimeout(() => setToast(null), 5000)
    }
  }

  const retryLoadItems = () => {
    setRetryingItems(true)
    setItemsError(null)
    getRun(runId)
      .then((data) => {
        if (data.hasOwnProperty('dawairx_report') && Array.isArray(data.dawairx_report)) {
          setItems(data.dawairx_report)
          return
        }
        return getRunItems(runId)
          .then((itemsData) => setItems(Array.isArray(itemsData) ? itemsData : []))
          .catch(() => setItemsError('Failed to fetch run items'))
      })
      .catch(() => setItemsError('Failed to fetch run items'))
      .finally(() => setRetryingItems(false))
  }

  if (loading && !run) {
    return (
      <Layout>
        <LoadingState message="Loading report…" />
      </Layout>
    )
  }

  if (error || !run) {
    return (
      <Layout>
        <div className="px-4 sm:px-6 lg:px-8 p-6 text-center rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20">
          <p className="text-red-600 dark:text-red-400 font-medium">{error || 'Report not found'}</p>
          <Link to="/" className="inline-block mt-3 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark text-sm">
            Back to Dashboard
          </Link>
        </div>
      </Layout>
    )
  }

  const config = run.config_summary || {}
  const dateFrom = config.date_from || ''
  const dateTo = config.date_to || ''
  const dateRangeStr = formatDateRange(dateFrom, dateTo)
  const created = run.created_at ? new Date(run.created_at).toLocaleString() : ''

  const tableCellClass = 'px-3 py-2 text-gray-700 dark:text-gray-300 whitespace-nowrap text-xs tabular-nums'
  const thClass = 'px-3 py-2 text-xs whitespace-nowrap cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 select-none font-medium text-gray-500 dark:text-gray-400'
  const isStickyCol = (colIndex) => colIndex === 0 || colIndex === 1
  const thStickyClass = (colIndex) => {
    const headerBg = 'sticky top-0 bg-gray-50 dark:bg-gray-800'
    const shadow = 'shadow-[2px_0_4px_rgba(0,0,0,0.1)]'
    if (colIndex === 0) return `${headerBg} left-0 min-w-[120px] z-[31] ${shadow}`
    if (colIndex === 1) return `${headerBg} left-[120px] min-w-[200px] z-[31] ${shadow}`
    return `${headerBg} z-[30]`
  }
  const tdStickyClass = (colIndex) => {
    if (isStickyCol(colIndex)) {
      const base = 'bg-white dark:bg-gray-900'
      const shadow = 'shadow-[2px_0_4px_rgba(0,0,0,0.1)]'
      if (colIndex === 0) return `sticky left-0 min-w-[120px] z-[20] ${base} ${shadow}`
      return `sticky left-[120px] min-w-[200px] z-[20] ${base} ${shadow}`
    }
    return ''
  }

  return (
    <Layout>
      <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
        <div className="flex-shrink-0 mb-6 px-4 sm:px-6 lg:px-8 pt-6 lg:pt-8">
          <Link to="/" className="inline-flex items-center gap-1.5 text-xs text-primary hover:underline mb-2">
            <span className="material-symbols-outlined text-base">arrow_back</span>
            Back to Report History
          </Link>
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-0">
                <span>{run.run_id || runId}</span>
              </h1>
              {dateRangeStr && <p className="text-base text-slate-600 dark:text-slate-400 mt-0.5">{dateRangeStr}</p>}
              {created && <p className="text-sm text-slate-500 dark:text-slate-500 mt-0.5">Generated {created}</p>}
            </div>
            <div className="flex flex-wrap gap-1.5 items-center">
              <button type="button" onClick={(e) => handleDownload(e, 'excel', 'audit_report.xlsx')} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 text-xs font-medium">
                <span className="material-symbols-outlined text-base">table_chart</span> Excel
              </button>
              <button type="button" onClick={(e) => handleDownload(e, 'pdf', 'audit_report.pdf')} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 text-xs font-medium">
                <span className="material-symbols-outlined text-base">picture_as_pdf</span> PDF
              </button>
              <button type="button" onClick={(e) => handleDownload(e, 'csv', 'remaining_inventory.csv')} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 text-xs font-medium">
                <span className="material-symbols-outlined text-base">description</span> Inventory CSV
              </button>
              <button type="button" onClick={handleDeleteClick} className="inline-flex items-center gap-1 px-2 py-1 rounded border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 text-xs font-medium" title="Delete report">
                <span className="material-symbols-outlined text-sm">delete</span> Delete
              </button>
            </div>
          </div>
        </div>

        <div className="flex-1 min-h-0 w-full px-4 sm:px-6 lg:px-8 flex flex-col">
          <div className="bg-surface-light dark:bg-surface-dark rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800 overflow-hidden flex flex-col flex-1 min-h-0">
            <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800 flex-shrink-0">
              <div className="flex flex-wrap items-center gap-4 mb-4">
                <div className="relative flex-1 min-w-[200px]">
                  <span className="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-base">search</span>
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search by medicine name..."
                    className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-gray-400 focus:ring-2 focus:ring-primary focus:border-primary transition-colors text-sm"
                  />
                </div>
                <label className="flex items-center gap-2 cursor-pointer select-none text-sm text-gray-700 dark:text-gray-300">
                  <input type="checkbox" checked={compactView} onChange={(e) => setCompactView(e.target.checked)} className="rounded border-gray-300 text-primary focus:ring-primary" />
                  <span>Compact view</span>
                  <span className="text-gray-400 dark:text-gray-500 text-xs">(fewer columns)</span>
                </label>
                <div className="relative" ref={columnFilterRef}>
                  <button
                    type="button"
                    onClick={() => setColumnFilterOpen((o) => !o)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 text-xs font-medium"
                    aria-expanded={columnFilterOpen}
                  >
                    <span className="material-symbols-outlined text-base">filter_list</span>
                    <span>Columns</span>
                    <span className="material-symbols-outlined text-sm">{columnFilterOpen ? 'expand_less' : 'expand_more'}</span>
                  </button>
                  {columnFilterOpen && allColumnKeys.length > 0 && (
                    <div className="absolute right-0 top-full mt-1 z-[var(--z-dropdown)] w-64 max-h-80 overflow-y-auto rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 shadow-lg py-2">
                      <p className="px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700 mb-2">Show columns (uncheck to hide)</p>
                      <div className="space-y-0.5 px-2">
                        {allColumnKeys.filter((k) => !isRequiredColumn(k)).map((key) => (
                          <label key={key} className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer text-xs text-gray-700 dark:text-gray-300">
                            <input type="checkbox" checked={!hiddenColumnKeys.includes(key)} onChange={() => toggleColumnVisibility(key)} className="rounded border-gray-300 text-primary focus:ring-primary" />
                            <span className="truncate">{getColumnDisplayLabel(key)}</span>
                          </label>
                        ))}
                      </div>
                      {hiddenColumnKeys.length > 0 && (
                        <button type="button" onClick={() => setHiddenColumnKeys([])} className="mt-2 mx-2 w-[calc(100%-1rem)] py-1.5 text-xs text-primary hover:bg-primary/10 rounded">
                          Show all columns
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">{filteredAndSortedItems.length} of {items.length} medicines</p>
            </div>

            <div
              ref={tableScrollRef}
              className="report-table-scroll scrollbar-hidden overflow-auto flex-1 min-h-0 min-h-[12rem]"
              onMouseEnter={showScrollbar}
              onMouseLeave={hideScrollbarAfterDelay}
              onScroll={() => { showScrollbar(); hideScrollbarAfterDelay() }}
            >
              {itemsError ? (
                <div className="p-6 text-center">
                  <p className="text-amber-600 dark:text-amber-400 font-medium mb-1 text-sm">Could not load table data</p>
                  <button type="button" onClick={retryLoadItems} disabled={retryingItems} className="px-3 py-1.5 bg-primary text-white rounded text-xs font-medium disabled:opacity-50">
                    {retryingItems ? 'Loading…' : 'Try again'}
                  </button>
                </div>
              ) : filteredAndSortedItems.length === 0 ? (
                <div className="p-6 text-center text-gray-500 dark:text-gray-400 text-sm">
                  {items.length === 0 ? 'No data in this report.' : 'No rows match your search.'}
                </div>
              ) : (
                <table className="w-full text-left border-collapse" style={{ minWidth: '100%' }}>
                  <thead className="sticky top-0 z-[50] bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 font-medium border-b border-gray-100 dark:border-gray-800">
                    <tr>
                      {displayColumnKeys.map((key, colIndex) => (
                        <th key={key} className={`${thClass} ${thStickyClass(colIndex)}`} onClick={() => handleSort(key)} title={normalizeColKey(key)}>
                          <div className="flex items-center gap-0.5">
                            {getColumnDisplayLabel(key)}
                            <span className={`material-symbols-outlined text-xs transition-opacity ${effectiveSortCol === key ? '' : 'opacity-0'}`} style={{ fontSize: 14 }}>
                              {effectiveSortCol === key ? (sortDir === 'asc' ? 'arrow_upward' : 'arrow_downward') : 'unfold_more'}
                            </span>
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                    {filteredAndSortedItems.map((row, idx) => (
                      <tr
                        key={(row.medicine_key ?? row.NDC ?? row.ndc ?? '') + idx}
                        role="button"
                        tabIndex={0}
                        onClick={() => {
                          setMedicinePanelRow(row)
                          setMedicineIdentifier(getMedicineIdentifier(row, displayColumnKeys))
                          setMedicinePanelOpen(true)
                        }}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            setMedicinePanelRow(row)
                            setMedicineIdentifier(getMedicineIdentifier(row, displayColumnKeys))
                            setMedicinePanelOpen(true)
                          }
                        }}
                        className="group hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors cursor-pointer medicine-row"
                      >
                        {displayColumnKeys.map((key, colIndex) => {
                          const raw = row[key]
                          const numVal = parseNumeric(raw)
                          const isNum = !Number.isNaN(numVal)
                          const cellClass = `${tableCellClass} ${tdStickyClass(colIndex)}`
                          const isEmpty = raw === '' || raw === undefined || raw === null
                          if (isEmpty) {
                            return <td key={key} className={cellClass}></td>
                          }
                          if (isShortageColumn(key) && isNum && numVal < 0) {
                            const fmt = numVal % 1 === 0 ? numVal.toLocaleString() : numVal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 })
                            return (
                              <td key={key} className={cellClass}>
                                <span className="text-red-600 dark:text-red-400 font-medium">{fmt}</span>
                              </td>
                            )
                          }
                          if (isAmountColumn(key) && isNum) {
                            return (
                              <td key={key} className={cellClass}>
                                <span className="tabular-nums">${numVal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                              </td>
                            )
                          }
                          if (isNum) {
                            const fmt = numVal % 1 === 0 ? numVal.toLocaleString() : numVal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 })
                            return <td key={key} className={cellClass}><span className="tabular-nums">{fmt}</span></td>
                          }
                          return <td key={key} className={cellClass}>{String(raw)}</td>
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
          </div>

          {/* Footer - always visible at bottom of table area */}
          {items.length > 0 && (
            <div className="px-4 py-2 border-t border-gray-100 dark:border-gray-800 text-center flex-shrink-0">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Showing {filteredAndSortedItems.length} of {items.length} medicines
              </p>
            </div>
          )}
        </div>
      </div>
      </div>

      <MedicineDetailPanel
        open={medicinePanelOpen}
        onClose={() => setMedicinePanelOpen(false)}
        runId={runId}
        medicineIdentifier={medicineIdentifier}
        fallbackRow={medicinePanelRow}
      />
      <AppToast toast={toast} onDismiss={() => setToast(null)} />
      <ConfirmDialog
        open={deleteConfirmOpen}
        title="Delete report"
        message={`Are you sure you want to delete report "${runId}"? This action cannot be undone.`}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteConfirmOpen(false)}
      />
    </Layout>
  )
}
