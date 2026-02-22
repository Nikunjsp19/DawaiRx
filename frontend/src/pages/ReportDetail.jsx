import React, { useState, useEffect, useMemo, useRef } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import MedicineDetailPanel from '../components/MedicineDetailPanel'
import { Button, Card, Input, Spinner, LoadingState, EmptyState, AppToast, ConfirmDialog, StatusBanner } from '../components/ui'
import { getRun, getRunItems, getRunItemsFromCsv, deleteRun, downloadFile } from '../api/client'

/* ── column helpers (unchanged business logic) ────────── */
const BASE_COLUMN_KEYS = new Set([
  'NDC', 'DRUG NAME', 'RANK', 'PKG SIZE',
  'TOTAL ORDERED-O', 'TOTAL BILLED-B', 'TOTAL SHORTAGE-S', 'HIGHEST SHORTAGE-S',
  'AMOUNT', 'COST', 'medicine_key', 'drug_name', 'ndc', 'strength', 'manufacturer',
  'ordered_total', 'sold_total', 'ordered_qty', 'sold_qty', 'remaining_qty', 'shortage_qty', 'leftover_qty',
])

function normalizeColKey(key) { return (key || '').replace(/\n/g, ' ').trim() }
function isRequiredColumn(key) { const n = normalizeColKey(key).toUpperCase(); return n === 'NDC' || n === 'DRUG NAME' || n === 'DRUG_NAME' }
function isBaseColumn(key) {
  const n = normalizeColKey(key)
  if (BASE_COLUMN_KEYS.has(n)) return true
  if (n.includes('TOTAL ORDERED') && n.endsWith('-O')) return true
  if (n.includes('TOTAL BILLED') && n.endsWith('-B')) return true
  if (n.includes('TOTAL SHORTAGE') && n.endsWith('-S') && !n.includes('HIGHEST')) return true
  if (n.includes('HIGHEST SHORTAGE') && n.endsWith('-S')) return true
  return false
}
function getColumnDisplayLabel(key) { return normalizeColKey(key) || key }
function parseNumeric(value) {
  if (value === '' || value == null) return NaN
  if (typeof value === 'number' && !Number.isNaN(value)) return value
  const s = String(value).trim(); if (s === '') return NaN
  const n = Number(value); return Number.isNaN(n) ? NaN : n
}
function isShortageColumn(key) { const n = normalizeColKey(key).toUpperCase(); return n.includes('SHORTAGE') || key === 'shortage_qty' }
function isAmountColumn(key) { const n = normalizeColKey(key).toUpperCase(); return n === 'AMOUNT' || n === 'COST' }
function getAllColumnKeys(items) {
  if (!items?.length) return []
  const keySet = new Set()
  for (const row of items) for (const k of Object.keys(row)) if (k !== 'run_id') keySet.add(k)
  const baseOrder = ['NDC','DRUG NAME','RANK','PKG SIZE','TOTAL ORDERED-O','TOTAL BILLED-B','TOTAL SHORTAGE-S','HIGHEST SHORTAGE-S','AMOUNT','COST','medicine_key','drug_name','ndc','strength','manufacturer','ordered_total','sold_total','ordered_qty','sold_qty','remaining_qty','shortage_qty','leftover_qty']
  const base = [], rest = []
  for (const k of keySet) (isBaseColumn(k) ? base : rest).push(k)
  base.sort((a, b) => { const ai = baseOrder.indexOf(normalizeColKey(a)), bi = baseOrder.indexOf(normalizeColKey(b)); if (ai !== -1 && bi !== -1) return ai - bi; if (ai !== -1) return -1; if (bi !== -1) return 1; return a.localeCompare(b) })
  rest.sort((a, b) => a.localeCompare(b))
  return [...base, ...rest]
}
function formatDateRange(from, to) {
  if (!from && !to) return ''
  const fmt = (s) => { if (!s) return ''; try { if (/^\d{4}-\d{2}-\d{2}$/.test(s)) { const [y,m,d] = s.split('-').map(Number); return new Date(y,m-1,d).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}) } const d = new Date(s); return isNaN(d.getTime()) ? s : d.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}) } catch { return s } }
  if (from && to) return `${fmt(from)} – ${fmt(to)}`
  if (from) return `From ${fmt(from)}`
  return `Until ${fmt(to)}`
}
function getMedicineIdentifier(row, keys = []) {
  if (!row) return ''
  const ndcKey = keys.find(k => String(k).toLowerCase().includes('ndc'))
  const drugKey = keys.find(k => String(k).toLowerCase().includes('drug') && String(k).toLowerCase().includes('name'))
  return String(row[ndcKey] ?? row.NDC ?? row.ndc ?? row.medicine_key ?? row[drugKey] ?? row['DRUG NAME'] ?? row.drug_name ?? '').trim()
}

/* ── component ────────────────────────────────────────── */
export default function ReportDetail() {
  const { runId } = useParams()
  const navigate = useNavigate()
  const [run, setRun] = useState(null)
  const [items, setItems] = useState([])
  const [itemsError, setItemsError] = useState(null)
  const [retrying, setRetrying] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [toast, setToast] = useState(null)
  const [search, setSearch] = useState('')
  const [sortCol, setSortCol] = useState('RANK')
  const [sortDir, setSortDir] = useState('asc')
  const [compactView, setCompactView] = useState(false)
  const [hiddenCols, setHiddenCols] = useState([])
  const [colFilterOpen, setColFilterOpen] = useState(false)
  const colFilterRef = useRef(null)
  const tableScrollRef = useRef(null)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [panelOpen, setPanelOpen] = useState(false)
  const [panelRow, setPanelRow] = useState(null)
  const [panelId, setPanelId] = useState('')

  /* ── data loading (unchanged logic) ─────────────────── */
  useEffect(() => {
    if (!runId) return; let cancel = false
    setLoading(true); setError(null); setItemsError(null)
    getRun(runId).then(data => {
      if (cancel) return
      setRun(data.run != null ? data.run : data)
      if (data.hasOwnProperty('dawairx_report') && Array.isArray(data.dawairx_report)) { setItems(data.dawairx_report); return }
      return getRunItems(runId).then(d => { if (!cancel) setItems(Array.isArray(d) ? d : []) })
        .catch(() => { if (cancel) return; getRunItemsFromCsv(runId).then(d => { if (!cancel) setItems(Array.isArray(d) ? d : []) }).catch(() => { if (!cancel) setItemsError('Failed to fetch run items') }) })
    }).catch(e => { if (!cancel) setError(e.message || 'Failed to load report') }).finally(() => { if (!cancel) setLoading(false) })
    return () => { cancel = true }
  }, [runId])

  const allColKeys = useMemo(() => getAllColumnKeys(items), [items])
  const baseColKeys = useMemo(() => allColKeys.filter(isBaseColumn), [allColKeys])
  const displayCols = useMemo(() => (compactView ? baseColKeys : allColKeys).filter(k => !hiddenCols.includes(k)), [allColKeys, baseColKeys, compactView, hiddenCols])

  const toggleCol = (key) => {
    if (isRequiredColumn(key)) return
    setHiddenCols(prev => {
      if (prev.includes(key)) return prev.filter(k => k !== key)
      const src = compactView ? baseColKeys : allColKeys
      if (src.filter(k => !prev.includes(k)).length <= 1) return prev
      return [...prev, key]
    })
  }

  useEffect(() => {
    if (!colFilterOpen) return
    const h = (e) => { if (colFilterRef.current && !colFilterRef.current.contains(e.target)) setColFilterOpen(false) }
    document.addEventListener('mousedown', h); return () => document.removeEventListener('mousedown', h)
  }, [colFilterOpen])

  const effectiveSort = sortCol && allColKeys.includes(sortCol) ? sortCol : (allColKeys[0] || 'medicine_key')

  const filtered = useMemo(() => {
    let list = items
    if (search.trim()) {
      const q = search.trim().toLowerCase()
      list = list.filter(row => { const dn = (row.drug_name ?? row['DRUG NAME'] ?? '').toString().toLowerCase(); const nd = (row.ndc ?? row.NDC ?? '').toString().toLowerCase(); return dn.includes(q) || nd.includes(q) })
    }
    return [...list].sort((a, b) => {
      const av = a[effectiveSort], bv = b[effectiveSort]
      const an = typeof av === 'number' || (av != null && String(av).trim() !== '' && !Number.isNaN(Number(av)))
      const bn = typeof bv === 'number' || (bv != null && String(bv).trim() !== '' && !Number.isNaN(Number(bv)))
      if (an && bn) { const x = typeof av === 'number' ? av : Number(av), y = typeof bv === 'number' ? bv : Number(bv); return sortDir === 'asc' ? x - y : y - x }
      const sa = av != null ? String(av) : '', sb = bv != null ? String(bv) : ''
      return sortDir === 'asc' ? sa.localeCompare(sb, undefined, { numeric: true }) : sb.localeCompare(sa, undefined, { numeric: true })
    })
  }, [items, search, effectiveSort, sortDir])

  const handleSort = (key) => { if (key === sortCol) setSortDir(d => d === 'asc' ? 'desc' : 'asc'); else { setSortCol(key); setSortDir('asc') } }

  const handleDownload = async (e, type) => {
    e.preventDefault()
    try { await downloadFile(runId, type === 'csv' ? 'inventory_report' : type === 'excel' ? 'audit_report' : 'audit_report_pdf'); setToast({ type: 'success', message: 'Download started' }) }
    catch (err) { setToast({ type: 'error', message: err.message || 'Download failed' }) }
    finally { setTimeout(() => setToast(null), 3000) }
  }

  const handleDelete = async () => {
    setDeleteOpen(false)
    try { await deleteRun(runId); setToast({ type: 'success', message: 'Report deleted' }); setTimeout(() => navigate('/'), 500) }
    catch (err) { setToast({ type: 'error', message: err.message || 'Delete failed' }); setTimeout(() => setToast(null), 5000) }
  }

  const retryItems = () => {
    setRetrying(true); setItemsError(null)
    getRun(runId).then(data => {
      if (data.hasOwnProperty('dawairx_report') && Array.isArray(data.dawairx_report)) { setItems(data.dawairx_report); return }
      return getRunItems(runId).then(d => setItems(Array.isArray(d) ? d : [])).catch(() => setItemsError('Failed to fetch run items'))
    }).catch(() => setItemsError('Failed to fetch run items')).finally(() => setRetrying(false))
  }

  const openPanel = (row) => { setPanelRow(row); setPanelId(getMedicineIdentifier(row, displayCols)); setPanelOpen(true) }

  /* ── Loading / Error states ─────────────────────────── */
  if (loading && !run) return <Layout><LoadingState message="Loading report..." subMessage="Fetching report data" useLottie /></Layout>
  if (error || !run) return (
    <Layout>
      <div className="p-8 text-center">
        <StatusBanner type="error" className="max-w-md mx-auto mb-4">{error || 'Report not found'}</StatusBanner>
        <Link to="/"><Button variant="primary" size="md">Back to Dashboard</Button></Link>
      </div>
    </Layout>
  )

  const config = run.config_summary || {}
  const dateRangeStr = formatDateRange(config.date_from, config.date_to)
  const created = run.created_at ? new Date(run.created_at).toLocaleString() : ''

  /* ── Sticky table classes ───────────────────────────── */
  const headerBg = 'bg-gray-50 dark:bg-gray-900'
  const bodyBg = 'bg-[var(--color-surface)]'
  const stickyS = 'shadow-[2px_0_6px_-2px_rgba(0,0,0,0.08)]'

  const thStickyClass = (i) => {
    if (i === 0) return `sticky top-0 left-0 z-[30] min-w-[120px] w-[120px] ${headerBg} ${stickyS}`
    if (i === 1) return `sticky top-0 left-[120px] z-[30] min-w-[200px] w-[200px] ${headerBg} ${stickyS}`
    return `sticky top-0 z-[20] ${headerBg}`
  }
  const tdStickyClass = (i) => {
    if (i === 0) return `sticky left-0 z-[10] min-w-[120px] w-[120px] ${bodyBg} group-hover:bg-gray-50 dark:group-hover:bg-gray-800/50 ${stickyS}`
    if (i === 1) return `sticky left-[120px] z-[10] min-w-[200px] w-[200px] ${bodyBg} group-hover:bg-gray-50 dark:group-hover:bg-gray-800/50 ${stickyS}`
    return ''
  }

  return (
    <Layout fullWidth>
      <div className="flex flex-col flex-1 min-h-0 -mb-3 lg:-mb-4">

        {/* ── Header bar ──────────────────────────────── */}
        <div className="shrink-0 px-3 sm:px-4 lg:px-5 pt-4 pb-1.5">
          <Link to="/" className="inline-flex items-center gap-1 text-xs font-medium text-[var(--color-ring)] hover:underline mb-1 align-middle leading-normal">
            <span className="material-symbols-outlined text-sm">arrow_back</span>Back to Dashboard
          </Link>
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0">
                <h1 className="text-xl font-bold text-[var(--color-text)] truncate">{run.run_id || runId}</h1>
                {created && <p className="text-xs text-[var(--color-text-muted)] shrink-0">Generated {created}</p>}
              </div>
              {dateRangeStr && <p className="text-xs text-[var(--color-text-secondary)] mt-0.5">{dateRangeStr}</p>}
            </div>
            <div className="flex flex-wrap gap-1 shrink-0">
              <Button variant="secondary" size="sm" onClick={(e) => handleDownload(e, 'excel')}><span className="material-symbols-outlined text-sm">table_chart</span>Excel</Button>
              <Button variant="secondary" size="sm" onClick={(e) => handleDownload(e, 'pdf')}><span className="material-symbols-outlined text-sm">picture_as_pdf</span>PDF</Button>
              <Button variant="secondary" size="sm" onClick={(e) => handleDownload(e, 'csv')}><span className="material-symbols-outlined text-sm">description</span>CSV</Button>
              <Button variant="danger-ghost" size="sm" onClick={() => setDeleteOpen(true)}><span className="material-symbols-outlined text-sm">delete</span>Delete</Button>
            </div>
          </div>
        </div>

        {/* ── Table card ──────────────────────────────── */}
        <div className="flex-1 min-h-0 px-3 sm:px-4 lg:px-5 pb-2 flex flex-col">
          <div className="rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-sm)] overflow-hidden flex flex-col flex-1 min-h-0">

            {/* Toolbar */}
            <div className="px-3 py-2 border-b border-[var(--color-border)] flex flex-wrap items-center gap-2 shrink-0">
              <div className="relative flex-1 min-w-[160px]">
                <span className="material-symbols-outlined absolute left-2 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] text-base pointer-events-none">search</span>
                <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by medicine name..."
                  className="w-full pl-8 pr-3 py-1.5 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] text-xs transition-default" />
              </div>
              <label className="flex items-center gap-2 cursor-pointer select-none text-sm text-[var(--color-text-secondary)]">
                <input type="checkbox" checked={compactView} onChange={(e) => setCompactView(e.target.checked)} className="rounded border-gray-300 text-[var(--color-ring)] focus:ring-[var(--color-ring)]" />
                Compact view
              </label>
              <div className="relative" ref={colFilterRef}>
                <Button variant="secondary" size="sm" onClick={() => setColFilterOpen(o => !o)} aria-expanded={colFilterOpen}>
                  <span className="material-symbols-outlined text-sm">view_column</span>Columns<span className="material-symbols-outlined text-xs">{colFilterOpen ? 'expand_less' : 'expand_more'}</span>
                </Button>
                {colFilterOpen && allColKeys.length > 0 && (
                  <div className="absolute right-0 top-full mt-1 z-[100] w-60 max-h-72 overflow-y-auto rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-lg)] py-1.5">
                    <p className="px-3 py-1.5 text-xs font-medium text-[var(--color-text-muted)] border-b border-[var(--color-border)] mb-1">Toggle columns</p>
                    {allColKeys.filter(k => !isRequiredColumn(k)).map(key => (
                      <label key={key} className="flex items-center gap-2 px-3 py-1.5 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer text-xs text-[var(--color-text)]">
                        <input type="checkbox" checked={!hiddenCols.includes(key)} onChange={() => toggleCol(key)} className="rounded border-gray-300 text-[var(--color-ring)] focus:ring-[var(--color-ring)]" />
                        <span className="truncate">{getColumnDisplayLabel(key)}</span>
                      </label>
                    ))}
                    {hiddenCols.length > 0 && (
                      <button type="button" onClick={() => setHiddenCols([])} className="w-full mt-1 py-1.5 text-xs text-[var(--color-ring)] hover:bg-[var(--color-ring)]/5 transition-default">Show all</button>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Table content */}
            {itemsError ? (
              <div className="flex-1 flex items-center justify-center p-8">
                <div className="text-center">
                  <StatusBanner type="warning" className="mb-3">Could not load table data</StatusBanner>
                  <Button size="sm" onClick={retryItems} disabled={retrying}>{retrying ? 'Loading...' : 'Try again'}</Button>
                </div>
              </div>
            ) : filtered.length === 0 ? (
              <EmptyState
                icon={items.length === 0 ? 'table_rows' : 'search_off'}
                title={items.length === 0 ? 'No data in this report' : 'No rows match your search'}
                className="flex-1"
              />
            ) : (
              <div className="flex flex-col flex-1 min-h-0">
                {/* Scrollable table */}
                <div ref={tableScrollRef} className="report-table-scroll overflow-auto flex-1 min-h-0 w-full">
                  <table className="w-full text-left border-separate border-spacing-0" style={{ minWidth: 'max(100%, max-content)' }}>
                    <thead>
                      <tr>
                        {displayCols.map((key, i) => (
                          <th key={key} className={`px-2.5 py-1.5 text-[11px] font-bold uppercase tracking-wider text-[#5F6368] dark:text-[#9AA0A6] cursor-pointer select-none hover:bg-gray-100 dark:hover:bg-gray-800 transition-default border-b border-[var(--color-border)] whitespace-nowrap ${thStickyClass(i)} ${i > 1 ? 'min-w-[70px]' : ''}`}
                            onClick={() => handleSort(key)} title={normalizeColKey(key)}>
                            <div className="flex items-center gap-1">
                              {getColumnDisplayLabel(key)}
                              {effectiveSort === key && <span className="material-symbols-outlined" style={{ fontSize: 14 }}>{sortDir === 'asc' ? 'arrow_upward' : 'arrow_downward'}</span>}
                            </div>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {filtered.map((row, idx) => (
                        <tr key={(row.medicine_key ?? row.NDC ?? row.ndc ?? '') + idx}
                          role="button" tabIndex={0}
                          onClick={() => openPanel(row)}
                          onKeyDown={(e) => { if (e.key === 'Enter') openPanel(row) }}
                          className="group cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-default">
                          {displayCols.map((key, i) => {
                            const raw = row[key]
                            const num = parseNumeric(raw)
                            const isNum = !Number.isNaN(num)
                            const base = `px-2.5 py-1.5 text-xs tabular-nums text-[var(--color-text)] whitespace-nowrap border-b border-[var(--color-border-subtle)] ${tdStickyClass(i)} ${i > 1 ? 'min-w-[70px]' : ''}`
                            const empty = raw === '' || raw === undefined || raw === null
                            if (empty) return <td key={key} className={base} />
                            if (isShortageColumn(key) && isNum && num < 0) return <td key={key} className={base}><span className="text-red-600 dark:text-red-400 font-medium">{num % 1 === 0 ? num.toLocaleString() : num.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:4})}</span></td>
                            if (isAmountColumn(key) && isNum) { const s = String(raw).trim(); return <td key={key} className={base}><span>{s.startsWith('$') ? s : `$${num.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})}`}</span></td> }
                            if (isNum) return <td key={key} className={base}><span>{num % 1 === 0 ? num.toLocaleString() : num.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:4})}</span></td>
                            return <td key={key} className={base}>{String(raw)}</td>
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Sticky footer */}
                <div className={`shrink-0 px-3 py-1.5 text-center text-xs font-medium text-[var(--color-text-muted)] border-t border-[var(--color-border)] ${headerBg}`}>
                  Showing {filtered.length} of {items.length} medicines
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <MedicineDetailPanel open={panelOpen} onClose={() => setPanelOpen(false)} runId={runId} medicineIdentifier={panelId} fallbackRow={panelRow} />
      <AppToast toast={toast} onDismiss={() => setToast(null)} />
      <ConfirmDialog open={deleteOpen} title="Delete report" message={`Delete report "${runId}"? This cannot be undone.`} confirmLabel="Delete" variant="danger" onConfirm={handleDelete} onCancel={() => setDeleteOpen(false)} />
    </Layout>
  )
}
