import { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { useQuery } from '@tanstack/react-query'
import { useMonth } from '../context/MonthContext'
import useInvalidateAnalytics from '../hooks/useInvalidateAnalytics'
import api from '../api/client'
import VaultTable from './VaultTable'
import TransactionPicker from './TransactionPicker'
import InlineEdit from './InlineEdit'
import AddRecurringForm from './AddRecurringForm'
import tableStyles from './VaultTable.module.css'
import styles from './RecurringSection.module.css'

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

/** Status badge cell renderer */
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

/** Amount cell with semantic color */
function AmountCell({ value, positive }) {
  const cls = positive ? tableStyles.positive : tableStyles.negative
  return <span className={cls}>R$ {fmt(value)}</span>
}

/** Inline type selector — portal-based dropdown to escape table overflow:hidden */
function TypeSelector({ value, onChange, disabled }) {
  const [isOpen, setIsOpen] = useState(false)
  const [dropdownPos, setDropdownPos] = useState(null)
  const triggerRef = useRef(null)
  const dropdownRef = useRef(null)

  const typeMap = {
    Fixo: { label: 'Fixo', cls: styles.typeFixo },
    Income: { label: 'Entrada', cls: styles.typeIncome },
    Investimento: { label: 'Invest.', cls: styles.typeInvest },
    Variavel: { label: 'Variável', cls: styles.typeVariable },
  }

  const types = ['Fixo', 'Variavel', 'Income', 'Investimento']
  const t = typeMap[value] || { label: value, cls: '' }

  // Position dropdown using fixed positioning (portal)
  useEffect(() => {
    if (!isOpen || !triggerRef.current) return
    const rect = triggerRef.current.getBoundingClientRect()
    let left = rect.left
    const dropdownWidth = 130
    if (left + dropdownWidth > window.innerWidth - 16) {
      left = window.innerWidth - dropdownWidth - 16
    }
    let top = rect.bottom + 4
    const dropdownHeight = 160
    if (top + dropdownHeight > window.innerHeight - 16) {
      top = rect.top - dropdownHeight - 4
    }
    setDropdownPos({ top, left, width: dropdownWidth })
  }, [isOpen])

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return
    function handleClick(e) {
      if (
        dropdownRef.current && !dropdownRef.current.contains(e.target) &&
        triggerRef.current && !triggerRef.current.contains(e.target)
      ) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [isOpen])

  if (disabled) {
    return <span className={`${styles.typeBadge} ${t.cls}`}>{t.label}</span>
  }

  return (
    <div className={styles.typeSelectWrap}>
      <button
        ref={triggerRef}
        className={`${styles.typeBadge} ${t.cls} ${styles.typeBadgeClickable}`}
        onClick={() => setIsOpen(!isOpen)}
        title="Clique para alterar tipo"
      >
        {t.label} ▾
      </button>
      {isOpen && dropdownPos && createPortal(
        <div
          ref={dropdownRef}
          className={styles.typeDropdown}
          style={{
            position: 'fixed',
            top: dropdownPos.top,
            left: dropdownPos.left,
            width: dropdownPos.width,
            zIndex: 9999,
          }}
        >
          {types.map((type) => {
            const ti = typeMap[type]
            return (
              <button
                key={type}
                className={`${styles.typeOption} ${type === value ? styles.typeOptionActive : ''}`}
                onClick={() => {
                  if (type !== value) onChange(type)
                  setIsOpen(false)
                }}
              >
                <span className={`${styles.typeDot} ${ti.cls}`} />
                {ti.label}
              </button>
            )
          })}
        </div>,
        document.body
      )}
    </div>
  )
}

const TABS = [
  { key: 'all', label: 'TODOS' },
  { key: 'income', label: 'ENTRADAS' },
  { key: 'fixo', label: 'FIXOS' },
  { key: 'investimento', label: 'INVESTIMENTOS' },
]

/** Summary totals bar below the table */
function RecurringTotals({ data, activeTab }) {
  const totals = useMemo(() => {
    if (!data) return null
    const computeGroup = (items) => {
      let expected = 0, actual = 0, count = 0, paid = 0, pending = 0
      for (const item of items) {
        if (item.is_skipped) continue
        expected += item.expected || 0
        actual += item.actual || 0
        count++
        if (item.status === 'Pago') paid++
        else if (item.status !== 'Pulado') pending++
      }
      return { expected, actual, count, paid, pending }
    }

    if (activeTab === 'all') {
      const income = computeGroup(data.income || [])
      const fixo = computeGroup(data.fixo || [])
      const invest = computeGroup(data.investimento || [])
      return { income, fixo, invest, isAll: true }
    }

    const items = data[activeTab] || []
    return { single: computeGroup(items), isAll: false, tab: activeTab }
  }, [data, activeTab])

  if (!totals) return null

  if (totals.isAll) {
    const { income, fixo, invest } = totals
    // Use dynamic savings target (20% of income) when it exceeds template total
    const dynamicTarget = data?.savings_target_amount ?? 0
    const investExpected = Math.max(invest.expected, dynamicTarget)
    return (
      <div className={styles.totalsBar}>
        <TotalRow label="Entradas" expected={income.expected} actual={income.actual} paid={income.paid} pending={income.pending} color="var(--color-green)" isIncome />
        <TotalRow label="Fixos" expected={fixo.expected} actual={fixo.actual} paid={fixo.paid} pending={fixo.pending} color="var(--color-red)" />
        <TotalRow label="Investimentos" expected={investExpected} actual={invest.actual} paid={invest.paid} pending={invest.pending} color="#6366f1" hint={investExpected > invest.expected ? `(meta ${data?.savings_target_pct ?? 20}%)` : null} />
        <div className={styles.totalsDivider} />
        <div className={styles.totalsNet}>
          <span className={styles.totalsNetLabel}>SOBRA PROJETADA</span>
          <span
            className={styles.totalsNetValue}
            style={{ color: income.expected - fixo.expected - investExpected >= 0 ? 'var(--color-green)' : 'var(--color-red)' }}
          >
            R$ {fmt(income.expected - fixo.expected - investExpected)}
          </span>
          <span className={styles.totalsNetHint}>entradas - fixos - invest (sem cartao/variavel)</span>
        </div>
      </div>
    )
  }

  const { single, tab } = totals
  const isIncome = tab === 'income'
  const label = tab === 'income' ? 'Entradas' : tab === 'fixo' ? 'Fixos' : 'Investimentos'
  const color = tab === 'income' ? 'var(--color-green)' : tab === 'fixo' ? 'var(--color-red)' : '#6366f1'
  // For investimento tab, use dynamic target as expected
  const expected = tab === 'investimento' ? Math.max(single.expected, data?.savings_target_amount ?? 0) : single.expected

  return (
    <div className={styles.totalsBar}>
      <TotalRow label={label} expected={expected} actual={single.actual} paid={single.paid} pending={single.pending} color={color} isIncome={isIncome} />
    </div>
  )
}

function TotalRow({ label, expected, actual, paid, pending, color, isIncome, hint }) {
  return (
    <div className={styles.totalsRow}>
      <span className={styles.totalsLabel} style={{ color }}>{label}</span>
      <span className={styles.totalsExpected}>
        Esperado: <strong>R$ {fmt(expected)}</strong>{hint ? <span style={{ opacity: 0.6, marginLeft: 4 }}>{hint}</span> : null}
      </span>
      <span className={styles.totalsActual}>
        {isIncome ? 'Recebido' : 'Pago'}: <strong style={{ color: actual > 0 ? color : 'var(--color-text-secondary)' }}>R$ {fmt(actual)}</strong>
      </span>
      <span className={styles.totalsStatus}>
        {paid > 0 && <span className={styles.totalsPaid}>{paid} pago{paid > 1 ? 's' : ''}</span>}
        {pending > 0 && <span className={styles.totalsPending}>{pending} pendente{pending > 1 ? 's' : ''}</span>}
      </span>
    </div>
  )
}


function RecurringSection() {
  const { selectedMonth } = useMonth()
  const { invalidateAll } = useInvalidateAnalytics()
  const [activeTab, setActiveTab] = useState('all')
  const [showAddForm, setShowAddForm] = useState(false)

  // --- API actions ---

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

  // --- Column definitions (with edit/actions) ---
  const recurringColumns = useMemo(() => [
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
            placeholder="\u2014"
            color="var(--color-text-secondary)"
          />
        )
      },
    },
    {
      accessorKey: 'name',
      header: 'ITEM',
      minSize: 140,
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
      accessorKey: 'template_type',
      header: 'TIPO',
      size: 100,
      cell: ({ getValue, row }) => {
        const item = row.original
        return (
          <TypeSelector
            value={getValue()}
            onChange={(newType) => handleUpdateItem(item.mapping_id, 'template_type', newType)}
            disabled={item.is_skipped}
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
      cell: ({ getValue, row }) => {
        const val = getValue()
        if (val === 0) return <span style={{ color: 'var(--color-text-secondary)' }}>{'\u2014'}</span>
        return <AmountCell value={val} positive={row.original.template_type === 'Income'} />
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
      header: 'TRANSAÇÃO',
      minSize: 220,
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
          <div className={styles.actions}>
            {item.is_skipped ? (
              <button
                className={styles.actionBtn}
                onClick={() => handleUnskip(item.mapping_id)}
                title="Restaurar item"
              >
                {'\u21ba'}
              </button>
            ) : (
              <button
                className={styles.actionBtn}
                onClick={() => handleSkip(item.mapping_id)}
                title="Pular este mês"
              >
                {'\u2298'}
              </button>
            )}
            {item.is_custom && (
              <button
                className={`${styles.actionBtn} ${styles.deleteBtn}`}
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

  // --- Data queries ---

  const { data: recData, isLoading: recLoading, error: recError } = useQuery({
    queryKey: ['analytics-recurring', selectedMonth],
    queryFn: () => api.get(`/analytics/recurring/?month_str=${selectedMonth}`),
    enabled: !!selectedMonth,
  })

  const [reapplying, setReapplying] = useState(false)
  const [autoLinking, setAutoLinking] = useState(false)
  const [autoLinkResult, setAutoLinkResult] = useState(null)

  // Row class for skipped items
  const rowClassName = useCallback((row) => {
    if (row.original.is_skipped) return tableStyles.skippedRow
    return ''
  }, [])

  // Compute tab data
  const tabData = useMemo(() => {
    if (!recData) return []
    switch (activeTab) {
      case 'all':
        return recData.all || []
      case 'income':
        return recData.income || []
      case 'fixo':
        return recData.fixo || []
      case 'investimento':
        return recData.investimento || []
      default:
        return []
    }
  }, [recData, activeTab])

  // Drag-to-reorder handler
  const handleReorder = useCallback(async (newData) => {
    // Optimistic: invalidate after saving to backend
    const orderedIds = newData.map((item) => item.mapping_id)
    try {
      await api.post('/analytics/recurring/reorder/', {
        month_str: selectedMonth,
        ordered_mapping_ids: orderedIds,
      })
      invalidateAll()
    } catch (err) {
      console.error('Failed to reorder:', err)
    }
  }, [selectedMonth, invalidateAll])

  const handleReapplyTemplate = useCallback(async () => {
    if (!confirm('Reaplicar template a este mês? Todos os itens recorrentes serão recriados a partir do template atual.')) return
    setReapplying(true)
    try {
      await api.post('/analytics/recurring/reapply/', { month_str: selectedMonth })
      invalidateAll()
    } catch (err) {
      console.error('Failed to reapply template:', err)
    } finally {
      setReapplying(false)
    }
  }, [selectedMonth, invalidateAll])

  const handleAutoLink = useCallback(async () => {
    setAutoLinking(true)
    setAutoLinkResult(null)
    try {
      const result = await api.post('/analytics/recurring/auto-link/', { month_str: selectedMonth })
      setAutoLinkResult(result)
      invalidateAll()
      // Auto-dismiss after 5 seconds
      setTimeout(() => setAutoLinkResult(null), 5000)
    } catch (err) {
      console.error('Auto-link failed:', err)
      setAutoLinkResult({ linked: 0, error: true })
      setTimeout(() => setAutoLinkResult(null), 4000)
    } finally {
      setAutoLinking(false)
    }
  }, [selectedMonth, invalidateAll])

  if (recLoading) {
    return <div className={styles.loading}>Carregando controle...</div>
  }

  if (recError) {
    return <div className={styles.loading}>Erro ao carregar controle recorrente.</div>
  }

  return (
    <div className={styles.section}>
      {/* Header with title + add button */}
      <div className={styles.header}>
        <h3 className={styles.title}>CONTROLE</h3>
        <div className={styles.headerActions}>
          <button
            className={styles.autoLinkBtn}
            onClick={handleAutoLink}
            disabled={autoLinking}
            title="Vincular automaticamente itens por nome, valor e padrão do mês anterior"
          >
            {autoLinking ? '...' : '⚡ Auto-link'}
          </button>
          <button
            className={styles.reapplyBtn}
            onClick={handleReapplyTemplate}
            disabled={reapplying}
            title="Recriar itens deste mês a partir do template atual"
          >
            {reapplying ? '...' : '↻ Template'}
          </button>
          <button
            className={styles.addBtn}
            onClick={() => setShowAddForm(!showAddForm)}
          >
            {showAddForm ? 'Fechar' : '+ Adicionar'}
          </button>
        </div>
      </div>

      {/* Auto-link result toast */}
      {autoLinkResult && (
        <div className={`${styles.autoLinkToast} ${autoLinkResult.error ? styles.toastError : autoLinkResult.linked > 0 ? styles.toastSuccess : styles.toastNeutral}`}>
          {autoLinkResult.error
            ? 'Erro ao vincular automaticamente.'
            : autoLinkResult.linked > 0
              ? `✓ ${autoLinkResult.linked} de ${autoLinkResult.total_unlinked} itens vinculados automaticamente`
              : 'Nenhum item pôde ser vinculado automaticamente.'
          }
          {autoLinkResult.details?.length > 0 && (
            <span className={styles.toastDetails}>
              {' — '}
              {autoLinkResult.details.map(d => d.name).join(', ')}
            </span>
          )}
        </div>
      )}

      {/* Inline add form */}
      {showAddForm && (
        <AddRecurringForm onClose={() => setShowAddForm(false)} />
      )}

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

      {/* Tab content */}
      <div className={styles.tabContent}>
        <VaultTable
          columns={recurringColumns}
          data={tabData || []}
          emptyMessage="Nenhum item recorrente."
          searchable={false}
          maxHeight={450}
          rowClassName={rowClassName}
          draggable
          onReorder={handleReorder}
        />
        <RecurringTotals data={recData} activeTab={activeTab} />
      </div>
    </div>
  )
}

export default RecurringSection
