import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { api, setTokens, clearTokens, getAccessToken, getRefreshToken, setProfileId } from '../api/client'

const AuthContext = createContext(null)

const GOOGLE_CLIENT_ID = '322466188232-agarvcbekbncq69237rcrllq43mm7ejk.apps.googleusercontent.com'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  // On mount: try to restore session from stored tokens
  useEffect(() => {
    async function restoreSession() {
      const token = getAccessToken()
      const refresh = getRefreshToken()
      if (!token && !refresh) {
        setIsLoading(false)
        return
      }

      try {
        const profile = await api.get('/auth/me/')
        setUser(profile)
        setProfileId(profile.id)
      } catch (err) {
        clearTokens()
      }
      setIsLoading(false)
    }
    restoreSession()
  }, [])

  const login = useCallback(async (googleIdToken) => {
    setError(null)
    try {
      const data = await fetch('/api/auth/google/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: googleIdToken }),
      }).then(r => {
        if (!r.ok) return r.json().then(d => { throw new Error(d.error || 'Login failed') })
        return r.json()
      })

      setTokens(data.access, data.refresh)
      setUser(data.profile)
      setProfileId(data.profile.id)
      return data.profile
    } catch (err) {
      setError(err.message)
      throw err
    }
  }, [])

  const logout = useCallback(() => {
    clearTokens()
    setUser(null)
  }, [])

  // Direct user set for redirect flow (tokens already stored by Login page)
  const setUserDirect = useCallback((userData) => {
    setUser(userData)
  }, [])

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      isLoading,
      error,
      login,
      logout,
      setUserDirect,
      googleClientId: GOOGLE_CLIENT_ID,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
