import { useCallback, useState, useMemo, useRef, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useMonth } from '../context/MonthContext'
import useInvalidateAnalytics from '../hooks/useInvalidateAnalytics'
import api from '../api/client'
import MetricCard from './MetricCard'
import InlineEdit from './InlineEdit'
import Skeleton from './Skeleton'
import styles from './MetricasSection.module.css'

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

const SAUDE_COLORS = {
  good: 'var(--color-green)',
  warning: 'var(--color-orange)',
  danger: 'var(--color-red)',
}

const STORAGE_KEY = 'vault-metricas-order'

const FALLBACK_ORDER = [
  'entradas_atuais', 'entradas_projetadas', 'a_entrar', 'a_pagar',
  'dias_fechamento', 'gastos_atuais', 'gastos_projetados', 'gastos_fixos',
  'gastos_variaveis', 'diario_max', 'fatura_master', 'fatura_visa',
  'parcelas', 'saldo_projetado', 'saude',
]

function buildCards(data) {
  const fechamentoValue = data.is_current_month
    ? `${data.dias_fechamento} dias`
    : '\u2014'
  const fechamentoSub = data.is_current_month
    ? 'ate o fechamento'
    : 'mes encerrado'

  const cards = {
    entradas_atuais: {
      label: 'ENTRADAS ATUAIS',
      value: `R$ ${fmt(data.entradas_atuais)}`,
      subtitle: 'recebido no mes',
      color: 'var(--color-green)',
    },
    entradas_projetadas: {
      label: 'ENTRADAS PROJETADAS',
      value: `R$ ${fmt(data.entradas_projetadas)}`,
      subtitle: 'receita esperada',
      color: '#6ee7b7',
    },
    gastos_atuais: {
      label: 'GASTOS ATUAIS',
      value: `R$ ${fmt(data.gastos_atuais)}`,
      subtitle: 'gasto total no mes',
      color: 'var(--color-red)',
    },
    gastos_projetados: {
      label: 'GASTOS PROJETADOS',
      value: `R$ ${fmt(data.gastos_projetados)}`,
      subtitle: 'despesa esperada',
      color: '#fca5a5',
    },
    gastos_fixos: {
      label: 'GASTOS FIXOS',
      value: `R$ ${fmt(data.gastos_fixos)}`,
      subtitle: 'fixos pagos',
      color: 'var(--color-red)',
    },
    gastos_variaveis: {
      label: 'GASTOS VARIAVEIS',
      value: `R$ ${fmt(data.gastos_variaveis)}`,
      subtitle: 'variaveis gastos',
      color: 'var(--color-orange)',
    },
    fatura_master: {
      label: 'FATURA MASTER',
      value: `R$ ${fmt(data.fatura_master)}`,
      subtitle: 'mastercard total',
      color: 'var(--color-red)',
    },
    fatura_visa: {
      label: 'FATURA VISA',
      value: `R$ ${fmt(data.fatura_visa)}`,
      subtitle: 'visa total',
      color: 'var(--color-red)',
    },
    parcelas: {
      label: 'PARCELAS',
      value: `R$ ${fmt(data.parcelas)}`,
      subtitle: 'parcelamentos',
      color: 'var(--color-orange)',
    },
    a_entrar: {
      label: 'A ENTRAR',
      value: `R$ ${fmt(data.a_entrar)}`,
      subtitle: data.a_entrar > 0 ? 'receita pendente' : 'tudo recebido',
      color: 'var(--color-green)',
    },
    a_pagar: {
      label: 'A PAGAR',
      value: `R$ ${fmt(data.a_pagar)}`,
      subtitle: data.a_pagar > 0 ? 'despesa pendente' : 'tudo pago',
      color: data.a_pagar > 0 ? 'var(--color-red)' : 'var(--color-green)',
    },
    saldo_projetado: {
      label: 'SALDO PROJETADO',
      value: `R$ ${fmt(data.saldo_projetado)}`,
      subtitle: data.balance_override != null
        ? 'baseado no saldo'
        : data.prev_month_saldo != null
          ? 'cascata do mes anterior'
          : 'calculado',
      color: data.saldo_projetado >= 0 ? 'var(--color-green)' : 'var(--color-red)',
    },
    dias_fechamento: {
      label: 'DIAS ATE FECHAMENTO',
      value: fechamentoValue,
      subtitle: fechamentoSub,
      color: '#6366f1',
    },
    diario_max: {
      label: 'GASTO DIARIO MAX',
      value: `R$ ${fmt(data.diario_recomendado)}`,
      subtitle: 'recomendado por dia',
      color: data.diario_recomendado >= 0 ? '#10b981' : 'var(--color-red)',
    },
    saude: {
      label: 'SAUDE DO MES',
      value: data.saude,
      color: SAUDE_COLORS[data.saude_level] || 'var(--color-text)',
    },
  }

  // Add custom metric cards from API response
  if (data.custom_metrics) {
    for (const cm of data.custom_metrics) {
      cards[cm.card_id] = {
        label: cm.label,
        value: cm.value,
        subtitle: cm.subtitle,
        color: cm.color,
        isCustom: true,
        customId: cm.id,
      }
    }
  }

  return cards
}

/* ── Helper to persist order + hidden to backend (debounced, flushes on unmount) ── */
function useDebouncedSave(selectedMonth) {
  const timer = useRef(null)
  const pendingSave = useRef(null)

  const flush = useCallback(() => {
    if (timer.current) {
      clearTimeout(timer.current)
      timer.current = null
    }
    if (pendingSave.current) {
      api.post('/analytics/metricas/order/', pendingSave.current)
      pendingSave.current = null
    }
  }, [])

  // Flush on unmount or month change
  useEffect(() => flush, [selectedMonth, flush])

  const save = useCallback((order, hidden) => {
    clearTimeout(timer.current)
    pendingSave.current = {
      month_str: selectedMonth,
      card_order: order,
      hidden_cards: hidden,
    }
    timer.current = setTimeout(() => {
      if (pendingSave.current) {
        api.post('/analytics/metricas/order/', pendingSave.current)
        pendingSave.current = null
      }
    }, 400)
  }, [selectedMonth])

  return save
}

function MetricasSection() {
  const { selectedMonth } = useMonth()
  const queryClient = useQueryClient()
  const { invalidateMetricas, invalidateMetricasOrder, invalidateProjection } = useInvalidateAnalytics()

  const [cardOrder, setCardOrder] = useState(FALLBACK_ORDER)
  const [hiddenCards, setHiddenCards] = useState([])
  const [dragId, setDragId] = useState(null)
  const [overId, setOverId] = useState(null)
  const [showAddCard, setShowAddCard] = useState(false)
  const [showHidden, setShowHidden] = useState(false)
  const [addingCard, setAddingCard] = useState(false)
  const [deletingCard, setDeletingCard] = useState(null)
  const dragNode = useRef(null)

  const debouncedSave = useDebouncedSave(selectedMonth)

  // Metricas data (values)
  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics-metricas', selectedMonth],
    queryFn: () => api.get(`/analytics/metricas/?month_str=${selectedMonth}`),
    enabled: !!selectedMonth,
  })

  // Card order config (from backend)
  const { data: orderConfig } = useQuery({
    queryKey: ['metricas-order', selectedMonth],
    queryFn: () => api.get(`/analytics/metricas/order/?month_str=${selectedMonth}`),
    enabled: !!selectedMonth,
  })

  // Custom metric options (categories list for add form)
  const { data: customOptions } = useQuery({
    queryKey: ['metricas-custom-options'],
    queryFn: () => api.get('/analytics/metricas/custom/'),
    staleTime: 60000,
  })

  // Sync card order + hidden from server
  useEffect(() => {
    if (orderConfig?.card_order) {
      setCardOrder(orderConfig.card_order)
      setHiddenCards(orderConfig.hidden_cards || [])
    }
  }, [orderConfig])

  // Migrate localStorage order on first load if no server override exists
  useEffect(() => {
    if (orderConfig && !orderConfig.has_month_override) {
      const localOrder = localStorage.getItem(STORAGE_KEY)
      if (localOrder) {
        try {
          const parsed = JSON.parse(localOrder)
          if (Array.isArray(parsed) && parsed.length > 0) {
            api.post('/analytics/metricas/make-default/', { card_order: parsed, hidden_cards: [] })
            localStorage.removeItem(STORAGE_KEY)
          }
        } catch {}
      }
    }
  }, [orderConfig])

  const handleSaveBalance = useCallback(async (newBalance) => {
    try {
      await api.post('/analytics/balance/', {
        month_str: selectedMonth,
        balance: newBalance,
      })
      invalidateMetricas()
      invalidateProjection()
    } catch (err) {
      console.error('Failed to save balance:', err)
    }
  }, [selectedMonth, invalidateMetricas, invalidateProjection])

  const cards = useMemo(() => (data ? buildCards(data) : null), [data])

  /* ── Drag handlers ── */
  const handleDragStart = useCallback((e, id) => {
    setDragId(id)
    dragNode.current = e.currentTarget
    e.currentTarget.style.opacity = '0.4'
    e.dataTransfer.effectAllowed = 'move'
  }, [])

  const handleDragEnd = useCallback((e) => {
    e.currentTarget.style.opacity = '1'
    setDragId(null)
    setOverId(null)
    dragNode.current = null
  }, [])

  const handleDragOver = useCallback((e, id) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setOverId(id)
  }, [])

  const handleDragLeave = useCallback(() => {
    setOverId(null)
  }, [])

  const handleDrop = useCallback((e, targetId) => {
    e.preventDefault()
    if (!dragId || dragId === targetId) {
      setOverId(null)
      return
    }
    setCardOrder((prev) => {
      const next = [...prev]
      const fromIdx = next.indexOf(dragId)
      const toIdx = next.indexOf(targetId)
      next.splice(fromIdx, 1)
      next.splice(toIdx, 0, dragId)
      debouncedSave(next, hiddenCards)
      return next
    })
    setOverId(null)
  }, [dragId, hiddenCards, debouncedSave])

  /* ── Hide / Show card ── */
  const handleHideCard = useCallback((cardId) => {
    setCardOrder((prev) => {
      const next = prev.filter((id) => id !== cardId)
      const newHidden = [...hiddenCards, cardId]
      setHiddenCards(newHidden)
      debouncedSave(next, newHidden)
      return next
    })
  }, [hiddenCards, debouncedSave])

  const handleShowCard = useCallback((cardId) => {
    setHiddenCards((prev) => {
      const newHidden = prev.filter((id) => id !== cardId)
      const newOrder = [...cardOrder, cardId]
      setCardOrder(newOrder)
      debouncedSave(newOrder, newHidden)
      return newHidden
    })
  }, [cardOrder, debouncedSave])

  const handleResetOrder = useCallback(() => {
    const defaultOrder = orderConfig?.global_default_order || FALLBACK_ORDER
    const defaultHidden = orderConfig?.global_hidden_cards || []
    setCardOrder(defaultOrder)
    setHiddenCards(defaultHidden)
    api.post('/analytics/metricas/order/', {
      month_str: selectedMonth,
      card_order: defaultOrder,
      hidden_cards: defaultHidden,
    })
  }, [orderConfig, selectedMonth])

  const handleMakeDefault = useCallback(async () => {
    await api.post('/analytics/metricas/make-default/', {
      card_order: cardOrder,
      hidden_cards: hiddenCards,
    })
    invalidateMetricasOrder()
  }, [cardOrder, hiddenCards, invalidateMetricasOrder])

  const handleToggleLock = useCallback(async () => {
    const newLocked = !orderConfig?.is_locked
    await api.post('/analytics/metricas/lock/', {
      month_str: selectedMonth,
      locked: newLocked,
    })
    invalidateMetricasOrder()
  }, [selectedMonth, orderConfig, invalidateMetricasOrder])

  const handleAddCustomMetric = useCallback(async (metricType, categoryId, categoryName, label, color) => {
    setAddingCard(true)
    try {
      await api.post('/analytics/metricas/custom/', {
        metric_type: metricType,
        label: label || `${metricType === 'category_total' ? 'GASTO' : 'RESTANTE'} ${categoryName}`.toUpperCase(),
        config: { category_id: categoryId },
        color: color || 'var(--color-accent)',
      })
      invalidateMetricas()
      invalidateMetricasOrder()
      queryClient.invalidateQueries({ queryKey: ['metricas-custom-options'] })
      setShowAddCard(false)
    } catch (err) {
      console.error('Failed to add custom metric:', err)
    } finally {
      setAddingCard(false)
    }
  }, [invalidateMetricas, invalidateMetricasOrder, queryClient])

  const handleDeleteCustomMetric = useCallback(async (customId) => {
    setDeletingCard(customId)
    try {
      await api.delete('/analytics/metricas/custom/', { id: customId })
      invalidateMetricas()
      invalidateMetricasOrder()
      queryClient.invalidateQueries({ queryKey: ['metricas-custom-options'] })
    } catch (err) {
      console.error('Failed to delete custom metric:', err)
    } finally {
      setDeletingCard(null)
    }
  }, [invalidateMetricas, invalidateMetricasOrder, queryClient])

  if (isLoading) return (
    <div className={styles.section}>
      <div className={styles.balanceRow}>
        <span className={styles.balanceLabel}>SALDO EM CONTA</span>
      </div>
      <h3 className={styles.title}>METRICAS</h3>
      <Skeleton variant="card" count={15} />
    </div>
  )
  if (error) return <div className={styles.error}>Erro ao carregar metricas</div>
  if (!data || !cards) return null

  const globalDefault = orderConfig?.global_default_order || FALLBACK_ORDER
  const globalHidden = orderConfig?.global_hidden_cards || []
  const isCustomOrder = (
    JSON.stringify(cardOrder) !== JSON.stringify(globalDefault) ||
    JSON.stringify(hiddenCards) !== JSON.stringify(globalHidden)
  )
  const isLocked = orderConfig?.is_locked || false

  return (
    <div className={styles.section}>
      {/* Balance input */}
      <div className={styles.balanceRow}>
        <span className={styles.balanceLabel}>SALDO EM CONTA</span>
        {data.is_current_month ? (
          <InlineEdit
            value={data.balance_override}
            onSave={handleSaveBalance}
            prefix="R$"
            color={
              data.balance_override != null
                ? data.balance_override >= 0
                  ? 'var(--color-green)'
                  : 'var(--color-red)'
                : undefined
            }
            placeholder={
              data.prev_month_saldo != null
                ? `proj. anterior: R$ ${fmt(data.prev_month_saldo)}`
                : 'clique para informar'
            }
          />
        ) : (
          <span
            className={styles.balanceAuto}
            style={{
              color: data.prev_month_saldo != null
                ? data.prev_month_saldo >= 0
                  ? 'var(--color-green)'
                  : 'var(--color-red)'
                : 'var(--color-text-secondary)',
            }}
          >
            {data.prev_month_saldo != null
              ? `R$ ${fmt(data.prev_month_saldo)}`
              : '—'
            }
          </span>
        )}
        {!data.is_current_month && data.prev_month_saldo != null && (
          <span className={styles.balanceHint}>saldo projetado anterior</span>
        )}
      </div>

      <div className={styles.titleRow}>
        <h3 className={styles.title}>METRICAS</h3>
        <div className={styles.titleActions}>
          <button
            className={`${styles.lockBtn} ${isLocked ? styles.lockBtnActive : ''}`}
            onClick={handleToggleLock}
            title={isLocked ? 'Destravar ordem deste mes' : 'Travar ordem deste mes'}
          >
            {isLocked ? '🔒' : '🔓'}
          </button>
          {isCustomOrder && (
            <button className={styles.actionBtn} onClick={handleResetOrder} title="Resetar para ordem padrao">
              ↺ Reset
            </button>
          )}
          {isCustomOrder && (
            <button className={styles.actionBtn} onClick={handleMakeDefault} title="Tornar esta ordem o padrao para todos os meses desbloqueados">
              ⭐ Tornar Padrão
            </button>
          )}
          <button
            className={styles.addBtn}
            onClick={() => setShowAddCard(!showAddCard)}
            title="Adicionar card personalizado"
          >
            {showAddCard ? '✕' : '+ Card'}
          </button>
        </div>
      </div>

      {/* Add custom card form */}
      {showAddCard && (
        <AddCardForm
          categories={customOptions?.available_categories || []}
          onAdd={handleAddCustomMetric}
          onClose={() => setShowAddCard(false)}
          saving={addingCard}
        />
      )}

      <div className={styles.grid}>
        {cardOrder.map((id) => {
          const c = cards[id]
          if (!c) return null
          const isDragging = dragId === id
          const isOver = overId === id && dragId !== id
          return (
            <div
              key={id}
              className={`${styles.draggable} ${isDragging ? styles.dragging : ''} ${isOver ? styles.dragOver : ''}`}
              draggable
              onDragStart={(e) => handleDragStart(e, id)}
              onDragEnd={handleDragEnd}
              onDragOver={(e) => handleDragOver(e, id)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, id)}
            >
              <div className={styles.dragHandle}>⠿</div>
              <button
                className={styles.hideBtn}
                onClick={(e) => {
                  e.stopPropagation()
                  if (c.isCustom) {
                    handleDeleteCustomMetric(c.customId)
                  } else {
                    handleHideCard(id)
                  }
                }}
                disabled={c.isCustom && deletingCard === c.customId}
                title={c.isCustom ? 'Remover card' : 'Ocultar card'}
              >
                ✕
              </button>
              <MetricCard
                label={c.label}
                value={c.value}
                subtitle={c.subtitle}
                color={c.color}
              />
            </div>
          )
        })}
      </div>

      {/* Hidden cards row */}
      {hiddenCards.length > 0 && (
        <div className={styles.hiddenSection}>
          <button
            className={styles.hiddenToggle}
            onClick={() => setShowHidden(!showHidden)}
          >
            {showHidden ? '▾' : '▸'} {hiddenCards.length} oculto{hiddenCards.length > 1 ? 's' : ''}
          </button>
          {showHidden && (
            <div className={styles.hiddenList}>
              {hiddenCards.map((id) => {
                const c = cards[id]
                const label = c ? c.label : id
                return (
                  <button
                    key={id}
                    className={styles.hiddenChip}
                    onClick={() => handleShowCard(id)}
                    title="Clique para mostrar"
                  >
                    + {label}
                  </button>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/* ── Inline Add Card Form ── */
function AddCardForm({ categories, onAdd, onClose, saving }) {
  const [metricType, setMetricType] = useState('category_total')
  const [categoryId, setCategoryId] = useState('')
  const [label, setLabel] = useState('')

  const selectedCat = categories.find((c) => c.id === categoryId)

  function handleSubmit(e) {
    e.preventDefault()
    if (!categoryId) return
    const autoLabel = `${metricType === 'category_total' ? 'GASTO' : 'RESTANTE'} ${selectedCat?.name || ''}`.toUpperCase()
    const color = metricType === 'category_remaining' ? 'var(--color-green)' : 'var(--color-accent)'
    onAdd(metricType, categoryId, selectedCat?.name || '', label || autoLabel, color)
  }

  return (
    <form className={styles.addCardForm} onSubmit={handleSubmit}>
      <select
        className={styles.addCardSelect}
        value={metricType}
        onChange={(e) => setMetricType(e.target.value)}
      >
        <option value="category_total">Gasto por Categoria</option>
        <option value="category_remaining">Orçamento Restante</option>
      </select>
      <select
        className={styles.addCardSelect}
        value={categoryId}
        onChange={(e) => setCategoryId(e.target.value)}
      >
        <option value="">Selecionar categoria...</option>
        {categories.map((c) => (
          <option key={c.id} value={c.id}>{c.name} ({c.category_type})</option>
        ))}
      </select>
      <input
        className={styles.addCardInput}
        type="text"
        placeholder="Label (auto)"
        value={label}
        onChange={(e) => setLabel(e.target.value)}
      />
      <button
        className={styles.addCardSaveBtn}
        type="submit"
        disabled={saving || !categoryId}
      >
        {saving ? '...' : 'Salvar'}
      </button>
      <button
        className={styles.addCardCancelBtn}
        type="button"
        onClick={onClose}
      >
        Cancelar
      </button>
    </form>
  )
}

export default MetricasSection
