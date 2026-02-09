import { NavLink, useLocation } from 'react-router-dom'
import MonthPicker from './MonthPicker'
import styles from './Layout.module.css'

function Layout({ children }) {
  const { pathname } = useLocation()
  const showMonthPicker = pathname !== '/settings' && pathname !== '/analytics'
  const isAnalytics = pathname === '/analytics'

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <div className={styles.topRow}>
          <h1 className={styles.title}>vault</h1>
          <nav className={styles.nav}>
            <NavLink
              to="/overview"
              className={({ isActive }) => isActive ? styles.activeTab : styles.navTab}
            >
              Mensal
            </NavLink>
            <NavLink
              to="/analytics"
              className={({ isActive }) => isActive ? styles.activeTab : styles.navTab}
            >
              Analytics
            </NavLink>
            <NavLink
              to="/settings"
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
