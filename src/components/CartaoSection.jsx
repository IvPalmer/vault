import { useMemo, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useMonth } from '../context/MonthContext'
import useInvalidateAnalytics from '../hooks/useInvalidateAnalytics'
import api from '../api/client'
import VaultTable from './VaultTable'
import TransactionPicker from './TransactionPicker'
import tableStyles from './VaultTable.module.css'
import recStyles from './RecurringSection.module.css'
import styles from './CartaoSection.module.css'

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

function CartaoSection() {
  const { selectedMonth } = useMonth()
  const { invalidateAll } = useInvalidateAnalytics()

  const { data: recData, isLoading } = useQuery({
    queryKey: ['analytics-recurring', selectedMonth],
    queryFn: () => api.get(`/analytics/recurring/?month_str=${selectedMonth}`),
    enabled: !!selectedMonth,
  })

  const items = recData?.cartao || []

  const totalExpected = useMemo(() => {
    return items.reduce((sum, item) => item.is_skipped ? sum : sum + (item.expected || 0), 0)
  }, [items])

  const totalActual = useMemo(() => {
    return items.reduce((sum, item) => item.is_skipped ? sum : sum + (item.actual || 0), 0)
  }, [items])

  const allPaid = totalExpected > 0 && totalActual >= totalExpected * 0.9
  const statusLabel = allPaid ? 'quitado' : 'pendente'

  const columns = useMemo(() => [
    {
      accessorKey: 'due_day',
      header: 'DIA',
      size: 55,
      cell: ({ getValue }) => {
        const val = getValue()
        if (val == null) return <span style={{ color: 'var(--color-text-secondary)' }}>{'\u2014'}</span>
        return <span style={{ color: 'var(--color-text-secondary)' }}>{val}</span>
      },
    },
    {
      accessorKey: 'name',
      header: 'ITEM',
      minSize: 160,
      cell: ({ getValue }) => (
        <span style={{ fontWeight: 600, color: 'var(--color-text)' }}>{getValue()}</span>
      ),
    },
    {
      accessorKey: 'expected',
      header: 'FATURA',
      size: 120,
      cell: ({ getValue }) => {
        const val = getValue()
        if (!val) return <span style={{ color: 'var(--color-text-secondary)' }}>{'\u2014'}</span>
        return <span style={{ color: 'var(--color-text-secondary)' }}>R$ {fmt(val)}</span>
      },
    },
    {
      accessorKey: 'actual',
      header: 'PAGO',
      size: 110,
      cell: ({ getValue }) => {
        const val = getValue()
        if (val === 0) return <span style={{ color: 'var(--color-text-secondary)' }}>{'\u2014'}</span>
        return <span className={tableStyles.negative} style={{ fontWeight: 700 }}>R$ {fmt(val)}</span>
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
  ], [])

  const rowClassName = useCallback((row) => {
    if (row.original.is_skipped) return tableStyles.skippedRow
    return ''
  }, [])

  if (isLoading) return null
  if (!items.length) return null

  return (
    <div className={styles.section}>
      <div className={styles.header}>
        <h3 className={styles.title}>CARTÃO</h3>
        <div className={styles.headerRight}>
          <span className={styles.totals}>
            Fatura: <strong>R$ {fmt(totalExpected)}</strong>
          </span>
          <span className={styles.separator}>·</span>
          <span className={styles.totals}>
            Pago: <strong style={{ color: totalActual > 0 ? 'var(--color-orange)' : 'var(--color-text-secondary)' }}>
              R$ {fmt(totalActual)}
            </strong>
          </span>
          <span className={allPaid ? styles.statusOk : styles.statusPending}>
            {statusLabel}
          </span>
        </div>
      </div>

      <VaultTable
        columns={columns}
        data={items}
        emptyMessage="Nenhum cartão configurado."
        searchable={false}
        maxHeight={200}
        rowClassName={rowClassName}
      />
    </div>
  )
}

export default CartaoSection
