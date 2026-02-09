import { useMemo } from 'react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend,
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

function ExpenseCompositionChart({ data }) {
  const chartData = useMemo(() => {
    if (!data?.length) return []
    return data.map(row => ({
      label: shortMonth(row.month),
      fixo: Math.abs(row.fixo || 0),
      parcelas: Math.abs(row.parcelas || 0),
      variavel: Math.abs(row.variavel || 0),
      investimento: Math.abs(row.investimento || 0),
    }))
  }, [data])

  if (!chartData.length) return null

  return (
    <ResponsiveContainer width="100%" height={350}>
      <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
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
            const labels = { fixo: 'Fixos', parcelas: 'Parcelas', variavel: 'Variável', investimento: 'Investimento' }
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
            const labels = { fixo: 'Fixos', parcelas: 'Parcelas', variavel: 'Variável', investimento: 'Investimento' }
            return labels[value] || value
          }}
        />
        <Bar dataKey="fixo" stackId="comp" fill="var(--color-red)" opacity={0.8} barSize={28} />
        <Bar dataKey="parcelas" stackId="comp" fill="var(--color-orange)" opacity={0.8} barSize={28} />
        <Bar dataKey="variavel" stackId="comp" fill="var(--color-blue)" opacity={0.8} barSize={28} />
        <Bar dataKey="investimento" stackId="comp" fill="var(--color-green)" opacity={0.7} barSize={28} radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export default ExpenseCompositionChart
