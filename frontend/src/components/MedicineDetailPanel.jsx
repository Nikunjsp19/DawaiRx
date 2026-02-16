import { useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import { getMedicineDetails } from '../api/client'
import { Spinner, StatusBanner } from './ui'

const FIELD_ORDER = ['RANK', 'PKG SIZE', 'TOTAL\nORDERED-O', 'TOTAL\nBILLED-B', 'TOTAL\nSHORTAGE-S', 'HIGHEST\nSHORTAGE-S', 'AMOUNT', 'COST']
const EXCLUDED_FIELDS = new Set(['NDC', 'DRUG NAME'])

function formatDate(dateStr) {
  if (!dateStr) return 'N/A'
  try {
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
      const [y, m, d] = dateStr.split('-').map(Number)
      const date = new Date(y, m - 1, d)
      if (date.getFullYear() === y && date.getMonth() === m - 1 && date.getDate() === d)
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
      return `${m}/${d}/${y}`
    }
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return String(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  } catch { return String(dateStr) }
}

function isMoneyField(f) { const u = String(f || '').toUpperCase(); return u.includes('AMOUNT') || u.includes('COST') }

function toDisplayValue(field, value) {
  if (value == null || value === '') return 'N/A'
  if (typeof value === 'number') return isMoneyField(field) ? `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : value.toLocaleString()
  const num = Number(value)
  if (!Number.isNaN(num) && value !== '' && String(value).trim() !== '') return isMoneyField(field) ? `$${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : num.toLocaleString()
  return String(value)
}

const TH = 'px-4 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-[var(--color-text-muted)]'
const TD = 'px-4 py-2.5 text-sm'

function MiniTable({ columns, rows, keyFn }) {
  return (
    <div className="rounded-[var(--radius-md)] border border-[var(--color-border)] overflow-hidden">
      <table className="w-full text-left">
        <thead className="bg-gray-50 dark:bg-gray-900 border-b border-[var(--color-border)]">
          <tr>{columns.map(c => <th key={c.key} className={`${TH} ${c.align === 'right' ? 'text-right' : ''}`}>{c.label}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-[var(--color-border-subtle)]">
          {rows.map((row, idx) => (
            <tr key={keyFn(row, idx)} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-default">
              {columns.map(c => <td key={c.key} className={`${TD} ${c.align === 'right' ? 'text-right' : ''} ${c.className || ''}`}>{c.render(row)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function MedicineDetailPanel({ open, onClose, runId, medicineIdentifier, fallbackRow }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [detail, setDetail] = useState(null)

  useEffect(() => {
    if (!open) return
    const h = (e) => { if (e.key === 'Escape') onClose?.() }
    document.addEventListener('keydown', h)
    return () => document.removeEventListener('keydown', h)
  }, [open, onClose])

  useEffect(() => {
    if (!open) return
    if (!runId || !medicineIdentifier) { setDetail(null); setError('Missing information.'); return }
    let cancel = false; setLoading(true); setError('')
    getMedicineDetails(runId, medicineIdentifier)
      .then(d => { if (!cancel) setDetail(d || null) })
      .catch(e => { if (!cancel) { setDetail(null); setError(e?.message || 'Failed to load.') } })
      .finally(() => { if (!cancel) setLoading(false) })
    return () => { cancel = true }
  }, [open, runId, medicineIdentifier])

  const ordered = Array.isArray(detail?.ordered_entries) ? detail.ordered_entries : []
  const sold = Array.isArray(detail?.sold_entries) ? detail.sold_entries : []
  const reportData = detail?.report_data && typeof detail.report_data === 'object' ? detail.report_data : (fallbackRow || {})
  const drugName = sold[0]?.drug_name || ordered[0]?.drug_name || fallbackRow?.['DRUG NAME'] || fallbackRow?.drug_name || medicineIdentifier || 'Medicine Details'
  const ndc = sold[0]?.ndc || ordered[0]?.ndc || reportData?.NDC || fallbackRow?.NDC || fallbackRow?.ndc || 'N/A'
  const totalOrdered = detail?.total_ordered ?? ordered.length
  const totalSold = detail?.total_sold ?? sold.length

  const sortedFields = useMemo(() => {
    const fields = Object.keys(reportData || {}).filter(f => !EXCLUDED_FIELDS.has(f) && reportData[f] != null && reportData[f] !== '' && reportData[f] !== 'N/A')
    fields.sort((a, b) => { const ai = FIELD_ORDER.indexOf(a), bi = FIELD_ORDER.indexOf(b); if (ai !== -1 && bi !== -1) return ai - bi; if (ai !== -1) return -1; if (bi !== -1) return 1; return a.localeCompare(b) })
    return fields
  }, [reportData])

  if (!open) return null

  const content = (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/30 z-[200]" onClick={onClose} aria-hidden="true" />

      {/* Panel */}
      <div className={`fixed inset-y-0 right-0 w-full sm:w-[480px] lg:w-[520px] bg-[var(--color-surface)] border-l border-[var(--color-border)] z-[201] flex flex-col shadow-[var(--shadow-xl)] transform transition-transform duration-200 ${open ? 'translate-x-0' : 'translate-x-full'}`}
        role="dialog" aria-modal="true" aria-label="Medicine details">

        {/* Header */}
        <div className="shrink-0 border-b border-[var(--color-border)] px-5 py-4 flex items-center justify-between">
          <div className="min-w-0">
            <h3 className="text-base font-semibold text-[var(--color-text)] truncate">{drugName}</h3>
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5">NDC: {ndc}</p>
          </div>
          <button type="button" onClick={onClose} className="shrink-0 size-8 flex items-center justify-center rounded-[var(--radius-md)] text-[var(--color-text-muted)] hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-[var(--color-text)] transition-default" aria-label="Close">
            <span className="material-symbols-outlined text-xl">close</span>
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5">
          {loading ? (
            <div className="flex items-center justify-center py-16"><Spinner size="lg" /></div>
          ) : error ? (
            <div className="py-12 text-center"><StatusBanner type="error">{error}</StatusBanner></div>
          ) : (
            <div className="space-y-6">
              {ordered.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Supplier Entries ({totalOrdered})</h4>
                  <MiniTable
                    columns={[
                      { key: 'supplier', label: 'Supplier', render: e => <span className="inline-flex items-center gap-1.5 text-[var(--color-text)]"><span className="w-1.5 h-1.5 rounded-full bg-green-500" />{e.supplier_name || 'Supplier'}</span> },
                      { key: 'date', label: 'Date', render: e => <span className="text-[var(--color-text-secondary)]">{formatDate(e.date)}</span> },
                      { key: 'qty', label: 'Qty', align: 'right', className: 'font-medium text-[var(--color-text)] tabular-nums', render: e => toDisplayValue('quantity', e.quantity ?? 0) },
                    ]}
                    rows={ordered}
                    keyFn={(e, i) => `${e.supplier_name || ''}-${e.date || ''}-${i}`}
                  />
                </div>
              )}

              {sold.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Inventory Entries ({totalSold})</h4>
                  <MiniTable
                    columns={[
                      { key: 'type', label: 'Type', render: e => <span className="inline-flex items-center gap-1.5 text-[var(--color-text)]"><span className="w-1.5 h-1.5 rounded-full bg-blue-500" />{e.source_name || 'Inventory'}</span> },
                      { key: 'date', label: 'Date', render: e => <span className="text-[var(--color-text-secondary)]">{formatDate(e.date)}</span> },
                      { key: 'qty', label: 'Qty', align: 'right', className: 'font-medium text-[var(--color-text)] tabular-nums', render: e => toDisplayValue('quantity', e.quantity ?? 0) },
                    ]}
                    rows={sold}
                    keyFn={(e, i) => `${e.source_name || ''}-${e.date || ''}-${i}`}
                  />
                </div>
              )}

              {sortedFields.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Report Data</h4>
                  <MiniTable
                    columns={[
                      { key: 'field', label: 'Field', className: 'font-medium text-[var(--color-text)]', render: f => f.replace(/\n/g, ' ') },
                      { key: 'value', label: 'Value', align: 'right', className: 'text-[var(--color-text)] tabular-nums', render: f => toDisplayValue(f, reportData[f]) },
                    ]}
                    rows={sortedFields}
                    keyFn={(f) => f}
                  />
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  )

  return createPortal(content, document.body)
}
