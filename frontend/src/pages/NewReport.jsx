import React, { useCallback, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import { Button, Card, Input, Label, StatusBanner, AppToast } from '../components/ui'
import { uploadReportFiles, runReport, UPLOAD_TIMEOUT_MS } from '../api/client'

function makeDefaultReportName(dateFrom, dateTo) {
  if (!dateFrom || !dateTo) return ''
  return `Report_${String(dateFrom).replaceAll('-', '')}_to_${String(dateTo).replaceAll('-', '')}`
}

function isDateRangeValid(dateFrom, dateTo) {
  if (!dateFrom || !dateTo) return false
  return new Date(dateFrom).getTime() <= new Date(dateTo).getTime()
}

/* ── Progress step icon ──────────────────────────────── */
function StepIcon({ status }) {
  if (status === 'complete')
    return (
      <div className="size-6 rounded-full bg-emerald-500 flex items-center justify-center">
        <span className="material-symbols-outlined text-white text-sm">check</span>
      </div>
    )
  if (status === 'active')
    return (
      <div className="size-6 rounded-full bg-[var(--color-ring)] animate-pulse flex items-center justify-center">
        <span className="material-symbols-outlined text-white text-sm">hourglass_empty</span>
      </div>
    )
  if (status === 'error')
    return (
      <div className="size-6 rounded-full bg-red-500 flex items-center justify-center">
        <span className="material-symbols-outlined text-white text-sm">close</span>
      </div>
    )
  return (
    <div className="size-6 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center">
      <span className="material-symbols-outlined text-gray-500 dark:text-gray-400 text-sm">radio_button_unchecked</span>
    </div>
  )
}

function formatTimeRemaining(seconds) {
  if (seconds < 60) return `${Math.round(seconds)}s`
  return `${Math.round(seconds / 60)}m`
}

export default function NewReport() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [reportName, setReportName] = useState('')
  const [orderedFiles, setOrderedFiles] = useState([])
  const [soldFile, setSoldFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [toast, setToast] = useState(null)
  const orderedRef = useRef(null)
  const soldRef = useRef(null)

  const [progress, setProgress] = useState({ percent: 0, text: '', stage: 'idle' })
  const progressStartRef = useRef(null)
  const abortRef = useRef(null)

  const canMoveStep1 = isDateRangeValid(dateFrom, dateTo)
  const canMoveStep2 = Boolean((reportName || makeDefaultReportName(dateFrom, dateTo)).trim())
  const canGenerate = orderedFiles.length > 0 && Boolean(soldFile)

  const computedName = useMemo(() => reportName.trim() || makeDefaultReportName(dateFrom, dateTo), [reportName, dateFrom, dateTo])

  const nextStep1 = () => { setError(''); if (!canMoveStep1) { setError('Please select a valid date range.'); return }; if (!reportName.trim()) setReportName(makeDefaultReportName(dateFrom, dateTo)); setStep(2) }
  const nextStep2 = () => { setError(''); if (!canMoveStep2) { setError('Please enter a report name.'); return }; setStep(3) }

  const updateProgress = useCallback((percent, text, stage) => {
    setProgress({ percent, text, stage })
  }, [])

  const handleCancel = useCallback(() => {
    if (abortRef.current) abortRef.current.abort()
    setLoading(false)
    setProgress({ percent: 0, text: '', stage: 'idle' })
  }, [])

  const handleGenerate = async () => {
    if (!canGenerate || loading) return
    setError(''); setLoading(true)
    progressStartRef.current = Date.now()
    abortRef.current = new AbortController()

    try {
      updateProgress(10, 'Uploading and validating files...', 'uploading')

      const uploadResult = await uploadReportFiles(orderedFiles, soldFile, null, dateFrom, dateTo, computedName)

      updateProgress(30, 'Processing batch 1 of 3...', 'validating')

      let runId = uploadResult?.run_id || uploadResult?.runId
      if (!runId) {
        const sessionId = uploadResult?.session_id || uploadResult?.sessionId
        if (!sessionId) throw new Error('Upload completed but no session ID returned.')

        updateProgress(50, 'Processing batch 2 of 3...', 'validating')

        const runResult = await runReport(sessionId, dateFrom, dateTo, computedName)
        runId = runResult?.run_id || runResult?.runId
      }

      updateProgress(80, 'Processing batch 3 of 3...', 'finalizing')

      if (!runId) throw new Error('Report generated but run ID was not returned.')

      updateProgress(100, 'Report generated successfully!', 'complete')
      await new Promise(r => setTimeout(r, 600))

      setToast({ type: 'success', message: 'Report generated successfully' })
      navigate(`/runs/${encodeURIComponent(runId)}`)
    } catch (err) {
      if (err?.name === 'AbortError') return
      const msg = err?.message || 'Failed to generate report'
      updateProgress(0, msg, 'error')
      setError(msg)
      setToast({ type: 'error', message: msg })
    } finally {
      setLoading(false)
    }
  }

  const stepClasses = (n) => step >= n
    ? 'bg-[var(--color-ring)] text-white'
    : 'bg-gray-200 dark:bg-gray-800 text-[var(--color-text-muted)]'
  const stepLabelClasses = (n) => step >= n
    ? 'text-[var(--color-text)] font-medium'
    : 'text-[var(--color-text-muted)]'

  const getStepStatus = (stageIndex) => {
    const stageOrder = ['uploading', 'validating', 'finalizing', 'complete']
    const currentIdx = stageOrder.indexOf(progress.stage)
    if (progress.stage === 'error' && stageIndex <= currentIdx) return stageIndex === currentIdx ? 'error' : 'complete'
    if (progress.stage === 'error') return stageIndex <= 0 ? 'error' : 'pending'
    if (currentIdx < 0) return 'pending'
    if (stageIndex < currentIdx) return 'complete'
    if (stageIndex === currentIdx) return progress.stage === 'complete' ? 'complete' : 'active'
    return 'pending'
  }

  const getStepStatusLabel = (stageIndex) => {
    const s = getStepStatus(stageIndex)
    if (s === 'complete') return 'Completed successfully'
    if (s === 'error') return 'Error occurred'
    if (s === 'active') {
      if (stageIndex === 0) return 'Uploading...'
      if (stageIndex === 1) return 'Scanning for discrepancies...'
      return 'Generating report...'
    }
    return 'Pending'
  }

  const estTimeRemaining = (() => {
    if (!progressStartRef.current || progress.percent <= 0 || progress.percent >= 100) return null
    const elapsed = (Date.now() - progressStartRef.current) / 1000
    const est = (elapsed / progress.percent) * (100 - progress.percent)
    return est
  })()

  return (
    <Layout>
      <div className="flex-1 flex flex-col items-center min-h-0 relative -mt-40" style={{ justifyContent: 'center', paddingBottom: '12%' }}>

        {/* Heading */}
        <div className="text-center mb-5 shrink-0">
          <h1 className="text-lg font-bold text-[var(--color-text)]">Create New Report</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-0.5">Follow the steps below to generate your inventory reconciliation report.</p>
        </div>

        {/* Step indicators */}
        <div className="w-full max-w-md mx-auto mb-5 shrink-0">
          <div className="flex items-center">
            {[{ n: 1, label: 'Date Range' }, { n: 2, label: 'Report Name' }, { n: 3, label: 'Upload Files' }].map((s, i, arr) => (
              <React.Fragment key={s.n}>
                <div className="flex flex-col items-center flex-shrink-0">
                  <div className={`size-8 rounded-full flex items-center justify-center text-xs font-semibold mb-1 transition-default ${stepClasses(s.n)}`}>{s.n}</div>
                  <span className={`text-[11px] ${stepLabelClasses(s.n)}`}>{s.label}</span>
                </div>
                {i < arr.length - 1 && (
                  <div className="flex-1 h-0.5 bg-gray-200 dark:bg-gray-800 mx-3 mt-[-16px]">
                    <div className="h-full bg-[var(--color-ring)] transition-all duration-300" style={{ width: step > s.n ? '100%' : '0%' }} />
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Step 1: Date Range */}
        {step === 1 && (
          <Card className="w-full max-w-md mx-auto shrink-0">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-[var(--color-ring)] text-lg">calendar_today</span>
              <h3 className="text-sm font-semibold text-[var(--color-text)]">Select Date Range</h3>
            </div>
            <p className="text-xs text-[var(--color-text-muted)] mb-4">Choose the period for your report.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
              <div><Label htmlFor="dateFrom" required>From Date</Label><Input type="date" id="dateFrom" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} required /></div>
              <div><Label htmlFor="dateTo" required>To Date</Label><Input type="date" id="dateTo" value={dateTo} onChange={(e) => setDateTo(e.target.value)} required /></div>
            </div>
            <div className="flex justify-end">
              <Button onClick={nextStep1}>Next<span className="material-symbols-outlined text-base">arrow_forward</span></Button>
            </div>
          </Card>
        )}

        {/* Step 2: Report Name */}
        {step === 2 && (
          <Card className="w-full max-w-md mx-auto shrink-0">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-[var(--color-ring)] text-lg">edit</span>
              <h3 className="text-sm font-semibold text-[var(--color-text)]">Report Name</h3>
            </div>
            <p className="text-xs text-[var(--color-text-muted)] mb-4">A default name has been generated based on your date range.</p>
            <div className="mb-4"><Label htmlFor="reportName" required>Report Name</Label><Input id="reportName" value={reportName} onChange={(e) => setReportName(e.target.value)} placeholder="Enter report name" required /></div>
            <div className="flex justify-between">
              <Button variant="secondary" onClick={() => setStep(1)}><span className="material-symbols-outlined text-base">arrow_back</span>Back</Button>
              <Button onClick={nextStep2}>Next<span className="material-symbols-outlined text-base">arrow_forward</span></Button>
            </div>
          </Card>
        )}

        {/* Step 3: Upload Files */}
        {step === 3 && (
          <div className="w-full max-w-xl mx-auto shrink-0">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
              {/* Inventory Report */}
              <Card className="text-center">
                <div className="mb-2 inline-flex items-center justify-center size-9 rounded-full bg-[var(--color-ring)]/10 text-[var(--color-ring)]">
                  <span className="material-symbols-outlined text-lg">point_of_sale</span>
                </div>
                <h3 className="text-xs font-semibold text-[var(--color-text)] mb-0.5">Inventory Report</h3>
                <p className="text-[11px] text-[var(--color-text-muted)] mb-2">Upload dispensing log</p>
                <input ref={soldRef} className="hidden" type="file" accept=".csv,.xlsx,.xls" onChange={(e) => { setSoldFile(e.target.files?.[0] || null); setError('') }} />
                <button type="button" onClick={() => soldRef.current?.click()} className="w-full flex flex-col items-center justify-center h-[68px] border border-dashed border-[var(--color-border)] rounded-[var(--radius-md)] hover:border-[var(--color-ring)] hover:bg-gray-50 dark:hover:bg-gray-800 transition-default">
                  <span className="material-symbols-outlined text-[var(--color-text-muted)] text-base mb-0.5">cloud_upload</span>
                  <span className="text-xs text-[var(--color-ring)] font-medium">Click to upload</span>
                  <span className="text-[11px] text-[var(--color-text-muted)] mt-0.5">{soldFile?.name || 'No file chosen'}</span>
                </button>
              </Card>

              {/* Supplier Reports */}
              <Card className="text-center">
                <div className="mb-2 inline-flex items-center justify-center size-9 rounded-full bg-teal-500/10 text-teal-600 dark:text-teal-400">
                  <span className="material-symbols-outlined text-lg">inventory_2</span>
                </div>
                <h3 className="text-xs font-semibold text-[var(--color-text)] mb-0.5">Supplier Reports</h3>
                <p className="text-[11px] text-[var(--color-text-muted)] mb-2">Upload wholesaler invoices</p>
                <input ref={orderedRef} className="hidden" type="file" accept=".csv,.xlsx,.xls" multiple onChange={(e) => { setOrderedFiles(Array.from(e.target.files || [])); setError('') }} />
                <button type="button" onClick={() => orderedRef.current?.click()} className="w-full flex flex-col items-center justify-center h-[68px] border border-dashed border-[var(--color-border)] rounded-[var(--radius-md)] hover:border-teal-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-default">
                  <span className="material-symbols-outlined text-[var(--color-text-muted)] text-base mb-0.5">cloud_upload</span>
                  <span className="text-xs text-teal-600 dark:text-teal-400 font-medium">Click to upload</span>
                  <span className="text-[11px] text-[var(--color-text-muted)] mt-0.5">{orderedFiles.length ? `${orderedFiles.length} file(s)` : 'No files chosen'}</span>
                </button>
                {orderedFiles.length > 0 && (
                  <div className="mt-2 space-y-1 max-h-28 overflow-y-auto text-left">
                    {orderedFiles.map((f, i) => (
                      <div key={`${f.name}-${i}`} className="flex items-center justify-between gap-2 px-2 py-1 rounded-[var(--radius-sm)] bg-gray-50 dark:bg-gray-800 border border-[var(--color-border)]">
                        <span className="text-[11px] text-[var(--color-text)] truncate">{f.name}</span>
                        <button type="button" onClick={() => setOrderedFiles((p) => p.filter((_, idx) => idx !== i))} className="text-red-500 hover:text-red-600 shrink-0" aria-label={`Remove ${f.name}`}>
                          <span className="material-symbols-outlined text-sm">close</span>
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>

            <div className="flex items-center gap-3">
              <Button variant="secondary" onClick={() => setStep(2)} disabled={loading}><span className="material-symbols-outlined text-base">arrow_back</span>Back</Button>
              <Button className="flex-1" onClick={handleGenerate} disabled={!canGenerate || loading}>
                <span className="material-symbols-outlined text-lg">{loading ? 'sync' : 'analytics'}</span>
                {loading ? 'Generating...' : 'Generate Report'}
              </Button>
            </div>
          </div>
        )}

        {error && <StatusBanner type="error" className="w-full max-w-md mx-auto mt-3 shrink-0">{error}</StatusBanner>}

        {/* ── Progress overlay ────────────────────────────── */}
        {loading && (
          <div className="absolute inset-0 z-40 bg-[var(--color-bg)]/95 backdrop-blur-sm flex items-center justify-center">
            <div className="bg-[var(--color-surface)] rounded-[var(--radius-xl)] shadow-[var(--shadow-xl)] border-2 border-[var(--color-ring)]/20 max-w-lg w-full mx-4 p-6 sm:p-8 relative overflow-hidden">
              <div className="absolute inset-0 rounded-[var(--radius-xl)] bg-gradient-to-br from-[var(--color-ring)]/5 via-transparent to-transparent pointer-events-none" />

              <div className="relative z-10">
                {/* Spinning icon */}
                <div className="flex justify-center mb-5">
                  <div className="size-14 rounded-full bg-[var(--color-ring)]/10 flex items-center justify-center">
                    <span className="material-symbols-outlined text-[var(--color-ring)] text-3xl animate-spin">sync</span>
                  </div>
                </div>

                {/* Title + description */}
                <h2 className="text-lg font-bold text-center text-[var(--color-text)] mb-1">Report Generation in Progress</h2>
                <p className="text-xs text-center text-[var(--color-text-muted)] mb-5">
                  Please wait while we reconcile your pharmacy data against the dispensing logs. Do not close this window.
                </p>

                {/* Progress bar */}
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-1.5">
                    <p className="text-xs font-medium text-[var(--color-ring)]">{progress.text || 'Starting...'}</p>
                    <p className="text-xs font-semibold text-[var(--color-ring)] tabular-nums">{progress.percent}%</p>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-[var(--color-ring)] to-[var(--color-ring)]/80 rounded-full transition-all duration-500 ease-out"
                      style={{ width: `${progress.percent}%` }}
                    />
                  </div>
                  <div className="flex items-center gap-1 mt-1.5 text-[11px] text-[var(--color-text-muted)]">
                    <span className="material-symbols-outlined text-xs">schedule</span>
                    <span>
                      {progress.percent >= 100
                        ? 'Completed!'
                        : estTimeRemaining != null
                          ? `Est. time remaining: ${formatTimeRemaining(estTimeRemaining)}`
                          : 'Est. time remaining: Calculating...'}
                    </span>
                  </div>
                </div>

                {/* Step checklist */}
                <div className="space-y-3 mb-5">
                  {[
                    { label: 'Uploading Inventory Data', idx: 0 },
                    { label: 'Validating Records', idx: 1 },
                    { label: 'Finalizing Report', idx: 2 },
                  ].map(({ label, idx }) => {
                    const status = getStepStatus(idx)
                    return (
                      <div key={idx} className="flex items-start gap-3">
                        <div className="flex-shrink-0 mt-0.5"><StepIcon status={status} /></div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-[var(--color-text)]">{label}</p>
                          <p className={`text-xs ${
                            status === 'complete' ? 'text-emerald-600 dark:text-emerald-400'
                              : status === 'active' ? 'text-[var(--color-ring)]'
                              : status === 'error' ? 'text-red-500'
                              : 'text-[var(--color-text-muted)]'
                          }`}>
                            {getStepStatusLabel(idx)}
                          </p>
                        </div>
                      </div>
                    )
                  })}
                </div>

                {/* Cancel button */}
                <div className="flex justify-center">
                  <button
                    type="button"
                    onClick={handleCancel}
                    className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-[var(--color-text-muted)] hover:text-red-600 dark:hover:text-red-400 transition-default rounded-[var(--radius-md)] hover:bg-red-50 dark:hover:bg-red-900/20"
                  >
                    <span className="material-symbols-outlined text-base">close</span>
                    Cancel Run
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      <AppToast toast={toast} onDismiss={() => setToast(null)} />
    </Layout>
  )
}
