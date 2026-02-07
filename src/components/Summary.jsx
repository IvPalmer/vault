import { useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useMonth } from '../context/MonthContext'
import useInvalidateAnalytics from '../hooks/useInvalidateAnalytics'
import api from '../api/client'
import MetricCard from './MetricCard'
import InlineEdit from './InlineEdit'
import Skeleton from './Skeleton'
import styles from './Summary.module.css'

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

function Summary() {
  const { selectedMonth } = useMonth()
  const { invalidateSummary, invalidateProjection } = useInvalidateAnalytics()

  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics-summary', selectedMonth],
    queryFn: () => api.get(`/analytics/summary/?month_str=${selectedMonth}`),
    enabled: !!selectedMonth,
  })

  // Fetch CC transactions to compute bill total
  const { data: cardsData } = useQuery({
    queryKey: ['analytics-cards', selectedMonth],
    queryFn: () => api.get(`/analytics/cards/?month_str=${selectedMonth}`),
    enabled: !!selectedMonth,
  })

  const handleSaveBalance = useCallback(async (newBalance) => {
    try {
      await api.post('/analytics/balance/', {
        month_str: selectedMonth,
        balance: newBalance,
      })
      invalidateSummary()
      invalidateProjection()
    } catch (err) {
      console.error('Failed to save balance:', err)
    }
  }, [selectedMonth, invalidateSummary, invalidateProjection])

  if (isLoading) return (
    <div className={styles.section}>
      <h3 className={styles.title}>RESUMO</h3>
      <Skeleton variant="card" count={6} />
    </div>
  )
  if (error) return <div className={styles.error}>Erro ao carregar resumo</div>
  if (!data) return null

  // Compute CC bill total from all transactions on the invoice
  const ccTotal = cardsData?.transactions
    ? Math.abs(cardsData.transactions.reduce((s, t) => s + t.amount, 0))
    : 0

  return (
    <div className={styles.section}>
      <h3 className={styles.title}>RESUMO</h3>
      <div className={styles.grid}>
        <MetricCard
          label="ENTRADAS"
          value={`R$ ${fmt(data.entradas)}`}
          color="var(--color-green)"
        />
        <MetricCard
          label="FATURA CC"
          value={`R$ ${fmt(ccTotal)}`}
          color="var(--color-red)"
        />
        <MetricCard
          label="PARCELAS"
          value={`R$ ${fmt(data.parcelas)}`}
          color="var(--color-orange)"
        />
        <MetricCard
          label="GASTOS FIXOS"
          value={`R$ ${fmt(data.gastos_fixos)}`}
          color="var(--color-red)"
        />
        <MetricCard
          label="GASTOS VARIÁVEIS"
          value={`R$ ${fmt(data.gastos_variaveis)}`}
          color="var(--color-red)"
        />
        <MetricCard
          label="SALDO"
          value={`R$ ${fmt(data.saldo)}`}
          color={data.saldo >= 0 ? 'var(--color-green)' : 'var(--color-red)'}
        />
      </div>

      {/* Balance input */}
      <div className={styles.balanceRow}>
        <span className={styles.balanceLabel}>SALDO EM CONTA</span>
        <InlineEdit
          value={data.balance_override}
          onSave={handleSaveBalance}
          prefix="R$"
          color={
            data.balance_override != null
              ? data.balance_override >= 0
                ? 'var(--color-green)'
                : 'var(--color-red)'
              : undefined
          }
          placeholder="clique para informar"
        />
      </div>
    </div>
  )
}

export default Summary
