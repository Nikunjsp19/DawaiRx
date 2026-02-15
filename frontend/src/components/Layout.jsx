import { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { isAdmin } from '../api/client'

export default function Layout({ children }) {
  const { userId, token, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [showAdminLink, setShowAdminLink] = useState(false)

  useEffect(() => {
    if (!token) {
      setShowAdminLink(false)
      return
    }
    isAdmin()
      .then((data) => setShowAdminLink(Boolean(data?.is_admin)))
      .catch(() => setShowAdminLink(false))
  }, [token])

  const toggleSidebar = () => setSidebarOpen((o) => !o)
  const closeSidebar = () => setSidebarOpen(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const navClass = (path) => {
    const isActive = location.pathname === path
    return isActive
      ? 'flex items-center gap-3 px-3 py-2.5 rounded-md bg-primary/10 text-primary font-medium transition-colors text-sm'
      : 'flex items-center gap-3 px-3 py-2.5 rounded-md text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-primary transition-colors text-sm'
  }

  return (
    <div className="bg-background-light dark:bg-background-dark text-[#110c1d] dark:text-gray-100 transition-colors duration-200 min-h-screen flex font-display overflow-hidden">
      <aside
        id="sidebar"
        className={`fixed inset-y-0 left-0 z-50 w-56 bg-surface-light dark:bg-surface-dark border-r border-gray-200/50 dark:border-gray-800/50 flex flex-col transform transition-transform duration-300 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex items-center gap-3 px-4 py-4 border-b border-gray-200/50 dark:border-gray-800/50">
          <div className="flex items-center justify-center size-10 bg-primary/10 rounded-md text-primary">
            <span className="material-symbols-outlined text-lg">local_pharmacy</span>
          </div>
          <h2 className="text-base font-semibold tracking-tight text-slate-900 dark:text-white">DawaiRx</h2>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          <Link to="/" className={navClass('/')} onClick={closeSidebar}>
            <span className="material-symbols-outlined text-lg">dashboard</span>
            <span>Dashboard</span>
          </Link>
          <Link to="/new-report" className={navClass('/new-report')} onClick={closeSidebar}>
            <span className="material-symbols-outlined text-lg">add_circle</span>
            <span>New Report</span>
          </Link>
          <Link to="/settings" className={navClass('/settings')} onClick={closeSidebar}>
            <span className="material-symbols-outlined text-lg">settings</span>
            <span>Settings</span>
          </Link>
          {showAdminLink && (
            <Link to="/admin" className={navClass('/admin')} onClick={closeSidebar}>
              <span className="material-symbols-outlined text-lg">admin_panel_settings</span>
              <span>Admin Panel</span>
            </Link>
          )}
        </nav>

        <div className="px-3 py-3 border-t border-gray-200/50 dark:border-gray-800/50">
          <button
            type="button"
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-red-600 dark:hover:text-red-400 transition-colors text-sm"
          >
            <span className="material-symbols-outlined text-lg">logout</span>
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      <div
        role="presentation"
        onClick={closeSidebar}
        className={`fixed inset-0 bg-black/50 z-40 lg:hidden ${sidebarOpen ? '' : 'hidden'}`}
        aria-hidden="true"
      />

      <div className="relative z-0 flex-1 flex flex-col lg:ml-56 min-w-0">
        <header className="lg:hidden sticky top-0 z-40 w-full border-b border-gray-200 dark:border-gray-800 bg-surface-light dark:bg-surface-dark px-4 py-3">
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={toggleSidebar}
              className="flex items-center justify-center size-10 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400"
            >
              <span className="material-symbols-outlined text-2xl">menu</span>
            </button>
            <div className="flex items-center gap-2">
              <div className="flex items-center justify-center size-8 bg-primary/10 rounded-lg text-primary">
                <span className="material-symbols-outlined">local_pharmacy</span>
              </div>
              <h2 className="text-base font-bold text-[#110c1d] dark:text-white">DawaiRx</h2>
            </div>
            <div className="w-10" />
          </div>
        </header>

        <main className="flex-1 w-full px-4 sm:px-6 lg:px-8 py-4 lg:py-6 overflow-auto">
          <div key={location.pathname} className="flex flex-col min-h-0">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
