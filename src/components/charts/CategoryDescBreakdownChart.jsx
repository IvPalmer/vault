import { useMemo, useState } from 'react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, LabelList,
} from 'recharts'
import styles from './CategoryDescBreakdownChart.module.css'

// Sub-item palette (slightly muted, diverse)
const SUB_COLORS = [
  '#b86530', '#3a8a5c', '#4a7fb5', '#c87a2a', '#c0392b',
  '#8c7e74', '#6a4c93', '#2a9d8f', '#e76f51', '#264653',
  '#d4a373', '#588157', '#bc6c25', '#606c38', '#9b2226',
  '#b5838d', '#6d6875', '#457b9d', '#e9c46a', '#f4a261',
]

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

/* Custom tooltip that shows expected amounts for recurring items */
function CustomTooltip({ active, payload, label, recurringMap }) {
  if (!active || !payload?.length) return null

  // Sort by value descending
  const sorted = [...payload].filter(p => p.value > 0).sort((a, b) => b.value - a.value)
  const total = sorted.reduce((sum, p) => sum + (p.value || 0), 0)

  return (
    <div className={styles.tooltip}>
      <div className={styles.tooltipTitle}>{label}</div>
      <div className={styles.tooltipItems}>
        {sorted.map((entry, i) => {
          const expected = recurringMap[entry.name]
          return (
            <div key={i} className={styles.tooltipRow}>
              <span
                className={styles.tooltipDot}
                style={{ background: entry.fill || entry.color }}
              />
              <span className={styles.tooltipName}>{entry.name}</span>
              <span className={styles.tooltipValue}>
                R$ {fmt(entry.value)}
                {expected != null && expected > 0 && (
                  <span className={styles.tooltipExpected}>
                    {' '}/ R$ {fmt(expected)}
                  </span>
                )}
              </span>
            </div>
          )
        })}
      </div>
      <div className={styles.tooltipTotal}>Total: R$ {fmt(total)}</div>
    </div>
  )
}

function CategoryDescBreakdownChart({ data }) {
  const [showAll, setShowAll] = useState(false)

  const { chartData, visibleData, recurringMap } = useMemo(() => {
    if (!data?.length) return { chartData: [], visibleData: [], recurringMap: {} }

    // Build map of item name → expected amount (for recurring items)
    const recurringMap = {}
    data.forEach(cat => {
      if (cat.is_recurring) {
        cat.items.forEach(item => {
          if (item.expected != null) {
            recurringMap[item.name] = item.expected
          }
        })
      }
    })

    const chartData = data.map(cat => {
      const entry = { category: cat.category, total: cat.total, is_recurring: cat.is_recurring }
      cat.items.forEach(item => {
        entry[item.name] = item.value
      })
      return entry
    })

    const visibleData = showAll ? chartData : chartData.slice(0, 8)
    return { chartData, visibleData, recurringMap }
  }, [data, showAll])

  if (!visibleData.length) return null

  // Collect item keys for just the visible categories
  const visibleDescs = new Set()
  visibleData.forEach(row => {
    Object.keys(row).forEach(k => {
      if (k !== 'category' && k !== 'total' && k !== 'is_recurring' && row[k] > 0) {
        visibleDescs.add(k)
      }
    })
  })
  const orderedDescs = [...visibleDescs]

  const chartHeight = Math.max(420, visibleData.length * 52 + 60)

  return (
    <div>
      <ResponsiveContainer width="100%" height={chartHeight}>
        <BarChart
          data={visibleData}
          layout="vertical"
          margin={{ top: 8, right: 60, bottom: 0, left: 8 }}
          barCategoryGap="20%"
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
          <XAxis
            type="number"
            tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }}
            axisLine={{ stroke: 'var(--color-border)' }}
            tickLine={false}
            tickFormatter={v => `${(v / 1000).toFixed(0)}k`}
          />
          <YAxis
            type="category"
            dataKey="category"
            tick={({ x, y, payload }) => {
              const entry = visibleData.find(d => d.category === payload.value)
              const isRecurring = entry?.is_recurring
              return (
                <g>
                  <text
                    x={x}
                    y={y}
                    dy={4}
                    textAnchor="end"
                    fill="var(--color-text)"
                    fontSize={11}
                    fontWeight={isRecurring ? 600 : 500}
                  >
                    {payload.value}
                  </text>
                  {isRecurring && (
                    <text
                      x={x}
                      y={y + 14}
                      textAnchor="end"
                      fill="var(--color-primary)"
                      fontSize={8}
                      fontWeight={500}
                    >
                      RECORRENTE
                    </text>
                  )}
                </g>
              )
            }}
            axisLine={false}
            tickLine={false}
            width={120}
          />
          <Tooltip
            content={<CustomTooltip recurringMap={recurringMap} />}
            cursor={{ fill: 'var(--color-bg)', opacity: 0.5 }}
          />
          {orderedDescs.map((desc, i) => {
            const isLast = i === orderedDescs.length - 1
            return (
              <Bar
                key={desc}
                dataKey={desc}
                stackId="desc"
                fill={SUB_COLORS[i % SUB_COLORS.length]}
                opacity={0.85}
                barSize={24}
              >
                {isLast && (
                  <LabelList
                    dataKey="total"
                    content={({ x, y, width, height, value }) => (
                      <text
                        x={x + width + 6}
                        y={y + height / 2 + 4}
                        fill="var(--color-text-secondary)"
                        fontSize={10}
                        fontWeight={600}
                      >
                        R$ {fmt(value)}
                      </text>
                    )}
                  />
                )}
              </Bar>
            )
          })}
        </BarChart>
      </ResponsiveContainer>

      {data?.length > 8 && (
        <button
          className={styles.toggle}
          onClick={() => setShowAll(!showAll)}
          type="button"
        >
          {showAll ? 'Mostrar menos' : `Ver todas (${data.length})`}
        </button>
      )}
    </div>
  )
}

export default CategoryDescBreakdownChart
