import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../../api/client'
import styles from './SubscriptionsControlCard.module.css'

const MONTH_LABELS = {
  '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
  '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
  '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez',
}

const CADENCE_LABELS = {
  weekly: 'Semanal',
  monthly: 'Mensal',
  quarterly: 'Trimestral',
  annual: 'Anual',
}

const STATUS_LABELS = {
  active: 'Ativa',
  expiring: 'Expirando',
  cancelled: 'Cancelada',
}

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function shortDate(dateStr) {
  if (!dateStr) return '—'
  const [y, m, d] = dateStr.split('-')
  return `${d} ${MONTH_LABELS[m]} ${y.slice(2)}`
}

function SubscriptionsControlCard() {
  const [statusFilter, setStatusFilter] = useState('all')
  const [showCancelled, setShowCancelled] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['subscriptions-control'],
    queryFn: () => api.get('/analytics/subscriptions/'),
    staleTime: 60_000,
  })

  const filtered = useMemo(() => {
    if (!data?.subscriptions) return []
    return data.subscriptions.filter(s => {
      if (!showCancelled && s.status === 'cancelled') return false
      if (statusFilter !== 'all' && s.status !== statusFilter) return false
      return true
    })
  }, [data, statusFilter, showCancelled])

  if (isLoading) return <div className={styles.empty}>Carregando…</div>
  if (!data?.subscriptions?.length) return <div className={styles.empty}>Nenhuma assinatura detectada</div>

  return (
    <div className={styles.wrap}>
      {/* Header com totais + filtros */}
      <div className={styles.header}>
        <div className={styles.totals}>
          <div className={styles.totalItem}>
            <span className={styles.totalLabel}>Mensal</span>
            <span className={styles.totalValue}>R$ {fmt(data.total_monthly)}</span>
          </div>
          <div className={styles.totalItem}>
            <span className={styles.totalLabel}>Anual</span>
            <span className={styles.totalValueSecondary}>R$ {fmt(data.total_annual)}</span>
          </div>
          <div className={styles.totalItem}>
            <span className={styles.totalLabel}>Ativas</span>
            <span className={styles.statActive}>{data.active_count}</span>
          </div>
          {data.expiring_count > 0 && (
            <div className={styles.totalItem}>
              <span className={styles.totalLabel}>Expirando</span>
              <span className={styles.statExpiring}>{data.expiring_count}</span>
            </div>
          )}
        </div>
        <div className={styles.filters}>
          <div className={styles.segmented}>
            {['all', 'active', 'expiring'].map(s => (
              <button
                key={s}
                type="button"
                className={`${styles.segBtn} ${statusFilter === s ? styles.segBtnActive : ''}`}
                onClick={() => setStatusFilter(s)}
              >
                {s === 'all' ? 'Todas' : STATUS_LABELS[s]}
              </button>
            ))}
          </div>
          <label className={styles.toggle}>
            <input type="checkbox" checked={showCancelled} onChange={e => setShowCancelled(e.target.checked)} />
            <span>Mostrar canceladas ({data.cancelled_count})</span>
          </label>
        </div>
      </div>

      {/* Breakdown por subcategoria */}
      {data.by_subcategory?.length > 0 && (
        <div className={styles.breakdown}>
          {data.by_subcategory.map((b, i) => (
            <div key={i} className={styles.breakdownItem}>
              <span className={styles.breakdownLabel}>{b.name}</span>
              <span className={styles.breakdownAmount}>R$ {fmt(b.monthly)}/mês</span>
              <span className={styles.breakdownCount}>{b.count}</span>
            </div>
          ))}
        </div>
      )}

      {/* Tabela detalhada */}
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th className={styles.thStatus}></th>
              <th className={styles.thMerchant}>Serviço</th>
              <th className={styles.thCat}>Categoria</th>
              <th className={styles.thCadence}>Cadência</th>
              <th className={styles.thAmount}>Valor</th>
              <th className={styles.thMonthly}>Equiv. mensal</th>
              <th className={styles.thDate}>Último</th>
              <th className={styles.thDate}>Próximo</th>
              <th className={styles.thFlags}></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((s, i) => {
              const variation = s.min_amount !== s.max_amount
              return (
                <tr key={i} className={`${styles.row} ${styles[`row_${s.status}`]}`}>
                  <td className={styles.statusCell}>
                    <span className={`${styles.statusDot} ${styles[`dot_${s.status}`]}`} title={STATUS_LABELS[s.status]} />
                  </td>
                  <td className={styles.merchant} title={s.merchant}>
                    {s.merchant.length > 35 ? s.merchant.slice(0, 35) + '…' : s.merchant}
                  </td>
                  <td className={styles.cat}>{s.subcategory || s.category}</td>
                  <td className={styles.cadence}>{CADENCE_LABELS[s.cadence]}</td>
                  <td className={styles.amount}>
                    R$ {fmt(s.avg_amount)}
                    {variation && (
                      <span className={styles.variation} title={`Min R$ ${fmt(s.min_amount)} · Max R$ ${fmt(s.max_amount)}`}>±</span>
                    )}
                  </td>
                  <td className={styles.monthly}>R$ {fmt(s.monthly_equivalent)}</td>
                  <td className={styles.date}>{shortDate(s.last_charge)}</td>
                  <td className={styles.date}>{s.status === 'cancelled' ? '—' : shortDate(s.next_predicted)}</td>
                  <td className={styles.flags}>
                    {s.flags?.includes('amount_varies') && <span className={styles.flag} title="Valor varia entre cobranças">~</span>}
                    {s.flags?.includes('price_dropped') && <span className={`${styles.flag} ${styles.flagGood}`} title="Preço caiu">↓</span>}
                    {s.flags?.includes('single_charge_assumed_annual') && <span className={styles.flag} title="1 cobrança apenas — assumi anual">?</span>}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default SubscriptionsControlCard
