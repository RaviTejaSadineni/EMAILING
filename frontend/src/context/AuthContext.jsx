import { createContext, useCallback, useEffect, useMemo, useState } from 'react'
import { getMe, login as loginApi, refreshToken, register as registerApi } from '../api/auth'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const setTokens = (tokens) => {
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
  }

  const clearTokens = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  const bootstrap = useCallback(async () => {
    const access = localStorage.getItem('access_token')
    const refresh = localStorage.getItem('refresh_token')
    if (!access || !refresh) {
      setLoading(false)
      return
    }

    try {
      const me = await getMe()
      setUser(me)
    } catch {
      try {
        const refreshed = await refreshToken(refresh)
        setTokens(refreshed)
        const me = await getMe()
        setUser(me)
      } catch {
        clearTokens()
        setUser(null)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    bootstrap()
  }, [bootstrap])

  const login = async (payload) => {
    const tokens = await loginApi(payload)
    setTokens(tokens)
    const me = await getMe()
    setUser(me)
  }

  const register = async (payload) => {
    await registerApi(payload)
    await login({ email: payload.email, password: payload.password })
  }

  const logout = () => {
    clearTokens()
    setUser(null)
  }

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
    }),
    [user, loading],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
