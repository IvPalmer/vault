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

function GastosPorCategoria() {
  const { selectedMonth } = useMonth()
  const [showAll, setShowAll] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics-orcamento', selectedMonth],
    queryFn: () => api.get(`/analytics/orcamento/?month_str=${selectedMonth}`),
    enabled: !!selectedMonth,
  })

  if (isLoading) return (
    <section className={styles.section}>
      <h3 className={styles.title}>GASTOS POR CATEGORIA</h3>
      <Skeleton variant="card" count={8} />
    </section>
  )
  if (error) return <div className={styles.error}>Erro ao carregar gastos</div>
  if (!data) return null

  const hideableCount = data.categories.filter(c => !c.has_current_spend).length
  const visibleCats = showAll
    ? data.categories
    : data.categories.filter(c => c.has_current_spend)

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <h3 className={styles.title}>GASTOS POR CATEGORIA</h3>
        <div className={styles.headerRight}>
          <span className={styles.headerSpent}>
            Total: R$ {fmt(data.total_spent)}
          </span>
          {data.has_envelope ? (
            <span className={styles.headerEnvelope}>
              Disponível: R$ {fmt(data.total_available)}
            </span>
          ) : data.deficit > 0 ? (
            <span className={styles.headerDeficit}>
              Déficit: R$ {fmt(data.deficit)}
            </span>
          ) : null}
        </div>
      </div>

      <div className={styles.grid}>
        {visibleCats.map(cat => (
          <CategoryCard key={cat.id} cat={cat} />
        ))}
      </div>

      {hideableCount > 0 && (
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

function CategoryCard({ cat }) {
  const [expanded, setExpanded] = useState(false)
  const hasSubs = cat.subcategories && cat.subcategories.length > 0
  const hasReference = cat.reference_amount > 0

  const pctClamped = hasReference ? Math.min(cat.pct_of_reference, 100) : 0
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
          {cat.current_share_pct > 0 && (
            <span className={styles.sharePct}>{cat.current_share_pct.toFixed(0)}%</span>
          )}
          {hasReference && cat.has_current_spend && (
            <span className={`${styles.catPct} ${styles[cat.status]}`}>
              {cat.pct_of_reference.toFixed(0)}%
            </span>
          )}
        </span>
      </div>

      {hasReference && (
        <div className={styles.barTrack}>
          <div
            className={styles.barFill}
            style={{ width: `${pctClamped}%`, background: barColor }}
          />
          {cat.pct_of_reference > 100 && (
            <div
              className={styles.barOverflow}
              style={{ width: `${Math.min(cat.pct_of_reference - 100, 100)}%` }}
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
        <div className={styles.cardRow}>
          <span className={styles.cardLabel}>Média 6m</span>
          <span className={styles.cardValueDim}>
            {cat.avg_6m > 0 ? `R$ ${fmt(cat.avg_6m)}` : '—'}
          </span>
        </div>
        {cat.has_current_spend && cat.reference_amount > 0 && (
          <div className={styles.cardRow}>
            <span className={styles.cardLabel}>
              Δ vs {cat.reference_source === 'manual' ? 'meta' : 'média'}
            </span>
            <span className={`${styles.cardValue} ${styles[cat.delta_vs_reference > 0 ? 'over' : 'ok']}`}>
              {fmtSigned(cat.delta_vs_reference)}
            </span>
          </div>
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

export default GastosPorCategoria
