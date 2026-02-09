import { useState, useMemo } from 'react'
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend,
} from 'recharts'
import styles from './CategoryTrendsChart.module.css'

const MONTH_LABELS = {
  '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
  '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
  '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez',
}

const COLORS = [
  '#b86530', '#3a8a5c', '#4a7fb5', '#c87a2a', '#c0392b',
  '#8c7e74', '#6a4c93', '#2a9d8f', '#e76f51', '#264653',
]

function shortMonth(monthStr) {
  const [y, m] = monthStr.split('-')
  return `${MONTH_LABELS[m]} ${y.slice(2)}`
}

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

function CategoryTrendsChart({ data }) {
  const [mode, setMode] = useState('value') // 'value' or 'pct'

  const { chartData, categories } = useMemo(() => {
    if (!data?.categories?.length || !data?.data?.length) {
      return { chartData: [], categories: [] }
    }
    const chartData = data.data.map(row => {
      const entry = { label: shortMonth(row.month) }
      data.categories.forEach(cat => {
        entry[cat] = Math.abs(row[cat] || 0)
      })
      return entry
    })
    return { chartData, categories: data.categories }
  }, [data])

  if (!chartData.length) return null

  return (
    <div>
      <div className={styles.header}>
        <div className={styles.toggle}>
          <button
            className={`${styles.btn} ${mode === 'value' ? styles.btnActive : ''}`}
            onClick={() => setMode('value')}
            type="button"
          >
            R$
          </button>
          <button
            className={`${styles.btn} ${mode === 'pct' ? styles.btnActive : ''}`}
            onClick={() => setMode('pct')}
            type="button"
          >
            %
          </button>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={380}>
        <AreaChart
          data={chartData}
          margin={{ top: 8, right: 8, bottom: 0, left: 0 }}
          stackOffset={mode === 'pct' ? 'expand' : 'none'}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }}
            axisLine={{ stroke: 'var(--color-border)' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={v => mode === 'pct' ? `${(v * 100).toFixed(0)}%` : `${(v / 1000).toFixed(0)}k`}
            width={40}
          />
          <Tooltip
            contentStyle={{
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              fontSize: 12,
            }}
            labelStyle={{ color: 'var(--color-text)', fontWeight: 600 }}
            formatter={(value, name) => [`R$ ${fmt(value)}`, name]}
          />
          <Legend
            verticalAlign="top"
            align="right"
            iconType="square"
            iconSize={8}
            wrapperStyle={{ fontSize: 10, paddingBottom: 4 }}
          />
          {categories.map((cat, i) => (
            <Area
              key={cat}
              type="monotone"
              dataKey={cat}
              stackId="cats"
              stroke={COLORS[i % COLORS.length]}
              fill={COLORS[i % COLORS.length]}
              fillOpacity={0.6}
              strokeWidth={1}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export default CategoryTrendsChart
