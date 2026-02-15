import React from 'react'

export default class ErrorBoundary extends React.Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('App error:', error, info)
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 24,
          fontFamily: 'Inter, sans-serif',
          backgroundColor: '#f8fafc',
          color: '#1e293b',
        }}>
          <h1 style={{ fontSize: 20, marginBottom: 12 }}>Something went wrong</h1>
          <pre style={{
            maxWidth: 600,
            padding: 16,
            backgroundColor: '#fee2e2',
            borderRadius: 8,
            fontSize: 12,
            overflow: 'auto',
            textAlign: 'left',
          }}>
            {this.state.error?.message || String(this.state.error)}
          </pre>
          <p style={{ marginTop: 16, fontSize: 14, color: '#64748b' }}>
            Check the browser console and ensure the backend is running on port 8080.
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            style={{
              marginTop: 16,
              padding: '10px 20px',
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: 8,
              cursor: 'pointer',
              fontSize: 14,
            }}
          >
            Reload page
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
