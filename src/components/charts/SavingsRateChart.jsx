import { useMemo } from 'react'
import {
  ResponsiveContainer, ComposedChart, Bar, Line, XAxis, YAxis,
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

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius-md)',
      padding: '8px 12px',
      fontSize: 12,
    }}>
      <div style={{ fontWeight: 600, color: 'var(--color-text)', marginBottom: 4 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, display: 'flex', gap: 8, justifyContent: 'space-between' }}>
          <span>{p.name}</span>
          <span style={{ fontWeight: 600 }}>
            {p.dataKey === 'rate' ? `${p.value.toFixed(1)}%` : `R$ ${fmt(p.value)}`}
          </span>
        </div>
      ))}
    </div>
  )
}

function SavingsRateChart({ data }) {
  const { chartData, avgRate } = useMemo(() => {
    if (!data?.length) return { chartData: [], avgRate: 0 }
    const chartData = data.map(row => ({
      label: shortMonth(row.month),
      renda: row.income,
      gastos: row.expenses,
      rate: row.rate,
    }))
    const avgRate = data.reduce((s, r) => s + r.rate, 0) / data.length
    return { chartData, avgRate }
  }, [data])

  if (!chartData.length) return null

  return (
    <ResponsiveContainer width="100%" height={380}>
      <ComposedChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }}
          axisLine={{ stroke: 'var(--color-border)' }}
          tickLine={false}
        />
        <YAxis
          yAxisId="money"
          tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={v => `${(v / 1000).toFixed(0)}k`}
          width={40}
        />
        <YAxis
          yAxisId="pct"
          orientation="right"
          tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={v => `${v}%`}
          width={40}
          domain={[0, 100]}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          verticalAlign="top"
          align="right"
          iconType="square"
          iconSize={8}
          wrapperStyle={{ fontSize: 10, paddingBottom: 4 }}
        />
        <Bar yAxisId="money" dataKey="renda" name="Renda" fill="var(--color-green)" opacity={0.7} barSize={20} />
        <Bar yAxisId="money" dataKey="gastos" name="Gastos" fill="var(--color-red)" opacity={0.7} barSize={20} />
        <Line
          yAxisId="pct"
          type="monotone"
          dataKey="rate"
          name="Poupança %"
          stroke="var(--color-accent)"
          strokeWidth={2.5}
          dot={{ r: 4, fill: 'var(--color-accent)' }}
        />
        <ReferenceLine
          yAxisId="pct"
          y={avgRate}
          stroke="var(--color-accent)"
          strokeDasharray="4 4"
          strokeOpacity={0.5}
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

export default SavingsRateChart
