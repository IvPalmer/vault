import { useState, useRef, useEffect } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import MonthPicker from './MonthPicker'
import ChatWidget from './widgets/ChatWidget'
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
      <button className={styles.userBtn} onClick={() => setOpen(!open)} aria-label="Menu do usuário">
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
  const [menuOpen, setMenuOpen] = useState(false)

  const isHome = pathname === '/home' || pathname.startsWith('/home/')
  const isPessoal = pathname.endsWith('/pessoal')
  const isSettings = pathname.endsWith('/settings') || pathname.endsWith('/categories')
  const isAnalytics = pathname.endsWith('/analytics')
  const isSaude = pathname.endsWith('/saude')
  const showMonthPicker = !isHome && !isPessoal && !isSettings && !isAnalytics && !isSaude

  useEffect(() => { setMenuOpen(false) }, [pathname])

  useEffect(() => {
    if (!menuOpen) return
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [menuOpen])

  const navLink = ({ isActive }) => isActive ? styles.activeTab : styles.navTab

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <div className={styles.topRow}>
          <button
            className={styles.menuToggle}
            onClick={() => setMenuOpen(true)}
            aria-label="Abrir menu"
            aria-expanded={menuOpen}
          >
            <span /><span /><span />
          </button>
          <h1 className={styles.title}>vault</h1>
          <nav className={styles.nav} aria-label="Navegação principal">
            <NavLink to="/home" className={navLink}>Home</NavLink>
            <NavLink to={`/${profileSlug}/pessoal`} className={navLink}>Pessoal</NavLink>
            <NavLink to={`/${profileSlug}/overview`} className={navLink}>Financeiro</NavLink>
            <NavLink to={`/${profileSlug}/saude`} className={navLink}>Saúde</NavLink>
            <NavLink to={`/${profileSlug}/analytics`} className={navLink}>Analytics</NavLink>
            <NavLink to={`/${profileSlug}/settings`} className={navLink}>Config</NavLink>
          </nav>
          <UserMenu />
        </div>
        {showMonthPicker && <MonthPicker />}
      </header>

      {menuOpen && (
        <>
          <button
            className={styles.mobileBackdrop}
            onClick={() => setMenuOpen(false)}
            aria-label="Fechar menu"
          />
          <nav className={styles.mobileNav} aria-label="Navegação mobile">
            <button className={styles.mobileNavClose} onClick={() => setMenuOpen(false)} aria-label="Fechar menu">×</button>
            <NavLink to="/home" className={navLink}>Home</NavLink>
            <NavLink to={`/${profileSlug}/pessoal`} className={navLink}>Pessoal</NavLink>
            <NavLink to={`/${profileSlug}/overview`} className={navLink}>Financeiro</NavLink>
            <NavLink to={`/${profileSlug}/saude`} className={navLink}>Saúde</NavLink>
            <NavLink to={`/${profileSlug}/analytics`} className={navLink}>Analytics</NavLink>
            <NavLink to={`/${profileSlug}/settings`} className={navLink}>Config</NavLink>
          </nav>
        </>
      )}

      <main className={(isHome || isPessoal || isAnalytics || isSaude) ? styles.mainWide : styles.main}>
        {children}
      </main>
      <ChatWidget />
    </div>
  )
}

export default Layout
