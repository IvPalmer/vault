import { useRef, useEffect, useMemo } from 'react'
import { useMonth } from '../context/MonthContext'
import styles from './MonthPicker.module.css'

const MONTH_LABELS = {
  '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
  '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
  '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez',
}

const MIN_MONTH = '2025-12'

function formatMonth(month) {
  const [year, m] = month.split('-')
  return `${MONTH_LABELS[m]} ${year.slice(2)}`
}

function getCurrentMonth() {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  return `${y}-${m}`
}

function MonthPicker() {
  const { months, selectedMonth, setSelectedMonth, isLoading } = useMonth()
  const activeRef = useRef(null)
  const scrollRef = useRef(null)
  const currentMonth = useMemo(() => getCurrentMonth(), [])

  // Only show months from MIN_MONTH onwards, sorted ascending (left-to-right)
  const visibleMonths = useMemo(() =>
    months.filter(m => m >= MIN_MONTH).slice().sort(),
    [months]
  )

  // Scroll active tab into view
  useEffect(() => {
    if (activeRef.current && scrollRef.current) {
      activeRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
        inline: 'center',
      })
    }
  }, [selectedMonth])

  if (isLoading) {
    return <div className={styles.bar}>...</div>
  }

  return (
    <div className={styles.bar} ref={scrollRef}>
      {visibleMonths.map((month) => {
        const isFuture = month > currentMonth
        return (
          <button
            key={month}
            ref={month === selectedMonth ? activeRef : null}
            className={[
              styles.tab,
              month === selectedMonth ? styles.active : '',
              isFuture && month !== selectedMonth ? styles.future : '',
            ].filter(Boolean).join(' ')}
            onClick={() => setSelectedMonth(month)}
          >
            {formatMonth(month)}
          </button>
        )
      })}
    </div>
  )
}

export default MonthPicker
