import { useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import { getMedicineDetails } from '../api/client'

const FIELD_ORDER = ['RANK', 'PKG SIZE', 'TOTAL\nORDERED-O', 'TOTAL\nBILLED-B', 'TOTAL\nSHORTAGE-S', 'HIGHEST\nSHORTAGE-S', 'AMOUNT', 'COST']
const EXCLUDED_FIELDS = new Set(['NDC', 'DRUG NAME'])

function formatDate(dateStr) {
  if (!dateStr) return 'N/A'
  try {
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
      const [year, month, day] = dateStr.split('-').map(Number)
      const date = new Date(year, month - 1, day)
      if (date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day) {
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
      }
      return `${month}/${day}/${year}`
    }
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return String(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  } catch {
    return String(dateStr)
  }
}

function isMoneyField(field) {
  const f = String(field || '').toUpperCase()
  return f.includes('AMOUNT') || f.includes('COST')
}

function toDisplayValue(field, value) {
  if (value == null || value === '') return 'N/A'
  if (typeof value === 'number') {
    if (isMoneyField(field)) {
      return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    }
    return value.toLocaleString()
  }
  const num = Number(value)
  if (!Number.isNaN(num) && value !== '' && String(value).trim() !== '') {
    if (isMoneyField(field)) {
      return `$${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    }
    return num.toLocaleString()
  }
  return String(value)
}

export default function MedicineDetailPanel({ open, onClose, runId, medicineIdentifier, fallbackRow }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [detail, setDetail] = useState(null)

  useEffect(() => {
    if (!open) return
    const onKeyDown = (e) => {
      if (e.key === 'Escape') onClose?.()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [open, onClose])

  useEffect(() => {
    if (!open) return
    if (!runId || !medicineIdentifier) {
      setDetail(null)
      setError('Missing information to load medicine details')
      return
    }

    let cancelled = false
    setLoading(true)
    setError('')
    getMedicineDetails(runId, medicineIdentifier)
      .then((data) => {
        if (!cancelled) setDetail(data || null)
      })
      .catch((e) => {
        if (!cancelled) {
          setDetail(null)
          setError(e?.message || 'Failed to load medicine details')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [open, runId, medicineIdentifier])

  const orderedEntries = Array.isArray(detail?.ordered_entries) ? detail.ordered_entries : []
  const soldEntries = Array.isArray(detail?.sold_entries) ? detail.sold_entries : []
  const reportData = detail?.report_data && typeof detail.report_data === 'object'
    ? detail.report_data
    : (fallbackRow && typeof fallbackRow === 'object' ? fallbackRow : {})

  const drugName = soldEntries[0]?.drug_name
    || orderedEntries[0]?.drug_name
    || fallbackRow?.['DRUG NAME']
    || fallbackRow?.drug_name
    || medicineIdentifier
    || 'Medicine Details'

  const ndc = soldEntries[0]?.ndc
    || orderedEntries[0]?.ndc
    || reportData?.NDC
    || fallbackRow?.NDC
    || fallbackRow?.ndc
    || 'N/A'

  const totalOrdered = detail?.total_ordered ?? orderedEntries.length
  const totalSold = detail?.total_sold ?? soldEntries.length

  const sortedReportFields = useMemo(() => {
    const fields = Object.keys(reportData || {}).filter((field) => !EXCLUDED_FIELDS.has(field))
    fields.sort((a, b) => {
      const aIdx = FIELD_ORDER.indexOf(a)
      const bIdx = FIELD_ORDER.indexOf(b)
      if (aIdx !== -1 && bIdx !== -1) return aIdx - bIdx
      if (aIdx !== -1) return -1
      if (bIdx !== -1) return 1
      return a.localeCompare(b)
    })
    return fields
  }, [reportData])

  if (!open) return null

  const content = (
    <div
      className={`fixed inset-y-0 right-0 w-full lg:w-1/2 xl:w-2/5 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-800 transform transition-transform duration-300 overflow-y-auto shadow-2xl ${open ? 'translate-x-0' : 'translate-x-full'}`}
      style={{ zIndex: 99999 }}
      role="dialog"
      aria-modal="true"
      aria-label="Medicine details"
    >
      <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-6 py-4 z-10">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{drugName}</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">NDC: {ndc}</p>
          </div>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" aria-label="Close">
            <span className="material-symbols-outlined text-2xl">close</span>
          </button>
        </div>
      </div>

      <div className="p-6">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-600 dark:text-red-400">Failed to load medicine details</p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">{error}</p>
          </div>
        ) : (
          <div className="space-y-6">
            {orderedEntries.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Supplier Entries ({totalOrdered})</h4>
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-100 dark:bg-gray-700">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 dark:text-gray-300">Supplier</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 dark:text-gray-300">Date</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-700 dark:text-gray-300">Quantity</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                      {orderedEntries.map((entry, idx) => (
                        <tr key={`${entry.supplier_name || 'supplier'}-${entry.date || ''}-${idx}`} className="hover:bg-gray-100 dark:hover:bg-gray-700">
                          <td className="px-4 py-2 text-sm text-gray-900 dark:text-white">
                            <span className="inline-flex items-center gap-1">
                              <span className="w-2 h-2 rounded-full bg-green-500" />
                              {entry.supplier_name || 'Supplier'}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">{formatDate(entry.date)}</td>
                          <td className="px-4 py-2 text-sm text-right font-medium text-gray-900 dark:text-white">{toDisplayValue('quantity', entry.quantity ?? 0)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {soldEntries.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Inventory Report Entries ({totalSold})</h4>
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-100 dark:bg-gray-700">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 dark:text-gray-300">Type</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 dark:text-gray-300">Date</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-700 dark:text-gray-300">Quantity</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                      {soldEntries.map((entry, idx) => (
                        <tr key={`${entry.source_name || 'inventory'}-${entry.date || ''}-${idx}`} className="hover:bg-gray-100 dark:hover:bg-gray-700">
                          <td className="px-4 py-2 text-sm text-gray-900 dark:text-white">
                            <span className="inline-flex items-center gap-1">
                              <span className="w-2 h-2 rounded-full bg-blue-500" />
                              {entry.source_name || 'Inventory'}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">{formatDate(entry.date)}</td>
                          <td className="px-4 py-2 text-sm text-right font-medium text-gray-900 dark:text-white">{toDisplayValue('quantity', entry.quantity ?? 0)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {sortedReportFields.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Report Data</h4>
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-100 dark:bg-gray-700">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 dark:text-gray-300">Field</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-700 dark:text-gray-300">Value</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                      {sortedReportFields.map((field) => (
                        <tr key={field} className="hover:bg-gray-100 dark:hover:bg-gray-700">
                          <td className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 font-medium">{field.replace(/\n/g, ' ')}</td>
                          <td className="px-4 py-2 text-sm text-right text-gray-900 dark:text-white">{toDisplayValue(field, reportData[field])}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )

  return createPortal(content, document.body)
}
