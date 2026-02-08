import { useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useMonth } from '../context/MonthContext'
import api from '../api/client'
import styles from './SmartCategorizeBar.module.css'

/**
 * SmartCategorizeBar — Runs the smart categorization engine for the selected month.
 * Shows a button + result feedback. Runs multiple passes (flywheel) until convergence.
 */
function SmartCategorizeBar() {
  const { selectedMonth } = useMonth()
  const queryClient = useQueryClient()
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)

  const handleCategorize = useCallback(async () => {
    if (!selectedMonth || running) return
    setRunning(true)
    setResult(null)

    try {
      let totalCategorized = 0
      let passes = 0
      let lastCategorized = -1

      // Flywheel: run passes until convergence
      while (passes < 10) {
        passes++
        const res = await api.post('/analytics/smart-categorize/', {
          month_str: selectedMonth,
          dry_run: false,
        })
        const newCat = res.categorized || 0
        totalCategorized += newCat

        // Converged when no new categorizations
        if (newCat === 0 || newCat === lastCategorized) break
        lastCategorized = newCat
      }

      // Also run a global pass (no month filter) to catch cross-month learning
      const globalRes = await api.post('/analytics/smart-categorize/', {
        dry_run: false,
      })
      totalCategorized += (globalRes.categorized || 0)

      setResult({
        success: true,
        categorized: totalCategorized,
        remaining: globalRes.remaining || 0,
        passes,
      })

      // Invalidate all analytics queries to refresh the data
      queryClient.invalidateQueries({ queryKey: ['analytics-checking'] })
      queryClient.invalidateQueries({ queryKey: ['analytics-cards'] })
      queryClient.invalidateQueries({ queryKey: ['analytics-metricas'] })
      queryClient.invalidateQueries({ queryKey: ['analytics-variable'] })
      queryClient.invalidateQueries({ queryKey: ['analytics-installments'] })
      queryClient.invalidateQueries({ queryKey: ['analytics-orcamento'] })
    } catch (err) {
      setResult({ success: false, error: err.message || 'Erro na categorização' })
    } finally {
      setRunning(false)
    }
  }, [selectedMonth, running, queryClient])

  return (
    <div className={styles.bar}>
      <button
        className={`${styles.button} ${running ? styles.running : ''}`}
        onClick={handleCategorize}
        disabled={running}
      >
        {running ? (
          <>
            <span className={styles.spinner} />
            Categorizando...
          </>
        ) : (
          <>
            <span className={styles.icon}>⚡</span>
            Smart Categorize
          </>
        )}
      </button>

      {result && (
        <span className={`${styles.feedback} ${result.success ? styles.success : styles.error}`}>
          {result.success
            ? `${result.categorized} categorizadas (${result.remaining} restantes)`
            : result.error
          }
        </span>
      )}
    </div>
  )
}

export default SmartCategorizeBar
