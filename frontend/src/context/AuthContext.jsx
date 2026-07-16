import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'
import { getAttribution } from '../utils/attribution'

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
  const [tokens, setTokensState] = useState(getStoredTokens)
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  // Miroir synchrone de `tokens`, pour que authFetch lise toujours la
  // dernière valeur même au sein d'appels concurrents (le state React est
  // asynchrone, un closure capturé sur `tokens` pourrait être périmé).
  const tokensRef = useRef(tokens)
  const setTokens = useCallback((next) => {
    tokensRef.current = next
    setTokensState(next)
    storeTokens(next)
  }, [])

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
        if (!cancelled) setTokens(null)
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
    setTokens({ access: data.access, refresh: data.refresh })
    setUser(data.user)
    return data.user
  }

  const register = async (email, password, displayName) => {
    const res = await fetch(`${API_BASE}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, display_name: displayName, ...getAttribution() }),
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(extractErrorMessage(data, 'Erreur lors de la création du compte'))
    }
    setTokens({ access: data.access, refresh: data.refresh })
    setUser(data.user)
    return data.user
  }

  const logout = async () => {
    const current = tokensRef.current
    if (current?.refresh) {
      try {
        await fetch(`${API_BASE}/api/auth/logout`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${current.access}`,
          },
          body: JSON.stringify({ refresh: current.refresh }),
        })
      } catch {
        // best effort : on déconnecte localement même si l'appel échoue
      }
    }
    setTokens(null)
    setUser(null)
  }

  // Rafraîchit l'access token à partir du refresh token stocké.
  const refreshAccessToken = useCallback(async () => {
    const current = tokensRef.current
    if (!current?.refresh) return null
    const res = await fetch(`${API_BASE}/api/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: current.refresh }),
    })
    if (!res.ok) return null
    const data = await res.json()
    const next = { access: data.access, refresh: data.refresh || current.refresh }
    setTokens(next)
    return next.access
  }, [setTokens])

  // fetch() authentifié : ajoute le header Authorization, et retente une
  // fois après un rafraîchissement du token en cas de 401.
  const authFetch = useCallback(async (path, options = {}) => {
    const doFetch = (accessToken) => fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        ...(options.headers || {}),
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
    })

    let res = await doFetch(tokensRef.current?.access)
    if (res.status === 401 && tokensRef.current?.refresh) {
      const newAccess = await refreshAccessToken()
      if (newAccess) {
        res = await doFetch(newAccess)
      } else {
        setTokens(null)
        setUser(null)
      }
    }
    return res
  }, [refreshAccessToken, setTokens])

  return (
    <AuthContext.Provider value={{
      user, isLoading, isAuthenticated: !!user,
      login, register, logout, authFetch,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth doit être utilisé dans un AuthProvider')
  return ctx
}
