import { createContext, useContext, useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../api/client'
import { useProfile } from './ProfileContext'

const MonthContext = createContext(null)

export function MonthProvider({ children }) {
  const { profileId } = useProfile()

  // Profile-scoped localStorage key
  const storageKey = profileId ? `vaultSelectedMonth_${profileId}` : 'vaultSelectedMonth'

  const [selectedMonth, setSelectedMonth] = useState(() => {
    return localStorage.getItem(storageKey) || null
  })

  const { data: months = [], isLoading } = useQuery({
    queryKey: ['months'],
    queryFn: () => api.get('/transactions/months/'),
    enabled: !!profileId,
  })

  // Reset selected month when profile changes
  useEffect(() => {
    if (profileId) {
      const stored = localStorage.getItem(storageKey)
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
      localStorage.setItem(storageKey, selectedMonth)
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
