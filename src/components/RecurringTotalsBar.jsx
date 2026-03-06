import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useMonth } from '../context/MonthContext'
import api from '../api/client'
import styles from './RecurringTotalsBar.module.css'

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

function TotalRow({ label, expected, actual, paid, pending, color, isIncome, hint }) {
  return (
    <div className={styles.totalsRow}>
      <span className={styles.totalsLabel} style={{ color }}>{label}</span>
      <span className={styles.totalsExpected}>
        Esperado: <strong>R$ {fmt(expected)}</strong>{hint ? <span style={{ opacity: 0.6, marginLeft: 4 }}>{hint}</span> : null}
      </span>
      <span className={styles.totalsActual}>
        {isIncome ? 'Recebido' : 'Pago'}: <strong style={{ color: actual > 0 ? color : 'var(--color-text-secondary)' }}>R$ {fmt(actual)}</strong>
      </span>
      <span className={styles.totalsStatus}>
        {paid > 0 && <span className={styles.totalsPaid}>{paid} pago{paid > 1 ? 's' : ''}</span>}
        {pending > 0 && <span className={styles.totalsPending}>{pending} pendente{pending > 1 ? 's' : ''}</span>}
      </span>
    </div>
  )
}

function computeGroup(items) {
  let expected = 0, actual = 0, paid = 0, pending = 0
  for (const item of items) {
    if (item.is_skipped) continue
    expected += item.expected || 0
    actual += item.actual || 0
    if (item.status === 'Pago') paid++
    else if (item.status !== 'Pulado') pending++
  }
  return { expected, actual, paid, pending }
}

function RecurringTotalsBar() {
  const { selectedMonth } = useMonth()

  const { data: recData } = useQuery({
    queryKey: ['analytics-recurring', selectedMonth],
    queryFn: () => api.get(`/analytics/recurring/?month_str=${selectedMonth}`),
    enabled: !!selectedMonth,
  })

  const { data: metricasData } = useQuery({
    queryKey: ['analytics-metricas', selectedMonth],
    queryFn: () => api.get(`/analytics/metricas/?month_str=${selectedMonth}`),
    enabled: !!selectedMonth,
    staleTime: 30_000,
  })

  const totals = useMemo(() => {
    if (!recData) return null
    const income = computeGroup(recData.income || [])
    const fixo = computeGroup(recData.fixo || [])
    const invest = computeGroup(recData.investimento || [])
    return { income, fixo, invest }
  }, [recData])

  if (!totals) return null

  const { income, fixo, invest } = totals

  // Use metricas invest_expected_total (authoritative, clamped) for target
  const metricasInvest = metricasData?.invest_expected_total
  const dynamicTarget = recData?.savings_target_amount ?? 0
  const investExpected = metricasInvest != null ? metricasInvest : Math.max(invest.expected, dynamicTarget)
  const investHint = investExpected > invest.expected ? `(meta ${recData?.savings_target_pct ?? 20}%)` : null

  const cartao = metricasData?.fatura_total ?? 0
  const sobra = income.expected - fixo.expected - investExpected - cartao

  return (
    <div className={styles.totalsBar}>
      <TotalRow label="Entradas" expected={income.expected} actual={income.actual} paid={income.paid} pending={income.pending} color="var(--color-green)" isIncome />
      <TotalRow label="Fixos" expected={fixo.expected} actual={fixo.actual} paid={fixo.paid} pending={fixo.pending} color="var(--color-red)" />
      <TotalRow label="Investimentos" expected={investExpected} actual={invest.actual} paid={invest.paid} pending={invest.pending} color="#6366f1" hint={investHint} />
      <div className={styles.totalsDivider} />
      <div className={styles.totalsNet}>
        <span className={styles.totalsNetLabel}>ORÇAMENTO VARIÁVEL</span>
        <span
          className={styles.totalsNetValue}
          style={{ color: sobra >= 0 ? 'var(--color-green)' : 'var(--color-red)' }}
        >
          R$ {fmt(sobra)}
        </span>
        <span className={styles.totalsNetHint}>entradas − fixos − invest − cartão</span>
      </div>
    </div>
  )
}

export default RecurringTotalsBar
