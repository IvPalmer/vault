import { NavLink, useLocation } from 'react-router-dom'
import MonthPicker from './MonthPicker'
import ProfileSwitcher from './ProfileSwitcher'
import { useProfile } from '../context/ProfileContext'
import styles from './Layout.module.css'

function Layout({ children }) {
  const { pathname } = useLocation()
  const { profileSlug } = useProfile()

  const isSettings = pathname.endsWith('/settings')
  const isAnalytics = pathname.endsWith('/analytics')
  const showMonthPicker = !isSettings && !isAnalytics

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <div className={styles.topRow}>
          <h1 className={styles.title}>vault</h1>
          <ProfileSwitcher />
          <nav className={styles.nav}>
            <NavLink
              to={`/${profileSlug}/overview`}
              className={({ isActive }) => isActive ? styles.activeTab : styles.navTab}
            >
              Mensal
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
      <main className={isAnalytics ? styles.mainWide : styles.main}>
        {children}
      </main>
    </div>
  )
}

export default Layout
