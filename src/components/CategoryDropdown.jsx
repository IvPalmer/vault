import { useState, useRef, useEffect, useMemo, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { useQuery } from '@tanstack/react-query'
import api from '../api/client'
import styles from './CategoryDropdown.module.css'

/**
 * CategoryDropdown — portal-based click-to-edit dropdown for transaction
 * category + subcategory with full scrollable list.
 *
 * Props:
 *   transactionId   - UUID of the transaction to update
 *   category        - current category name (display)
 *   categoryId      - current category UUID
 *   subcategory     - current subcategory name (display)
 *   subcategoryId   - current subcategory UUID
 *   field           - 'category' | 'subcategory' (which field this dropdown edits)
 *   onUpdated       - callback() after successful save (for cache invalidation)
 *   installmentMode - if true, uses the installment sibling-propagation endpoint
 */
function CategoryDropdown({
  transactionId,
  category,
  categoryId,
  subcategory,
  subcategoryId,
  field = 'category',
  onUpdated,
  installmentMode = false,
}) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [saving, setSaving] = useState(false)
  const [dropdownPos, setDropdownPos] = useState({ top: 0, left: 0, width: 0 })
  const triggerRef = useRef(null)
  const dropdownRef = useRef(null)
  const inputRef = useRef(null)

  // Fetch categories with nested subcategories
  const { data: categories } = useQuery({
    queryKey: ['categories-dropdown'],
    queryFn: () => api.get('/categories/?is_active=true'),
    staleTime: 60_000,
  })

  // Position dropdown using fixed positioning (portal)
  useEffect(() => {
    if (!open || !triggerRef.current) return
    const rect = triggerRef.current.getBoundingClientRect()
    const dropdownWidth = field === 'category' ? 260 : 240
    let left = rect.left
    if (left + dropdownWidth > window.innerWidth - 16) {
      left = window.innerWidth - dropdownWidth - 16
    }
    if (left < 8) left = 8

    // Check if dropdown would go below viewport
    const dropdownHeight = 340
    let top = rect.bottom + 2
    if (top + dropdownHeight > window.innerHeight - 16) {
      top = rect.top - dropdownHeight - 2
      if (top < 8) top = 8
    }
    setDropdownPos({ top, left, width: dropdownWidth })
  }, [open, field])

  // Close on outside click
  useEffect(() => {
    if (!open) return
    function handleClick(e) {
      if (
        dropdownRef.current && !dropdownRef.current.contains(e.target) &&
        triggerRef.current && !triggerRef.current.contains(e.target)
      ) {
        setOpen(false)
        setSearch('')
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  // Focus search when opening
  useEffect(() => {
    if (open && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [open])

  // Build options based on field type
  const options = useMemo(() => {
    if (!categories) return []
    const q = search.toLowerCase().trim()

    if (field === 'category') {
      // All remaining categories are taxonomy (transaction classification)
      // after RecurringTemplate migration — show all active categories
      const filtered = categories
      if (!q) return filtered
      return filtered.filter(c => c.name.toLowerCase().includes(q))
    }

    // subcategory mode — show subcategories for the current category
    if (!categoryId) return []
    const cat = categories.find(c => c.id === categoryId)
    if (!cat || !cat.subcategories) return []
    const subs = cat.subcategories
    if (!q) return subs
    return subs.filter(s => s.name.toLowerCase().includes(q))
  }, [categories, search, field, categoryId])

  const handleSelect = useCallback(async (option) => {
    setOpen(false)
    setSearch('')
    setSaving(true)

    try {
      if (installmentMode) {
        // Installment mode: use the sibling-propagation endpoint
        const payload = {
          transaction_id: transactionId,
        }
        if (field === 'category') {
          payload.category_id = option.id
          // Keep current subcategory if it still belongs to the new category
          if (subcategoryId && option.subcategories) {
            const stillValid = option.subcategories.some(s => s.id === subcategoryId)
            if (stillValid) payload.subcategory_id = subcategoryId
          }
        } else {
          payload.category_id = categoryId
          payload.subcategory_id = option.id
        }
        await api.post('/transactions/categorize-installment/', payload)
      } else if (field === 'category') {
        const payload = {
          transaction_ids: [transactionId],
          category_id: option.id,
        }
        // If the new category has subcategories, try to keep current one if it belongs
        if (subcategoryId && option.subcategories) {
          const stillValid = option.subcategories.some(s => s.id === subcategoryId)
          if (stillValid) {
            payload.subcategory_id = subcategoryId
          }
        }
        await api.post('/transactions/bulk-categorize/', payload)
      } else {
        await api.post('/transactions/bulk-categorize/', {
          transaction_ids: [transactionId],
          category_id: categoryId,
          subcategory_id: option.id,
        })
      }
      if (onUpdated) onUpdated()
    } catch (err) {
      console.error('Failed to update category:', err)
    } finally {
      setSaving(false)
    }
  }, [field, transactionId, categoryId, subcategoryId, onUpdated, installmentMode])

  // Remove category (set to uncategorized)
  const handleClear = useCallback(async () => {
    setOpen(false)
    setSearch('')
    setSaving(true)
    try {
      if (field === 'category') {
        await api.patch(`/transactions/${transactionId}/`, {
          category: null,
          subcategory: null,
        })
      } else {
        await api.patch(`/transactions/${transactionId}/`, {
          subcategory: null,
        })
      }
      // Note: clear only affects this single transaction (not siblings)
      // because removing categorization should be intentional per-item
      if (onUpdated) onUpdated()
    } catch (err) {
      console.error('Failed to clear:', err)
    } finally {
      setSaving(false)
    }
  }, [field, transactionId, onUpdated])

  const displayValue = field === 'category' ? category : subcategory
  const isEmpty = !displayValue || displayValue === 'Não categorizado'
  const currentId = field === 'category' ? categoryId : subcategoryId

  // Portal dropdown
  const dropdown = open
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
          {/* Search bar */}
          <div className={styles.searchRow}>
            <input
              ref={inputRef}
              type="text"
              className={styles.searchInput}
              placeholder={field === 'category' ? 'Filtrar categorias...' : 'Filtrar subcategorias...'}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  setOpen(false)
                  setSearch('')
                }
              }}
            />
            <button
              className={styles.closeBtn}
              onClick={() => {
                setOpen(false)
                setSearch('')
              }}
              title="Fechar"
            >
              ×
            </button>
          </div>

          {/* Options list */}
          <div className={styles.list}>
            {/* Clear option */}
            {field === 'category' && categoryId && (
              <button
                className={`${styles.option} ${styles.clearOption}`}
                onClick={handleClear}
                disabled={saving}
              >
                <span className={styles.clearIcon}>✕</span>
                <span>Remover categoria</span>
              </button>
            )}
            {field === 'subcategory' && subcategoryId && (
              <button
                className={`${styles.option} ${styles.clearOption}`}
                onClick={handleClear}
                disabled={saving}
              >
                <span className={styles.clearIcon}>✕</span>
                <span>Remover subcategoria</span>
              </button>
            )}

            {/* All options */}
            {options.length === 0 && (
              <div className={styles.emptyRow}>
                {search ? 'Nenhum resultado' : 'Sem opções disponíveis'}
              </div>
            )}
            {options.map((opt) => {
              const isSelected = opt.id === currentId
              return (
                <button
                  key={opt.id}
                  className={`${styles.option} ${isSelected ? styles.optionSelected : ''}`}
                  onClick={() => handleSelect(opt)}
                  disabled={saving}
                >
                  <span className={`${styles.optionCheck} ${isSelected ? styles.optionCheckOn : ''}`}>
                    {isSelected ? '●' : '○'}
                  </span>
                  <span className={styles.optionName}>{opt.name}</span>
                  {field === 'category' && opt.subcategories?.length > 0 && (
                    <span className={styles.subCount}>
                      {opt.subcategories.length} sub
                    </span>
                  )}
                </button>
              )
            })}
          </div>

          {/* Footer count */}
          <div className={styles.footer}>
            <span>{options.length} {field === 'category' ? 'categorias' : 'subcategorias'}</span>
          </div>
        </div>,
        document.body
      )
    : null

  return (
    <>
      <button
        ref={triggerRef}
        className={`${styles.trigger} ${open ? styles.triggerActive : ''} ${isEmpty ? styles.empty : ''}`}
        onClick={() => setOpen(!open)}
        title="Clique para alterar"
        disabled={saving}
      >
        {isEmpty ? (
          <span className={styles.placeholder}>
            {field === 'category' ? 'Sem categoria' : '—'}
          </span>
        ) : (
          <span className={styles.triggerText}>{displayValue}</span>
        )}
        <span className={styles.chevron}>{open ? '▴' : '▾'}</span>
      </button>
      {dropdown}
    </>
  )
}

export default CategoryDropdown
