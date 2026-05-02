import { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './components/Home'
import MonthlyOverview from './components/MonthlyOverview'
import Analytics from './components/Analytics'
import Settings from './components/Settings'
import PersonalOrganizer from './components/PersonalOrganizer'
import Saude from './components/Saude'
import CategoryManager from './components/CategoryManager'
import SetupWizard from './components/SetupWizard'
import ErrorBoundary from './components/ErrorBoundary'
import Login from './pages/Login'
import { useProfile } from './context/ProfileContext'
import { useAuth } from './context/AuthContext'
import './App.css'

function AuthGuard({ children }) {
  const { isAuthenticated, isLoading } = useAuth()
  if (isLoading) return null
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return children
}

function App() {
  const { currentProfile, isLoading: profileLoading, profileSlug } = useProfile()
  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const [showWizard, setShowWizard] = useState(false)
  const [wizardEditMode, setWizardEditMode] = useState(false)

  useEffect(() => {
    if (!profileLoading && currentProfile && currentProfile.setup_completed === false) {
      setWizardEditMode(false)
      setShowWizard(true)
    }
  }, [currentProfile, profileLoading])

  const handleOpenWizardFromSettings = () => {
    setWizardEditMode(true)
    setShowWizard(true)
  }

  const handleCloseWizard = () => {
    setShowWizard(false)
    setWizardEditMode(false)
  }

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/*" element={
        <AuthGuard>
          <Layout>
            <Routes>
              <Route path="/home" element={<ErrorBoundary fallbackMessage="Erro ao carregar Home"><Home /></ErrorBoundary>} />
              <Route path="/:profileSlug/pessoal" element={<ErrorBoundary fallbackMessage="Erro ao carregar Pessoal"><PersonalOrganizer /></ErrorBoundary>} />
              <Route path="/:profileSlug/overview" element={<ErrorBoundary fallbackMessage="Erro ao carregar Visão Mensal"><MonthlyOverview /></ErrorBoundary>} />
              <Route path="/:profileSlug/saude" element={<ErrorBoundary fallbackMessage="Erro ao carregar Saúde"><Saude /></ErrorBoundary>} />
              <Route path="/:profileSlug/analytics" element={<ErrorBoundary fallbackMessage="Erro ao carregar Analytics"><Analytics /></ErrorBoundary>} />
              <Route path="/:profileSlug/settings" element={<ErrorBoundary fallbackMessage="Erro ao carregar Configurações"><Settings onOpenWizard={handleOpenWizardFromSettings} /></ErrorBoundary>} />
              <Route path="/:profileSlug/categories" element={<ErrorBoundary fallbackMessage="Erro ao carregar Categorias"><CategoryManager /></ErrorBoundary>} />
              <Route path="/overview" element={profileSlug ? <Navigate to={`/${profileSlug}/overview`} replace /> : null} />
              <Route path="/saude" element={profileSlug ? <Navigate to={`/${profileSlug}/saude`} replace /> : null} />
              <Route path="/analytics" element={profileSlug ? <Navigate to={`/${profileSlug}/analytics`} replace /> : null} />
              <Route path="/settings" element={profileSlug ? <Navigate to={`/${profileSlug}/settings`} replace /> : null} />
              <Route path="/" element={<Navigate to="/home" replace />} />
            </Routes>
          </Layout>
          {showWizard && <SetupWizard onClose={handleCloseWizard} editMode={wizardEditMode} />}
        </AuthGuard>
      } />
    </Routes>
  )
}

export default App
