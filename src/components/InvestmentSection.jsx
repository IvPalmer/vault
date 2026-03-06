import { useMemo, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useMonth } from '../context/MonthContext'
import useInvalidateAnalytics from '../hooks/useInvalidateAnalytics'
import api from '../api/client'
import VaultTable from './VaultTable'
import TransactionPicker from './TransactionPicker'
import InlineEdit from './InlineEdit'
import tableStyles from './VaultTable.module.css'
import recStyles from './RecurringSection.module.css'
import styles from './InvestmentSection.module.css'

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

function StatusBadge({ value }) {
  const clsMap = {
    Pago: tableStyles.badgePago,
    Faltando: tableStyles.badgeFaltando,
    Parcial: tableStyles.badgeParcial,
    Pulado: tableStyles.badgePulado,
  }
  const cls = clsMap[value] || tableStyles.badgeFaltando
  return <span className={`${tableStyles.badge} ${cls}`}>{value}</span>
}

function AmountCell({ value }) {
  return <span className={tableStyles.negative}>R$ {fmt(value)}</span>
}

function InvestmentSection() {
  const { selectedMonth } = useMonth()
  const { invalidateAll } = useInvalidateAnalytics()

  const { data: recData, isLoading } = useQuery({
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

  const handleUpdateItem = useCallback(async (mappingId, field, value) => {
    try {
      await api.patch('/analytics/recurring/update/', {
        mapping_id: mappingId,
        [field]: value,
      })
      invalidateAll()
    } catch (err) {
      console.error(`Failed to update ${field}:`, err)
    }
  }, [invalidateAll])

  const handleUpdateExpected = useCallback(async (mappingId, newAmount) => {
    try {
      await api.patch('/analytics/recurring/expected/', {
        mapping_id: mappingId,
        expected_amount: newAmount,
      })
      invalidateAll()
    } catch (err) {
      console.error('Failed to update expected:', err)
    }
  }, [invalidateAll])

  const handleSkip = useCallback(async (mappingId) => {
    try {
      await api.post('/analytics/recurring/skip/', { mapping_id: mappingId })
      invalidateAll()
    } catch (err) {
      console.error('Failed to skip:', err)
    }
  }, [invalidateAll])

  const handleUnskip = useCallback(async (mappingId) => {
    try {
      await api.delete('/analytics/recurring/skip/', { mapping_id: mappingId })
      invalidateAll()
    } catch (err) {
      console.error('Failed to unskip:', err)
    }
  }, [invalidateAll])

  const handleDeleteCustom = useCallback(async (mappingId) => {
    try {
      await api.delete('/analytics/recurring/custom/', { mapping_id: mappingId })
      invalidateAll()
    } catch (err) {
      console.error('Failed to delete custom:', err)
    }
  }, [invalidateAll])

  const columns = useMemo(() => [
    {
      accessorKey: 'due_day',
      header: 'DIA',
      size: 55,
      cell: ({ getValue, row }) => {
        const item = row.original
        const val = getValue()
        if (val == null) {
          return <span style={{ color: 'var(--color-text-secondary)' }}>{'\u2014'}</span>
        }
        return (
          <InlineEdit
            value={val}
            onSave={(v) => handleUpdateItem(item.mapping_id, 'due_day', v)}
            disabled={item.is_skipped}
            format="currency"
            prefix=""
            placeholder={'\u2014'}
            color="var(--color-text-secondary)"
          />
        )
      },
    },
    {
      accessorKey: 'name',
      header: 'ITEM',
      minSize: 160,
      cell: ({ getValue, row }) => {
        const item = row.original
        return (
          <InlineEdit
            value={getValue()}
            onSave={(val) => handleUpdateItem(item.mapping_id, 'name', val)}
            disabled={item.is_skipped}
            format="text"
            prefix=""
            color={item.is_custom ? 'var(--color-accent)' : 'var(--color-text)'}
          />
        )
      },
    },
    {
      accessorKey: 'expected',
      header: 'ESPERADO',
      size: 120,
      cell: ({ getValue, row }) => {
        const item = row.original
        return (
          <InlineEdit
            value={getValue()}
            onSave={(val) => handleUpdateExpected(item.mapping_id, val)}
            disabled={item.is_skipped}
            color="var(--color-text-secondary)"
          />
        )
      },
    },
    {
      accessorKey: 'actual',
      header: 'REAL',
      size: 110,
      cell: ({ getValue }) => {
        const val = getValue()
        if (val === 0) return <span style={{ color: 'var(--color-text-secondary)' }}>{'\u2014'}</span>
        return <AmountCell value={val} />
      },
    },
    {
      accessorKey: 'status',
      header: 'STATUS',
      size: 90,
      cell: ({ getValue }) => <StatusBadge value={getValue()} />,
    },
    {
      accessorKey: 'matched_desc',
      header: 'TRANSACAO',
      minSize: 200,
      cell: ({ getValue, row }) => {
        const item = row.original
        if (item.is_skipped) return <span style={{ color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>Pulado</span>
        return (
          <TransactionPicker
            mappingId={item.mapping_id}
            categoryName={item.name}
            currentMatch={getValue()}
            matchedTransactionId={item.matched_transaction_id}
            matchedTransactionIds={item.matched_transaction_ids}
            matchType={item.match_type}
            matchCount={item.match_count}
            matchMode={item.match_mode}
            suggested={item.suggested}
            status={item.status}
          />
        )
      },
    },
    {
      id: 'actions',
      header: '',
      size: 60,
      cell: ({ row }) => {
        const item = row.original
        return (
          <div className={recStyles.actions}>
            {item.is_skipped ? (
              <button
                className={recStyles.actionBtn}
                onClick={() => handleUnskip(item.mapping_id)}
                title="Restaurar item"
              >
                {'\u21ba'}
              </button>
            ) : (
              <button
                className={recStyles.actionBtn}
                onClick={() => handleSkip(item.mapping_id)}
                title="Pular este mes"
              >
                {'\u2298'}
              </button>
            )}
            {item.is_custom && (
              <button
                className={`${recStyles.actionBtn} ${recStyles.deleteBtn}`}
                onClick={() => handleDeleteCustom(item.mapping_id)}
                title="Remover item"
              >
                {'\u00d7'}
              </button>
            )}
          </div>
        )
      },
    },
  ], [handleUpdateItem, handleUpdateExpected, handleSkip, handleUnskip, handleDeleteCustom])

  const items = recData?.investimento || []

  // Totals
  const totalActual = useMemo(() => {
    return items.reduce((sum, item) => item.is_skipped ? sum : sum + (item.actual || 0), 0)
  }, [items])

  const templateExpected = useMemo(() => {
    return items.reduce((sum, item) => item.is_skipped ? sum : sum + (item.expected || 0), 0)
  }, [items])

  // Dynamic target from metricas (authoritative, includes clamping)
  const target = metricasData?.invest_expected_total ?? templateExpected
  const savingsTargetPct = recData?.savings_target_pct ?? 20
  const isDynamic = target > templateExpected

  const pct = target > 0 ? Math.round(totalActual / target * 100) : 0
  const pctClamped = Math.min(pct, 100)
  const barColor = pct >= 100 ? 'var(--color-green)' : pct >= 50 ? 'var(--color-orange)' : 'var(--color-red)'

  const affordable = metricasData?.savings_affordable !== false
  const paused = target === 0 && savingsTargetPct > 0

  const rowClassName = useCallback((row) => {
    if (row.original.is_skipped) return tableStyles.skippedRow
    return ''
  }, [])

  if (isLoading) return null
  if (!items.length && !target) return null

  return (
    <div className={styles.section}>
      <div className={styles.header}>
        <h3 className={styles.title}>INVESTIMENTOS</h3>
        <div className={styles.targetInfo}>
          {paused ? (
            <span className={styles.paused}>PAUSADO</span>
          ) : (
            <>
              <span className={styles.actual}>R$ {fmt(totalActual)}</span>
              <span className={styles.separator}>/</span>
              <span className={styles.target}>R$ {fmt(target)}</span>
              {isDynamic && (
                <span className={styles.hint}>(meta {savingsTargetPct}%)</span>
              )}
              <span className={`${styles.pct} ${pct >= 100 ? styles.pctOk : pct >= 50 ? styles.pctWarn : styles.pctLow}`}>
                {pct}%
              </span>
            </>
          )}
        </div>
      </div>

      {/* Progress bar */}
      {!paused && target > 0 && (
        <div className={styles.barTrack}>
          <div
            className={styles.barFill}
            style={{ width: `${pctClamped}%`, background: barColor }}
          />
        </div>
      )}

      {!affordable && !paused && (
        <div className={styles.warningBanner}>
          Saldo insuficiente para meta de investimento completa
        </div>
      )}

      <VaultTable
        columns={columns}
        data={items}
        emptyMessage="Nenhum investimento configurado."
        searchable={false}
        maxHeight={300}
        rowClassName={rowClassName}
      />

    </div>
  )
}

export default InvestmentSection
