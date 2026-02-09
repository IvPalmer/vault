import { useMemo } from 'react'
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ReferenceLine,
} from 'recharts'

const MONTH_LABELS = {
  '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
  '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
  '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez',
}

function shortMonth(monthStr) {
  const [y, m] = monthStr.split('-')
  return `${MONTH_LABELS[m]} ${y.slice(2)}`
}

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

function SpendingTrendsChart({ data }) {
  const { chartData, avgExpense } = useMemo(() => {
    if (!data?.length) return { chartData: [], avgExpense: 0 }
    const chartData = data.map(row => ({
      label: shortMonth(row.month),
      entradas: row.income,
      gastos: row.expenses,
      saldo: row.net,
    }))
    const avgExpense = data.reduce((s, r) => s + r.expenses, 0) / data.length
    return { chartData, avgExpense }
  }, [data])

  if (!chartData.length) return null

  return (
    <ResponsiveContainer width="100%" height={380}>
      <AreaChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
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
          }}
          labelStyle={{ color: 'var(--color-text)', fontWeight: 600 }}
          formatter={(value, name) => {
            const labels = { entradas: 'Entradas', gastos: 'Gastos', saldo: 'Saldo' }
            return [`R$ ${fmt(value)}`, labels[name] || name]
          }}
        />
        <Legend
          verticalAlign="top"
          align="right"
          iconType="square"
          iconSize={8}
          wrapperStyle={{ fontSize: 10, paddingBottom: 4 }}
          formatter={(value) => {
            const labels = { entradas: 'Entradas', gastos: 'Gastos', saldo: 'Saldo' }
            return labels[value] || value
          }}
        />
        <ReferenceLine
          y={avgExpense}
          stroke="var(--color-red)"
          strokeDasharray="4 4"
          strokeOpacity={0.4}
          label={{
            value: `média: ${(avgExpense / 1000).toFixed(0)}k`,
            position: 'right',
            fill: 'var(--color-text-secondary)',
            fontSize: 10,
          }}
        />
        <Area
          type="monotone"
          dataKey="entradas"
          stroke="var(--color-green)"
          fill="var(--color-green)"
          fillOpacity={0.1}
          strokeWidth={2}
        />
        <Area
          type="monotone"
          dataKey="gastos"
          stroke="var(--color-red)"
          fill="var(--color-red)"
          fillOpacity={0.1}
          strokeWidth={2}
        />
        <Area
          type="monotone"
          dataKey="saldo"
          stroke="var(--color-blue)"
          fill="none"
          strokeWidth={2}
          strokeDasharray="5 3"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export default SpendingTrendsChart
