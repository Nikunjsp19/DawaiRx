import { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import { useAuth } from '../context/AuthContext'
import { getCurrentUser, updateSettings } from '../api/client'

export default function Settings() {
  const { userId: authUserId } = useAuth()

  const [userId, setUserId] = useState(authUserId || 'Loading...')
  const [email, setEmail] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [saving, setSaving] = useState(false)
  const [status, setStatus] = useState(null)

  useEffect(() => {
    let cancelled = false
    getCurrentUser()
      .then((data) => {
        if (cancelled) return
        setUserId(data?.user_id || authUserId || 'Unknown')
        setEmail(data?.email || '')
      })
      .catch(() => {
        if (!cancelled) setUserId(authUserId || 'Unknown')
      })
    return () => { cancelled = true }
  }, [authUserId])

  const onSubmit = async (event) => {
    event.preventDefault()
    setStatus(null)

    if (newPassword && newPassword !== confirmPassword) {
      setStatus({ type: 'error', message: 'New passwords do not match.' })
      return
    }

    if (newPassword && newPassword.length < 6) {
      setStatus({ type: 'error', message: 'New password must be at least 6 characters.' })
      return
    }

    if (newPassword && !currentPassword) {
      setStatus({ type: 'error', message: 'Current password is required to change password.' })
      return
    }

    if (!email.trim() && !newPassword) {
      setStatus({ type: 'error', message: 'Please enter at least one field to update.' })
      return
    }

    setSaving(true)
    try {
      await updateSettings({
        email: email.trim(),
        currentPassword,
        newPassword,
      })

      setStatus({ type: 'success', message: 'Settings updated successfully.' })
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      setStatus({ type: 'error', message: err?.message || 'Failed to update settings.' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <Layout>
      <div className="max-w-xl mx-auto">
        <div className="text-center mb-6">
          <h2 className="text-2xl lg:text-3xl font-bold tracking-tight text-slate-900 dark:text-white mb-2">
            Profile Settings
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Manage your account information and preferences
          </p>
        </div>

        <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-slate-200/50 dark:border-slate-700/50 overflow-hidden">
          <div className="p-6">
            {status && (
              <div className={`mb-5 p-4 rounded-lg border ${status.type === 'success' ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-900/30 text-green-800 dark:text-green-300' : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-900/30 text-red-800 dark:text-red-300'}`}>
                <p className="text-sm">{status.message}</p>
              </div>
            )}

            <div className="mb-6 p-4 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-primary text-xl">badge</span>
                <div>
                  <p className="text-sm font-medium text-slate-500 dark:text-slate-400">User ID</p>
                  <p className="text-lg font-semibold text-slate-900 dark:text-white">{userId}</p>
                </div>
              </div>
            </div>

            <form onSubmit={onSubmit} className="space-y-5">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  <span className="material-symbols-outlined text-lg align-middle mr-1">email</span>
                  Email (Optional)
                </label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:ring-2 focus:ring-primary focus:border-primary transition-colors text-sm"
                  placeholder="Enter your email"
                />
              </div>

              <div>
                <label htmlFor="currentPassword" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  <span className="material-symbols-outlined text-lg align-middle mr-1">lock</span>
                  Current Password
                </label>
                <input
                  type="password"
                  id="currentPassword"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:ring-2 focus:ring-primary focus:border-primary transition-colors text-sm"
                  placeholder="Enter current password (required for password changes)"
                />
              </div>

              <div>
                <label htmlFor="newPassword" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  <span className="material-symbols-outlined text-lg align-middle mr-1">key</span>
                  New Password (Optional)
                </label>
                <input
                  type="password"
                  id="newPassword"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:ring-2 focus:ring-primary focus:border-primary transition-colors text-sm"
                  placeholder="Enter new password (min 6 characters)"
                />
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  <span className="material-symbols-outlined text-lg align-middle mr-1">check_circle</span>
                  Confirm New Password
                </label>
                <input
                  type="password"
                  id="confirmPassword"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:ring-2 focus:ring-primary focus:border-primary transition-colors text-sm"
                  placeholder="Confirm new password"
                />
              </div>

              <button
                type="submit"
                disabled={saving}
                className="w-full flex items-center justify-center gap-2 h-10 px-4 bg-primary hover:bg-primary/90 text-white text-sm font-bold rounded-lg shadow-lg shadow-primary/30 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-60"
              >
                <span className="material-symbols-outlined">{saving ? 'sync' : 'save'}</span>
                <span>{saving ? 'Saving...' : 'Save Changes'}</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    </Layout>
  )
}
