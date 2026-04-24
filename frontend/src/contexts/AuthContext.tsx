import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import type { ReactNode } from 'react'
import type { User } from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

interface AuthContextValue {
  user: User | null
  loading: boolean
  logout: () => Promise<void>
  refresh: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchMe = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/auth/me`, { credentials: 'include' })
      if (res.ok) {
        setUser(await res.json())
      } else if (res.status === 401) {
        // Try to refresh the session silently
        const refreshRes = await fetch(`${API_URL}/auth/refresh`, {
          method: 'POST',
          credentials: 'include',
        })
        if (refreshRes.ok) {
          setUser(await refreshRes.json())
        } else {
          setUser(null)
        }
      }
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchMe()
  }, [fetchMe])

  const logout = useCallback(async () => {
    await fetch(`${API_URL}/auth/logout`, { method: 'POST', credentials: 'include' })
    setUser(null)
  }, [])

  const refresh = useCallback(async () => {
    await fetchMe()
  }, [fetchMe])

  return (
    <AuthContext.Provider value={{ user, loading, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
