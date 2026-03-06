import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useMonth } from '../context/MonthContext'
import api from '../api/client'
import Skeleton from './Skeleton'
import styles from './OrcamentoSection.module.css'

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

function OrcamentoSection() {
  const { selectedMonth } = useMonth()

  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics-orcamento', selectedMonth],
    queryFn: () => api.get(`/analytics/orcamento/?month_str=${selectedMonth}`),
    enabled: !!selectedMonth,
  })

  if (isLoading) return (
    <section className={styles.section}>
      <h3 className={styles.title}>ORÇAMENTO VARIÁVEL</h3>
      <Skeleton variant="card" count={8} />
    </section>
  )
  if (error) return <div className={styles.error}>Erro ao carregar orçamento</div>
  if (!data) return null

  const noBudget = data.total_available <= 0
  const totalStatus = noBudget ? 'over' : data.total_pct > 100 ? 'over' : data.total_pct > 80 ? 'warning' : 'ok'

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <h3 className={styles.title}>ORÇAMENTO VARIÁVEL</h3>
        <span className={`${styles.headerTotal} ${styles[totalStatus]}`}>
          R$ {fmt(data.total_spent)} / R$ {fmt(data.total_limit)}
          <span className={styles.headerPct}>({data.total_pct.toFixed(0)}%)</span>
        </span>
      </div>

      {noBudget && (
        <div className={styles.noBudgetBanner}>
          Sem orçamento disponível — despesas comprometidas excedem a receita projetada.
        </div>
      )}

      {data.total_available > 0 && (
        <div className={styles.availableBanner}>
          Disponível: R$ {fmt(data.total_available)}
          <span className={styles.availableDetail}>
            (receita − fixo − investimentos − cartão)
          </span>
        </div>
      )}

      <div className={styles.grid}>
        {data.categories.map(cat => (
          <BudgetCard key={cat.id} cat={cat} />
        ))}
      </div>
    </section>
  )
}

function BudgetCard({ cat }) {
  const [expanded, setExpanded] = useState(false)
  const hasSubs = cat.subcategories && cat.subcategories.length > 0

  const pctClamped = Math.min(cat.pct, 100)
  const barColor =
    cat.status === 'over' ? 'var(--color-red)' :
    cat.status === 'warning' ? 'var(--color-orange)' :
    'var(--color-green)'

  const borderColor =
    cat.status === 'over' ? 'var(--color-red)' :
    cat.status === 'warning' ? 'var(--color-orange)' :
    'var(--color-border)'

  return (
    <div className={styles.card} style={{ borderColor }}>
      <div
        className={`${styles.cardHeader} ${hasSubs ? styles.clickable : ''}`}
        onClick={() => hasSubs && setExpanded(!expanded)}
      >
        <span className={styles.catName}>
          {hasSubs && (
            <span className={styles.expandIcon}>{expanded ? '▾' : '▸'}</span>
          )}
          {cat.name}
        </span>
        <span className={styles.catMeta}>
          {cat.share_pct > 0 && (
            <span className={styles.sharePct}>{cat.share_pct.toFixed(0)}%</span>
          )}
          <span className={`${styles.catPct} ${styles[cat.status]}`}>
            {cat.pct.toFixed(0)}%
          </span>
        </span>
      </div>

      {/* Progress bar */}
      <div className={styles.barTrack}>
        <div
          className={styles.barFill}
          style={{ width: `${pctClamped}%`, background: barColor }}
        />
        {cat.pct > 100 && (
          <div
            className={styles.barOverflow}
            style={{ width: `${Math.min(cat.pct - 100, 100)}%` }}
          />
        )}
      </div>

      <div className={styles.cardBody}>
        <div className={styles.cardRow}>
          <span className={styles.cardLabel}>Gasto</span>
          <span className={`${styles.cardValue} ${styles[cat.status]}`}>
            R$ {fmt(cat.spent)}
          </span>
        </div>
        <div className={styles.cardRow}>
          <span className={styles.cardLabel}>Limite</span>
          <span className={styles.cardValue}>R$ {fmt(cat.limit)}</span>
        </div>
        <div className={styles.cardRow}>
          <span className={styles.cardLabel}>Restante</span>
          <span className={styles.cardValue}>
            {cat.remaining > 0 ? `R$ ${fmt(cat.remaining)}` : '—'}
          </span>
        </div>
        {cat.avg_6m > 0 && (
          <div className={styles.cardRow}>
            <span className={styles.cardLabel}>Média 6m</span>
            <span className={styles.cardValueDim}>R$ {fmt(cat.avg_6m)}</span>
          </div>
        )}
      </div>

      {/* Subcategory breakdown */}
      {expanded && hasSubs && (
        <div className={styles.subBreakdown}>
          {cat.subcategories.map(sub => (
            <div key={sub.id} className={styles.subRow}>
              <div className={styles.subHeader}>
                <span className={styles.subName}>{sub.name}</span>
                <span className={styles.subSpent}>R$ {fmt(sub.spent)}</span>
              </div>
            </div>
          ))}
          {cat.uncategorized_spent > 0 && (
            <div className={styles.subRow}>
              <div className={styles.subHeader}>
                <span className={`${styles.subName} ${styles.subNameDim}`}>Sem subcategoria</span>
                <span className={styles.subSpent}>R$ {fmt(cat.uncategorized_spent)}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default OrcamentoSection
