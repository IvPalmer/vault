import { useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useMonth } from '../context/MonthContext'
import useInvalidateAnalytics from '../hooks/useInvalidateAnalytics'
import api from '../api/client'
import MetricCard from './MetricCard'
import InlineEdit from './InlineEdit'
import Skeleton from './Skeleton'
import styles from './MetricasSection.module.css'

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

const SAUDE_COLORS = {
  good: 'var(--color-green)',
  warning: 'var(--color-orange)',
  danger: 'var(--color-red)',
}

function MetricasSection() {
  const { selectedMonth } = useMonth()
  const { invalidateMetricas, invalidateProjection } = useInvalidateAnalytics()

  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics-metricas', selectedMonth],
    queryFn: () => api.get(`/analytics/metricas/?month_str=${selectedMonth}`),
    enabled: !!selectedMonth,
  })

  const handleSaveBalance = useCallback(async (newBalance) => {
    try {
      await api.post('/analytics/balance/', {
        month_str: selectedMonth,
        balance: newBalance,
      })
      invalidateMetricas()
      invalidateProjection()
    } catch (err) {
      console.error('Failed to save balance:', err)
    }
  }, [selectedMonth, invalidateMetricas, invalidateProjection])

  if (isLoading) return (
    <div className={styles.section}>
      <div className={styles.balanceRow}>
        <span className={styles.balanceLabel}>SALDO EM CONTA</span>
      </div>
      <h3 className={styles.title}>METRICAS</h3>
      <Skeleton variant="card" count={15} />
    </div>
  )
  if (error) return <div className={styles.error}>Erro ao carregar metricas</div>
  if (!data) return null

  const fechamentoValue = data.is_current_month
    ? `${data.dias_fechamento} dias`
    : '\u2014'
  const fechamentoSub = data.is_current_month
    ? 'ate o fechamento'
    : 'mes encerrado'

  return (
    <div className={styles.section}>
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

      <h3 className={styles.title}>METRICAS</h3>

      <div className={styles.grid}>
        <MetricCard
          label="ENTRADAS ATUAIS"
          value={`R$ ${fmt(data.entradas_atuais)}`}
          subtitle="recebido no mes"
          color="var(--color-green)"
        />
        <MetricCard
          label="ENTRADAS PROJETADAS"
          value={`R$ ${fmt(data.entradas_projetadas)}`}
          subtitle="receita esperada"
          color="#6ee7b7"
        />
        <MetricCard
          label="GASTOS ATUAIS"
          value={`R$ ${fmt(data.gastos_atuais)}`}
          subtitle="gasto total no mes"
          color="var(--color-red)"
        />
        <MetricCard
          label="GASTOS PROJETADOS"
          value={`R$ ${fmt(data.gastos_projetados)}`}
          subtitle="despesa esperada"
          color="#fca5a5"
        />
        <MetricCard
          label="GASTOS FIXOS"
          value={`R$ ${fmt(data.gastos_fixos)}`}
          subtitle="fixos pagos"
          color="var(--color-red)"
        />
        <MetricCard
          label="GASTOS VARIAVEIS"
          value={`R$ ${fmt(data.gastos_variaveis)}`}
          subtitle="variaveis gastos"
          color="var(--color-orange)"
        />
        <MetricCard
          label="FATURA MASTER"
          value={`R$ ${fmt(data.fatura_master)}`}
          subtitle="mastercard total"
          color="var(--color-red)"
        />
        <MetricCard
          label="FATURA VISA"
          value={`R$ ${fmt(data.fatura_visa)}`}
          subtitle="visa total"
          color="var(--color-red)"
        />
        <MetricCard
          label="PARCELAS"
          value={`R$ ${fmt(data.parcelas)}`}
          subtitle="parcelamentos"
          color="var(--color-orange)"
        />
        <MetricCard
          label="A ENTRAR"
          value={`R$ ${fmt(data.a_entrar)}`}
          subtitle={data.a_entrar > 0 ? 'receita pendente' : 'tudo recebido'}
          color="var(--color-green)"
        />
        <MetricCard
          label="A PAGAR"
          value={`R$ ${fmt(data.a_pagar)}`}
          subtitle={data.a_pagar > 0 ? 'despesa pendente' : 'tudo pago'}
          color={data.a_pagar > 0 ? 'var(--color-red)' : 'var(--color-green)'}
        />
        <MetricCard
          label="SALDO PROJETADO"
          value={`R$ ${fmt(data.saldo_projetado)}`}
          subtitle={data.balance_override != null ? 'baseado no saldo' : 'calculado'}
          color={data.saldo_projetado >= 0 ? 'var(--color-green)' : 'var(--color-red)'}
        />
        <MetricCard
          label="DIAS ATE FECHAMENTO"
          value={fechamentoValue}
          subtitle={fechamentoSub}
          color="#6366f1"
        />
        <MetricCard
          label="GASTO DIARIO MAX"
          value={`R$ ${fmt(data.diario_recomendado)}`}
          subtitle="recomendado por dia"
          color={data.diario_recomendado >= 0 ? '#10b981' : 'var(--color-red)'}
        />
        <MetricCard
          label="SAUDE DO MES"
          value={data.saude}
          color={SAUDE_COLORS[data.saude_level] || 'var(--color-text)'}
        />
      </div>
    </div>
  )
}

export default MetricasSection
