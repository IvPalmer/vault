import { useState, useMemo, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useMonth } from '../context/MonthContext'
import api from '../api/client'
import VaultTable from './VaultTable'
import CategoryDropdown from './CategoryDropdown'
import DescriptionEdit from './DescriptionEdit'
import TypeBadge from './TypeBadge'
import tableStyles from './VaultTable.module.css'
import styles from './CardsSection.module.css'

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 2, minimumFractionDigits: 2 })
}


/** "2026-07" → "julho/26" (pt-BR). */
function monthLabel(monthStr) {
  if (!monthStr) return ''
  const d = new Date(monthStr + '-01T00:00:00')
  return d.toLocaleDateString('pt-BR', { month: 'long', year: '2-digit' })
}

/** Add n months to "YYYY-MM". */
function addMonths(monthStr, n) {
  if (!monthStr) return ''
  const [y, m] = monthStr.split('-').map(Number)
  const idx = (y * 12 + (m - 1)) + n
  return `${String(Math.floor(idx / 12)).padStart(4, '0')}-${String((idx % 12) + 1).padStart(2, '0')}`
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

function CardsSection() {
  const { selectedMonth } = useMonth()
  const [activeTab, setActiveTab] = useState('all')
  const [showInstallments, setShowInstallments] = useState(true)
  const queryClient = useQueryClient()

  // Fetch credit card accounts for current profile to build dynamic tabs
  const { data: accountsData } = useQuery({
    queryKey: ['accounts-cc'],
    queryFn: () => api.get('/accounts/?account_type=credit_card'),
    staleTime: 300_000,
  })

  const TABS = useMemo(() => {
    if (!accountsData) return [{ key: 'all', label: 'Todos', filter: null }]

    const ccAccounts = (Array.isArray(accountsData) ? accountsData : accountsData.results || [])
      .filter(a => a.account_type === 'credit_card')
      .sort((a, b) => a.name.localeCompare(b.name, 'pt-BR'))

    // Build short labels: "Mastercard Black" → "MC Black", "NuBank Cartão" → "NuBank", etc.
    const cardTabs = ccAccounts.map((acct) => {
      let label = acct.name
        .replace(/^Mastercard\s*/i, 'MC ')
        .replace(/^NuBank\s*/i, 'NuBank ')
        .replace(/^[-–—]\s*/, '')
        .trim() || acct.name
      return { key: acct.id, label, filter: acct.name }
    })

    // Skip "Todos" tab when there's only 1 card
    if (cardTabs.length <= 1) return cardTabs.length === 1 ? cardTabs : [{ key: 'all', label: 'Todos', filter: null }]

    return [{ key: 'all', label: 'Todos', filter: null }, ...cardTabs]
  }, [accountsData])

  // Reset to first tab if active tab no longer exists (profile switch, single-card)
  const effectiveTab = TABS.find(t => t.key === activeTab) ? activeTab : TABS[0]?.key || 'all'

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

  // Cancelling/shortening a series affects every future month → invalidate broadly.
  const invalidateSeries = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['analytics-installments'] })
    queryClient.invalidateQueries({ queryKey: ['analytics-metricas'] })
    queryClient.invalidateQueries({ queryKey: ['analytics-projection'] })
    queryClient.invalidateQueries({ queryKey: ['analytics-cards'] })
  }, [queryClient])

  const capSeries = useCallback(async (r) => {
    const pos = parseInt(String(r.parcela || '').split('/')[0], 10)
    if (!r.id || !pos) return
    if (!window.confirm(`Encerrar esta série na parcela ${r.parcela}? A projeção para de prever as próximas parcelas.`)) return
    try {
      await api.post('/installment-overrides/', { transaction_id: r.id, effective_total: pos })
      invalidateSeries()
    } catch (e) { window.alert(e?.message || 'Erro ao encerrar série') }
  }, [invalidateSeries])

  const uncapSeries = useCallback(async (r) => {
    if (!r.id) return
    try {
      await api.delete('/installment-overrides/', { transaction_id: r.id })
      invalidateSeries()
    } catch (e) { window.alert(e?.message || 'Erro ao reativar série') }
  }, [invalidateSeries])

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
      accessorKey: 'transaction_type',
      header: 'TIPO',
      size: 90,
      cell: ({ getValue }) => <TypeBadge value={getValue()} />,
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
      minSize: 160,
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
      size: 110,
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
      accessorKey: 'transaction_type',
      header: 'TIPO',
      size: 90,
      cell: ({ getValue }) => <TypeBadge value={getValue()} />,
    },
    {
      accessorKey: 'category',
      header: 'CATEGORIA',
      size: 150,
      cell: ({ row }) => {
        if (!row.original.id) {
          return row.original.category || '-'
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
    {
      accessorKey: 'cap',
      header: '',
      size: 120,
      cell: ({ row }) => {
        const r = row.original
        if (r.projected || !r.id) return null
        if (r.capped) {
          return (
            <button className={styles.capBtn} title="Série encerrada — reativar projeção"
              onClick={() => uncapSeries(r)}>encerrada · reativar</button>
          )
        }
        return (
          <button className={styles.capBtn} title="Encerrar série nesta parcela (para a projeção)"
            onClick={() => capSeries(r)}>encerrar série</button>
        )
      },
    },
  ], [invalidate, capSeries, uncapSeries])

  // COMPRAS = à vista (non-installment) purchases of the month. Every installment
  // — including the first (1/N) — lives in the PARCELAS table (the bill that
  // closes with this month's purchases).
  const filteredData = useMemo(() => {
    if (!data?.transactions) return []
    const currentTab = TABS.find(t => t.key === effectiveTab)
    let txns = data.transactions.filter(t => !t.is_installment)
    if (currentTab?.filter) {
      txns = txns.filter(t => t.account === currentTab.filter)
    }
    return txns
  }, [data, effectiveTab, TABS])

  // Variable total (non-installment purchases only)
  const variableTotal = useMemo(() =>
    Math.abs(filteredData.reduce((s, t) => s + t.amount, 0)),
  [filteredData])

  // Filter installments by active tab
  const filteredInstallments = useMemo(() => {
    if (!instData?.items) return []
    const currentTab = TABS.find(t => t.key === effectiveTab)
    if (!currentTab?.filter) return instData.items
    return instData.items.filter(i => i.account === currentTab.filter)
  }, [instData, effectiveTab, TABS])

  // Use API-provided deduped total for "all" tab; client-side sum for filtered tabs
  const instTotal = useMemo(() => {
    if (effectiveTab === 'all' && instData?.total != null) return instData.total
    return filteredInstallments.reduce((s, i) => s + i.amount, 0)
  }, [filteredInstallments, effectiveTab, instData])

  if (isLoading) {
    return <div className={styles.loading}>Carregando cartões...</div>
  }

  /* For filtered tabs or single-card profiles, hide the CARTÃO column */
  const showAllCards = effectiveTab === 'all' && TABS.length > 1
  const cols = showAllCards ? cardColumns : cardColumns.filter(c => c.accessorKey !== 'account')
  const instCols = showAllCards
    ? installmentColumns
    : installmentColumns.filter(c => c.accessorKey !== 'account')

  return (
    <div className={styles.section}>
      <h3 className={styles.title}>CONTROLE CARTÕES</h3>
      {data?.cc_display_mode === 'transaction' ? (
        <div className={styles.subtitle}>
          Compras e parcelas de {monthLabel(selectedMonth)} — entram na fatura paga em {monthLabel(addMonths(selectedMonth, 1))}
        </div>
      ) : (
        <div className={styles.subtitle}>Fatura paga em {monthLabel(selectedMonth)}</div>
      )}

      {/* Tab bar — hidden when only 1 card */}
      {TABS.length > 1 && (
        <div className={styles.tabBar}>
          {TABS.map((tab) => (
            <button
              key={tab.key}
              className={`${styles.tab} ${effectiveTab === tab.key ? styles.active : ''}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {/* Totals bar — like Conta Corrente summary */}
      <div className={styles.cardSummary}>
        <span>
          Parcelas: <span className={tableStyles.negative}>R$ {fmt(instTotal)}</span>
        </span>
        <span>
          Compras: <span className={tableStyles.negative}>R$ {fmt(variableTotal)}</span>
        </span>
        <span>
          Total: <span className={tableStyles.negative}>R$ {fmt(instTotal + variableTotal)}</span>
        </span>
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
              <span className={styles.summaryCount}>
                {effectiveTab === 'all' && instData?.count != null ? instData.count : filteredInstallments.length} parcelas
              </span>
              <span className={tableStyles.negative}>R$ {fmt(instTotal)}</span>
            </span>
            <span className={styles.chevron}>{showInstallments ? '▾' : '▸'}</span>
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

      {/* Variable transactions */}
      <div className={styles.installmentSection}>
        <div className={styles.installmentHeader} style={{ cursor: 'default' }}>
          <span className={styles.installmentTitle}>
            COMPRAS
            <span className={styles.summaryCount}>{filteredData.length} transações</span>
            <span className={tableStyles.negative}>R$ {fmt(variableTotal)}</span>
          </span>
        </div>
        <VaultTable
          columns={cols}
          data={filteredData}
          emptyMessage="Sem transações de cartão neste mês."
          maxHeight={500}
          initialSorting={[{ id: 'date', desc: true }]}
        />
      </div>
    </div>
  )
}

export default CardsSection
