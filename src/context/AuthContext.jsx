import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { api, setTokens, clearTokens, getAccessToken, getRefreshToken, setProfileId } from '../api/client'

const AuthContext = createContext(null)

const GOOGLE_CLIENT_ID = '322466188232-agarvcbekbncq69237rcrllq43mm7ejk.apps.googleusercontent.com'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  // On mount: restore from stored tokens; failing that, try the silent SSO
  // exchange — behind the oauth2-proxy gate the browser already did Google
  // SSO, so /api/auth/sso/ turns that identity into a JWT pair without a
  // second login screen. Outside the proxy (local dev) it 403s and the
  // normal Login page shows. Skipped after an explicit logout (see logout),
  // otherwise "sair" would re-entrar sozinho.
  useEffect(() => {
    async function restoreSession() {
      const token = getAccessToken()
      const refresh = getRefreshToken()
      if (token || refresh) {
        try {
          const profile = await api.get('/auth/me/')
          setUser(profile)
          setProfileId(profile.id)
          setIsLoading(false)
          return
        } catch (err) {
          clearTokens()
        }
      }

      if (localStorage.getItem('vaultSsoLoggedOut') !== '1') {
        try {
          const resp = await fetch('/api/auth/sso/', { method: 'POST' })
          if (resp.ok) {
            const data = await resp.json()
            setTokens(data.access, data.refresh)
            setUser(data.profile)
            setProfileId(data.profile.id)
          }
        } catch {
          // sem proxy (dev local) ou sem identidade — cai no Login normal
        }
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
      localStorage.removeItem('vaultSsoLoggedOut')
      return data.profile
    } catch (err) {
      setError(err.message)
      throw err
    }
  }, [])

  const logout = useCallback(() => {
    clearTokens()
    setUser(null)
    // Suppress the silent SSO exchange until the user logs in on purpose,
    // and best-effort kill the oauth2-proxy cookie too — otherwise logout
    // would auto re-authenticate on the next page load.
    localStorage.setItem('vaultSsoLoggedOut', '1')
    fetch('/oauth2/sign_out', { redirect: 'manual' }).catch(() => {})
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
