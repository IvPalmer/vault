import { useState, useRef, useEffect, useMemo } from 'react'
import styles from './AnalyticsFilters.module.css'

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

/** Subtract N months from a YYYY-MM string */
function subtractMonths(monthStr, n) {
  const [y, m] = monthStr.split('-').map(Number)
  const totalMonths = y * 12 + (m - 1) - n
  const newY = Math.floor(totalMonths / 12)
  const newM = (totalMonths % 12) + 1
  return `${newY}-${String(newM).padStart(2, '0')}`
}

const ACCOUNT_TABS = [
  { key: '', label: 'Todos' },
  { key: 'mastercard', label: 'Master' },
  { key: 'visa', label: 'Visa' },
  { key: 'checking', label: 'Conta' },
]

const QUICK_PERIODS = [
  { key: '3m', label: '3M', months: 3 },
  { key: '6m', label: '6M', months: 6 },
  { key: '1a', label: '1A', months: 12 },
  { key: 'all', label: 'Tudo', months: null },
]

function AnalyticsFilters({ filters, setFilters, months, availableCategories }) {
  const [catOpen, setCatOpen] = useState(false)
  const catRef = useRef(null)

  // Filter months to only show from MIN_MONTH onwards, sorted ascending
  const visibleMonths = (months || []).filter(m => m >= MIN_MONTH).sort()

  const latestMonth = visibleMonths.length ? visibleMonths[visibleMonths.length - 1] : null

  // Determine which quick period is currently active
  const activeQuickPeriod = useMemo(() => {
    if (!latestMonth) return null
    for (const qp of QUICK_PERIODS) {
      if (qp.months === null) {
        // "Tudo" = startMonth is MIN_MONTH or null/empty
        if (!filters.startMonth || filters.startMonth <= MIN_MONTH) {
          if (!filters.endMonth) return qp.key
        }
      } else {
        const target = subtractMonths(latestMonth, qp.months - 1)
        const clamped = target < MIN_MONTH ? MIN_MONTH : target
        if (filters.startMonth === clamped && !filters.endMonth) return qp.key
      }
    }
    return null
  }, [filters.startMonth, filters.endMonth, latestMonth])

  // Close category dropdown on outside click
  useEffect(() => {
    function handleClick(e) {
      if (catRef.current && !catRef.current.contains(e.target)) {
        setCatOpen(false)
      }
    }
    if (catOpen) {
      document.addEventListener('mousedown', handleClick)
      return () => document.removeEventListener('mousedown', handleClick)
    }
  }, [catOpen])

  const updateFilter = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const toggleCategory = (catId) => {
    setFilters(prev => {
      const cats = prev.categories.includes(catId)
        ? prev.categories.filter(c => c !== catId)
        : [...prev.categories, catId]
      return { ...prev, categories: cats }
    })
  }

  const applyQuickPeriod = (qp) => {
    if (!latestMonth) return
    if (qp.months === null) {
      setFilters(prev => ({ ...prev, startMonth: null, endMonth: null }))
    } else {
      const target = subtractMonths(latestMonth, qp.months - 1)
      const clamped = target < MIN_MONTH ? MIN_MONTH : target
      setFilters(prev => ({ ...prev, startMonth: clamped, endMonth: null }))
    }
  }

  const clearAll = () => {
    setFilters({
      startMonth: null,
      endMonth: null,
      categories: [],
      accounts: '',
    })
  }

  const hasFilters = filters.startMonth || filters.endMonth || filters.categories.length > 0 || filters.accounts

  return (
    <div className={styles.bar}>
      {/* Period: De / Até */}
      <div className={styles.group}>
        <label className={styles.label}>De</label>
        <select
          className={styles.select}
          value={filters.startMonth || ''}
          onChange={e => updateFilter('startMonth', e.target.value || null)}
        >
          <option value="">Início</option>
          {visibleMonths.map(m => (
            <option key={m} value={m}>{formatMonth(m)}</option>
          ))}
        </select>
      </div>

      <div className={styles.group}>
        <label className={styles.label}>Até</label>
        <select
          className={styles.select}
          value={filters.endMonth || ''}
          onChange={e => updateFilter('endMonth', e.target.value || null)}
        >
          <option value="">Atual</option>
          {visibleMonths.map(m => (
            <option key={m} value={m}>{formatMonth(m)}</option>
          ))}
        </select>
      </div>

      {/* Quick period buttons */}
      <div className={styles.group}>
        <label className={styles.label}>Período</label>
        <div className={styles.pills}>
          {QUICK_PERIODS.map(qp => (
            <button
              key={qp.key}
              className={`${styles.pill} ${activeQuickPeriod === qp.key ? styles.pillActive : ''}`}
              onClick={() => applyQuickPeriod(qp)}
              type="button"
            >
              {qp.label}
            </button>
          ))}
        </div>
      </div>

      {/* Categories multi-select dropdown */}
      <div className={styles.group} ref={catRef}>
        <label className={styles.label}>Categorias</label>
        <button
          className={styles.select}
          onClick={() => setCatOpen(!catOpen)}
          type="button"
        >
          {filters.categories.length === 0
            ? 'Todas'
            : `${filters.categories.length} selecionada${filters.categories.length > 1 ? 's' : ''}`
          }
          <span className={styles.chevron}>{catOpen ? '\u25B2' : '\u25BC'}</span>
        </button>
        {catOpen && (
          <div className={styles.dropdown}>
            {(availableCategories || []).map(cat => (
              <label key={cat.id} className={styles.checkItem}>
                <input
                  type="checkbox"
                  checked={filters.categories.includes(cat.id)}
                  onChange={() => toggleCategory(cat.id)}
                />
                <span>{cat.name}</span>
              </label>
            ))}
            {filters.categories.length > 0 && (
              <button
                className={styles.clearCats}
                onClick={() => updateFilter('categories', [])}
                type="button"
              >
                Limpar seleção
              </button>
            )}
          </div>
        )}
      </div>

      {/* Account/Card pill toggle */}
      <div className={styles.group}>
        <label className={styles.label}>Conta</label>
        <div className={styles.pills}>
          {ACCOUNT_TABS.map(tab => (
            <button
              key={tab.key}
              className={`${styles.pill} ${filters.accounts === tab.key ? styles.pillActive : ''}`}
              onClick={() => updateFilter('accounts', tab.key)}
              type="button"
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Clear all */}
      {hasFilters && (
        <button className={styles.clearAll} onClick={clearAll} type="button">
          Limpar
        </button>
      )}
    </div>
  )
}

export default AnalyticsFilters
