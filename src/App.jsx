import { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import MonthlyOverview from './components/MonthlyOverview'
import Analytics from './components/Analytics'
import Settings from './components/Settings'
import SetupWizard from './components/SetupWizard'
import { useProfile } from './context/ProfileContext'
import './App.css'

function App() {
  const { currentProfile, isLoading } = useProfile()
  const [showWizard, setShowWizard] = useState(false)

  // Auto-open wizard when profile hasn't completed setup
  useEffect(() => {
    if (!isLoading && currentProfile && currentProfile.setup_completed === false) {
      setShowWizard(true)
    }
  }, [currentProfile, isLoading])

  return (
    <>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/overview" replace />} />
          <Route path="/overview" element={<MonthlyOverview />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings" element={<Settings onOpenWizard={() => setShowWizard(true)} />} />
        </Routes>
      </Layout>
      {showWizard && <SetupWizard onClose={() => setShowWizard(false)} />}
    </>
  )
}

export default App
