import { createContext, useContext, useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../api/client'
import { useProfile } from './ProfileContext'

const MonthContext = createContext(null)

function safeGetItem(key) {
  try { return localStorage.getItem(key) } catch { return null }
}

function safeSetItem(key, value) {
  try { localStorage.setItem(key, value) } catch { /* quota exceeded or disabled */ }
}

export function MonthProvider({ children }) {
  const { profileId } = useProfile()

  // Profile-scoped localStorage key
  const storageKey = profileId ? `vaultSelectedMonth_${profileId}` : 'vaultSelectedMonth'

  const [selectedMonth, setSelectedMonth] = useState(() => {
    return safeGetItem(storageKey) || null
  })

  const { data: months = [], isLoading } = useQuery({
    queryKey: ['months'],
    queryFn: () => api.get('/transactions/months/'),
    enabled: !!profileId,
  })

  // Reset selected month when profile changes
  useEffect(() => {
    if (profileId) {
      const stored = safeGetItem(storageKey)
      setSelectedMonth(stored || null)
    }
  }, [profileId, storageKey])

  // Set default to latest month when months load, or reset if stored month is invalid
  useEffect(() => {
    if (months.length > 0) {
      if (!selectedMonth || !months.includes(selectedMonth)) {
        setSelectedMonth(months[0]) // months are sorted descending
      }
    }
  }, [months]) // eslint-disable-line react-hooks/exhaustive-deps

  // Persist selection (profile-scoped)
  useEffect(() => {
    if (selectedMonth && profileId) {
      safeSetItem(storageKey, selectedMonth)
    }
  }, [selectedMonth, storageKey, profileId])

  return (
    <MonthContext.Provider value={{ months, selectedMonth, setSelectedMonth, isLoading }}>
      {children}
    </MonthContext.Provider>
  )
}

export function useMonth() {
  const context = useContext(MonthContext)
  if (!context) {
    throw new Error('useMonth must be used within a MonthProvider')
  }
  return context
}

export default MonthContext
