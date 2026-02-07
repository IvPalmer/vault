import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import MonthlyOverview from './components/MonthlyOverview'
import Analytics from './components/Analytics'
import Settings from './components/Settings'
import './App.css'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/overview" replace />} />
        <Route path="/overview" element={<MonthlyOverview />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App
