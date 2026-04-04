import { useQuery } from '@tanstack/react-query'
import { useProfile } from '../../context/ProfileContext'
import api from '../../api/client'

function useMetricas() {
  const { currentProfile } = useProfile()
  const now = new Date()
  const monthStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

  return useQuery({
    queryKey: ['metricas-widget', monthStr, currentProfile?.id],
    queryFn: () => api.get(`/analytics/metricas/?month_str=${monthStr}`),
    staleTime: 120000,
    enabled: !!currentProfile?.id,
  })
}

const s = {
  wrap: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    boxShadow: 'var(--shadow-sm)',
    gap: 4,
    transition: 'border-color 0.15s',
  },
  value: {
    fontSize: '1.4rem',
    fontWeight: 800,
    lineHeight: 1,
    fontVariantNumeric: 'tabular-nums',
  },
  label: {
    fontSize: '0.68rem',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '1px',
    color: 'var(--color-text-secondary)',
  },
  loading: {
    fontSize: '0.78rem',
    color: 'var(--color-text-secondary)',
  },
}

function fmt(v) {
  if (v == null) return '—'
  return 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

export function FinSaldo() {
  const { data, isLoading } = useMetricas()
  const val = data?.saldo_projetado
  const color = val != null && val < 0 ? 'var(--color-red)' : 'var(--color-text)'

  return (
    <div style={s.wrap}>
      {isLoading ? (
        <span style={s.loading}>...</span>
      ) : (
        <>
          <span style={{ ...s.value, color }}>{fmt(val)}</span>
          <span style={s.label}>Saldo Projetado</span>
        </>
      )}
    </div>
  )
}

export function FinSobra() {
  const { data, isLoading } = useMetricas()
  const orcamento = data?.orcamento_variavel
  const gastos = data?.variable_spending || 0
  const sobra = orcamento != null ? orcamento - gastos : null
  const color = sobra != null && sobra < 0 ? 'var(--color-red)' : '#4caf50'

  return (
    <div style={s.wrap}>
      {isLoading ? (
        <span style={s.loading}>...</span>
      ) : (
        <>
          <span style={{ ...s.value, color }}>{fmt(sobra)}</span>
          <span style={s.label}>Sobra do Mes</span>
        </>
      )}
    </div>
  )
}

export function FinFatura() {
  const { data, isLoading } = useMetricas()
  const val = data?.fatura_total

  return (
    <div style={s.wrap}>
      {isLoading ? (
        <span style={s.loading}>...</span>
      ) : (
        <>
          <span style={{ ...s.value, color: 'var(--color-text)' }}>{fmt(val)}</span>
          <span style={s.label}>Fatura CC</span>
        </>
      )}
    </div>
  )
}
