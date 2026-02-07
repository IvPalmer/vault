import { useRef, useEffect } from 'react'
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

function MonthPicker() {
  const { months, selectedMonth, setSelectedMonth, isLoading } = useMonth()
  const activeRef = useRef(null)
  const scrollRef = useRef(null)

  // Only show months from MIN_MONTH onwards
  const visibleMonths = months.filter(m => m >= MIN_MONTH)

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
      {visibleMonths.map((month) => (
        <button
          key={month}
          ref={month === selectedMonth ? activeRef : null}
          className={`${styles.tab} ${month === selectedMonth ? styles.active : ''}`}
          onClick={() => setSelectedMonth(month)}
        >
          {formatMonth(month)}
        </button>
      ))}
    </div>
  )
}

export default MonthPicker
