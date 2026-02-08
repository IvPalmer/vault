import { useState, useMemo, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useMonth } from '../context/MonthContext'
import api from '../api/client'
import VaultTable from './VaultTable'
import CategoryDropdown from './CategoryDropdown'
import DescriptionEdit from './DescriptionEdit'
import tableStyles from './VaultTable.module.css'
import styles from './CardsSection.module.css'

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 2, minimumFractionDigits: 2 })
}

/** Amount cell with semantic color */
function AmountCell({ value }) {
  const cls = value > 0 ? tableStyles.positive : tableStyles.negative
  return <span className={cls}>R$ {fmt(value)}</span>
}

/** Parcela cell with orange bold */
function ParcelaCell({ value }) {
  if (!value) return <span style={{ color: 'var(--color-text-secondary)' }}>—</span>
  return <span className={tableStyles.parcela}>{value}</span>
}

const TABS = [
  { key: 'all', label: 'TODOS', filter: null },
  { key: 'master', label: 'MASTER', filter: 'Mastercard Black' },
  { key: 'visa', label: 'VISA', filter: 'Visa Infinite' },
  { key: 'rafa', label: 'RAFA', filter: 'Mastercard - Rafa' },
]

function CardsSection() {
  const { selectedMonth } = useMonth()
  const [activeTab, setActiveTab] = useState('all')
  const [showInstallments, setShowInstallments] = useState(true)
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['analytics-cards', selectedMonth],
    queryFn: () => api.get(`/analytics/cards/?month_str=${selectedMonth}`),
    enabled: !!selectedMonth,
  })

  // Fetch installment breakdown
  const { data: instData } = useQuery({
    queryKey: ['analytics-installments', selectedMonth],
    queryFn: () => api.get(`/analytics/installments/?month_str=${selectedMonth}`),
    enabled: !!selectedMonth,
  })

  const invalidate = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['analytics-cards', selectedMonth] })
    queryClient.invalidateQueries({ queryKey: ['analytics-installments', selectedMonth] })
    queryClient.invalidateQueries({ queryKey: ['analytics-metricas', selectedMonth] })
    queryClient.invalidateQueries({ queryKey: ['analytics-variable', selectedMonth] })
  }, [queryClient, selectedMonth])

  // Build columns with inline category editing
  const cardColumns = useMemo(() => [
    {
      accessorKey: 'date',
      header: 'DATA',
      size: 100,
      cell: ({ getValue }) => {
        const d = new Date(getValue() + 'T00:00:00')
        return d.toLocaleDateString('pt-BR')
      },
    },
    {
      accessorKey: 'account',
      header: 'CARTÃO',
      size: 160,
    },
    {
      accessorKey: 'category',
      header: 'CATEGORIA',
      size: 150,
      cell: ({ row }) => (
        <CategoryDropdown
          transactionId={row.original.id}
          category={row.original.category}
          categoryId={row.original.category_id}
          subcategory={row.original.subcategory}
          subcategoryId={row.original.subcategory_id}
          field="category"
          onUpdated={invalidate}
        />
      ),
    },
    {
      accessorKey: 'subcategory',
      header: 'SUBCATEGORIA',
      size: 140,
      cell: ({ row }) => (
        <CategoryDropdown
          transactionId={row.original.id}
          category={row.original.category}
          categoryId={row.original.category_id}
          subcategory={row.original.subcategory}
          subcategoryId={row.original.subcategory_id}
          field="subcategory"
          onUpdated={invalidate}
        />
      ),
    },
    {
      accessorKey: 'description',
      header: 'DESCRIÇÃO',
      minSize: 250,
      cell: ({ getValue, row }) => (
        <DescriptionEdit
          transactionId={row.original.id}
          description={getValue()}
          onUpdated={invalidate}
        />
      ),
    },
    {
      accessorKey: 'amount',
      header: 'VALOR',
      size: 130,
      cell: ({ getValue }) => <AmountCell value={getValue()} />,
    },
    {
      accessorKey: 'parcela',
      header: 'PARCELA',
      size: 90,
      cell: ({ getValue }) => <ParcelaCell value={getValue()} />,
    },
  ], [invalidate])

  /* Installment breakdown columns — with inline category/subcategory editing */
  const installmentColumns = useMemo(() => [
    {
      accessorKey: 'date',
      header: 'DATA',
      size: 100,
      cell: ({ getValue }) => {
        const d = new Date(getValue() + 'T00:00:00')
        return d.toLocaleDateString('pt-BR')
      },
    },
    {
      accessorKey: 'account',
      header: 'CARTÃO',
      size: 160,
    },
    {
      accessorKey: 'category',
      header: 'CATEGORIA',
      size: 150,
      cell: ({ row }) => {
        if (!row.original.id) {
          return row.original.category || 'Não categorizado'
        }
        return (
          <CategoryDropdown
            transactionId={row.original.id}
            category={row.original.category}
            categoryId={row.original.category_id}
            subcategory={row.original.subcategory}
            subcategoryId={row.original.subcategory_id}
            field="category"
            onUpdated={invalidate}
            installmentMode
          />
        )
      },
    },
    {
      accessorKey: 'subcategory',
      header: 'SUBCATEGORIA',
      size: 140,
      cell: ({ row }) => {
        if (!row.original.id) {
          const val = row.original.subcategory
          if (!val) return <span style={{ color: 'var(--color-text-secondary)' }}>—</span>
          return val
        }
        return (
          <CategoryDropdown
            transactionId={row.original.id}
            category={row.original.category}
            categoryId={row.original.category_id}
            subcategory={row.original.subcategory}
            subcategoryId={row.original.subcategory_id}
            field="subcategory"
            onUpdated={invalidate}
            installmentMode
          />
        )
      },
    },
    {
      accessorKey: 'description',
      header: 'DESCRIÇÃO',
      minSize: 250,
    },
    {
      accessorKey: 'amount',
      header: 'VALOR',
      size: 130,
      cell: ({ getValue }) => (
        <span className={tableStyles.negative}>R$ {fmt(getValue())}</span>
      ),
    },
    {
      accessorKey: 'parcela',
      header: 'PARCELA',
      size: 90,
      cell: ({ getValue }) => <ParcelaCell value={getValue()} />,
    },
  ], [invalidate])

  // Filter transactions by active tab; compute bill total from ALL rows
  const { filteredData, billTotal } = useMemo(() => {
    if (!data?.transactions) return { filteredData: [], billTotal: 0 }

    const currentTab = TABS.find(t => t.key === activeTab)
    let txns = data.transactions

    if (currentTab?.filter) {
      txns = txns.filter(t => t.account === currentTab.filter)
    }

    return {
      filteredData: txns,
      // Sum of ALL transactions on the invoice (charges + refunds) = what you actually pay
      billTotal: Math.abs(txns.reduce((s, t) => s + t.amount, 0)),
    }
  }, [data, activeTab])

  // Filter installments by active tab
  const filteredInstallments = useMemo(() => {
    if (!instData?.items) return []
    const currentTab = TABS.find(t => t.key === activeTab)
    if (!currentTab?.filter) return instData.items
    return instData.items.filter(i => i.account === currentTab.filter)
  }, [instData, activeTab])

  // Use API-provided deduped total for "all" tab; client-side sum for filtered tabs
  const instTotal = useMemo(() => {
    if (activeTab === 'all' && instData?.total != null) return instData.total
    return filteredInstallments.reduce((s, i) => s + i.amount, 0)
  }, [filteredInstallments, activeTab, instData])

  if (isLoading) {
    return <div className={styles.loading}>Carregando cartões...</div>
  }

  /* For filtered tabs, hide the CARTÃO column */
  const cols = activeTab === 'all' ? cardColumns : cardColumns.filter(c => c.accessorKey !== 'account')
  const instCols = activeTab === 'all'
    ? installmentColumns
    : installmentColumns.filter(c => c.accessorKey !== 'account' && c.accessorKey !== 'subcategory')

  return (
    <div className={styles.section}>
      <h3 className={styles.title}>CONTROLE CARTÕES</h3>

      {/* Tab bar */}
      <div className={styles.tabBar}>
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`${styles.tab} ${activeTab === tab.key ? styles.active : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Installment breakdown */}
      {instData && filteredInstallments.length > 0 && (
        <div className={styles.installmentSection}>
          <button
            className={styles.installmentHeader}
            onClick={() => setShowInstallments(!showInstallments)}
          >
            <span className={styles.installmentTitle}>
              PARCELAS
              {instData.source === 'projected' && (
                <span className={styles.projectedBadge}>PROJETADO</span>
              )}
            </span>
            <span className={styles.installmentMeta}>
              <span className={tableStyles.negative}>R$ {fmt(instTotal)}</span>
              <span className={styles.summaryCount}>
                {' '}{activeTab === 'all' && instData?.count != null ? instData.count : filteredInstallments.length} parcelas
              </span>
              <span className={styles.chevron}>{showInstallments ? '▾' : '▸'}</span>
            </span>
          </button>
          {showInstallments && (
            <VaultTable
              columns={instCols}
              data={filteredInstallments}
              emptyMessage="Sem parcelas."
              searchable={false}
              maxHeight={300}
            />
          )}
        </div>
      )}

      {/* Summary — Total = sum of all invoice transactions (what you actually pay) */}
      <div className={styles.cardSummary}>
        <span>
          Total fatura: <span className={tableStyles.negative}>R$ {fmt(billTotal)}</span>
        </span>
      </div>

      {/* Table */}
      <VaultTable
        columns={cols}
        data={filteredData}
        emptyMessage="Sem transações de cartão neste mês."
        maxHeight={500}
      />
    </div>
  )
}

export default CardsSection
