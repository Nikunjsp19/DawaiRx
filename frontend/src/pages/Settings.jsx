import { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import { useAuth } from '../context/AuthContext'
import { getCurrentUser, updateSettings } from '../api/client'
import { Button, Card, Input, Label, PageHeader, StatusBanner } from '../components/ui'

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
    let cancel = false
    getCurrentUser()
      .then(d => { if (!cancel) { setUserId(d?.user_id || authUserId || 'Unknown'); setEmail(d?.email || '') } })
      .catch(() => { if (!cancel) setUserId(authUserId || 'Unknown') })
    return () => { cancel = true }
  }, [authUserId])

  const onSubmit = async (e) => {
    e.preventDefault(); setStatus(null)
    if (newPassword && newPassword !== confirmPassword) { setStatus({ type: 'error', message: 'New passwords do not match.' }); return }
    if (newPassword && newPassword.length < 6) { setStatus({ type: 'error', message: 'New password must be at least 6 characters.' }); return }
    if (newPassword && !currentPassword) { setStatus({ type: 'error', message: 'Current password is required to change password.' }); return }
    if (!email.trim() && !newPassword) { setStatus({ type: 'error', message: 'Please enter at least one field to update.' }); return }
    setSaving(true)
    try {
      await updateSettings({ email: email.trim(), currentPassword, newPassword })
      setStatus({ type: 'success', message: 'Settings updated successfully.' })
      setCurrentPassword(''); setNewPassword(''); setConfirmPassword('')
    } catch (err) { setStatus({ type: 'error', message: err?.message || 'Failed to update settings.' }) }
    finally { setSaving(false) }
  }

  return (
    <Layout>
      <div className="max-w-lg mx-auto">
        <PageHeader title="Profile Settings" description="Manage your account information and preferences." className="text-center" />

        <Card>
          {status && <StatusBanner type={status.type} className="mb-5">{status.message}</StatusBanner>}

          {/* User ID badge */}
          <div className="mb-6 p-4 rounded-[var(--radius-md)] bg-gray-50 dark:bg-gray-800/50 border border-[var(--color-border)]">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-[var(--color-ring)] text-lg">badge</span>
              <div>
                <p className="text-xs font-medium text-[var(--color-text-muted)]">User ID</p>
                <p className="text-base font-semibold text-[var(--color-text)]">{userId}</p>
              </div>
            </div>
          </div>

          <form onSubmit={onSubmit} className="space-y-5">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" icon="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Enter your email" />
            </div>
            <div>
              <Label htmlFor="currentPassword">Current Password</Label>
              <Input id="currentPassword" type="password" icon="lock" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} placeholder="Required for password change" />
            </div>
            <div>
              <Label htmlFor="newPassword">New Password</Label>
              <Input id="newPassword" type="password" icon="key" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="Min 6 characters" />
            </div>
            <div>
              <Label htmlFor="confirmPassword">Confirm New Password</Label>
              <Input id="confirmPassword" type="password" icon="check_circle" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="Confirm new password" />
            </div>
            <Button type="submit" disabled={saving} size="lg" className="w-full">
              <span className="material-symbols-outlined text-lg">{saving ? 'sync' : 'save'}</span>
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </form>
        </Card>
      </div>
    </Layout>
  )
}
