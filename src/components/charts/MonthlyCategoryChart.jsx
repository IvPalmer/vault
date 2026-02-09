import { useMemo } from 'react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, Cell, LabelList,
} from 'recharts'

const MONTH_LABELS = {
  '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
  '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
  '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez',
}

// Extended palette for many categories
const COLORS = [
  '#b86530', '#3a8a5c', '#4a7fb5', '#c87a2a', '#c0392b',
  '#8c7e74', '#6a4c93', '#2a9d8f', '#e76f51', '#264653',
  '#d4a373', '#588157', '#bc6c25', '#606c38', '#9b2226',
]

function shortMonth(monthStr) {
  const [y, m] = monthStr.split('-')
  return `${MONTH_LABELS[m]} ${y.slice(2)}`
}

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

function CustomTotalLabel({ x, y, width, value }) {
  if (!value) return null
  return (
    <text
      x={x + width / 2}
      y={y - 6}
      textAnchor="middle"
      fill="var(--color-text-secondary)"
      fontSize={10}
      fontWeight={600}
    >
      R$ {fmt(value)}
    </text>
  )
}

function MonthlyCategoryChart({ data }) {
  const { chartData, categories } = useMemo(() => {
    if (!data?.categories?.length || !data?.data?.length) {
      return { chartData: [], categories: [] }
    }
    const chartData = data.data.map(row => ({
      ...row,
      label: shortMonth(row.month),
    }))
    return { chartData, categories: data.categories }
  }, [data])

  if (!chartData.length) return null

  // Calculate chart height based on data to give enough room
  const chartHeight = Math.max(420, 380)

  return (
    <ResponsiveContainer width="100%" height={chartHeight}>
      <BarChart data={chartData} margin={{ top: 24, right: 8, bottom: 0, left: 0 }}>
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
          tickFormatter={v => `${(v / 1000).toFixed(0)}k`}
          width={40}
        />
        <Tooltip
          contentStyle={{
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            fontSize: 12,
            maxHeight: 300,
            overflowY: 'auto',
          }}
          labelStyle={{ color: 'var(--color-text)', fontWeight: 600 }}
          formatter={(value, name) => [`R$ ${fmt(value)}`, name]}
          itemSorter={(item) => -(item.value || 0)}
        />
        <Legend
          verticalAlign="top"
          align="right"
          iconType="square"
          iconSize={8}
          wrapperStyle={{ fontSize: 9, paddingBottom: 4, maxWidth: '60%' }}
        />
        {categories.map((cat, i) => {
          const isLast = i === categories.length - 1
          return (
            <Bar
              key={cat}
              dataKey={cat}
              stackId="monthly"
              fill={COLORS[i % COLORS.length]}
              opacity={0.85}
              barSize={36}
              radius={isLast ? [3, 3, 0, 0] : undefined}
            >
              {isLast && (
                <LabelList
                  dataKey="total"
                  content={<CustomTotalLabel />}
                />
              )}
            </Bar>
          )
        })}
      </BarChart>
    </ResponsiveContainer>
  )
}

export default MonthlyCategoryChart
