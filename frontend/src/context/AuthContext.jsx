import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const AuthContext = createContext(null)

const API_BASE = import.meta.env.VITE_API_URL || ''
const STORAGE_KEY = 'imgopt_auth'

function getStoredTokens() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
  } catch {
    return null
  }
}

function storeTokens(tokens) {
  if (tokens) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens))
  } else {
    localStorage.removeItem(STORAGE_KEY)
  }
}

function extractErrorMessage(data, fallback) {
  if (data?.detail) return data.detail
  const firstField = Object.values(data || {})[0]
  if (Array.isArray(firstField)) return firstField[0]
  return fallback
}

export function AuthProvider({ children }) {
  const [tokens, setTokens] = useState(getStoredTokens)
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  const fetchMe = useCallback(async (accessToken) => {
    const res = await fetch(`${API_BASE}/api/auth/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
    if (!res.ok) throw new Error('unauthorized')
    return res.json()
  }, [])

  useEffect(() => {
    let cancelled = false

    async function init() {
      if (!tokens?.access) {
        setIsLoading(false)
        return
      }
      try {
        const me = await fetchMe(tokens.access)
        if (!cancelled) setUser(me)
      } catch {
        if (!cancelled) {
          setTokens(null)
          storeTokens(null)
        }
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    init()
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const login = async (email, password) => {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(extractErrorMessage(data, 'Email ou mot de passe incorrect'))
    }
    const newTokens = { access: data.access, refresh: data.refresh }
    setTokens(newTokens)
    storeTokens(newTokens)
    setUser(data.user)
    return data.user
  }

  const register = async (email, password, displayName) => {
    const res = await fetch(`${API_BASE}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, display_name: displayName }),
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(extractErrorMessage(data, 'Erreur lors de la création du compte'))
    }
    const newTokens = { access: data.access, refresh: data.refresh }
    setTokens(newTokens)
    storeTokens(newTokens)
    setUser(data.user)
    return data.user
  }

  const logout = async () => {
    if (tokens?.refresh) {
      try {
        await fetch(`${API_BASE}/api/auth/logout`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${tokens.access}`,
          },
          body: JSON.stringify({ refresh: tokens.refresh }),
        })
      } catch {
        // best effort : on déconnecte localement même si l'appel échoue
      }
    }
    setTokens(null)
    storeTokens(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated: !!user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth doit être utilisé dans un AuthProvider')
  return ctx
}
