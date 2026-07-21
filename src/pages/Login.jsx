import { useEffect, useRef, useCallback, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { setTokens, setProfileId } from '../api/client'
import styles from './Login.module.css'

export default function Login() {
  const { login, isAuthenticated, isLoading, error, googleClientId, setUserDirect } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const btnRef = useRef(null)
  const initialized = useRef(false)
  const [gisLoaded, setGisLoaded] = useState(false)
  const [redirectError, setRedirectError] = useState(null)

  // Handle redirect callback: tokens in URL fragment (#auth=...)
  useEffect(() => {
    const hash = window.location.hash
    if (hash.startsWith('#auth=')) {
      const params = new URLSearchParams(hash.slice(6)) // skip "#auth="
      const access = params.get('access')
      const refresh = params.get('refresh')
      if (access && refresh) {
        setTokens(access, refresh)
        const profileId = params.get('profile_id')
        if (profileId) setProfileId(profileId)
        // Set user in AuthContext
        setUserDirect({
          id: profileId,
          name: params.get('profile_name'),
          slug: params.get('profile_slug'),
          email: params.get('email'),
          picture: params.get('picture') || null,
        })
        // Clean URL and navigate
        window.history.replaceState(null, '', '/login')
        navigate(`/${params.get('profile_slug')}/overview`, { replace: true })
        return
      }
    }
    // Handle error from redirect flow
    const searchParams = new URLSearchParams(location.search)
    const err = searchParams.get('error')
    if (err) setRedirectError(err)
  }, [])

  // If already authenticated, redirect
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate('/', { replace: true })
    }
  }, [isAuthenticated, isLoading, navigate])

  // Silent SSO: if we landed here (e.g. JWT expirado) but the oauth2-proxy
  // cookie is still valid, exchange it for a JWT and skip the Google button.
  // Skipped after an explicit logout. While pending, render nothing so the
  // Google button doesn't flash before the auto-login resolves.
  const ssoTried = useRef(false)
  const [ssoPending, setSsoPending] = useState(
    () => localStorage.getItem('vaultSsoLoggedOut') !== '1',
  )
  useEffect(() => {
    if (isLoading || isAuthenticated || ssoTried.current) return
    if (localStorage.getItem('vaultSsoLoggedOut') === '1') { setSsoPending(false); return }
    ssoTried.current = true
    fetch('/api/auth/sso/', { method: 'POST' })
      .then(r => (r.ok ? r.json() : null))
      .then(data => {
        if (!data?.access) { setSsoPending(false); return }
        setTokens(data.access, data.refresh)
        setProfileId(data.profile.id)
        setUserDirect(data.profile)
        navigate(`/${data.profile.slug}/overview`, { replace: true })
      })
      .catch(() => setSsoPending(false))
  }, [isLoading, isAuthenticated, navigate, setUserDirect])

  const handleCredentialResponse = useCallback(async (response) => {
    try {
      const profile = await login(response.credential)
      navigate(`/${profile.slug}/overview`, { replace: true })
    } catch {
      // error is set in AuthContext
    }
  }, [login, navigate])

  // Initialize GIS — only after the silent SSO attempt settled (the button
  // div only exists then; the ref would be null during the pending render).
  useEffect(() => {
    if (ssoPending || initialized.current || !btnRef.current) return
    if (!window.google?.accounts?.id) {
      const checkInterval = setInterval(() => {
        if (window.google?.accounts?.id) {
          clearInterval(checkInterval)
          initGIS()
        }
      }, 100)
      const timeout = setTimeout(() => clearInterval(checkInterval), 5000)
      return () => { clearInterval(checkInterval); clearTimeout(timeout) }
    }
    initGIS()

    function initGIS() {
      if (initialized.current) return
      initialized.current = true
      setGisLoaded(true)
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: handleCredentialResponse,
      })
      window.google.accounts.id.renderButton(btnRef.current, {
        theme: 'outline',
        size: 'large',
        text: 'signin_with',
        shape: 'rectangular',
        width: 300,
      })
    }
  }, [ssoPending, googleClientId, handleCredentialResponse])

  // Fallback: redirect to Google OAuth via backend when GIS doesn't load
  const handleManualLogin = () => {
    localStorage.removeItem('vaultSsoLoggedOut')
    window.location.href = `/api/auth/google-start/?next=${encodeURIComponent(window.location.origin + '/login')}`
  }

  if (isLoading || ssoPending) return null

  const displayError = error || redirectError

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1 className={styles.title}>vault</h1>
        <div ref={btnRef} className={styles.googleBtn} />
        {!gisLoaded && (
          <button className={styles.fallbackBtn} onClick={handleManualLogin}>
            Entrar com Google
          </button>
        )}
        {displayError && <p className={styles.error}>{displayError}</p>}
      </div>
    </div>
  )
}
