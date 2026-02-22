import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { login as apiLogin, register as apiRegister, requestAccess, checkRequestStatus } from '../api/client'
import { Button, Input, Label, Textarea, StatusBanner } from '../components/ui'

const VIEWS = { login: 'login', request: 'request', check: 'check', register: 'register' }

export default function Login() {
  // Keep login interactions fast because this is the primary first-load route.
  const navigate = useNavigate()
  const { login: setAuth } = useAuth()

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

  const clear = () => { setError(''); setSuccess('') }

  /* ── handlers (unchanged business logic) ───────────── */
  const handleLogin = async (e) => {
    e.preventDefault(); clear(); setLoading(true)
    try {
      const data = await apiLogin(loginUserId.trim(), loginPassword)
      setAuth(data.access_token, data.user_id)
      navigate('/', { replace: true })
    } catch (err) { setError(err?.message || 'Login failed') }
    finally { setLoading(false) }
  }

  const handleRequestAccess = async (e) => {
    e.preventDefault(); clear()
    if (requestUserId.trim().length < 3) { setError('Desired User ID must be at least 3 characters.'); return }
    setLoading(true)
    try {
      await requestAccess({ userId: requestUserId.trim(), email: requestEmail.trim(), company: requestCompany.trim(), reason: requestReason.trim() })
      setSuccess('Registration request submitted. Admin will review your request.')
      setTimeout(() => { setView(VIEWS.login); setSuccess('') }, 2200)
    } catch (err) { setError(err?.message || 'Request failed') }
    finally { setLoading(false) }
  }

  const handleCheckStatus = async (e) => {
    e.preventDefault(); clear(); setCheckResult(null)
    if (!checkUserId.trim()) { setError('Please enter your User ID.'); return }
    setLoading(true)
    try {
      const result = await checkRequestStatus(checkUserId.trim())
      setCheckResult(result)
      if (result?.approved || result?.status === 'approved') { setRegisterUserId(checkUserId.trim()); setView(VIEWS.register) }
    } catch (err) { setError(err?.message || 'Failed to check request status') }
    finally { setLoading(false) }
  }

  const handleRegister = async (e) => {
    e.preventDefault(); clear()
    if (registerUserId.trim().length < 3) { setError('User ID must be at least 3 characters.'); return }
    if (registerPassword.length < 6) { setError('Password must be at least 6 characters.'); return }
    setLoading(true)
    try {
      const data = await apiRegister({ userId: registerUserId.trim(), email: registerEmail.trim(), password: registerPassword })
      if (data?.access_token) { setAuth(data.access_token, data.user_id || registerUserId.trim()); navigate('/', { replace: true }); return }
      setSuccess('Registration successful! Please sign in.'); setView(VIEWS.login)
    } catch (err) { setError(err?.message || 'Registration failed') }
    finally { setLoading(false) }
  }

  const switchView = (v) => { clear(); setCheckResult(null); setView(v) }

  /* ── shared sub-components ─────────────────────────── */
  // Keep alert rendering simple to avoid extra work during auth transitions.
  const Alerts = () => (
    <>
      {error && <StatusBanner type="error" className="mb-4">{error}</StatusBanner>}
      {success && <StatusBanner type="success" className="mb-4">{success}</StatusBanner>}
    </>
  )

  const TextLink = ({ onClick, children }) => (
    <button type="button" onClick={onClick} className="text-[var(--color-ring)] hover:underline font-medium text-sm transition-default">
      {children}
    </button>
  )

  /* ── render ────────────────────────────────────────── */
  return (
    <div className="min-h-screen flex flex-col bg-[var(--color-bg)] font-display">
      {/* Header */}
      <header className="border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 h-14 flex items-center shrink-0">
        <div className="mx-auto max-w-7xl w-full flex items-center gap-3">
          <div className="flex items-center justify-center size-8 bg-[var(--color-ring)]/10 rounded-[var(--radius-sm)] text-[var(--color-ring)]">
            <span className="material-symbols-outlined text-lg">local_pharmacy</span>
          </div>
          <span className="text-lg font-bold tracking-tight text-[var(--color-text)]">DawaiRx</span>
        </div>
      </header>

      {/* Body */}
      <main className="flex-1 flex items-center justify-center px-4 py-10">
        <div className="w-full max-w-sm">

          {/* ── Sign In ──────────────────────────────── */}
          {view === VIEWS.login && (
            <div className="bg-[var(--color-surface)] rounded-[var(--radius-xl)] border border-[var(--color-border)] shadow-[var(--shadow-md)] p-6">
              <div className="text-center mb-6">
                <div className="inline-flex items-center justify-center size-12 rounded-full bg-[var(--color-ring)]/10 text-[var(--color-ring)] mb-3">
                  <span className="material-symbols-outlined text-2xl">lock</span>
                </div>
                <h2 className="text-xl font-semibold text-[var(--color-text)]">Welcome Back</h2>
                <p className="text-sm text-[var(--color-text-muted)] mt-1">Sign in to your account</p>
              </div>
              <Alerts />
              <form onSubmit={handleLogin} className="space-y-4">
                <div><Label htmlFor="userId">User ID</Label><Input id="userId" icon="person" value={loginUserId} onChange={(e) => { setLoginUserId(e.target.value); clear() }} placeholder="Enter your user ID" autoComplete="username" required /></div>
                <div><Label htmlFor="password">Password</Label><Input id="password" icon="lock" type="password" value={loginPassword} onChange={(e) => { setLoginPassword(e.target.value); clear() }} placeholder="Enter your password" autoComplete="current-password" required /></div>
                <Button type="submit" disabled={loading} size="lg" className="w-full">
                  <span className={`material-symbols-outlined text-lg ${loading ? 'animate-spin' : ''}`}>{loading ? 'sync' : 'login'}</span>
                  {loading ? 'Signing in...' : 'Sign In'}
                </Button>
              </form>
              <div className="mt-6 text-center space-y-2 text-sm text-[var(--color-text-muted)]">
                <p>Don't have an account? <TextLink onClick={() => switchView(VIEWS.request)}>Request Access</TextLink></p>
                <p><TextLink onClick={() => switchView(VIEWS.check)}>Check request status</TextLink></p>
              </div>
            </div>
          )}

          {/* ── Request Access ───────────────────────── */}
          {view === VIEWS.request && (
            <div className="bg-[var(--color-surface)] rounded-[var(--radius-xl)] border border-[var(--color-border)] shadow-[var(--shadow-md)] p-6">
              <div className="text-center mb-6">
                <div className="inline-flex items-center justify-center size-12 rounded-full bg-[var(--color-ring)]/10 text-[var(--color-ring)] mb-3">
                  <span className="material-symbols-outlined text-2xl">person_add</span>
                </div>
                <h2 className="text-xl font-semibold text-[var(--color-text)]">Request Access</h2>
                <p className="text-sm text-[var(--color-text-muted)] mt-1">Submit a registration request for admin approval</p>
              </div>
              <Alerts />
              <form onSubmit={handleRequestAccess} className="space-y-4">
                <div><Label htmlFor="reqUserId" required>Desired User ID</Label><Input id="reqUserId" icon="person" value={requestUserId} onChange={(e) => { setRequestUserId(e.target.value); clear() }} placeholder="Choose a user ID" required minLength={3} /></div>
                <div><Label htmlFor="reqEmail">Email</Label><Input id="reqEmail" icon="email" type="email" value={requestEmail} onChange={(e) => { setRequestEmail(e.target.value); clear() }} placeholder="Enter your email" /></div>
                <div><Label htmlFor="reqCompany">Company / Organization</Label><Input id="reqCompany" icon="business" value={requestCompany} onChange={(e) => { setRequestCompany(e.target.value); clear() }} placeholder="Enter company name" /></div>
                <div><Label htmlFor="reqReason">Reason for Access</Label><Textarea id="reqReason" rows={3} value={requestReason} onChange={(e) => { setRequestReason(e.target.value); clear() }} placeholder="Tell us why you need access" /></div>
                <Button type="submit" disabled={loading} size="lg" className="w-full">
                  <span className={`material-symbols-outlined text-lg ${loading ? 'animate-spin' : ''}`}>{loading ? 'sync' : 'send'}</span>
                  {loading ? 'Submitting...' : 'Submit Request'}
                </Button>
              </form>
              <p className="mt-5 text-center text-sm text-[var(--color-text-muted)]">Already have an account? <TextLink onClick={() => switchView(VIEWS.login)}>Sign In</TextLink></p>
            </div>
          )}

          {/* ── Check Status ─────────────────────────── */}
          {view === VIEWS.check && (
            <div className="bg-[var(--color-surface)] rounded-[var(--radius-xl)] border border-[var(--color-border)] shadow-[var(--shadow-md)] p-6">
              <div className="text-center mb-6">
                <div className="inline-flex items-center justify-center size-12 rounded-full bg-[var(--color-ring)]/10 text-[var(--color-ring)] mb-3">
                  <span className="material-symbols-outlined text-2xl">search</span>
                </div>
                <h2 className="text-xl font-semibold text-[var(--color-text)]">Check Request Status</h2>
                <p className="text-sm text-[var(--color-text-muted)] mt-1">Enter your User ID to check approval status</p>
              </div>
              <Alerts />
              <form onSubmit={handleCheckStatus} className="space-y-4">
                <div><Label htmlFor="checkUserId">User ID</Label><Input id="checkUserId" icon="person" value={checkUserId} onChange={(e) => { setCheckUserId(e.target.value); clear(); setCheckResult(null) }} placeholder="Enter your requested user ID" required /></div>
                <Button type="submit" disabled={loading} size="lg" className="w-full">
                  <span className={`material-symbols-outlined text-lg ${loading ? 'animate-spin' : ''}`}>{loading ? 'sync' : 'search'}</span>
                  {loading ? 'Checking...' : 'Check Status'}
                </Button>
              </form>
              {checkResult && (
                <StatusBanner type={checkResult.approved || checkResult.status === 'approved' ? 'success' : checkResult.status === 'pending' ? 'warning' : 'error'} className="mt-4">
                  <p className="font-medium">Status: {String(checkResult.status || 'unknown').toUpperCase()}</p>
                  {checkResult.message && <p className="mt-1">{checkResult.message}</p>}
                </StatusBanner>
              )}
              <p className="mt-5 text-center"><TextLink onClick={() => switchView(VIEWS.login)}>Back to Sign In</TextLink></p>
            </div>
          )}

          {/* ── Register ─────────────────────────────── */}
          {view === VIEWS.register && (
            <div className="bg-[var(--color-surface)] rounded-[var(--radius-xl)] border border-[var(--color-border)] shadow-[var(--shadow-md)] p-6">
              <div className="text-center mb-6">
                <div className="inline-flex items-center justify-center size-12 rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 mb-3">
                  <span className="material-symbols-outlined text-2xl">check_circle</span>
                </div>
                <h2 className="text-xl font-semibold text-[var(--color-text)]">Create Account</h2>
                <p className="text-sm text-green-600 dark:text-green-400 mt-1">Your request is approved! Complete your registration.</p>
              </div>
              <Alerts />
              <form onSubmit={handleRegister} className="space-y-4">
                <div><Label htmlFor="regUserId">User ID</Label><Input id="regUserId" icon="person" value={registerUserId} onChange={(e) => setRegisterUserId(e.target.value)} className="bg-gray-50 dark:bg-gray-800 cursor-not-allowed" readOnly required /></div>
                <div><Label htmlFor="regEmail">Email</Label><Input id="regEmail" icon="email" type="email" value={registerEmail} onChange={(e) => setRegisterEmail(e.target.value)} placeholder="Enter your email" /></div>
                <div><Label htmlFor="regPassword">Password</Label><Input id="regPassword" icon="lock" type="password" value={registerPassword} onChange={(e) => setRegisterPassword(e.target.value)} placeholder="Min 6 characters" required minLength={6} /></div>
                <Button type="submit" disabled={loading} size="lg" className="w-full">
                  <span className={`material-symbols-outlined text-lg ${loading ? 'animate-spin' : ''}`}>{loading ? 'sync' : 'person_add'}</span>
                  {loading ? 'Creating...' : 'Complete Registration'}
                </Button>
              </form>
              <p className="mt-5 text-center"><TextLink onClick={() => switchView(VIEWS.login)}>Back to Sign In</TextLink></p>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--color-border)] py-4 text-center shrink-0">
        <p className="text-xs text-[var(--color-text-muted)]">&copy; {new Date().getFullYear()} DawaiRx. All rights reserved.</p>
      </footer>
    </div>
  )
}
