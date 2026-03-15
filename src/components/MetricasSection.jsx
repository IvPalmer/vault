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

const SAUDE_EXPLANATIONS = {
  good: 'Gastos abaixo do projetado, boa reserva.',
  warning: 'Gastos se aproximando do limite projetado.',
  danger: 'Gastos acima do projetado ou saldo negativo.',
}

const STORAGE_KEY = 'vault-metricas-order'

const FALLBACK_ORDER = [
  'entradas_atuais', 'entradas_projetadas', 'a_entrar', 'a_pagar',
  'dias_fechamento', 'gastos_atuais', 'gastos_projetados', 'gastos_fixos',
  'gastos_invest', 'gastos_variaveis', 'diario_max',
  'parcelas', 'saldo_projetado', 'saude', 'meta_poupanca',
]

// Group definitions — cards are visually grouped under these headings
const CARD_GROUPS = [
  {
    key: 'receitas',
    label: 'RECEITAS',
    color: 'var(--color-green)',
    cards: ['entradas_atuais', 'entradas_projetadas', 'a_entrar'],
  },
  {
    key: 'despesas',
    label: 'DESPESAS',
    color: 'var(--color-red)',
    cards: ['gastos_atuais', 'gastos_projetados', 'gastos_fixos', 'gastos_invest', 'gastos_variaveis', 'a_pagar'],
  },
  {
    key: 'cartoes',
    label: 'CARTOES',
    color: 'var(--color-orange)',
    cards: ['parcelas'],  // fatura cards injected dynamically from fatura_by_card
    dynamic: true,
  },
  {
    key: 'resumo',
    label: 'RESUMO',
    color: '#6366f1',
    cards: ['saldo_projetado', 'diario_max', 'dias_fechamento', 'saude', 'meta_poupanca'],
  },
]

function buildCards(data) {
  const fechamentoValue = data.is_current_month
    ? `${data.dias_fechamento} dias`
    : '\u2014'
  const fechamentoSub = data.is_current_month
    ? 'ate o fechamento'
    : 'mes encerrado'

  const incomeProgress = data.entradas_projetadas > 0
    ? (data.entradas_atuais / data.entradas_projetadas) * 100
    : null
  const expenseProgress = data.gastos_projetados > 0
    ? (data.gastos_atuais / data.gastos_projetados) * 100
    : null

  // Derived values for subtitles
  const fixoExpected = data.fixo_expected_total || 0
  const investExpected = data.invest_expected_total || 0
  const fixoPaid = data.gastos_fixos
  const fixoPending = data.a_pagar_fixo
  const investPending = data.a_pagar_invest || 0
  const faturaTotal = data.fatura_total || 0
  const faturaRemaining = data.fatura_remaining || 0
  const ccForProjection = faturaTotal > 0 ? faturaTotal : (data.parcelas || 0)

  const cards = {
    entradas_atuais: {
      label: 'ENTRADAS ATUAIS',
      value: `R$ ${fmt(data.entradas_atuais)}`,
      subtitle: data.entradas_projetadas > 0
        ? `${Math.round((data.entradas_atuais / data.entradas_projetadas) * 100)}% de R$ ${fmt(data.entradas_projetadas)}`
        : 'recebido no mes',
      color: 'var(--color-green)',
      progress: incomeProgress,
      tooltip: 'Total ja recebido neste mes (salario, freelance, etc). A barra mostra quanto do total esperado ja entrou.',
    },
    entradas_projetadas: {
      label: 'ENTRADAS PROJETADAS',
      value: `R$ ${fmt(data.entradas_projetadas)}`,
      subtitle: `recebido R$ ${fmt(data.entradas_atuais)} + pendente R$ ${fmt(data.a_entrar)}`,
      color: '#6ee7b7',
      tooltip: 'Total de receitas esperadas no mes (Controle > Income). Soma do que ja entrou + o que ainda falta entrar.',
    },
    gastos_atuais: {
      label: 'GASTOS ATUAIS',
      value: `R$ ${fmt(data.gastos_atuais)}`,
      subtitle: data.gastos_projetados > 0
        ? `${Math.round((data.gastos_atuais / data.gastos_projetados) * 100)}% de R$ ${fmt(data.gastos_projetados)}`
        : 'gasto total no mes',
      color: 'var(--color-red)',
      progress: expenseProgress,
      tooltip: 'Total de despesas ja realizadas (debitos + cartao). A barra mostra quanto do projetado ja foi gasto.',
    },
    gastos_projetados: {
      label: 'GASTOS PROJETADOS',
      value: `R$ ${fmt(data.gastos_projetados)}`,
      subtitle: `fixo R$ ${fmt(fixoExpected)} + invest R$ ${fmt(investExpected)} + cartao R$ ${fmt(ccForProjection)}`,
      color: '#fca5a5',
      tooltip: `Previsao total de saidas da conta: fixos (R$ ${fmt(fixoExpected)}) + investimentos (R$ ${fmt(investExpected)}) + fatura cartao (R$ ${fmt(ccForProjection)}).`,
    },
    gastos_fixos: {
      label: 'GASTOS FIXOS',
      value: `R$ ${fmt(fixoPaid)}`,
      subtitle: fixoExpected > 0
        ? `pagos de R$ ${fmt(fixoExpected)} esperado`
        : 'pagos ate agora',
      color: 'var(--color-red)',
      progress: fixoExpected > 0 ? (fixoPaid / fixoExpected) * 100 : null,
      tooltip: `Fixos ja pagos: R$ ${fmt(fixoPaid)}. Falta pagar: R$ ${fmt(fixoPending)}. Total esperado: R$ ${fmt(fixoExpected)}.`,
    },
    gastos_invest: {
      label: 'GASTOS INVEST.',
      value: `R$ ${fmt(data.invest_actual || 0)}`,
      subtitle: investExpected > 0
        ? `pagos de R$ ${fmt(investExpected)} esperado`
        : 'investimentos pagos',
      color: '#6366f1',
      progress: investExpected > 0 ? ((data.invest_actual || 0) / investExpected) * 100 : null,
      tooltip: `Investimentos pagos: R$ ${fmt(data.invest_actual || 0)}. Pendente: R$ ${fmt(investPending)}. Total esperado: R$ ${fmt(investExpected)}.`,
    },
    gastos_variaveis: {
      label: 'GASTOS VARIAVEIS',
      value: `R$ ${fmt(data.gastos_variaveis_checking ?? data.gastos_variaveis)}`,
      subtitle: 'exceto fixos, investimentos e cartão',
      color: 'var(--color-orange)',
      tooltip: 'Gastos variáveis na conta corrente (PIX, boletos, etc). CC variável já está no cartão.',
    },
    // Dynamic per-card fatura entries are injected below after cards object is built
    parcelas: {
      label: 'PARCELAS',
      value: `R$ ${fmt(data.parcelas)}`,
      subtitle: faturaTotal > 0
        ? `${Math.round((data.parcelas / faturaTotal) * 100)}% da fatura de R$ ${fmt(faturaTotal)}`
        : 'parcelamentos projetados',
      color: 'var(--color-orange)',
      tooltip: `Parcelas de compras parceladas na fatura deste mes. Sao parte da fatura (R$ ${fmt(faturaTotal)}), nao um custo extra.`,
    },
    a_entrar: {
      label: 'A ENTRAR',
      value: `R$ ${fmt(data.a_entrar)}`,
      subtitle: data.a_entrar > 0
        ? `falta de R$ ${fmt(data.entradas_projetadas)} esperado`
        : 'tudo recebido',
      color: 'var(--color-green)',
      tooltip: 'Receitas pendentes: itens no Controle ainda sem transacao vinculada. Projetadas - Atuais = A Entrar.',
    },
    a_pagar: {
      label: 'A PAGAR',
      value: `R$ ${fmt(data.a_pagar)}`,
      subtitle: data.a_pagar > 0
        ? [
            fixoPending > 0 && `fixo R$ ${fmt(fixoPending)}`,
            investPending > 0 && `invest R$ ${fmt(investPending)}`,
            faturaRemaining > 0 && `fatura R$ ${fmt(faturaRemaining)}`,
          ].filter(Boolean).join(' + ') || 'tudo pago'
        : 'tudo pago',
      color: data.a_pagar > 0 ? 'var(--color-red)' : 'var(--color-green)',
      tooltip: `Ainda vai sair da conta: fixos (R$ ${fmt(fixoPending)}) + investimentos (R$ ${fmt(investPending)}) + fatura cartao (R$ ${fmt(faturaRemaining)}).`,
    },
    saldo_projetado: {
      label: 'SALDO PROJETADO',
      value: `${data.saldo_projetado < 0 ? '-' : ''}R$ ${fmt(data.saldo_projetado)}`,
      subtitle: data.balance_override != null
        ? `R$ ${fmt(data.balance_override)} + R$ ${fmt(data.a_entrar)} - R$ ${fmt(data.a_pagar)}`
        : data.balance_anchor_value != null
          ? `R$ ${fmt(data.balance_anchor_value)} (Pluggy) + R$ ${fmt(data.a_entrar)} - R$ ${fmt(data.a_pagar)}`
          : !data.is_current_month && data.checking_balance_eom != null
            ? 'saldo real da conta'
            : data.prev_month_saldo != null
              ? 'cascata do mes anterior'
              : 'calculado',
      color: data.saldo_projetado >= 0 ? 'var(--color-green)' : 'var(--color-red)',
      tooltip: data.balance_override != null
        ? `Saldo informado (R$ ${fmt(data.balance_override)}) + receitas pendentes (R$ ${fmt(data.a_entrar)}) - despesas pendentes (R$ ${fmt(data.a_pagar)}).`
        : data.balance_anchor_value != null
          ? `Saldo Pluggy (R$ ${fmt(data.balance_anchor_value)}, ${data.balance_anchor_date}) + receitas pendentes (R$ ${fmt(data.a_entrar)}) - despesas pendentes (R$ ${fmt(data.a_pagar)}).`
          : 'Projecao do saldo no fim do mes. Para meses fechados, usa saldo real do extrato.',
    },
    dias_fechamento: {
      label: 'DIAS ATE FECHAMENTO',
      value: fechamentoValue,
      subtitle: fechamentoSub,
      color: '#6366f1',
      tooltip: 'Dias restantes ate o ultimo dia do mes.',
    },
    diario_max: {
      label: 'GASTO DIARIO MAX',
      value: `${data.diario_recomendado < 0 ? '-' : ''}R$ ${fmt(data.diario_recomendado)}`,
      subtitle: data.dias_fechamento > 0
        ? `por dia nos proximos ${data.dias_fechamento} dias`
        : 'recomendado por dia',
      color: data.diario_recomendado >= 0 ? '#10b981' : 'var(--color-red)',
      tooltip: 'Quanto voce pode gastar por dia sem estourar. Se negativo, voce ja ultrapassou o orcamento.',
    },
    saude: {
      label: 'SAUDE DO MES',
      value: data.saude,
      color: SAUDE_COLORS[data.saude_level] || 'var(--color-text)',
      tooltip: `${SAUDE_EXPLANATIONS[data.saude_level] || 'Sem dados suficientes.'} Baseado em gastos vs projetado e saldo.`,
    },
    meta_poupanca: (() => {
      const achievement = data.savings_rate ?? 0
      const targetAmount = data.savings_target_amount ?? 0
      const investActual = data.invest_actual ?? 0
      const affordable = data.savings_affordable
      const headroom = data.savings_headroom ?? 0
      const fmtR = (v) => `R$ ${Math.abs(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}`

      const investExpected = data.invest_expected_total ?? 0
      const skipped = targetAmount > 0 && investExpected === 0
      const partial = targetAmount > 0 && investExpected > 0 && investExpected < targetAmount * 0.99

      let subtitle
      if (skipped) {
        subtitle = `sem margem (meta ${fmtR(targetAmount)})`
      } else if (partial) {
        subtitle = `${fmtR(investExpected)} de ${fmtR(targetAmount)} possivel`
      } else if (targetAmount > 0) {
        subtitle = `${fmtR(investActual)} de ${fmtR(targetAmount)}`
      } else {
        subtitle = `meta: ${data.savings_target_pct ?? 20}%`
      }

      let color
      if (skipped) color = 'var(--color-text-secondary)'
      else if (achievement >= 100) color = 'var(--color-green)'
      else if (achievement >= 50) color = 'var(--color-orange)'
      else color = 'var(--color-red)'

      const tooltipParts = [
        `Investido: ${fmtR(investActual)} de ${fmtR(targetAmount)} (${data.savings_target_pct}% da renda)`,
        affordable
          ? `Saldo comporta a meta (folga: ${fmtR(headroom)})`
          : `Saldo insuficiente para meta (faltam ${fmtR(Math.abs(headroom))})`
      ]

      return {
        label: 'META POUPANCA',
        value: skipped ? 'PAUSADO' : `${achievement.toFixed(1)}%`,
        subtitle,
        color,
        progress: skipped ? 0 : Math.min(achievement, 100),
        tooltip: tooltipParts.join('. '),
      }
    })(),
  }

  // Add dynamic per-card fatura cards
  if (data.fatura_by_card) {
    for (const [cardName, amount] of Object.entries(data.fatura_by_card)) {
      const key = `fatura_${cardName.toLowerCase().replace(/\s+/g, '_')}`
      cards[key] = {
        label: `FATURA ${cardName.toUpperCase()}`,
        value: `R$ ${fmt(amount)}`,
        subtitle: faturaTotal > 0
          ? `${Math.round((amount / faturaTotal) * 100)}% da fatura total`
          : 'fatura deste mes',
        color: 'var(--color-red)',
        tooltip: `Fatura ${cardName} que vence neste mes (compras do mes anterior + parcelas).`,
      }
    }
  }
  // Sub-cards (additional cards on another bill) — visibility only
  if (data.fatura_sub_cards) {
    for (const [cardName, amount] of Object.entries(data.fatura_sub_cards)) {
      const key = `fatura_${cardName.toLowerCase().replace(/\s+/g, '_')}`
      cards[key] = {
        label: `${cardName.toUpperCase()}`,
        value: `R$ ${fmt(amount)}`,
        subtitle: 'cartão adicional (incluso na fatura)',
        color: 'var(--color-red)',
        tooltip: `Compras de ${cardName} — já incluídas na fatura do cartão principal.`,
      }
    }
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

  const handleAddCustomMetric = useCallback(async (metricType, config, label, color) => {
    setAddingCard(true)
    try {
      await api.post('/analytics/metricas/custom/', {
        metric_type: metricType,
        label,
        config,
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

  // Build visible card set for quick lookup
  const visibleSet = new Set(cardOrder)

  // Collect dynamic fatura card keys from the cards object
  const faturaCardKeys = Object.keys(cards).filter((k) => k.startsWith('fatura_'))

  // Group cards: each group shows its visible cards in cardOrder sequence
  const groupedCards = CARD_GROUPS.map((group) => {
    // For the cartoes group, include dynamic fatura cards
    const groupKeys = group.dynamic
      ? [...faturaCardKeys, ...group.cards]
      : group.cards
    const groupCardIds = groupKeys.filter(
      (id) => cards[id] && !hiddenCards.includes(id)
    )
    // Respect user's drag order within the group, new cards at end
    groupCardIds.sort((a, b) => {
      const ai = cardOrder.indexOf(a)
      const bi = cardOrder.indexOf(b)
      if (ai === -1 && bi === -1) return 0
      if (ai === -1) return 1
      if (bi === -1) return 1
      return ai - bi
    })
    return { ...group, visibleCards: groupCardIds }
  })

  // Custom cards that don't belong to any group
  const allGroupCards = new Set(CARD_GROUPS.flatMap((g) => g.cards))
  faturaCardKeys.forEach((k) => allGroupCards.add(k))
  const groupedCardSet = allGroupCards
  const customCardIds = cardOrder.filter(
    (id) => !groupedCardSet.has(id) && cards[id] && !hiddenCards.includes(id)
  )

  return (
    <div className={styles.section}>
      {/* Balance input */}
      <div className={styles.balanceRow}>
        <span className={styles.balanceLabel}>SALDO EM CONTA</span>
        {data.is_current_month ? (
          data.balance_anchor_value != null ? (
            <>
              <span
                className={styles.balanceAuto}
                style={{ color: data.balance_anchor_value >= 0 ? 'var(--color-green)' : 'var(--color-red)' }}
              >
                R$ {fmt(data.balance_anchor_value)}
              </span>
              <span className={styles.balanceHint}>Pluggy {data.balance_anchor_date}</span>
            </>
          ) : (
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
          )
        ) : data.is_future && data.projected_balance != null ? (
          <>
            <span
              className={styles.balanceAuto}
              style={{ color: data.projected_balance >= 0 ? 'var(--color-green)' : 'var(--color-red)' }}
            >
              {data.projected_balance < 0 ? '-' : ''}R$ {fmt(data.projected_balance)}
            </span>
            <span className={styles.balanceHint}>projetado do mes anterior</span>
          </>
        ) : (
          <>
            <span
              className={styles.balanceAuto}
              style={{
                color: (data.checking_balance_eom ?? data.prev_month_saldo) != null
                  ? (data.checking_balance_eom ?? data.prev_month_saldo) >= 0
                    ? 'var(--color-green)'
                    : 'var(--color-red)'
                  : 'var(--color-text-secondary)',
              }}
            >
              {data.checking_balance_eom != null
                ? `R$ ${fmt(data.checking_balance_eom)}`
                : data.prev_month_saldo != null
                  ? `R$ ${fmt(data.prev_month_saldo)}`
                  : '\u2014'
              }
            </span>
            {!data.is_current_month && (
              <span className={styles.balanceHint}>
                {data.checking_balance_eom != null ? 'saldo final do mes' : data.prev_month_saldo != null ? 'saldo projetado anterior' : ''}
              </span>
            )}
          </>
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
              Reset
            </button>
          )}
          {isCustomOrder && (
            <button className={styles.actionBtn} onClick={handleMakeDefault} title="Tornar esta ordem o padrao para todos os meses desbloqueados">
              Tornar Padrao
            </button>
          )}
          <button
            className={styles.addBtn}
            onClick={() => setShowAddCard(!showAddCard)}
            title="Adicionar card personalizado"
          >
            {showAddCard ? 'Fechar' : '+ Card'}
          </button>
        </div>
      </div>

      {/* Add custom card form */}
      {showAddCard && (
        <AddCardForm
          categories={customOptions?.available_categories || []}
          templates={customOptions?.available_templates || []}
          builtins={customOptions?.available_builtins || []}
          onAdd={handleAddCustomMetric}
          onClose={() => setShowAddCard(false)}
          saving={addingCard}
        />
      )}

      {/* Grouped metric cards */}
      {groupedCards.map((group) => {
        if (group.visibleCards.length === 0) return null
        return (
          <div key={group.key} className={styles.cardGroup}>
            <div className={styles.groupHeader}>
              <span className={styles.groupDot} style={{ background: group.color }} />
              <span className={styles.groupLabel}>{group.label}</span>
            </div>
            <div className={styles.grid}>
              {group.visibleCards.map((id) => {
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
                      <svg width="10" height="10" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                        <path d="M2 2l8 8M10 2l-8 8" />
                      </svg>
                    </button>
                    <MetricCard
                      label={c.label}
                      value={c.value}
                      subtitle={c.subtitle}
                      color={c.color}
                      tooltip={c.tooltip}
                      progress={c.progress}
                    />
                  </div>
                )
              })}
            </div>
          </div>
        )
      })}

      {/* Custom cards (not in any group) */}
      {customCardIds.length > 0 && (
        <div className={styles.cardGroup}>
          <div className={styles.groupHeader}>
            <span className={styles.groupDot} style={{ background: 'var(--color-accent)' }} />
            <span className={styles.groupLabel}>PERSONALIZADOS</span>
          </div>
          <div className={styles.grid}>
            {customCardIds.map((id) => {
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
                  <button
                    className={styles.hideBtn}
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteCustomMetric(c.customId)
                    }}
                    disabled={deletingCard === c.customId}
                    title="Remover card"
                  >
                    <svg width="10" height="10" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                      <path d="M2 2l8 8M10 2l-8 8" />
                    </svg>
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
        </div>
      )}

      {/* Hidden cards row */}
      {hiddenCards.length > 0 && (
        <div className={styles.hiddenSection}>
          <button
            className={styles.hiddenToggle}
            onClick={() => setShowHidden(!showHidden)}
          >
            {showHidden ? '\u25be' : '\u25b8'} {hiddenCards.length} oculto{hiddenCards.length > 1 ? 's' : ''}
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
function AddCardForm({ categories, templates, builtins, onAdd, onClose, saving }) {
  const [metricType, setMetricType] = useState('category_total')
  const [categoryId, setCategoryId] = useState('')
  const [templateId, setTemplateId] = useState('')
  const [builtinKey, setBuiltinKey] = useState('')
  const [label, setLabel] = useState('')

  // Determine which selector to show
  const needsCategory = metricType === 'category_total' || metricType === 'category_remaining'
  const needsTemplate = metricType === 'recurring_item'
  const needsBuiltin = metricType === 'builtin_clone'
  const noSelector = metricType === 'fixo_total' || metricType === 'investimento_total' || metricType === 'income_total'

  const selectedCat = categories.find((c) => c.id === categoryId)
  const selectedTpl = templates.find((t) => t.id === templateId)
  const selectedBuiltin = builtins.find((b) => b.key === builtinKey)

  // Determine if form is valid
  const isValid = noSelector ||
    (needsCategory && categoryId) ||
    (needsTemplate && templateId) ||
    (needsBuiltin && builtinKey)

  function handleSubmit(e) {
    e.preventDefault()
    if (!isValid) return

    let config = {}
    let autoLabel = ''
    let color = 'var(--color-accent)'

    if (needsCategory) {
      config = { category_id: categoryId }
      autoLabel = `${metricType === 'category_total' ? 'GASTO' : 'RESTANTE'} ${selectedCat?.name || ''}`.toUpperCase()
      color = metricType === 'category_remaining' ? 'var(--color-green)' : 'var(--color-accent)'
    } else if (needsTemplate) {
      config = { template_id: templateId }
      autoLabel = (selectedTpl?.name || 'ITEM').toUpperCase()
      color = 'var(--color-accent)'
    } else if (needsBuiltin) {
      config = { builtin_key: builtinKey, subtitle: selectedBuiltin?.subtitle || '' }
      autoLabel = selectedBuiltin?.label || builtinKey.toUpperCase()
      color = 'var(--color-accent)'
    } else if (metricType === 'fixo_total') {
      autoLabel = 'FIXOS PAGOS'
      color = 'var(--color-red)'
    } else if (metricType === 'investimento_total') {
      autoLabel = 'INVESTIMENTOS'
      color = '#6366f1'
    } else if (metricType === 'income_total') {
      autoLabel = 'ENTRADAS CONTROLE'
      color = 'var(--color-green)'
    }

    onAdd(metricType, config, label || autoLabel, color)
  }

  return (
    <form className={styles.addCardForm} onSubmit={handleSubmit}>
      <select
        className={styles.addCardSelect}
        value={metricType}
        onChange={(e) => {
          setMetricType(e.target.value)
          setCategoryId('')
          setTemplateId('')
          setBuiltinKey('')
        }}
      >
        <optgroup label="Categorias">
          <option value="category_total">Gasto por Categoria</option>
          <option value="category_remaining">Orcamento Restante</option>
        </optgroup>
        <optgroup label="Controle (Recorrentes)">
          <option value="fixo_total">Total Gastos Fixos</option>
          <option value="investimento_total">Total Investimentos</option>
          <option value="income_total">Total Entradas</option>
          <option value="recurring_item">Item Recorrente Especifico</option>
        </optgroup>
        <optgroup label="Cards Padrao">
          <option value="builtin_clone">Clonar Card Existente</option>
        </optgroup>
      </select>

      {/* Category selector */}
      {needsCategory && (
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
      )}

      {/* Template selector */}
      {needsTemplate && (
        <select
          className={styles.addCardSelect}
          value={templateId}
          onChange={(e) => setTemplateId(e.target.value)}
        >
          <option value="">Selecionar item...</option>
          {templates.map((t) => (
            <option key={t.id} value={t.id}>{t.name} ({t.template_type})</option>
          ))}
        </select>
      )}

      {/* Builtin card selector */}
      {needsBuiltin && (
        <select
          className={styles.addCardSelect}
          value={builtinKey}
          onChange={(e) => setBuiltinKey(e.target.value)}
        >
          <option value="">Selecionar card...</option>
          {builtins.map((b) => (
            <option key={b.key} value={b.key}>{b.label}</option>
          ))}
        </select>
      )}

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
        disabled={saving || !isValid}
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
