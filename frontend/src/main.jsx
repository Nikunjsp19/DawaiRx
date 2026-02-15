import React from 'react'
import ReactDOM from 'react-dom/client'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import ErrorBoundary from './ErrorBoundary'
import App from './App'
import './index.css'

function showLoadError(err) {
  const root = document.getElementById('root')
  if (!root) return
  root.innerHTML = [
    '<div style="padding:24px;font-family:Inter,sans-serif;max-width:600px;margin:0 auto">',
    '<h2 style="color:#dc2626;margin-bottom:12px">Failed to load app</h2>',
    '<pre style="background:#fef2f2;padding:16px;border-radius:8px;overflow:auto;font-size:12px">',
    String(err?.message || err).replace(/</g, '&lt;'),
    '</pre>',
    '<p style="margin-top:16px;color:#64748b;font-size:14px">Check the browser console (F12) for more details.</p>',
    '<button onclick="location.reload()" style="margin-top:12px;padding:10px 20px;background:#3b82f6;color:white;border:none;border-radius:8px;cursor:pointer">Reload</button>',
    '</div>',
  ].join('')
}

try {
  const rootEl = document.getElementById('root')
  if (!rootEl) throw new Error('Root element #root not found')
  ReactDOM.createRoot(rootEl).render(
    <React.StrictMode>
      <ErrorBoundary>
        <ThemeProvider>
          <AuthProvider>
            <App />
          </AuthProvider>
        </ThemeProvider>
      </ErrorBoundary>
    </React.StrictMode>
  )
} catch (err) {
  console.error('App load error:', err)
  showLoadError(err)
}
