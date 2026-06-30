import { useMemo } from 'react'
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceLine, ReferenceDot,
} from 'recharts'

const MONTH_LABELS = {
  '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
  '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
  '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez',
}

function fmt(n) {
  return Math.round(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

function CashflowDiarioChart({ data }) {
  const { chartData, valeDots, minVale, overdraft } = useMemo(() => {
    const series = data?.series || []
    if (!series.length) return { chartData: [], valeDots: [], minVale: null, overdraft: false }
    const chartData = series.map(p => ({ date: p.date, saldo: p.balance }))
    // One marker per month at its lowest point ("vale")
    const valeDots = Object.entries(data.vales || {}).map(([month, v]) => ({
      date: `${month}-${String(v.day).padStart(2, '0')}`,
      balance: v.balance,
    }))
    return {
      chartData,
      valeDots,
      minVale: data.min_vale || null,
      overdraft: !!data.overdraft,
    }
  }, [data])

  if (!chartData.length) return null

  return (
    <div>
      <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
        <div>
          <div style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>VALE MÍNIMO (PIOR DIA)</div>
          <div style={{ fontSize: 20, fontWeight: 600, color: overdraft ? 'var(--color-red)' : 'var(--color-green)' }}>
            R$ {minVale ? fmt(minVale.balance) : '—'}
          </div>
        </div>
        <div>
          <div style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>CHEQUE ESPECIAL</div>
          <div style={{ fontSize: 20, fontWeight: 600, color: overdraft ? 'var(--color-red)' : 'var(--color-green)' }}>
            {overdraft ? 'Risco' : 'Nunca'}
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={340}>
        <LineChart data={chartData} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }}
            axisLine={{ stroke: 'var(--color-border)' }}
            tickLine={false}
            interval="preserveStartEnd"
            minTickGap={40}
            tickFormatter={d => (d.endsWith('-01') ? MONTH_LABELS[d.slice(5, 7)] : '')}
          />
          <YAxis
            tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={v => `${v < 0 ? '-' : ''}${Math.abs(Math.round(v / 1000))}k`}
            width={44}
          />
          <Tooltip
            contentStyle={{
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              fontSize: 12,
            }}
            labelStyle={{ color: 'var(--color-text)', fontWeight: 600 }}
            formatter={value => [`R$ ${fmt(value)}`, 'Saldo']}
            labelFormatter={d => {
              const [, m, day] = d.split('-')
              return `${day} ${MONTH_LABELS[m]}`
            }}
          />
          <ReferenceLine
            y={0}
            stroke="var(--color-red)"
            strokeDasharray="4 4"
            label={{ value: 'cheque especial', position: 'insideTopLeft', fill: 'var(--color-red)', fontSize: 10 }}
          />
          <Line
            type="monotone"
            dataKey="saldo"
            stroke="var(--color-green)"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
          {valeDots.map(v => (
            <ReferenceDot
              key={v.date}
              x={v.date}
              y={v.balance}
              r={4}
              fill="var(--color-amber, #eda100)"
              stroke="var(--color-surface)"
              strokeWidth={1}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default CashflowDiarioChart
