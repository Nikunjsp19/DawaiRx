import { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { isAdmin } from '../api/client'

const NAV_ITEMS = [
  { path: '/',           icon: 'dashboard',             label: 'Dashboard' },
  { path: '/new-report', icon: 'note_add',              label: 'New Report' },
  { path: '/settings',   icon: 'settings',              label: 'Settings' },
]

export default function Layout({ children, fullWidth = false }) {
  const { userId, token, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [showAdminLink, setShowAdminLink] = useState(false)

  useEffect(() => {
    if (!token) { setShowAdminLink(false); return }
    isAdmin().then((d) => setShowAdminLink(Boolean(d?.is_admin))).catch(() => setShowAdminLink(false))
  }, [token])

  const closeSidebar = () => setSidebarOpen(false)
  const handleLogout = () => { logout(); navigate('/login') }

  const navClass = (path) => {
    const active = location.pathname === path || (path !== '/' && location.pathname.startsWith(path))
    return [
      'flex items-center gap-3 px-3 py-2 rounded-[var(--radius-md)] text-sm font-medium transition-default',
      active
        ? 'bg-[var(--color-ring)]/10 text-[var(--color-ring)]'
        : 'text-[var(--color-text-secondary)] hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-[var(--color-text)]',
    ].join(' ')
  }

  return (
    <div className="h-screen flex overflow-hidden bg-[var(--color-bg)] text-[var(--color-text)] font-display">
      {/* ── Sidebar ────────────────────────────────────────── */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-56 bg-[var(--color-surface)] border-r border-[var(--color-border)] flex flex-col transform transition-transform duration-200 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Brand */}
        <div className="flex items-center gap-3 px-4 h-14 border-b border-[var(--color-border)] shrink-0">
          <div className="flex items-center justify-center size-8 bg-[var(--color-ring)]/10 rounded-[var(--radius-sm)] text-[var(--color-ring)]">
            <span className="material-symbols-outlined text-lg">local_pharmacy</span>
          </div>
          <span className="text-base font-semibold tracking-tight">DawaiRx</span>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto">
          {NAV_ITEMS.map((item) => (
            <Link key={item.path} to={item.path} className={navClass(item.path)} onClick={closeSidebar}>
              <span className="material-symbols-outlined text-lg">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
          {showAdminLink && (
            <Link to="/admin" className={navClass('/admin')} onClick={closeSidebar}>
              <span className="material-symbols-outlined text-lg">admin_panel_settings</span>
              <span>Admin</span>
            </Link>
          )}
        </nav>

        {/* Footer actions */}
        <div className="px-3 py-3 border-t border-[var(--color-border)] space-y-0.5 shrink-0">
          <button
            type="button"
            onClick={toggleTheme}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-[var(--radius-md)] text-sm text-[var(--color-text-secondary)] hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-[var(--color-text)] transition-default"
          >
            <span className="material-symbols-outlined text-lg">{theme === 'dark' ? 'light_mode' : 'dark_mode'}</span>
            <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
          </button>
          <button
            type="button"
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-[var(--radius-md)] text-sm text-[var(--color-text-secondary)] hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400 transition-default"
          >
            <span className="material-symbols-outlined text-lg">logout</span>
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* ── Overlay (mobile) ──────────────────────────────── */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/40 z-40 lg:hidden" onClick={closeSidebar} aria-hidden="true" />
      )}

      {/* ── Main area ─────────────────────────────────────── */}
      <div className="relative z-0 flex-1 flex flex-col lg:ml-56 min-w-0 min-h-0">
        {/* Mobile header */}
        <header className="lg:hidden sticky top-0 z-40 h-14 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 flex items-center justify-between shrink-0">
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="flex items-center justify-center size-9 rounded-[var(--radius-md)] hover:bg-gray-100 dark:hover:bg-gray-800 text-[var(--color-text-secondary)] transition-default"
            aria-label="Open menu"
          >
            <span className="material-symbols-outlined text-xl">menu</span>
          </button>
          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center size-7 bg-[var(--color-ring)]/10 rounded-[var(--radius-sm)] text-[var(--color-ring)]">
              <span className="material-symbols-outlined text-base">local_pharmacy</span>
            </div>
            <span className="text-sm font-bold">DawaiRx</span>
          </div>
          <div className="w-9" />
        </header>

        <main className="flex-1 w-full px-4 sm:px-5 lg:px-6 py-3 lg:py-4 flex flex-col min-h-0 overflow-hidden">
          <div className={fullWidth ? 'w-full flex-1 flex flex-col min-h-0 overflow-auto' : 'max-w-[1280px] mx-auto w-full flex-1 flex flex-col min-h-0 overflow-auto'}>
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
