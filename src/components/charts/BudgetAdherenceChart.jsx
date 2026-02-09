import { useMemo } from 'react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Cell, LabelList,
} from 'recharts'

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

function BudgetAdherenceChart({ data }) {
  const chartData = useMemo(() => {
    if (!data?.length) return []
    return data
      .filter(row => row.budgeted > 0)
      .map(row => ({
        name: row.category,
        orcamento: row.budgeted,
        real: row.actual,
        pct: row.pct,
        over: row.actual > row.budgeted,
      }))
  }, [data])

  if (!chartData.length) return null

  return (
    <ResponsiveContainer width="100%" height={Math.max(200, chartData.length * 48 + 40)}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ top: 8, right: 50, bottom: 0, left: 0 }}
        barGap={2}
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
          dataKey="name"
          tick={{ fill: 'var(--color-text)', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={90}
        />
        <Tooltip
          contentStyle={{
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            fontSize: 12,
          }}
          formatter={(value, name) => {
            const labels = { orcamento: 'Orçamento', real: 'Real' }
            return [`R$ ${fmt(value)}`, labels[name] || name]
          }}
        />
        <Bar dataKey="orcamento" fill="var(--color-text-secondary)" opacity={0.2} barSize={14} radius={[0, 3, 3, 0]} />
        <Bar dataKey="real" barSize={14} radius={[0, 3, 3, 0]}>
          {chartData.map((entry, i) => (
            <Cell
              key={i}
              fill={entry.over ? 'var(--color-red)' : 'var(--color-green)'}
              opacity={0.8}
            />
          ))}
          <LabelList
            dataKey="pct"
            position="right"
            formatter={(v) => `${Math.round(v)}%`}
            style={{ fill: 'var(--color-text-secondary)', fontSize: 10, fontWeight: 600 }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export default BudgetAdherenceChart
