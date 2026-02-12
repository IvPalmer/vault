import { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './components/Home'
import MonthlyOverview from './components/MonthlyOverview'
import Analytics from './components/Analytics'
import Settings from './components/Settings'
import SetupWizard from './components/SetupWizard'
import { useProfile } from './context/ProfileContext'
import './App.css'

function App() {
  const { currentProfile, isLoading, profileSlug } = useProfile()
  const [showWizard, setShowWizard] = useState(false)
  const [wizardEditMode, setWizardEditMode] = useState(false)

  // Auto-open wizard when profile hasn't completed setup
  useEffect(() => {
    if (!isLoading && currentProfile && currentProfile.setup_completed === false) {
      setWizardEditMode(false)
      setShowWizard(true)
    }
  }, [currentProfile, isLoading])

  const handleOpenWizardFromSettings = () => {
    setWizardEditMode(true)
    setShowWizard(true)
  }

  const handleCloseWizard = () => {
    setShowWizard(false)
    setWizardEditMode(false)
  }

  return (
    <>
      <Layout>
        <Routes>
          {/* Shared home (no profile slug) */}
          <Route path="/home" element={<Home />} />

          {/* Profile-scoped routes */}
          <Route path="/:profileSlug/overview" element={<MonthlyOverview />} />
          <Route path="/:profileSlug/analytics" element={<Analytics />} />
          <Route path="/:profileSlug/settings" element={<Settings onOpenWizard={handleOpenWizardFromSettings} />} />

          {/* Legacy routes — redirect to profile-scoped versions */}
          <Route path="/overview" element={profileSlug ? <Navigate to={`/${profileSlug}/overview`} replace /> : null} />
          <Route path="/analytics" element={profileSlug ? <Navigate to={`/${profileSlug}/analytics`} replace /> : null} />
          <Route path="/settings" element={profileSlug ? <Navigate to={`/${profileSlug}/settings`} replace /> : null} />

          {/* Root redirect — now goes to /home */}
          <Route path="/" element={<Navigate to="/home" replace />} />
        </Routes>
      </Layout>
      {showWizard && (
        <SetupWizard
          onClose={handleCloseWizard}
          editMode={wizardEditMode}
        />
      )}
    </>
  )
}

export default App
