import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useMonth } from '../context/MonthContext'
import api from '../api/client'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, Cell,
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

function ProjectionSection() {
  const { selectedMonth } = useMonth()

  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics-projection', selectedMonth],
    queryFn: () => api.get(`/analytics/projection/?month_str=${selectedMonth}&months=6`),
    enabled: !!selectedMonth,
  })

  const chartData = useMemo(() => {
    if (!data?.months) return []
    return data.months.map(row => ({
      label: shortMonth(row.month),
      entradas: row.income,
      fixos: row.fixo + row.investimento,
      parcelas: row.installments,
      variavel: row.variable,
      sobra: row.net,
    }))
  }, [data])

  if (isLoading) return (
    <section className={styles.section}>
      <h3 className={styles.title}>PROJEÇÃO</h3>
      <Skeleton variant="chart" height="200px" />
      <Skeleton variant="row" count={6} />
    </section>
  )
  if (error) return <div className={styles.error}>Erro ao carregar projeção</div>
  if (!data) return null

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <h3 className={styles.title}>PROJEÇÃO</h3>
        {data.starting_balance != null && data.starting_balance !== 0 && (
          <span className={styles.subtitle}>
            Saldo em conta: {data.starting_balance < 0 ? '−' : ''}R$ {fmt(data.starting_balance)}
          </span>
        )}
      </div>

      {/* Chart — income vs stacked expenses */}
      <div className={styles.chartWrap}>
        <ResponsiveContainer width="100%" height={220}>
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
              width={36}
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
                const labels = {
                  entradas: 'Entradas',
                  fixos: 'Fixos + Invest',
                  parcelas: 'Parcelas',
                  variavel: 'Variável',
                  sobra: 'Sobra',
                }
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
                const labels = {
                  entradas: 'Entradas',
                  fixos: 'Fixos',
                  parcelas: 'Parcelas',
                  variavel: 'Variável',
                  sobra: 'Sobra',
                }
                return labels[value] || value
              }}
            />
            {/* Income bar */}
            <Bar dataKey="entradas" fill="var(--color-green)" radius={[3, 3, 0, 0]} barSize={20} opacity={0.8} />
            {/* Stacked expenses */}
            <Bar dataKey="fixos" stackId="expenses" fill="var(--color-red)" barSize={20} opacity={0.7} />
            <Bar dataKey="parcelas" stackId="expenses" fill="var(--color-orange)" barSize={20} opacity={0.8} />
            <Bar dataKey="variavel" stackId="expenses" fill="var(--color-text-secondary)" barSize={20} opacity={0.4} />
            <Bar dataKey="sobra" stackId="expenses" radius={[3, 3, 0, 0]} barSize={20} opacity={0.6}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.sobra >= 0 ? 'var(--color-green)' : 'var(--color-red)'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Table */}
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>MÊS</th>
              <th className={styles.numCol}>ENTRADAS</th>
              <th className={styles.numCol}>FIXOS</th>
              <th className={styles.numCol}>PARCELAS</th>
              <th className={styles.numCol}>VARIÁVEL</th>
              <th className={styles.numCol}>SOBRA</th>
            </tr>
          </thead>
          <tbody>
            {data.months.map((row, i) => (
              <tr key={row.month} className={i === 0 ? styles.currentRow : ''}>
                <td className={styles.monthCell}>{shortMonth(row.month)}</td>
                <td className={`${styles.numCol} ${styles.green}`}>
                  R$ {fmt(row.income)}
                </td>
                <td className={`${styles.numCol} ${styles.red}`}>
                  R$ {fmt(row.fixo + row.investimento)}
                </td>
                <td className={`${styles.numCol} ${styles.orange}`}>
                  R$ {fmt(row.installments)}
                </td>
                <td className={`${styles.numCol} ${styles.dimmed}`}>
                  R$ {fmt(row.variable)}
                </td>
                <td className={`${styles.numCol} ${row.net >= 0 ? styles.green : styles.red}`}>
                  <strong>R$ {fmt(row.net)}</strong>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default ProjectionSection
