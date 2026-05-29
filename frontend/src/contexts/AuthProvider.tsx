import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { fetchMeApi, loginApi, logoutApi, signupApi } from '../api/auth'
import { getStoredToken } from '../api/http'
import type { User } from '../types/auth'
import type { AuthContextValue } from '../types/context'
import { AuthContext } from './AuthContext'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    if (!getStoredToken()) {
      setUser(null)
      return
    }
    const me = await fetchMeApi()
    setUser(me)
  }, [])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        if (getStoredToken()) {
          await refresh()
        }
      } catch {
        logoutApi()
        if (!cancelled) {
          setUser(null)
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [refresh])

  const login = useCallback(async (email: string, password: string) => {
    setError(null)
    const sessionUser = await loginApi(email, password)
    setUser(sessionUser)
    return sessionUser
  }, [])

  const signup = useCallback(async (email: string, password: string, orgName: string) => {
    setError(null)
    const sessionUser = await signupApi(email, password, orgName)
    setUser(sessionUser)
    return sessionUser
  }, [])

  const logout = useCallback(() => {
    logoutApi()
    setUser(null)
    setError(null)
  }, [])

  const clearError = useCallback(() => setError(null), [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      error,
      login,
      signup,
      logout,
      clearError,
    }),
    [user, isLoading, error, login, signup, logout, clearError],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
