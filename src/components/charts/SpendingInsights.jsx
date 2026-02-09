import { useQuery } from '@tanstack/react-query'
import api from '../../api/client'
import styles from './SpendingInsights.module.css'

const ICON_MAP = {
  trending_up: '\u2191',
  trending_down: '\u2193',
  category: '\u25A0',
  savings: '\u2605',
  budget: '\u26A0',
  timeline: '\u2192',
  new: '\u2726',
}

const TYPE_STYLES = {
  positive: { bg: 'var(--color-green-bg, #f0fdf4)', border: 'var(--color-green)', color: 'var(--color-green)' },
  warning: { bg: 'var(--color-orange-bg, #fff7ed)', border: 'var(--color-orange)', color: 'var(--color-orange)' },
  danger: { bg: 'var(--color-red-bg, #fef2f2)', border: 'var(--color-red)', color: 'var(--color-red)' },
  info: { bg: 'var(--color-accent-bg, #fef3e2)', border: 'var(--color-accent)', color: 'var(--color-accent)' },
}

function SpendingInsights() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['spending-insights'],
    queryFn: () => api.get('/analytics/insights/'),
    staleTime: 5 * 60 * 1000,
  })

  if (isLoading) return null
  if (error || !data?.insights?.length) return null

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>INSIGHTS</h3>
        <span className={styles.subtitle}>
          {data.summary} ({data.months_analyzed} meses analisados)
        </span>
      </div>
      <div className={styles.grid}>
        {data.insights.map((insight, i) => {
          const typeStyle = TYPE_STYLES[insight.type] || TYPE_STYLES.info
          return (
            <div
              key={i}
              className={styles.card}
              style={{
                backgroundColor: typeStyle.bg,
                borderLeftColor: typeStyle.border,
              }}
            >
              <div className={styles.cardHeader}>
                <span className={styles.icon} style={{ color: typeStyle.color }}>
                  {ICON_MAP[insight.icon] || '\u2022'}
                </span>
                <span className={styles.cardTitle} style={{ color: typeStyle.color }}>
                  {insight.title}
                </span>
              </div>
              <p className={styles.message}>{insight.message}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default SpendingInsights
