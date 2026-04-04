import { useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import styles from './Login.module.css'

export default function Login() {
  const { login, isAuthenticated, isLoading, error, googleClientId } = useAuth()
  const navigate = useNavigate()
  const btnRef = useRef(null)
  const initialized = useRef(false)

  // If already authenticated, redirect
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate('/', { replace: true })
    }
  }, [isAuthenticated, isLoading, navigate])

  const handleCredentialResponse = useCallback(async (response) => {
    try {
      const profile = await login(response.credential)
      navigate(`/${profile.slug}/overview`, { replace: true })
    } catch {
      // error is set in AuthContext
    }
  }, [login, navigate])

  // Initialize GIS
  useEffect(() => {
    if (initialized.current || !btnRef.current) return
    if (!window.google?.accounts?.id) {
      const checkInterval = setInterval(() => {
        if (window.google?.accounts?.id) {
          clearInterval(checkInterval)
          initGIS()
        }
      }, 100)
      const timeout = setTimeout(() => clearInterval(checkInterval), 10000)
      return () => { clearInterval(checkInterval); clearTimeout(timeout) }
    }
    initGIS()

    function initGIS() {
      if (initialized.current) return
      initialized.current = true
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
  }, [googleClientId, handleCredentialResponse])

  if (isLoading) return null

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1 className={styles.title}>vault</h1>
        <p className={styles.subtitle}>Finanças pessoais</p>
        <div ref={btnRef} className={styles.googleBtn} />
        {error && <p className={styles.error}>{error}</p>}
      </div>
    </div>
  )
}
