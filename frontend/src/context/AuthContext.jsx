import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../lib/api'
import { clearAuthSession, getStoredUser, getToken, setAuthSession } from '../lib/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getStoredUser())
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = getToken()
    if (!token) {
      setLoading(false)
      return
    }
    apiFetch('/auth/me')
      .then(async (res) => {
        if (!res.ok) throw new Error('Session expired')
        const data = await res.json()
        setUser(data.user)
      })
      .catch(() => {
        clearAuthSession()
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const login = async ({ email, password }) => {
    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data?.detail || 'Login failed')
    }
    setAuthSession(data.access_token, data.user)
    setUser(data.user)
    return data.user
  }

  const signup = async ({ name, email, password }) => {
    const res = await fetch('/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password }),
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data?.detail || 'Signup failed')
    }
    setAuthSession(data.access_token, data.user)
    setUser(data.user)
    return data.user
  }

  const logout = () => {
    clearAuthSession()
    setUser(null)
  }

  const value = useMemo(() => ({
    user,
    loading,
    isAuthenticated: Boolean(user),
    login,
    signup,
    logout,
  }), [user, loading])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
