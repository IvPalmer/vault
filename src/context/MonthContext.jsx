import { createContext, useContext, useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../api/client'

const MonthContext = createContext(null)

export function MonthProvider({ children }) {
  const [selectedMonth, setSelectedMonth] = useState(() => {
    return localStorage.getItem('vaultSelectedMonth') || null
  })

  const { data: months = [], isLoading } = useQuery({
    queryKey: ['months'],
    queryFn: () => api.get('/transactions/months/'),
  })

  // Set default to latest month when months load, or reset if stored month is invalid
  useEffect(() => {
    if (months.length > 0) {
      if (!selectedMonth || !months.includes(selectedMonth)) {
        setSelectedMonth(months[0]) // months are sorted descending
      }
    }
  }, [months]) // eslint-disable-line react-hooks/exhaustive-deps

  // Persist selection
  useEffect(() => {
    if (selectedMonth) {
      localStorage.setItem('vaultSelectedMonth', selectedMonth)
    }
  }, [selectedMonth])

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
