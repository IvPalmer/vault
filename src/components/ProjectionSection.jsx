import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../api/client'
import {
  ResponsiveContainer, ComposedChart, Bar, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ReferenceLine,
} from 'recharts'
import Skeleton from './Skeleton'
import styles from './ProjectionSection.module.css'

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

function shortMonth(monthStr) {
  const [y, m] = monthStr.split('-')
  const names = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
  return `${names[parseInt(m) - 1]} ${y.slice(2)}`
}

function currentMonth() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

// Custom dot: red when negative, green when positive
function SaldoDot(props) {
  const { cx, cy, payload } = props
  if (cx == null || cy == null) return null
  const color = payload.saldo >= 0 ? 'var(--color-green)' : 'var(--color-red)'
  return <circle cx={cx} cy={cy} r={4} fill={color} stroke="#fff" strokeWidth={1.5} />
}

function ProjectionSection() {
  const month = currentMonth()

  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics-projection', month],
    queryFn: () => api.get(`/analytics/projection/?month_str=${month}`),
  })

  const { chartData, breakevenLabel } = useMemo(() => {
    if (!data?.months) return { chartData: [], breakevenLabel: null }
    const rows = data.months.map(row => ({
      label: shortMonth(row.month),
      month: row.month,
      entradas: row.income,
      gastos: row.fixo + row.investimento + row.installments + (row.variable || 0),
      saldo: row.cumulative,
    }))
    // Find breakeven: first month where saldo >= 0 after being negative
    let be = null
    for (let i = 1; i < rows.length; i++) {
      if (rows[i - 1].saldo < 0 && rows[i].saldo >= 0) {
        be = rows[i].label
        break
      }
    }
    return { chartData: rows, breakevenLabel: be }
  }, [data])

  if (isLoading) return (
    <section className={styles.section}>
      <h3 className={styles.title}>PROJECAO</h3>
      <Skeleton variant="chart" height="200px" />
      <Skeleton variant="row" count={6} />
    </section>
  )
  if (error) return <div className={styles.error}>Erro ao carregar projecao</div>
  if (!data) return null

  const bal = data.starting_balance
  const hasNegative = chartData.some(d => d.saldo < 0)
  // hasNegative used for zero line styling

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <h3 className={styles.title}>PROJECAO</h3>
        {breakevenLabel && (
          <span className={styles.breakevenHint}>
            positivo a partir de {breakevenLabel}
          </span>
        )}
      </div>

      <div className={styles.chartWrap}>
        <ResponsiveContainer width="100%" height={260}>
          <ComposedChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }}
              axisLine={{ stroke: 'var(--color-border)' }}
              tickLine={false}
            />
            <YAxis
              yAxisId="bars"
              tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={v => `${(v / 1000).toFixed(0)}k`}
              width={36}
            />
            <YAxis
              yAxisId="line"
              orientation="right"
              tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={v => `${(v / 1000).toFixed(0)}k`}
              width={42}
            />
            {/* Zero line — prominent when there's negative saldo */}
            <ReferenceLine
              yAxisId="line"
              y={0}
              stroke={hasNegative ? 'var(--color-red)' : 'var(--color-border)'}
              strokeWidth={hasNegative ? 1.5 : 1}
              strokeDasharray={hasNegative ? '6 3' : '3 3'}
              label={hasNegative ? { value: 'R$ 0', position: 'left', fill: 'var(--color-red)', fontSize: 10 } : undefined}
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
                const sign = name === 'saldo' && value < 0 ? '-' : ''
                return [`${sign}R$ ${fmt(value)}`, labels[name] || name]
              }}
            />
            <Legend
              verticalAlign="top"
              align="right"
              iconType="square"
              iconSize={8}
              wrapperStyle={{ fontSize: 10, paddingBottom: 4 }}
              formatter={(value) => {
                if (value === 'saldoNeg') return null
                const labels = { entradas: 'Entradas', gastos: 'Gastos', saldo: 'Saldo' }
                return labels[value] || value
              }}
              payload={[
                { value: 'entradas', type: 'square', color: 'var(--color-green)' },
                { value: 'gastos', type: 'square', color: 'var(--color-red)' },
                { value: 'saldo', type: 'line', color: 'var(--color-accent)' },
              ]}
            />
            <Bar yAxisId="bars" dataKey="entradas" fill="var(--color-green)" radius={[3, 3, 0, 0]} barSize={18} opacity={0.7} />
            <Bar yAxisId="bars" dataKey="gastos" fill="var(--color-red)" radius={[3, 3, 0, 0]} barSize={18} opacity={0.7} />
            {/* Saldo line with colored dots */}
            <Line
              yAxisId="line"
              type="monotone"
              dataKey="saldo"
              stroke="var(--color-accent)"
              strokeWidth={2}
              dot={<SaldoDot />}
              activeDot={{ r: 6 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Table */}
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>MES</th>
              <th className={styles.numCol}>ENTRADAS</th>
              <th className={styles.numCol}>FIXOS</th>
              <th className={styles.numCol}>INVEST.</th>
              <th className={styles.numCol}>CARTAO</th>
              <th className={styles.numCol}>VARIAVEL</th>
              <th className={styles.numCol}>SOBRA</th>
              <th className={styles.numCol}>SALDO</th>
            </tr>
          </thead>
          <tbody>
            {/* Starting balance row */}
            <tr className={styles.balanceRow}>
              <td className={styles.monthCell}>
                <span className={styles.balanceLabel}>Saldo em Conta</span>
              </td>
              <td colSpan={6}></td>
              <td className={`${styles.numCol} ${styles.saldoCol} ${bal >= 0 ? styles.green : styles.red}`}>
                <strong>{bal < 0 ? '-' : ''}R$ {fmt(bal)}</strong>
              </td>
            </tr>
            {data.months.map((row, i) => {
              const isBreakeven = breakevenLabel && shortMonth(row.month) === breakevenLabel
              return (
                <tr
                  key={row.month}
                  className={`${i === 0 ? styles.currentRow : ''} ${isBreakeven ? styles.breakevenRow : ''}`}
                >
                  <td className={styles.monthCell}>{shortMonth(row.month)}</td>
                  <td className={`${styles.numCol} ${styles.green}`}>
                    R$ {fmt(row.income)}
                  </td>
                  <td className={`${styles.numCol} ${styles.red}`}>
                    R$ {fmt(row.fixo)}
                  </td>
                  <td className={`${styles.numCol} ${styles.purple}`} title={
                    row.investimento === 0 && row.savings_target_amount > 0
                      ? `Sem margem para investir (meta: R$ ${fmt(row.savings_target_amount)})`
                      : row.investimento < row.savings_target_amount
                        ? `Parcial: R$ ${fmt(row.investimento)} de R$ ${fmt(row.savings_target_amount)}`
                        : `Meta ${Math.round(row.investimento / row.income * 100)}% atingida`
                  }>
                    {row.investimento === 0 && row.savings_target_amount > 0 ? (
                      <span style={{ color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>-</span>
                    ) : row.investimento < row.savings_target_amount * 0.99 ? (
                      <span style={{ opacity: 0.7 }}>R$ {fmt(row.investimento)} <span style={{ fontSize: '0.7em' }}>parcial</span></span>
                    ) : (
                      <>R$ {fmt(row.investimento)}</>
                    )}
                  </td>
                  <td className={`${styles.numCol} ${styles.orange}`}>
                    R$ {fmt(row.installments)}
                  </td>
                  <td className={`${styles.numCol} ${styles.dimmed}`}>
                    {row.variable > 0 ? `R$ ${fmt(row.variable)}` : '-'}
                  </td>
                  <td className={`${styles.numCol} ${row.net >= 0 ? styles.green : styles.red}`}>
                    {row.net < 0 ? '-' : ''}R$ {fmt(row.net)}
                  </td>
                  <td className={`${styles.numCol} ${styles.saldoCol} ${row.cumulative >= 0 ? styles.green : styles.red}`}>
                    <strong>{row.cumulative < 0 ? '-' : ''}R$ {fmt(row.cumulative)}</strong>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default ProjectionSection
