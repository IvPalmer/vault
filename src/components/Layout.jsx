import { NavLink, useLocation } from 'react-router-dom'
import MonthPicker from './MonthPicker'
import ProfileSwitcher from './ProfileSwitcher'
import { useProfile } from '../context/ProfileContext'
import styles from './Layout.module.css'

function Layout({ children }) {
  const { pathname } = useLocation()
  const { profileSlug } = useProfile()

  const isHome = pathname === '/home' || pathname.startsWith('/home/')
  const isSettings = pathname.endsWith('/settings')
  const isAnalytics = pathname.endsWith('/analytics')
  const showMonthPicker = !isHome && !isSettings && !isAnalytics

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <div className={styles.topRow}>
          <h1 className={styles.title}>vault</h1>
          {!isHome && <ProfileSwitcher />}
          <nav className={styles.nav}>
            <NavLink
              to="/home"
              className={({ isActive }) => isActive ? styles.activeTab : styles.navTab}
            >
              Home
            </NavLink>
            <NavLink
              to={`/${profileSlug}/overview`}
              className={({ isActive }) => isActive ? styles.activeTab : styles.navTab}
            >
              Financeiro
            </NavLink>
            <NavLink
              to={`/${profileSlug}/analytics`}
              className={({ isActive }) => isActive ? styles.activeTab : styles.navTab}
            >
              Analytics
            </NavLink>
            <NavLink
              to={`/${profileSlug}/settings`}
              className={({ isActive }) => isActive ? styles.activeTab : styles.navTab}
            >
              Config
            </NavLink>
          </nav>
        </div>
        {showMonthPicker && <MonthPicker />}
      </header>
      <main className={isHome ? styles.mainWide : (isAnalytics ? styles.mainWide : styles.main)}>
        {children}
      </main>
    </div>
  )
}

export default Layout
