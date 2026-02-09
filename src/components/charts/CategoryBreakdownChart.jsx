import { useMemo } from 'react'
import {
  ResponsiveContainer, PieChart, Pie, Cell, Tooltip,
} from 'recharts'
import styles from './CategoryBreakdownChart.module.css'

// Warm palette matching the app's aesthetic
const COLORS = [
  '#b86530', '#3a8a5c', '#4a7fb5', '#c87a2a', '#c0392b',
  '#8c7e74', '#6a4c93', '#2a9d8f', '#e76f51', '#264653',
]

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

function CategoryBreakdownChart({ data }) {
  const { chartData, total } = useMemo(() => {
    if (!data?.length) return { chartData: [], total: 0 }

    const sorted = [...data].sort((a, b) => b.total - a.total)
    const top8 = sorted.slice(0, 8)
    const rest = sorted.slice(8)
    const restTotal = rest.reduce((s, c) => s + c.total, 0)

    const items = top8.map((c, i) => ({
      name: c.category,
      value: c.total,
      color: COLORS[i % COLORS.length],
    }))

    if (restTotal > 0) {
      items.push({
        name: 'Outros',
        value: Math.round(restTotal * 100) / 100,
        color: COLORS[8 % COLORS.length],
      })
    }

    const total = items.reduce((s, c) => s + c.value, 0)
    return { chartData: items, total }
  }, [data])

  if (!chartData.length) return null

  return (
    <div className={styles.wrap}>
      <div className={styles.chartArea}>
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={70}
              outerRadius={120}
              dataKey="value"
              paddingAngle={2}
              stroke="none"
            >
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                fontSize: 12,
              }}
              formatter={(value) => [`R$ ${fmt(value)}`, '']}
            />
          </PieChart>
        </ResponsiveContainer>
        {/* Center label */}
        <div className={styles.centerLabel}>
          <span className={styles.centerAmount}>R$ {fmt(total)}</span>
          <span className={styles.centerSub}>total</span>
        </div>
      </div>

      {/* Custom legend */}
      <div className={styles.legend}>
        {chartData.map((entry, i) => (
          <div key={i} className={styles.legendItem}>
            <span className={styles.dot} style={{ backgroundColor: entry.color }} />
            <span className={styles.legendName}>{entry.name}</span>
            <span className={styles.legendValue}>R$ {fmt(entry.value)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default CategoryBreakdownChart
