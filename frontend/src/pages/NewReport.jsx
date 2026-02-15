import { useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import { AppToast } from '../components/ui'
import { uploadReportFiles, runReport } from '../api/client'

function makeDefaultReportName(dateFrom, dateTo) {
  if (!dateFrom || !dateTo) return ''
  const from = String(dateFrom).replaceAll('-', '')
  const to = String(dateTo).replaceAll('-', '')
  return `Report_${from}_to_${to}`
}

function isDateRangeValid(dateFrom, dateTo) {
  if (!dateFrom || !dateTo) return false
  return new Date(dateFrom).getTime() <= new Date(dateTo).getTime()
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

  const orderedInputRef = useRef(null)
  const soldInputRef = useRef(null)
  const canMoveStep1 = isDateRangeValid(dateFrom, dateTo)
  const canMoveStep2 = Boolean((reportName || makeDefaultReportName(dateFrom, dateTo)).trim())
  const canGenerate = orderedFiles.length > 0 && Boolean(soldFile)

  const computedReportName = useMemo(() => {
    if (reportName.trim()) return reportName
    return makeDefaultReportName(dateFrom, dateTo)
  }, [reportName, dateFrom, dateTo])

  const handleStep1Next = () => {
    setError('')
    if (!canMoveStep1) {
      setError('Please select a valid date range.')
      return
    }
    if (!reportName.trim()) setReportName(makeDefaultReportName(dateFrom, dateTo))
    setStep(2)
  }

  const handleStep2Next = () => {
    setError('')
    if (!canMoveStep2) {
      setError('Please enter a report name.')
      return
    }
    setStep(3)
  }

  const handleGenerate = async () => {
    if (!canGenerate || loading) return
    setError('')
    setLoading(true)

    try {
      // Pass date range and report name so backend (Java) applies date filter in single upload+run request.
      const uploadResult = await uploadReportFiles(orderedFiles, soldFile, null, dateFrom, dateTo, computedReportName)
      let runId = uploadResult?.run_id || uploadResult?.runId

      // Legacy Python flow: upload returns session_id and then /api/run is called with dates.
      if (!runId) {
        const sessionId = uploadResult?.session_id || uploadResult?.sessionId
        if (!sessionId) {
          throw new Error('Upload completed but no session ID was returned.')
        }
        const runResult = await runReport(sessionId, dateFrom, dateTo, computedReportName)
        runId = runResult?.run_id || runResult?.runId
      }

      if (!runId) throw new Error('Report generation completed but run ID was not returned.')

      setToast({ type: 'success', message: 'Report generated successfully' })
      navigate(`/runs/${encodeURIComponent(runId)}`)
    } catch (err) {
      const message = err?.message || 'Failed to generate report'
      setError(message)
      setToast({ type: 'error', message })
    } finally {
      setLoading(false)
    }
  }

  const handleOrderedChange = (event) => {
    const files = event.target.files ? Array.from(event.target.files) : []
    setOrderedFiles(files)
    setError('')
  }

  const removeOrderedFile = (indexToRemove) => {
    setOrderedFiles((prev) => prev.filter((_, index) => index !== indexToRemove))
  }

  return (
    <Layout>
      <main className="flex-1 w-full flex flex-col overflow-hidden relative">
        <div className="flex-1 flex flex-col items-center justify-start w-full px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
          <div className="text-center mb-8 w-full max-w-4xl" id="pageHeading">
            <h2 className="text-3xl lg:text-4xl font-bold tracking-tight text-slate-900 dark:text-white mb-2">
              Create New Report
            </h2>
            <p className="text-base text-slate-500 dark:text-slate-400">
              Follow the steps below to generate your inventory reconciliation report.
            </p>
          </div>

          <div className="w-full max-w-3xl mx-auto mb-8" id="stepIndicators">
            <div className="flex items-center justify-between">
              <div className="flex flex-col items-center flex-1">
                <div className={`size-10 rounded-full flex items-center justify-center font-semibold text-base mb-2 transition-all ${step >= 1 ? 'bg-primary text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'}`}>
                  1
                </div>
                <p className={`text-sm font-medium ${step >= 1 ? 'text-slate-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}`}>Date Range</p>
              </div>
              <div className="flex-1 h-1 bg-gray-200 dark:bg-gray-700 mx-3">
                <div className="h-full bg-primary transition-all duration-300" style={{ width: step >= 2 ? '100%' : '0%' }} />
              </div>

              <div className="flex flex-col items-center flex-1">
                <div className={`size-10 rounded-full flex items-center justify-center font-semibold text-base mb-2 transition-all ${step >= 2 ? 'bg-primary text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'}`}>
                  2
                </div>
                <p className={`text-sm font-medium ${step >= 2 ? 'text-slate-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}`}>Report Name</p>
              </div>
              <div className="flex-1 h-1 bg-gray-200 dark:bg-gray-700 mx-3">
                <div className="h-full bg-primary transition-all duration-300" style={{ width: step >= 3 ? '100%' : '0%' }} />
              </div>

              <div className="flex flex-col items-center flex-1">
                <div className={`size-10 rounded-full flex items-center justify-center font-semibold text-base mb-2 transition-all ${step >= 3 ? 'bg-primary text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'}`}>
                  3
                </div>
                <p className={`text-sm font-medium ${step >= 3 ? 'text-slate-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}`}>Upload Files</p>
              </div>
            </div>
          </div>

          {step === 1 && (
            <div className="w-full max-w-2xl mx-auto mb-6">
              <div className="bg-surface-light dark:bg-surface-dark rounded-xl shadow-sm border border-slate-200/50 dark:border-slate-700/50 p-8">
                <div className="flex items-center gap-3 mb-4">
                  <span className="material-symbols-outlined text-primary text-xl">calendar_today</span>
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Select Date Range</h3>
                </div>
                <p className="text-slate-500 dark:text-slate-400 mb-4 text-sm">
                  Choose the date range for your report.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <label htmlFor="dateFrom" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      From Date <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="date"
                      id="dateFrom"
                      value={dateFrom}
                      onChange={(e) => setDateFrom(e.target.value)}
                      className="w-full px-4 py-2.5 text-sm rounded-md border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                      required
                    />
                  </div>
                  <div>
                    <label htmlFor="dateTo" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      To Date <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="date"
                      id="dateTo"
                      value={dateTo}
                      onChange={(e) => setDateTo(e.target.value)}
                      className="w-full px-4 py-2.5 text-sm rounded-md border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
                      required
                    />
                  </div>
                </div>
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={handleStep1Next}
                    className="px-5 py-2.5 bg-primary hover:bg-primary/90 text-white text-sm font-medium rounded-md transition-colors flex items-center gap-2"
                  >
                    <span>Next</span>
                    <span className="material-symbols-outlined text-base">arrow_forward</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="w-full max-w-2xl mx-auto mb-6">
              <div className="bg-surface-light dark:bg-surface-dark rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-8">
                <div className="flex items-center gap-3 mb-4">
                  <span className="material-symbols-outlined text-primary text-2xl">edit</span>
                  <h3 className="text-xl font-bold text-slate-900 dark:text-white">Report Name</h3>
                </div>
                <p className="text-slate-600 dark:text-slate-300 mb-4 text-sm">
                  Enter a name for your report. A default name has been generated based on your selected date range.
                </p>
                <div className="mb-4">
                  <label htmlFor="reportName" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Report Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="reportName"
                    value={reportName}
                    onChange={(e) => setReportName(e.target.value)}
                    placeholder="Enter report name"
                    className="w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-primary focus:border-transparent"
                    required
                  />
                </div>
                <div className="flex justify-between">
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="px-6 py-3 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 font-semibold rounded-lg transition-colors flex items-center gap-2"
                  >
                    <span className="material-symbols-outlined">arrow_back</span>
                    <span>Back</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleStep2Next}
                    className="px-6 py-3 bg-primary hover:bg-primary/90 text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
                  >
                    <span>Next</span>
                    <span className="material-symbols-outlined">arrow_forward</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="w-full max-w-4xl mx-auto mb-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 items-start">
                <div className="group relative flex flex-col bg-surface-light dark:bg-surface-dark rounded-lg border border-slate-200/50 dark:border-slate-700/50 overflow-hidden h-fit">
                  <div className="p-5 flex flex-col items-center">
                    <div className="mb-4 p-3 rounded-full bg-primary/5 text-primary group-hover:bg-primary/10 transition-colors">
                      <span className="material-symbols-outlined text-2xl">point_of_sale</span>
                    </div>
                    <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-2">Inventory Report</h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400 text-center mb-4">Upload dispensing log</p>

                    <input
                      ref={soldInputRef}
                      className="hidden"
                      id="soldFile"
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      onChange={(e) => {
                        setSoldFile(e.target.files?.[0] || null)
                        setError('')
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => soldInputRef.current?.click()}
                      className="w-full relative flex flex-col items-center justify-center h-24 border border-dashed border-slate-200 dark:border-slate-600 rounded-md bg-slate-50/50 dark:bg-slate-800/30 hover:bg-slate-100 dark:hover:bg-slate-800 hover:border-primary transition-all"
                    >
                      <span className="material-symbols-outlined text-slate-400 mb-1 text-lg">cloud_upload</span>
                      <p className="text-sm text-slate-500 dark:text-slate-400"><span className="font-medium text-primary">Click to upload</span></p>
                      <p className="text-xs text-slate-400 mt-1">{soldFile?.name || 'No file chosen'}</p>
                    </button>
                  </div>
                </div>

                <div className="group relative flex flex-col bg-surface-light dark:bg-surface-dark rounded-lg border border-slate-200/50 dark:border-slate-700/50 overflow-hidden h-fit">
                  <div className="p-5 flex flex-col items-center">
                    <div className="mb-4 p-3 rounded-full bg-teal-500/10 text-teal-600 dark:text-teal-400 group-hover:bg-teal-500/20 transition-colors">
                      <span className="material-symbols-outlined text-2xl">inventory_2</span>
                    </div>
                    <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-2">Supplier Reports</h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400 text-center mb-4">Upload wholesaler invoice</p>

                    <input
                      ref={orderedInputRef}
                      className="hidden"
                      id="orderedFiles"
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      multiple
                      onChange={handleOrderedChange}
                    />
                    <button
                      type="button"
                      onClick={() => orderedInputRef.current?.click()}
                      className="w-full relative flex flex-col items-center justify-center h-24 border border-dashed border-slate-200 dark:border-slate-600 rounded-md bg-slate-50/50 dark:bg-slate-800/30 hover:bg-slate-100 dark:hover:bg-slate-800 hover:border-teal-500 transition-all"
                    >
                      <span className="material-symbols-outlined text-slate-400 mb-1 text-lg">cloud_upload</span>
                      <p className="text-sm text-slate-500 dark:text-slate-400"><span className="font-medium text-teal-600 dark:text-teal-400">Click to upload</span></p>
                      <p className="text-xs text-slate-400 mt-1">{orderedFiles.length ? `${orderedFiles.length} file(s) chosen` : 'No files chosen'}</p>
                    </button>

                    {orderedFiles.length > 0 && (
                      <div className="mt-3 w-full space-y-2 max-h-48 overflow-y-auto">
                        {orderedFiles.map((file, index) => (
                          <div key={`${file.name}-${index}`} className="flex items-center justify-between gap-2 px-3 py-2 rounded-md bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                            <p className="text-xs text-slate-700 dark:text-slate-300 truncate">{file.name}</p>
                            <button
                              type="button"
                              onClick={() => removeOrderedFile(index)}
                              className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                              aria-label={`Remove ${file.name}`}
                            >
                              <span className="material-symbols-outlined text-base">delete</span>
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="w-full max-w-4xl mx-auto flex flex-col items-center justify-center gap-4">
                <div className="flex items-center gap-4 w-full">
                  <button
                    type="button"
                    onClick={() => setStep(2)}
                    disabled={loading}
                    className="px-5 py-2.5 border border-slate-200 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 text-sm font-medium rounded-md transition-colors flex items-center gap-2 disabled:opacity-50"
                  >
                    <span className="material-symbols-outlined text-lg">arrow_back</span>
                    <span>Back</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleGenerate}
                    disabled={!canGenerate || loading}
                    className="flex-1 group flex items-center justify-center gap-2 h-12 px-5 bg-primary hover:bg-primary/90 text-white text-sm font-semibold rounded-md transition-all disabled:opacity-60"
                  >
                    <span className="material-symbols-outlined text-lg">{loading ? 'sync' : 'analytics'}</span>
                    <span>{loading ? 'Generating Report...' : 'Generate Report'}</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="w-full max-w-2xl mt-2 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-900/30">
              <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
            </div>
          )}
        </div>

        {loading && (
          <div className="absolute inset-0 z-40 bg-background-light/95 dark:bg-background-dark/95 backdrop-blur-sm flex items-center justify-center">
            <div className="bg-surface-light dark:bg-surface-dark rounded-2xl shadow-2xl border-2 border-primary/20 max-w-xl w-full mx-4 p-8 text-center">
              <div className="inline-flex items-center justify-center size-16 rounded-full bg-primary/10 text-primary mb-4">
                <span className="material-symbols-outlined text-4xl animate-spin">sync</span>
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Audit in Progress</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400">Processing uploads and generating reconciliation report...</p>
            </div>
          </div>
        )}
      </main>

      <AppToast toast={toast} onDismiss={() => setToast(null)} />
    </Layout>
  )
}
