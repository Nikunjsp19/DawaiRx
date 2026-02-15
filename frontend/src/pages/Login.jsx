import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { login as apiLogin, register as apiRegister, requestAccess, checkRequestStatus } from '../api/client'

const VIEWS = {
  login: 'login',
  request: 'request',
  check: 'check',
  register: 'register',
}

export default function Login() {
  const navigate = useNavigate()
  const { token, login: setAuth } = useAuth()

  const [view, setView] = useState(VIEWS.login)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [loginUserId, setLoginUserId] = useState('')
  const [loginPassword, setLoginPassword] = useState('')

  const [requestUserId, setRequestUserId] = useState('')
  const [requestEmail, setRequestEmail] = useState('')
  const [requestCompany, setRequestCompany] = useState('')
  const [requestReason, setRequestReason] = useState('')

  const [checkUserId, setCheckUserId] = useState('')
  const [checkResult, setCheckResult] = useState(null)

  const [registerUserId, setRegisterUserId] = useState('')
  const [registerEmail, setRegisterEmail] = useState('')
  const [registerPassword, setRegisterPassword] = useState('')

  const clearMessages = () => {
    setError('')
    setSuccess('')
  }

  const handleLogin = async (event) => {
    event.preventDefault()
    clearMessages()
    setLoading(true)
    try {
      const data = await apiLogin(loginUserId.trim(), loginPassword)
      setAuth(data.access_token, data.user_id)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err?.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleRequestAccess = async (event) => {
    event.preventDefault()
    clearMessages()

    if (requestUserId.trim().length < 3) {
      setError('Desired User ID must be at least 3 characters.')
      return
    }

    setLoading(true)
    try {
      await requestAccess({
        userId: requestUserId.trim(),
        email: requestEmail.trim(),
        company: requestCompany.trim(),
        reason: requestReason.trim(),
      })

      setSuccess('Registration request submitted successfully. Admin will review your request.')
      setTimeout(() => {
        setView(VIEWS.login)
        setSuccess('')
      }, 2200)
    } catch (err) {
      setError(err?.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  const handleCheckStatus = async (event) => {
    event.preventDefault()
    clearMessages()
    setCheckResult(null)

    if (!checkUserId.trim()) {
      setError('Please enter your User ID.')
      return
    }

    setLoading(true)
    try {
      const result = await checkRequestStatus(checkUserId.trim())
      setCheckResult(result)
      if (result?.approved || result?.status === 'approved') {
        setRegisterUserId(checkUserId.trim())
        setView(VIEWS.register)
      }
    } catch (err) {
      setError(err?.message || 'Failed to check request status')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (event) => {
    event.preventDefault()
    clearMessages()

    if (registerUserId.trim().length < 3) {
      setError('User ID must be at least 3 characters.')
      return
    }

    if (registerPassword.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }

    setLoading(true)
    try {
      const data = await apiRegister({
        userId: registerUserId.trim(),
        email: registerEmail.trim(),
        password: registerPassword,
      })

      if (data?.access_token) {
        setAuth(data.access_token, data.user_id || registerUserId.trim())
        navigate('/', { replace: true })
        return
      }

      setSuccess('Registration successful! Please sign in.')
      setView(VIEWS.login)
    } catch (err) {
      setError(err?.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const inputClass = 'login-input w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:ring-2 focus:ring-primary focus:border-primary transition-colors text-sm'
  const labelClass = 'block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2'
  const btnPrimary = 'w-full flex items-center justify-center gap-2 h-12 px-5 bg-primary hover:bg-primary/90 text-white text-sm font-bold rounded-lg shadow-lg shadow-primary/30 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70 disabled:pointer-events-none'

  return (
    <div className="login-page-wrap min-h-screen flex flex-col bg-background-light dark:bg-background-dark text-slate-900 dark:text-slate-100 transition-colors duration-200 font-display">
      <header className="login-header w-full border-b border-slate-200 dark:border-slate-800 bg-surface-light dark:bg-surface-dark px-6 py-4 lg:px-10">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-3 text-primary">
            <div className="login-logo flex items-center justify-center size-10 bg-primary/10 rounded-lg">
              <span className="material-symbols-outlined text-3xl">medication_liquid</span>
            </div>
            <h1 className="text-xl lg:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">DawaiRx</h1>
          </div>
        </div>
      </header>

      <main className="flex-1 w-full max-w-7xl mx-auto px-3 sm:px-4 lg:px-6 py-4 lg:py-6 flex flex-col items-center justify-center">
        <div className="w-full max-w-sm">
          {view === VIEWS.login && (
            <div className="login-card bg-surface-light dark:bg-surface-dark rounded-lg border border-slate-200/50 dark:border-slate-700/50 overflow-hidden shadow-sm">
              <div className="p-6">
                <div className="text-center mb-6">
                  <div className="login-card-icon inline-flex items-center justify-center size-12 rounded-full bg-primary/10 text-primary mb-3">
                    <span className="material-symbols-outlined text-2xl">lock</span>
                  </div>
                  <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-1">Welcome Back</h2>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Sign in to your account to continue</p>
                </div>

                {error && (
                  <div className="mb-5 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-900/30">
                    <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
                  </div>
                )}
                {success && (
                  <div className="mb-5 p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-900/30">
                    <p className="text-sm text-green-800 dark:text-green-300">{success}</p>
                  </div>
                )}

                <form onSubmit={handleLogin} className="space-y-4">
                  <div>
                    <label htmlFor="userId" className={labelClass}>User ID</label>
                    <div className="relative">
                      <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xl">person</span>
                      <input
                        type="text"
                        id="userId"
                        value={loginUserId}
                        onChange={(e) => { setLoginUserId(e.target.value); clearMessages() }}
                        className={inputClass}
                        placeholder="Enter your user ID"
                        autoComplete="username"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="password" className={labelClass}>Password</label>
                    <div className="relative">
                      <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xl">lock</span>
                      <input
                        type="password"
                        id="password"
                        value={loginPassword}
                        onChange={(e) => { setLoginPassword(e.target.value); clearMessages() }}
                        className={inputClass}
                        placeholder="Enter your password"
                        autoComplete="current-password"
                        required
                      />
                    </div>
                  </div>

                  <button type="submit" disabled={loading} className={btnPrimary}>
                    <span className="material-symbols-outlined text-lg">{loading ? 'sync' : 'login'}</span>
                    <span>{loading ? 'Signing in...' : 'Sign In'}</span>
                  </button>
                </form>

                <div className="mt-6 text-center">
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    Don't have an account?{' '}
                    <button type="button" onClick={() => { setView(VIEWS.request); clearMessages() }} className="login-link text-primary hover:text-primary/80 font-semibold underline decoration-slate-300 dark:decoration-slate-600 underline-offset-4 transition-colors">
                      Request Access
                    </button>
                  </p>
                  <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                    <button type="button" onClick={() => { setView(VIEWS.check); clearMessages() }} className="login-link text-primary hover:text-primary/80 font-semibold underline decoration-slate-300 dark:decoration-slate-600 underline-offset-4 transition-colors">
                      Check request status
                    </button>
                  </p>
                </div>
              </div>
            </div>
          )}

          {view === VIEWS.request && (
            <div className="mt-6 bg-surface-light dark:bg-surface-dark rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
              <div className="p-8">
                <div className="text-center mb-8">
                  <div className="inline-flex items-center justify-center size-16 rounded-full bg-primary/10 text-primary mb-4">
                    <span className="material-symbols-outlined text-4xl">person_add</span>
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Request Access</h2>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Submit a registration request for admin approval</p>
                </div>

                {error && (
                  <div className="mb-5 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-900/30">
                    <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
                  </div>
                )}
                {success && (
                  <div className="mb-5 p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-900/30">
                    <p className="text-sm text-green-800 dark:text-green-300">{success}</p>
                  </div>
                )}

                <form onSubmit={handleRequestAccess} className="space-y-4">
                  <div>
                    <label htmlFor="reqUserId" className={labelClass}>Desired User ID *</label>
                    <div className="relative">
                      <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xl">person</span>
                      <input
                        type="text"
                        id="reqUserId"
                        value={requestUserId}
                        onChange={(e) => { setRequestUserId(e.target.value); clearMessages() }}
                        className={inputClass}
                        placeholder="Choose a user ID"
                        required
                        minLength={3}
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="reqEmail" className={labelClass}>Email (Optional)</label>
                    <div className="relative">
                      <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xl">email</span>
                      <input
                        type="email"
                        id="reqEmail"
                        value={requestEmail}
                        onChange={(e) => { setRequestEmail(e.target.value); clearMessages() }}
                        className={inputClass}
                        placeholder="Enter your email"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="reqCompany" className={labelClass}>Company/Organization (Optional)</label>
                    <div className="relative">
                      <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xl">business</span>
                      <input
                        type="text"
                        id="reqCompany"
                        value={requestCompany}
                        onChange={(e) => { setRequestCompany(e.target.value); clearMessages() }}
                        className={inputClass}
                        placeholder="Enter company name"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="reqReason" className={labelClass}>Reason for Access (Optional)</label>
                    <textarea
                      id="reqReason"
                      value={requestReason}
                      onChange={(e) => { setRequestReason(e.target.value); clearMessages() }}
                      rows={3}
                      className="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:ring-2 focus:ring-primary focus:border-primary transition-colors resize-none"
                      placeholder="Tell us why you need access to DawaiRx"
                    />
                  </div>

                  <button type="submit" disabled={loading} className={btnPrimary}>
                    <span className="material-symbols-outlined text-lg">{loading ? 'sync' : 'send'}</span>
                    <span>{loading ? 'Submitting...' : 'Submit Request'}</span>
                  </button>
                </form>

                <div className="mt-6 text-center">
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    Already have an account?{' '}
                    <button type="button" onClick={() => { setView(VIEWS.login); clearMessages() }} className="text-primary hover:text-primary/80 font-semibold underline decoration-slate-300 dark:decoration-slate-600 underline-offset-4 transition-colors">
                      Sign In
                    </button>
                  </p>
                </div>
              </div>
            </div>
          )}

          {view === VIEWS.check && (
            <div className="mt-6 bg-surface-light dark:bg-surface-dark rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
              <div className="p-8">
                <div className="text-center mb-6">
                  <div className="inline-flex items-center justify-center size-16 rounded-full bg-primary/10 text-primary mb-4">
                    <span className="material-symbols-outlined text-4xl">search</span>
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Check Request Status</h2>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Enter your desired User ID to check approval status</p>
                </div>

                {error && (
                  <div className="mb-5 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-900/30">
                    <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
                  </div>
                )}

                <form onSubmit={handleCheckStatus} className="space-y-4">
                  <div>
                    <label htmlFor="checkUserId" className={labelClass}>User ID</label>
                    <div className="relative">
                      <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xl">person</span>
                      <input
                        type="text"
                        id="checkUserId"
                        value={checkUserId}
                        onChange={(e) => { setCheckUserId(e.target.value); clearMessages(); setCheckResult(null) }}
                        className={inputClass}
                        placeholder="Enter your requested user ID"
                        required
                      />
                    </div>
                  </div>

                  <button type="submit" disabled={loading} className={btnPrimary}>
                    <span className="material-symbols-outlined text-lg">{loading ? 'sync' : 'search'}</span>
                    <span>{loading ? 'Checking...' : 'Check Status'}</span>
                  </button>
                </form>

                {checkResult && (
                  <div className={`mt-4 p-4 rounded-lg border ${checkResult.approved || checkResult.status === 'approved' ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-900/30 text-green-800 dark:text-green-300' : checkResult.status === 'pending' ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-900/30 text-yellow-800 dark:text-yellow-300' : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-900/30 text-red-800 dark:text-red-300'}`}>
                    <p className="text-sm font-medium">Status: {String(checkResult.status || 'unknown').toUpperCase()}</p>
                    {checkResult.message && <p className="text-sm mt-1">{checkResult.message}</p>}
                  </div>
                )}

                <div className="mt-6 text-center">
                  <button type="button" onClick={() => { setView(VIEWS.login); clearMessages(); setCheckResult(null) }} className="text-primary hover:text-primary/80 font-semibold underline decoration-slate-300 dark:decoration-slate-600 underline-offset-4 transition-colors text-sm">
                    Back to Sign In
                  </button>
                </div>
              </div>
            </div>
          )}

          {view === VIEWS.register && (
            <div className="mt-6 bg-surface-light dark:bg-surface-dark rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
              <div className="p-8">
                <div className="text-center mb-8">
                  <div className="inline-flex items-center justify-center size-16 rounded-full bg-green-500/10 text-green-500 mb-4">
                    <span className="material-symbols-outlined text-4xl">check_circle</span>
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Create Account</h2>
                  <p className="text-sm text-green-600 dark:text-green-400">Your request has been approved! Complete your registration.</p>
                </div>

                {error && (
                  <div className="mb-5 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-900/30">
                    <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
                  </div>
                )}
                {success && (
                  <div className="mb-5 p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-900/30">
                    <p className="text-sm text-green-800 dark:text-green-300">{success}</p>
                  </div>
                )}

                <form onSubmit={handleRegister} className="space-y-4">
                  <div>
                    <label htmlFor="regUserId" className={labelClass}>User ID</label>
                    <div className="relative">
                      <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xl">person</span>
                      <input
                        type="text"
                        id="regUserId"
                        value={registerUserId}
                        onChange={(e) => setRegisterUserId(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-white cursor-not-allowed"
                        readOnly
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="regEmail" className={labelClass}>Email (Optional)</label>
                    <div className="relative">
                      <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xl">email</span>
                      <input
                        type="email"
                        id="regEmail"
                        value={registerEmail}
                        onChange={(e) => setRegisterEmail(e.target.value)}
                        className={inputClass}
                        placeholder="Enter your email"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="regPassword" className={labelClass}>Password</label>
                    <div className="relative">
                      <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xl">lock</span>
                      <input
                        type="password"
                        id="regPassword"
                        value={registerPassword}
                        onChange={(e) => setRegisterPassword(e.target.value)}
                        className={inputClass}
                        placeholder="Enter password (min 6 characters)"
                        required
                        minLength={6}
                      />
                    </div>
                  </div>

                  <button type="submit" disabled={loading} className={btnPrimary}>
                    <span className="material-symbols-outlined text-lg">{loading ? 'sync' : 'person_add'}</span>
                    <span>{loading ? 'Creating...' : 'Complete Registration'}</span>
                  </button>
                </form>

                <div className="mt-6 text-center">
                  <button type="button" onClick={() => { setView(VIEWS.login); clearMessages() }} className="text-primary hover:text-primary/80 font-semibold underline decoration-slate-300 dark:decoration-slate-600 underline-offset-4 transition-colors text-sm">
                    Back to Sign In
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="login-footer w-full border-t border-slate-200 dark:border-slate-800 py-6 text-center">
        <p className="text-xs text-slate-400 dark:text-slate-500">© 2024 DawaiRx. All rights reserved. Secure & Private.</p>
      </footer>
    </div>
  )
}
