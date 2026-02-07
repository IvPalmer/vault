import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { createPortal } from 'react-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useMonth } from '../context/MonthContext'
import useInvalidateAnalytics from '../hooks/useInvalidateAnalytics'
import api from '../api/client'
import styles from './TransactionPicker.module.css'

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

/**
 * TransactionPicker — inline dropdown for mapping recurring items to transactions.
 * Supports two match modes:
 *   - manual: select one or many specific transactions (checkbox-style, persistent list)
 *   - category: select a category, auto-match all transactions in it
 *
 * UX principles:
 *   - Clicking a row toggles selection, rows never vanish from the list
 *   - Linked items always shown at top with green styling and checkmarks
 *   - Category mode shows a selectable list of categories with transaction counts
 *   - Clear/unlink button always visible when items are linked
 */
function TransactionPicker({
  categoryId,
  categoryName,
  mappingId,
  currentMatch,
  matchedTransactionId,
  matchedTransactionIds = [],
  matchType,
  matchCount,
  matchMode,
  suggested,
  status,
  onMapped,
}) {
  const { selectedMonth } = useMonth()
  const queryClient = useQueryClient()
  const { invalidateAll } = useInvalidateAnalytics()
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [saving, setSaving] = useState(false)
  const [dropdownPos, setDropdownPos] = useState({ top: 0, left: 0, width: 0 })
  const triggerRef = useRef(null)
  const dropdownRef = useRef(null)
  const inputRef = useRef(null)

  const [sourceFilter, setSourceFilter] = useState('checking') // 'all' | 'checking' | 'credit_card'
  const [sortBy, setSortBy] = useState('relevance') // 'relevance' | 'date' | 'amount' | 'name'

  const isMapped = !!(currentMatch && (status === 'Pago' || status === 'Parcial'))

  // Local view mode — switching tabs is just a UI change, no backend call
  // Only synced from props on initial mount or when dropdown opens
  const [viewMode, setViewMode] = useState(matchMode || 'manual')
  const isCategory = viewMode === 'category'

  // Reset viewMode and source filter to match server state whenever dropdown opens
  useEffect(() => {
    if (isOpen) {
      setViewMode(matchMode || 'manual')
      setSourceFilter('checking')
      setSortBy('relevance')
    }
  }, [isOpen, matchMode])

  // Track linked IDs locally for instant UI feedback
  const [localLinkedIds, setLocalLinkedIds] = useState(
    () => new Set(matchedTransactionIds || [])
  )

  // Sync local state when props change (e.g., after query refetch)
  useEffect(() => {
    setLocalLinkedIds(new Set(matchedTransactionIds || []))
  }, [matchedTransactionIds])

  // Fetch candidates when dropdown opens (manual mode)
  const candidateParam = categoryId
    ? `category_id=${categoryId}`
    : `mapping_id=${mappingId}`
  const { data: candidateData, isLoading: candidatesLoading } = useQuery({
    queryKey: ['mapping-candidates', selectedMonth, categoryId || mappingId],
    queryFn: () =>
      api.get(
        `/analytics/recurring/candidates/?month_str=${selectedMonth}&${candidateParam}`
      ),
    enabled: isOpen && !!selectedMonth && !!(categoryId || mappingId),
    staleTime: 15000,
  })

  // Fetch categories when dropdown opens (category mode)
  const { data: categoryData, isLoading: categoriesLoading } = useQuery({
    queryKey: ['month-categories', selectedMonth],
    queryFn: () =>
      api.get(`/analytics/month-categories/?month_str=${selectedMonth}`),
    enabled: isOpen && !!selectedMonth,
    staleTime: 30000,
  })

  // Position dropdown
  useEffect(() => {
    if (!isOpen || !triggerRef.current) return
    const rect = triggerRef.current.getBoundingClientRect()
    const dropdownWidth = Math.max(480, rect.width)
    let left = rect.left
    if (left + dropdownWidth > window.innerWidth - 16) {
      left = window.innerWidth - dropdownWidth - 16
    }
    if (left < 8) left = 8

    // Check if dropdown would go below viewport
    const dropdownHeight = 420 // estimated max height
    let top = rect.bottom + 2
    if (top + dropdownHeight > window.innerHeight - 16) {
      top = rect.top - dropdownHeight - 2
      if (top < 8) top = 8
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
        setSearch('')
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [isOpen])

  // Focus search when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [isOpen, isCategory])

  // Sort candidates: apply source filter, search, then sort
  const sortedCandidates = useMemo(() => {
    let candidates = candidateData?.candidates || []

    // Apply source filter
    if (sourceFilter !== 'all') {
      candidates = candidates.filter((c) => c.source === sourceFilter)
    }

    // Apply search filter
    if (search) {
      const q = search.toLowerCase()
      candidates = candidates.filter((c) =>
        c.description.toLowerCase().includes(q) ||
        c.account.toLowerCase().includes(q) ||
        c.category.toLowerCase().includes(q) ||
        String(Math.abs(c.amount)).includes(q)
      )
    }

    return [...candidates].sort((a, b) => {
      // Always: linked to THIS mapping first
      const aLinked = localLinkedIds.has(a.id) || a.is_linked ? -2 : 0
      const bLinked = localLinkedIds.has(b.id) || b.is_linked ? -2 : 0
      if (aLinked !== bLinked) return aLinked - bLinked
      // Always: globally linked to bottom
      const aGlobal = a.is_globally_linked ? 1 : 0
      const bGlobal = b.is_globally_linked ? 1 : 0
      if (aGlobal !== bGlobal) return aGlobal - bGlobal
      // Then apply user sort
      switch (sortBy) {
        case 'date':
          return b.date.localeCompare(a.date) // newest first
        case 'amount':
          return Math.abs(b.amount) - Math.abs(a.amount) // largest first
        case 'name':
          return a.description.localeCompare(b.description)
        default: // 'relevance' — backend order (amount match)
          return 0
      }
    })
  }, [candidateData, search, localLinkedIds, sourceFilter, sortBy])

  const invalidateWithCandidates = useCallback(() => {
    invalidateAll()
    queryClient.invalidateQueries({ queryKey: ['mapping-candidates'] })
    queryClient.invalidateQueries({ queryKey: ['month-categories'] })
  }, [invalidateAll, queryClient])

  // Map (add) a transaction — optimistic update
  const handleToggleTransaction = useCallback(
    async (txn) => {
      const isCurrentlyLinked = localLinkedIds.has(txn.id)
      setSaving(true)

      // Optimistic: update local state immediately
      setLocalLinkedIds((prev) => {
        const next = new Set(prev)
        if (isCurrentlyLinked) {
          next.delete(txn.id)
        } else {
          next.add(txn.id)
        }
        return next
      })

      try {
        if (isCurrentlyLinked) {
          // Unmap
          await api.delete('/analytics/recurring/map/', {
            transaction_id: txn.id,
            mapping_id: mappingId,
          })
        } else {
          // Map
          const payload = { transaction_id: txn.id }
          if (categoryId) payload.category_id = categoryId
          if (mappingId) payload.mapping_id = mappingId
          await api.post('/analytics/recurring/map/', payload)
        }
        invalidateWithCandidates()
        if (onMapped && !isCurrentlyLinked) onMapped(txn)
      } catch (err) {
        console.error('Toggle failed:', err)
        // Revert optimistic update on error
        setLocalLinkedIds((prev) => {
          const next = new Set(prev)
          if (isCurrentlyLinked) {
            next.add(txn.id) // re-add
          } else {
            next.delete(txn.id) // re-remove
          }
          return next
        })
      } finally {
        setSaving(false)
      }
    },
    [categoryId, mappingId, localLinkedIds, invalidateWithCandidates, onMapped]
  )

  // Clear all linked transactions
  const handleClearAll = useCallback(async () => {
    if (localLinkedIds.size === 0) return
    setSaving(true)
    const idsToRemove = [...localLinkedIds]
    // Optimistic clear
    setLocalLinkedIds(new Set())
    try {
      for (const txnId of idsToRemove) {
        await api.delete('/analytics/recurring/map/', {
          transaction_id: txnId,
          mapping_id: mappingId,
        })
      }
      invalidateWithCandidates()
    } catch (err) {
      console.error('Clear all failed:', err)
      // Revert
      setLocalLinkedIds(new Set(idsToRemove))
    } finally {
      setSaving(false)
    }
  }, [localLinkedIds, mappingId, invalidateWithCandidates])

  // Switch to category mode (actually persists to backend — only called when user selects a category)
  const handleSwitchToCategory = useCallback(async (catId) => {
    if (!mappingId) return
    setSaving(true)
    try {
      await api.post('/analytics/recurring/match-mode/', {
        mapping_id: mappingId,
        match_mode: 'category',
        category_id: catId,
      })
      invalidateWithCandidates()
    } catch (err) {
      console.error('Switch to category failed:', err)
    } finally {
      setSaving(false)
    }
  }, [mappingId, invalidateWithCandidates])

  // Switch to manual mode (persists to backend — preserves existing M2M links)
  const handleSwitchToManual = useCallback(async () => {
    if (!mappingId) return
    setSaving(true)
    try {
      await api.post('/analytics/recurring/match-mode/', {
        mapping_id: mappingId,
        match_mode: 'manual',
      })
      invalidateWithCandidates()
    } catch (err) {
      console.error('Switch to manual failed:', err)
    } finally {
      setSaving(false)
    }
  }, [mappingId, invalidateWithCandidates])

  // Handle selecting a category in category mode — this is the only action
  // that actually persists the category mode switch to the backend
  const handleSelectCategory = useCallback(async (catId) => {
    await handleSwitchToCategory(catId)
  }, [handleSwitchToCategory])

  // Linked summary for footer
  const linkedTotal = useMemo(() => {
    if (!candidateData?.candidates) return 0
    return candidateData.candidates
      .filter((c) => localLinkedIds.has(c.id))
      .reduce((sum, c) => sum + Math.abs(c.amount), 0)
  }, [candidateData, localLinkedIds])

  // Dropdown content
  const dropdown = isOpen
    ? createPortal(
        <div
          ref={dropdownRef}
          className={styles.dropdown}
          style={{
            position: 'fixed',
            top: dropdownPos.top,
            left: dropdownPos.left,
            width: dropdownPos.width,
            zIndex: 9999,
          }}
        >
          {/* Header with mode toggle + close */}
          <div className={styles.header}>
            <div className={styles.modeRow}>
              <button
                className={`${styles.modeBtn} ${!isCategory ? styles.modeBtnActive : ''}`}
                onClick={() => {
                  setViewMode('manual')
                  setSearch('')
                  // If server mode was category, switch to manual (preserves M2M)
                  if (matchMode === 'category') handleSwitchToManual()
                }}
                disabled={saving}
              >
                Manual
              </button>
              <button
                className={`${styles.modeBtn} ${isCategory ? styles.modeBtnActive : ''}`}
                onClick={() => {
                  setViewMode('category')
                  setSearch('')
                  // Don't call backend — user must select a category first
                }}
                disabled={saving}
              >
                Via categoria
              </button>
            </div>
            <button
              className={styles.closeBtn}
              onClick={() => {
                setIsOpen(false)
                setSearch('')
              }}
              title="Fechar"
            >
              ×
            </button>
          </div>

          {isCategory ? (
            /* ===== CATEGORY MODE ===== */
            <div className={styles.categorySection}>
              <div className={styles.categoryHeader}>
                <span className={styles.categoryLabel}>
                  {categoryId ? (
                    <>
                      <span className={styles.categoryBadge}>CATEGORIA</span>
                      <span>{categoryName}</span>
                      {matchCount > 0 && (
                        <span className={styles.categoryCount}>
                          {matchCount} transação(ões)
                        </span>
                      )}
                    </>
                  ) : (
                    <span className={styles.categoryEmpty}>
                      Selecione uma categoria abaixo
                    </span>
                  )}
                </span>
              </div>

              {/* Search categories */}
              <div className={styles.searchRow}>
                <input
                  ref={inputRef}
                  type="text"
                  className={styles.searchInput}
                  placeholder="Buscar categoria..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Escape') {
                      setIsOpen(false)
                      setSearch('')
                    }
                  }}
                />
              </div>

              <div className={styles.list}>
                {categoriesLoading && (
                  <div className={styles.loadingRow}>Carregando categorias...</div>
                )}

                {!categoriesLoading && (categoryData?.categories || []).filter((cat) => {
                  if (!search) return true
                  return cat.name.toLowerCase().includes(search.toLowerCase())
                }).map((cat) => {
                  const isSelected = categoryId === cat.id
                  return (
                    <button
                      key={cat.id}
                      className={`${styles.catRow} ${isSelected ? styles.catRowSelected : ''}`}
                      onClick={() => handleSelectCategory(cat.id)}
                      disabled={saving}
                    >
                      <span className={styles.catCheck}>
                        {isSelected ? '●' : '○'}
                      </span>
                      <span className={styles.catName}>{cat.name}</span>
                      <span className={styles.catType}>{cat.category_type}</span>
                      <span className={styles.catTxnCount}>
                        {cat.transaction_count} txn{cat.transaction_count !== 1 ? 's' : ''}
                      </span>
                      <span className={styles.catTotal}>
                        R$ {fmt(cat.total_amount)}
                      </span>
                    </button>
                  )
                })}

                {!categoriesLoading && categoryData?.categories?.length === 0 && (
                  <div className={styles.emptyRow}>Nenhuma categoria com transações neste mês</div>
                )}
              </div>
            </div>
          ) : (
            /* ===== MANUAL MODE ===== */
            <>
              {/* Search + actions bar */}
              <div className={styles.searchRow}>
                <input
                  ref={inputRef}
                  type="text"
                  className={styles.searchInput}
                  placeholder={`Buscar transação para ${categoryName}...`}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Escape') {
                      setIsOpen(false)
                      setSearch('')
                    }
                  }}
                />
                {localLinkedIds.size > 0 && (
                  <button
                    className={styles.clearBtn}
                    onClick={handleClearAll}
                    disabled={saving}
                    title="Desvincular todas"
                  >
                    Limpar ({localLinkedIds.size})
                  </button>
                )}
              </div>

              {/* Source filter + sort controls */}
              <div className={styles.filterBar}>
                <div className={styles.sourceFilter}>
                  <button
                    className={`${styles.sourceBtn} ${sourceFilter === 'all' ? styles.sourceBtnActive : ''}`}
                    onClick={() => setSourceFilter('all')}
                  >
                    Todos
                    {candidateData && (
                      <span className={styles.sourceCount}>{candidateData.total}</span>
                    )}
                  </button>
                  <button
                    className={`${styles.sourceBtn} ${sourceFilter === 'checking' ? styles.sourceBtnActive : ''}`}
                    onClick={() => setSourceFilter('checking')}
                  >
                    Conta
                    {candidateData && (
                      <span className={styles.sourceCount}>{candidateData.checking_count}</span>
                    )}
                  </button>
                  <button
                    className={`${styles.sourceBtn} ${sourceFilter === 'credit_card' ? styles.sourceBtnActive : ''}`}
                    onClick={() => setSourceFilter('credit_card')}
                  >
                    Cartão
                    {candidateData && (
                      <span className={styles.sourceCount}>{candidateData.cc_count}</span>
                    )}
                  </button>
                  {candidateData?.prior_count > 0 && (
                    <button
                      className={`${styles.sourceBtn} ${styles.sourceBtnPrior} ${sourceFilter === 'prior_month' ? styles.sourceBtnActive : ''}`}
                      onClick={() => setSourceFilter('prior_month')}
                    >
                      Mês Ant.
                      <span className={styles.sourceCount}>{candidateData.prior_count}</span>
                    </button>
                  )}
                </div>
                <div className={styles.sortControls}>
                  {[
                    { key: 'relevance', label: '≈' , title: 'Relevância (valor similar)' },
                    { key: 'date', label: '📅', title: 'Data' },
                    { key: 'amount', label: 'R$', title: 'Valor' },
                    { key: 'name', label: 'AZ', title: 'Nome' },
                  ].map((s) => (
                    <button
                      key={s.key}
                      className={`${styles.sortBtn} ${sortBy === s.key ? styles.sortBtnActive : ''}`}
                      onClick={() => setSortBy(s.key)}
                      title={s.title}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Linked summary bar (when items are selected) */}
              {localLinkedIds.size > 0 && (
                <div className={styles.linkedSummary}>
                  <span className={styles.linkedIcon}>✓</span>
                  <span>
                    {localLinkedIds.size} vinculada(s)
                    {linkedTotal > 0 && (
                      <span className={styles.linkedAmount}> · R$ {fmt(linkedTotal)}</span>
                    )}
                  </span>
                  {candidateData?.expected > 0 && (
                    <span className={styles.linkedExpected}>
                      esperado R$ {fmt(candidateData.expected)}
                    </span>
                  )}
                </div>
              )}

              {/* Transaction list */}
              <div className={styles.list}>
                {candidatesLoading && (
                  <div className={styles.loadingRow}>Carregando transações...</div>
                )}

                {!candidatesLoading && sortedCandidates.length === 0 && (
                  <div className={styles.emptyRow}>
                    {search ? 'Nenhum resultado' : 'Sem transações neste mês'}
                  </div>
                )}

                {sortedCandidates.map((txn) => {
                  const isLinked = localLinkedIds.has(txn.id)
                  const isGloballyLinked = txn.is_globally_linked && !isLinked
                  const isCrossMonthMoved = txn.cross_month_moved && !isLinked
                  return (
                    <button
                      key={txn.id}
                      className={`${styles.candidate} ${isLinked ? styles.candidateLinked : ''} ${isGloballyLinked || isCrossMonthMoved ? styles.candidateGlobal : ''}`}
                      onClick={() => handleToggleTransaction(txn)}
                      disabled={saving}
                      title={
                        isCrossMonthMoved
                          ? `Movida para ${txn.cross_month_target}`
                          : isGloballyLinked
                            ? 'Vinculada a outro item recorrente'
                            : txn.is_cross_month
                              ? 'Transação do mês anterior'
                              : ''
                      }
                    >
                      <div className={styles.candTop}>
                        <span className={`${styles.candCheck} ${isLinked ? styles.candCheckOn : (isGloballyLinked || isCrossMonthMoved) ? styles.candCheckGlobal : styles.candCheckOff}`}>
                          {isLinked ? '✓' : (isGloballyLinked || isCrossMonthMoved) ? '—' : ''}
                        </span>
                        <span className={styles.candDesc}>
                          {txn.description}
                        </span>
                        {txn.is_cross_month && !isLinked && (
                          <span className={styles.candCrossMonth}>mês ant.</span>
                        )}
                        {isCrossMonthMoved && (
                          <span className={styles.candMovedTo}>movida → {txn.cross_month_target?.slice(5)}/{txn.cross_month_target?.slice(0,4)}</span>
                        )}
                        {txn.installment_info && (
                          <span className={styles.candInstallment}>{txn.installment_info}</span>
                        )}
                        <span className={isLinked ? styles.candAmtLinked : txn.amount > 0 ? styles.candAmtPositive : styles.candAmt}>
                          {txn.amount > 0 ? '+ ' : ''}R$ {fmt(txn.amount)}
                        </span>
                      </div>
                      <div className={styles.candBottom}>
                        <span className={styles.candDate}>
                          {txn.source === 'credit_card'
                            ? `Fatura ${new Date(txn.date + 'T00:00:00').toLocaleDateString('pt-BR', { month: '2-digit', year: 'numeric' })}`
                            : new Date(txn.date + 'T00:00:00').toLocaleDateString('pt-BR')
                          }
                        </span>
                        {txn.purchase_date && (
                          <span className={styles.candDate}>
                            compra {new Date(txn.purchase_date + 'T00:00:00').toLocaleDateString('pt-BR')}
                          </span>
                        )}
                        <span className={styles.candAcct}>{txn.account}</span>
                        {txn.category !== 'Não categorizado' && (
                          <span className={styles.candCat}>{txn.category}</span>
                        )}
                      </div>
                    </button>
                  )
                })}
              </div>

              {/* Footer */}
              {candidateData && (
                <div className={styles.footer}>
                  <span>
                    {sortedCandidates.length}{sourceFilter !== 'all' ? ` ${sourceFilter === 'checking' ? 'conta' : 'cartão'}` : ''} de {candidateData.total} transações
                  </span>
                </div>
              )}
            </>
          )}
        </div>,
        document.body
      )
    : null

  // Trigger button
  return (
    <>
      <button
        ref={triggerRef}
        className={`${styles.trigger} ${isOpen ? styles.triggerActive : ''} ${isMapped ? styles.triggerMapped : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        title={isMapped ? 'Clique para alterar mapeamento' : 'Clique para mapear uma transação'}
      >
        {isMapped && isCategory && matchCount > 1 ? (
          <span className={styles.categoryMatchText}>
            {matchCount} transações via categoria
          </span>
        ) : isMapped && matchType === 'multi' ? (
          <span className={styles.multiMatchText}>
            {matchCount} transações vinculadas
          </span>
        ) : isMapped ? (
          <span className={styles.matchedText}>{currentMatch}</span>
        ) : suggested ? (
          <span className={styles.suggestedText}>{suggested}</span>
        ) : (
          <span className={styles.placeholder}>Mapear transação...</span>
        )}
        <span className={styles.chevron}>▾</span>
      </button>
      {dropdown}
    </>
  )
}

export default TransactionPicker
