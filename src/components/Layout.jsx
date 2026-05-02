import { useState, useRef, useEffect } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import MonthPicker from './MonthPicker'
import { useProfile } from '../context/ProfileContext'
import { useAuth } from '../context/AuthContext'
import styles from './Layout.module.css'

function UserMenu() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    if (!open) return
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  if (!user) return null

  const handleLogout = () => {
    setOpen(false)
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div ref={ref} className={styles.userMenu}>
      <button className={styles.userBtn} onClick={() => setOpen(!open)}>
        {user.picture ? (
          <img src={user.picture} alt="" className={styles.avatar} referrerPolicy="no-referrer" />
        ) : (
          <span className={styles.avatarFallback}>{user.name?.[0] || '?'}</span>
        )}
        <span className={styles.userName}>{user.name}</span>
      </button>
      {open && (
        <div className={styles.userDropdown}>
          <div className={styles.userInfo}>
            <span className={styles.userEmail}>{user.email}</span>
          </div>
          <button className={styles.logoutBtn} onClick={handleLogout}>
            Sair
          </button>
        </div>
      )}
    </div>
  )
}

function Layout({ children }) {
  const { pathname } = useLocation()
  const { profileSlug } = useProfile()

  const isHome = pathname === '/home' || pathname.startsWith('/home/')
  const isPessoal = pathname.endsWith('/pessoal')
  const isSettings = pathname.endsWith('/settings') || pathname.endsWith('/categories')
  const isAnalytics = pathname.endsWith('/analytics')
  const isSaude = pathname.endsWith('/saude')
  const showMonthPicker = !isHome && !isPessoal && !isSettings && !isAnalytics && !isSaude

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <div className={styles.topRow}>
          <h1 className={styles.title}>vault</h1>
          <nav className={styles.nav}>
            <NavLink to="/home" className={({ isActive }) => isActive ? styles.activeTab : styles.navTab}>Home</NavLink>
            <NavLink to={`/${profileSlug}/pessoal`} className={({ isActive }) => isActive ? styles.activeTab : styles.navTab}>Pessoal</NavLink>
            <NavLink to={`/${profileSlug}/overview`} className={({ isActive }) => isActive ? styles.activeTab : styles.navTab}>Financeiro</NavLink>
            <NavLink to={`/${profileSlug}/saude`} className={({ isActive }) => isActive ? styles.activeTab : styles.navTab}>Saúde</NavLink>
            <NavLink to={`/${profileSlug}/analytics`} className={({ isActive }) => isActive ? styles.activeTab : styles.navTab}>Analytics</NavLink>
            <NavLink to={`/${profileSlug}/settings`} className={({ isActive }) => isActive ? styles.activeTab : styles.navTab}>Config</NavLink>
          </nav>
          <UserMenu />
        </div>
        {showMonthPicker && <MonthPicker />}
      </header>
      <main className={(isHome || isPessoal || isAnalytics || isSaude) ? styles.mainWide : styles.main}>
        {children}
      </main>
    </div>
  )
}

export default Layout
