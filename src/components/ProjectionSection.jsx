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

// Colored dot: red below zero, green at/above zero
function SaldoDot({ cx, cy, payload }) {
  if (cx == null || cy == null) return null
  const color = payload.saldo >= 0 ? 'var(--color-green)' : 'var(--color-red)'
  return <circle cx={cx} cy={cy} r={5} fill={color} stroke="#fff" strokeWidth={2} />
}

function ProjectionSection() {
  const month = currentMonth()

  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics-projection', month],
    queryFn: () => api.get(`/analytics/projection/?month_str=${month}`),
  })

  const { chartData, breakevenLabel, breakevenIdx } = useMemo(() => {
    if (!data?.months) return { chartData: [], breakevenLabel: null, breakevenIdx: -1, historyCount: 0 }
    // Merge history (past months) + current/future into one timeline
    const allMonths = [...(data.history || []), ...data.months]
    const historyCount = (data.history || []).length
    const rows = allMonths.map(row => ({
      label: shortMonth(row.month),
      month: row.month,
      entradas: row.income,
      gastos: row.fixo + row.investimento + row.installments,
      saldo: row.cumulative,
      isHistory: !!row.is_history,
    }))
    // Find breakeven: first month where saldo >= 0 after being negative
    let be = null
    let beIdx = -1
    for (let i = 1; i < rows.length; i++) {
      if (rows[i - 1].saldo < 0 && rows[i].saldo >= 0) {
        be = rows[i].label
        beIdx = i
        break
      }
    }
    return { chartData: rows, breakevenLabel: be, breakevenIdx: beIdx, historyCount }
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
          <ComposedChart data={chartData} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }}
              axisLine={{ stroke: 'var(--color-border)' }}
              tickLine={false}
            />
            {/* Left axis: bars (income/expenses) */}
            <YAxis
              yAxisId="bars"
              tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={v => `${(v / 1000).toFixed(0)}k`}
              width={36}
            />
            {/* Right axis: saldo line */}
            <YAxis
              yAxisId="saldo"
              orientation="right"
              tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={v => `${v < 0 ? '-' : ''}${Math.abs(v / 1000).toFixed(0)}k`}
              width={42}
            />
            {/* Zero reference line on saldo axis */}
            {hasNegative && (
              <ReferenceLine
                yAxisId="saldo"
                y={0}
                stroke="var(--color-red)"
                strokeWidth={1}
                strokeDasharray="6 3"
                strokeOpacity={0.6}
              />
            )}
            {/* Breakeven month marker */}
            {breakevenLabel && (
              <ReferenceLine
                yAxisId="bars"
                x={breakevenLabel}
                stroke="var(--color-green)"
                strokeWidth={1.5}
                strokeDasharray="4 3"
                label={{
                  value: `${breakevenLabel}`,
                  position: 'top',
                  fill: 'var(--color-green)',
                  fontSize: 10,
                  fontWeight: 600,
                }}
              />
            )}
            <Tooltip
              contentStyle={{
                background: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                fontSize: 12,
              }}
              labelStyle={{ color: 'var(--color-text)', fontWeight: 600 }}
              formatter={(value, name) => {
                const labels = { entradas: 'Entradas', gastos: 'Comprometidos', saldo: 'Saldo' }
                const sign = value < 0 ? '-' : ''
                return [`${sign}R$ ${fmt(value)}`, labels[name] || name]
              }}
            />
            <Legend
              verticalAlign="top"
              align="right"
              iconSize={8}
              wrapperStyle={{ fontSize: 10, paddingBottom: 4 }}
              payload={[
                { value: 'Entradas', type: 'square', color: 'var(--color-green)' },
                { value: 'Comprometidos', type: 'square', color: 'var(--color-red)' },
                { value: 'Saldo', type: 'line', color: 'var(--color-accent)' },
              ]}
            />
            <Bar yAxisId="bars" dataKey="entradas" fill="var(--color-green)" radius={[3, 3, 0, 0]} barSize={18} opacity={0.75} />
            <Bar yAxisId="bars" dataKey="gastos" fill="var(--color-red)" radius={[3, 3, 0, 0]} barSize={18} opacity={0.75} />
            <Line
              yAxisId="saldo"
              type="monotone"
              dataKey="saldo"
              stroke="var(--color-accent)"
              strokeWidth={2.5}
              dot={<SaldoDot />}
              activeDot={{ r: 7 }}
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
              <th className={styles.numCol} title="Gasto variável / orçamento disponível">VAR. / ORC.</th>
              <th className={styles.numCol} title="Saldo projetado ao fim do mês">SALDO</th>
            </tr>
          </thead>
          <tbody>
            {/* History rows (closed months) */}
            {(data.history || []).map((row) => (
              <tr key={row.month} style={{ opacity: 0.6 }}>
                <td className={styles.monthCell}>{shortMonth(row.month)}</td>
                <td className={`${styles.numCol} ${styles.green}`}>R$ {fmt(row.income)}</td>
                <td className={`${styles.numCol} ${styles.red}`}>R$ {fmt(row.fixo)}</td>
                <td className={`${styles.numCol} ${styles.purple}`}>R$ {fmt(row.investimento)}</td>
                <td className={`${styles.numCol} ${styles.orange}`}>R$ {fmt(row.installments)}</td>
                <td className={`${styles.numCol}`}>
                  <span style={{ color: 'var(--color-red)' }}>R$ {fmt(row.variable)}</span>
                  <span style={{ color: 'var(--color-text-secondary)', opacity: 0.5 }}> / </span>
                  <span style={{ color: row.budget < 0 ? 'var(--color-red)' : 'var(--color-green)' }}>
                    {row.budget < 0 ? `${'\u2212'}R$ ${fmt(row.budget)}` : `R$ ${fmt(row.budget)}`}
                  </span>
                </td>
                <td className={`${styles.numCol} ${styles.saldoCol} ${row.cumulative >= 0 ? styles.green : styles.red}`}>
                  <strong>{row.cumulative < 0 ? '-' : ''}R$ {fmt(row.cumulative)}</strong>
                </td>
              </tr>
            ))}
            {/* Divider between history and projection */}
            {(data.history || []).length > 0 && (
              <tr className={styles.balanceRow}>
                <td className={styles.monthCell}>
                  <span className={styles.balanceLabel}>Saldo Anterior</span>
                </td>
                <td colSpan={5}></td>
                <td className={`${styles.numCol} ${styles.saldoCol} ${bal >= 0 ? styles.green : styles.red}`}>
                  <strong>{bal < 0 ? '-' : ''}R$ {fmt(bal)}</strong>
                </td>
              </tr>
            )}
            {/* Current + future months */}
            {data.months.map((row, i) => {
              const isCurrent = i === 0
              const isBreakeven = breakevenLabel && shortMonth(row.month) === breakevenLabel
              return (
                <tr
                  key={row.month}
                  className={`${isCurrent ? styles.currentRow : ''} ${isBreakeven ? styles.breakevenRow : ''}`}
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
                  <td className={`${styles.numCol}`}>
                    {isCurrent ? (
                      <>
                        <span style={{ color: 'var(--color-red)' }}>R$ {fmt(row.variable)}</span>
                        <span style={{ color: 'var(--color-text-secondary)', opacity: 0.5 }}> / </span>
                        <span style={{ color: row.budget < 0 ? 'var(--color-red)' : 'var(--color-green)' }}>
                          {row.budget < 0 ? `${'\u2212'}R$ ${fmt(row.budget)}` : `R$ ${fmt(row.budget)}`}
                        </span>
                      </>
                    ) : (
                      <>
                        <span style={{ color: 'var(--color-text-secondary)' }}>{'\u2014'}</span>
                        <span style={{ color: 'var(--color-text-secondary)', opacity: 0.5 }}> / </span>
                        <span style={{ color: row.budget < 0 ? 'var(--color-red)' : 'var(--color-green)' }}>
                          {row.budget < 0 ? `${'\u2212'}R$ ${fmt(row.budget)}` : `R$ ${fmt(row.budget)}`}
                        </span>
                      </>
                    )}
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
