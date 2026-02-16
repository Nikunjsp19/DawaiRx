import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('auth_token'))
  const [userId, setUserId] = useState(() => localStorage.getItem('user_id'))

  useEffect(() => {
    if (token) {
      localStorage.setItem('auth_token', token)
    } else {
      localStorage.removeItem('auth_token')
    }
  }, [token])

  useEffect(() => {
    if (userId) {
      localStorage.setItem('user_id', userId)
    } else {
      localStorage.removeItem('user_id')
    }
  }, [userId])

  const login = (t, uid) => {
    if (t) localStorage.setItem('auth_token', t)
    if (uid) localStorage.setItem('user_id', uid)
    setToken(t)
    setUserId(uid)
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_id')
    setToken(null)
    setUserId(null)
  }

  return (
    <AuthContext.Provider value={{ token, userId, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
