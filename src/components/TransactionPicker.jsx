import { useState, useEffect, useRef, useCallback } from 'react'
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
 * TransactionPicker — inline dropdown for mapping a recurring category to a transaction.
 * Uses a portal to render the dropdown outside the table, avoiding overflow clipping.
 *
 * Props:
 *   categoryId - UUID of the category to map
 *   categoryName - display name
 *   currentMatch - current matched description (if any)
 *   matchedTransactionId - UUID of currently mapped transaction (for unmap)
 *   suggested - suggested match text
 *   status - 'Pago' | 'Faltando' | 'Parcial'
 *   onMapped - callback after successful mapping
 */
function TransactionPicker({
  categoryId,
  categoryName,
  mappingId,
  currentMatch,
  matchedTransactionId,
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

  const isMapped = !!(currentMatch && (status === 'Pago' || status === 'Parcial'))

  // Fetch candidates when dropdown opens — use category_id or mapping_id
  const candidateParam = categoryId
    ? `category_id=${categoryId}`
    : `mapping_id=${mappingId}`
  const { data, isLoading } = useQuery({
    queryKey: ['mapping-candidates', selectedMonth, categoryId || mappingId],
    queryFn: () =>
      api.get(
        `/analytics/recurring/candidates/?month_str=${selectedMonth}&${candidateParam}`
      ),
    enabled: isOpen && !!selectedMonth && !!(categoryId || mappingId),
    staleTime: 30000,
  })

  // Position the dropdown when opening
  useEffect(() => {
    if (!isOpen || !triggerRef.current) return
    const rect = triggerRef.current.getBoundingClientRect()
    const dropdownWidth = Math.max(440, rect.width)
    let left = rect.left
    if (left + dropdownWidth > window.innerWidth - 16) {
      left = window.innerWidth - dropdownWidth - 16
    }
    if (left < 8) left = 8

    setDropdownPos({
      top: rect.bottom + 2,
      left,
      width: dropdownWidth,
    })
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
    return () => {
      document.removeEventListener('mousedown', handleClick)
    }
  }, [isOpen])

  // Focus search input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  // Filter candidates by search
  const filtered = data?.candidates?.filter((c) => {
    if (!search) return true
    const q = search.toLowerCase()
    return (
      c.description.toLowerCase().includes(q) ||
      c.account.toLowerCase().includes(q) ||
      String(c.amount).includes(q)
    )
  }) || []

  const invalidateWithCandidates = useCallback(() => {
    invalidateAll()
    queryClient.invalidateQueries({ queryKey: ['mapping-candidates'] })
  }, [invalidateAll, queryClient])

  // Map a transaction
  const handleSelect = useCallback(
    async (txn) => {
      setSaving(true)
      try {
        const payload = { transaction_id: txn.id }
        if (categoryId) payload.category_id = categoryId
        if (mappingId) payload.mapping_id = mappingId
        await api.post('/analytics/recurring/map/', payload)
        invalidateWithCandidates()
        setIsOpen(false)
        setSearch('')
        if (onMapped) onMapped(txn)
      } catch (err) {
        console.error('Mapping failed:', err)
      } finally {
        setSaving(false)
      }
    },
    [categoryId, mappingId, invalidateWithCandidates, onMapped]
  )

  // Unmap a transaction
  const handleUnmap = useCallback(async () => {
    if (!matchedTransactionId) return
    setSaving(true)
    try {
      await api.delete('/analytics/recurring/map/', {
        transaction_id: matchedTransactionId,
      })
      invalidateWithCandidates()
      setIsOpen(false)
      setSearch('')
    } catch (err) {
      console.error('Unmap failed:', err)
    } finally {
      setSaving(false)
    }
  }, [matchedTransactionId, invalidateWithCandidates])

  // Dropdown rendered via portal
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
          {/* Unmap option if currently mapped */}
          {isMapped && matchedTransactionId && (
            <button
              className={styles.unmapRow}
              onClick={handleUnmap}
              disabled={saving}
            >
              <span className={styles.unmapIcon}>✕</span>
              <span>Remover mapeamento atual</span>
            </button>
          )}

          <div className={styles.searchRow}>
            <input
              ref={inputRef}
              type="text"
              className={styles.searchInput}
              placeholder={`Buscar para ${categoryName}...`}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  setIsOpen(false)
                  setSearch('')
                }
              }}
            />
            <button
              className={styles.closeBtn}
              onClick={() => {
                setIsOpen(false)
                setSearch('')
              }}
            >
              ×
            </button>
          </div>

          <div className={styles.list}>
            {isLoading && (
              <div className={styles.loadingRow}>Carregando...</div>
            )}

            {!isLoading && filtered.length === 0 && (
              <div className={styles.emptyRow}>
                {search ? 'Nenhum resultado' : 'Sem candidatos'}
              </div>
            )}

            {filtered.map((txn) => (
              <button
                key={txn.id}
                className={styles.candidate}
                onClick={() => handleSelect(txn)}
                disabled={saving}
              >
                <div className={styles.candTop}>
                  <span className={styles.candDesc}>{txn.description}</span>
                  <span className={styles.candAmt}>
                    R$ {fmt(txn.amount)}
                  </span>
                </div>
                <div className={styles.candBottom}>
                  <span className={styles.candDate}>
                    {new Date(txn.date + 'T00:00:00').toLocaleDateString('pt-BR')}
                  </span>
                  <span className={styles.candAcct}>{txn.account}</span>
                  {txn.category !== 'Não categorizado' && (
                    <span className={styles.candCat}>{txn.category}</span>
                  )}
                </div>
              </button>
            ))}
          </div>

          {data && (
            <div className={styles.footer}>
              {filtered.length} de {data.total} transações
              {data.expected > 0 && (
                <span> · esperado R$ {fmt(data.expected)}</span>
              )}
            </div>
          )}
        </div>,
        document.body
      )
    : null

  // Trigger button — always clickable, shows different content based on state
  return (
    <>
      <button
        ref={triggerRef}
        className={`${styles.trigger} ${isOpen ? styles.triggerActive : ''} ${isMapped ? styles.triggerMapped : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        title={isMapped ? 'Clique para alterar mapeamento' : 'Clique para mapear uma transação'}
      >
        {isMapped ? (
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
