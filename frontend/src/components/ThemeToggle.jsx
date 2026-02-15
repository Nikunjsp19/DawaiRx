import { useTheme } from '../context/ThemeContext'

export default function ThemeToggle({ isDark, onToggle }) {
  const { theme, toggleTheme } = useTheme()
  const dark = isDark ?? theme === 'dark'
  return (
    <button
      type="button"
      onClick={onToggle ?? toggleTheme}
      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-sm"
      aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      <span className="material-symbols-outlined text-lg">{dark ? 'light_mode' : 'dark_mode'}</span>
      <span>Theme</span>
    </button>
  )
}
