import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const AuthContext = createContext(null)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [user, setUser] = useState(null)
  const [authError, setAuthError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadSession() {
      try {
        const response = await fetch(`${API_BASE_URL}/auth/session/`, {
          credentials: 'include',
        })
        const data = await response.json()

        if (cancelled) {
          return
        }

        setIsAuthenticated(Boolean(data.authenticated))
        setUser(data.user || null)
      } catch {
        if (!cancelled) {
          setIsAuthenticated(false)
          setUser(null)
          setAuthError('Unable to reach the backend authentication service.')
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    const params = new URLSearchParams(window.location.search)
    const authStatus = params.get('auth')
    const reason = params.get('reason')

    if (authStatus === 'error') {
      setAuthError(reason ? `GitHub login failed: ${reason}` : 'GitHub login failed.')
    } else if (authStatus === 'success') {
      setAuthError('')
    }

    if (authStatus) {
      params.delete('auth')
      params.delete('reason')
      const nextSearch = params.toString()
      const nextUrl = `${window.location.pathname}${nextSearch ? `?${nextSearch}` : ''}${window.location.hash}`
      window.history.replaceState({}, '', nextUrl)
    }

    loadSession()

    return () => {
      cancelled = true
    }
  }, [])

  function login() {
    const loginUrl = new URL(`${API_BASE_URL}/auth/github/login/`)
    loginUrl.searchParams.set('origin', window.location.origin)
    window.location.assign(loginUrl.toString())
  }

  async function logout() {
    try {
      await fetch(`${API_BASE_URL}/auth/logout/`, {
        method: 'POST',
        credentials: 'include',
      })
    } finally {
      setAuthError('')
      setIsAuthenticated(false)
      setUser(null)
    }
  }

  const value = useMemo(() => {
    return { authError, isAuthenticated, isLoading, login, logout, user }
  }, [authError, isAuthenticated, isLoading, user])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return ctx
}
