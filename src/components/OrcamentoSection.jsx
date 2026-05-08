import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useMonth } from '../context/MonthContext'
import api from '../api/client'
import Skeleton from './Skeleton'
import styles from './OrcamentoSection.module.css'

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

function fmtSigned(n) {
  const sign = n >= 0 ? '+' : '−'
  return `${sign}R$ ${fmt(n)}`
}

function OrcamentoSection() {
  const { selectedMonth } = useMonth()
  const [showAll, setShowAll] = useState(false)

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

  const isBudget = data.display_mode === 'budget'
  const isTracking = data.display_mode === 'tracking'

  const hideableCount = isTracking
    ? data.categories.filter(c => !c.has_current_spend).length
    : 0
  const visibleCats = isTracking && !showAll
    ? data.categories.filter(c => c.has_current_spend)
    : data.categories

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <h3 className={styles.title}>ORÇAMENTO VARIÁVEL</h3>
        <div className={styles.headerRight}>
          <span className={styles.headerSpent}>
            Gasto: R$ {fmt(data.total_spent)}
          </span>
          {isBudget && (
            <span className={styles.headerEnvelope}>
              / R$ {fmt(data.total_available)}
              <span className={styles.headerPct}>({data.total_pct.toFixed(0)}%)</span>
            </span>
          )}
          {isTracking && data.deficit > 0 && (
            <span className={styles.headerDeficit}>
              Déficit: R$ {fmt(data.deficit)}
            </span>
          )}
        </div>
      </div>

      {isTracking && (
        <div className={styles.trackingBanner}>
          Sem envelope variável — compromissos excedem receita em R$ {fmt(data.deficit)}.
          Cards comparam gasto atual vs média histórica.
        </div>
      )}

      {isBudget && data.total_available > 0 && (
        <div className={styles.availableBanner}>
          Disponível: R$ {fmt(data.total_available)}
          <span className={styles.availableDetail}>
            (receita − fixo − investimentos − cartão)
          </span>
        </div>
      )}

      <div className={styles.grid}>
        {visibleCats.map(cat => (
          <BudgetCard key={cat.id} cat={cat} mode={data.display_mode} />
        ))}
      </div>

      {isTracking && hideableCount > 0 && (
        <button
          className={styles.toggleHidden}
          onClick={() => setShowAll(s => !s)}
        >
          {showAll
            ? `Ocultar ${hideableCount} categoria${hideableCount > 1 ? 's' : ''} sem gasto`
            : `Mostrar ${hideableCount} categoria${hideableCount > 1 ? 's' : ''} sem gasto`}
        </button>
      )}
    </section>
  )
}

function BudgetCard({ cat, mode }) {
  const [expanded, setExpanded] = useState(false)
  const hasSubs = cat.subcategories && cat.subcategories.length > 0

  const isTracking = mode === 'tracking'
  const refAmount = cat.reference_amount || 0
  const pctRef = cat.pct_of_reference || 0
  const pctClamped = Math.min(pctRef, 100)

  const barColor =
    cat.status === 'over' ? 'var(--color-red)' :
    cat.status === 'warning' ? 'var(--color-orange)' :
    'var(--color-green)'

  const borderColor =
    cat.status === 'over' ? 'var(--color-red)' :
    cat.status === 'warning' ? 'var(--color-orange)' :
    'var(--color-border)'

  const showBar = refAmount > 0
  const headerPct = refAmount > 0 ? pctRef : null

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
          {headerPct !== null && (
            <span className={`${styles.catPct} ${styles[cat.status]}`}>
              {headerPct.toFixed(0)}%
            </span>
          )}
        </span>
      </div>

      {showBar && (
        <div className={styles.barTrack}>
          <div
            className={styles.barFill}
            style={{ width: `${pctClamped}%`, background: barColor }}
          />
          {pctRef > 100 && (
            <div
              className={styles.barOverflow}
              style={{ width: `${Math.min(pctRef - 100, 100)}%` }}
            />
          )}
        </div>
      )}

      <div className={styles.cardBody}>
        <div className={styles.cardRow}>
          <span className={styles.cardLabel}>Gasto</span>
          <span className={`${styles.cardValue} ${styles[cat.status]}`}>
            R$ {fmt(cat.spent)}
          </span>
        </div>
        {cat.fixo_spent > 0 && (
          <div className={styles.cardRow} title="Gasto fixo nesta categoria (já contabilizado em Fixo)">
            <span className={styles.cardLabelDim}>+ fixo</span>
            <span className={styles.cardValueDim}>R$ {fmt(cat.fixo_spent)}</span>
          </div>
        )}

        {isTracking ? (
          <>
            <div className={styles.cardRow}>
              <span className={styles.cardLabel}>Média</span>
              <span className={styles.cardValueDim}>
                {cat.avg_6m > 0 ? `R$ ${fmt(cat.avg_6m)}` : '—'}
              </span>
            </div>
            {cat.avg_6m > 0 && cat.has_current_spend && (
              <div className={styles.cardRow}>
                <span className={styles.cardLabel}>Δ vs média</span>
                <span className={`${styles.cardValue} ${styles[cat.delta_vs_reference > 0 ? 'over' : 'ok']}`}>
                  {fmtSigned(cat.delta_vs_reference)}
                </span>
              </div>
            )}
          </>
        ) : (
          <>
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
                <span className={styles.cardLabel}>Média</span>
                <span className={styles.cardValueDim}>R$ {fmt(cat.avg_6m)}</span>
              </div>
            )}
          </>
        )}
      </div>

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
