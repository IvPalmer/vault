import { useState, useMemo, useCallback, useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'
import styles from './CategoryManager.module.css'

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function useDebounce(value, delay) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  return debounced
}

function CategoryManager() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [expandedCats, setExpandedCats] = useState(new Set())
  const [selection, setSelection] = useState(null) // { type: 'sub'|'cat_nosub'|'uncat', catId, subId, catName, subName }
  const [renaming, setRenaming] = useState(null)
  const [renameValue, setRenameValue] = useState('')
  const [moving, setMoving] = useState(false)
  const [moveTarget, setMoveTarget] = useState('')
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState(null)
  const [tab, setTab] = useState('categories')
  const [editingMapping, setEditingMapping] = useState(null)
  const [mappingEdit, setMappingEdit] = useState({ category_id: '', subcategory_id: '' })
  const [addingCategory, setAddingCategory] = useState(false)
  const [newCatName, setNewCatName] = useState('')
  const [addingSubTo, setAddingSubTo] = useState(null) // catId
  const [newSubName, setNewSubName] = useState('')
  const [selectedTxns, setSelectedTxns] = useState(new Set()) // txn ids
  const [txnMoveTarget, setTxnMoveTarget] = useState('')

  const { data: treeData, isLoading } = useQuery({
    queryKey: ['category-tree'],
    queryFn: () => api.get('/categories/tree/'),
    staleTime: 10000,
  })

  const { data: pluggyMappings, isLoading: pluggyLoading } = useQuery({
    queryKey: ['pluggy-mappings'],
    queryFn: () => api.get('/pluggy-category-mappings/'),
    staleTime: 10000,
    enabled: tab === 'pluggy',
  })

  const [detailPage, setDetailPage] = useState(1)
  const detailPageSize = 50

  // Reset page when selection changes
  useEffect(() => { setDetailPage(1) }, [selection?.type, selection?.catId, selection?.subId])

  const detailQueryParams = useMemo(() => {
    if (!selection) return null
    const p = new URLSearchParams()
    if (selection.type === 'uncat') p.set('uncategorized', '1')
    else if (selection.type === 'sub') p.set('subcategory_id', selection.subId)
    else if (selection.type === 'cat') { p.set('category_id', selection.catId) }
    else if (selection.type === 'cat_nosub') { p.set('category_id', selection.catId); p.set('no_subcategory', '1') }
    p.set('page', detailPage)
    p.set('page_size', detailPageSize)
    return p.toString()
  }, [selection, detailPage])

  const { data: sampleTxns, isLoading: txnsLoading } = useQuery({
    queryKey: ['category-sample', detailQueryParams],
    queryFn: () => api.get(`/categories/bulk/?${detailQueryParams}`),
    enabled: !!detailQueryParams,
    staleTime: 5000,
    keepPreviousData: true,
  })

  const detailTotal = sampleTxns?.total || 0
  const detailTotalPages = Math.ceil(detailTotal / detailPageSize)

  const categories = treeData?.categories || []
  const uncategorizedCount = treeData?.uncategorized_count || 0

  const totalTxns = useMemo(() => {
    return categories.reduce((sum, c) => sum + c.transaction_count, 0) + uncategorizedCount
  }, [categories, uncategorizedCount])

  const totalSubs = useMemo(() => {
    return categories.reduce((sum, c) => sum + c.subcategories.length, 0)
  }, [categories])

  const filteredCategories = useMemo(() => {
    if (!search) return categories
    const q = search.toLowerCase()
    return categories.filter(c =>
      c.name.toLowerCase().includes(q) ||
      c.subcategories.some(s =>
        s.name.toLowerCase().includes(q) ||
        s.pluggy_mappings?.some(p => p.pluggy_name.toLowerCase().includes(q))
      ) ||
      c.pluggy_mappings?.some(p => p.pluggy_name.toLowerCase().includes(q))
    )
  }, [categories, search])

  const showToast = useCallback((msg, isError) => {
    setToast({ msg, isError })
    setTimeout(() => setToast(null), 4000)
  }, [])

  const invalidate = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['category-tree'] })
    queryClient.invalidateQueries({ queryKey: ['category-sample'] })
    queryClient.invalidateQueries({ queryKey: ['categories'] })
    queryClient.invalidateQueries({ queryKey: ['pluggy-mappings'] })
  }, [queryClient])

  const handleSaveMapping = useCallback(async (mappingId) => {
    setSaving(true)
    try {
      await api.patch(`/pluggy-category-mappings/${mappingId}/`, {
        category: mappingEdit.category_id || null,
        subcategory: mappingEdit.subcategory_id || null,
      })
      showToast('Mapeamento atualizado')
      setEditingMapping(null)
      invalidate()
    } catch (err) {
      showToast('Erro: ' + (err.message || ''), true)
    } finally {
      setSaving(false)
    }
  }, [mappingEdit, showToast, invalidate])

  const toggleExpand = useCallback((catId) => {
    setExpandedCats(prev => {
      const next = new Set(prev)
      if (next.has(catId)) next.delete(catId)
      else next.add(catId)
      return next
    })
  }, [])

  const handleSelect = useCallback((type, catId, subId, catName, subName) => {
    setSelection({ type, catId, subId, catName, subName })
    setMoving(false)
    setMoveTarget('')
    setRenaming(null)
    setSelectedTxns(new Set())
    setTxnMoveTarget('')
  }, [])

  // Rename
  const startRename = useCallback(() => {
    if (!selection) return
    if (selection.type === 'sub') {
      setRenaming({ id: selection.subId, name: selection.subName, type: 'sub' })
      setRenameValue(selection.subName)
    } else if (selection.type === 'cat_nosub' || selection.type === 'cat') {
      setRenaming({ id: selection.catId, name: selection.catName, type: 'cat' })
      setRenameValue(selection.catName)
    }
  }, [selection])

  const handleRename = useCallback(async () => {
    if (!renaming || !renameValue.trim() || renameValue === renaming.name) return
    setSaving(true)
    try {
      if (renaming.type === 'sub') {
        await api.post('/categories/bulk/', {
          action: 'rename_subcategory',
          subcategory_id: renaming.id,
          name: renameValue.trim(),
        })
      } else {
        await api.patch(`/categories/${renaming.id}/`, { name: renameValue.trim() })
      }
      showToast(`Renomeado para "${renameValue.trim()}"`)
      setRenaming(null)
      setSelection(prev => prev ? { ...prev, subName: renaming.type === 'sub' ? renameValue.trim() : prev.subName, catName: renaming.type === 'cat' ? renameValue.trim() : prev.catName } : null)
      invalidate()
    } catch (err) {
      showToast('Erro ao renomear: ' + (err.message || ''), true)
    } finally {
      setSaving(false)
    }
  }, [renaming, renameValue, showToast, invalidate])

  // Move all transactions from subcategory/uncategorized
  const handleMove = useCallback(async () => {
    if (!selection || !moveTarget) return
    setSaving(true)
    const isUncategorize = moveTarget === 'uncategorize:'
    try {
      if (isUncategorize && (selection.type === 'sub' || selection.type === 'cat_nosub' || selection.type === 'cat')) {
        // Move all transactions in this selection to uncategorized
        const qs = selection.type === 'sub'
          ? { subcategory_id: selection.subId }
          : { category_id: selection.catId }
        await api.post('/categories/bulk/', {
          action: 'bulk_uncategorize',
          ...qs,
        })
      } else if (selection.type === 'sub') {
        await api.post('/categories/bulk/', {
          action: 'reassign_subcategory',
          from_subcategory_id: selection.subId,
          to_subcategory_id: moveTarget,
        })
      } else if (selection.type === 'cat_nosub') {
        await api.post('/categories/bulk/', {
          action: 'set_subcategory',
          category_id: selection.catId,
          to_subcategory_id: moveTarget,
        })
      } else if (selection.type === 'uncat') {
        const [catId, subId] = moveTarget.split(':')
        await api.post('/categories/bulk/', {
          action: 'move_uncategorized',
          to_category_id: catId,
          to_subcategory_id: subId || undefined,
        })
      }
      showToast('Transacoes movidas com sucesso')
      setMoving(false)
      setMoveTarget('')
      setSelection(null)
      invalidate()
    } catch (err) {
      showToast('Erro ao mover: ' + (err.message || ''), true)
    } finally {
      setSaving(false)
    }
  }, [selection, moveTarget, showToast, invalidate])

  // Merge subcategories
  const handleMerge = useCallback(async () => {
    if (!selection || selection.type !== 'sub' || !moveTarget) return
    if (!confirm(`Mesclar "${selection.subName}" em outra subcategoria? As transacoes serao movidas e a subcategoria original sera excluida.`)) return
    setSaving(true)
    try {
      await api.post('/categories/bulk/', {
        action: 'merge_subcategories',
        source_subcategory_id: selection.subId,
        target_subcategory_id: moveTarget,
      })
      showToast('Subcategorias mescladas')
      setMoving(false)
      setMoveTarget('')
      setSelection(null)
      invalidate()
    } catch (err) {
      showToast('Erro ao mesclar: ' + (err.message || ''), true)
    } finally {
      setSaving(false)
    }
  }, [selection, moveTarget, showToast, invalidate])

  // Recategorize individual transaction(s) — auto-matches all same descriptions
  const handleRecategorizeTxns = useCallback(async () => {
    if (selectedTxns.size === 0 || !txnMoveTarget) return
    setSaving(true)
    const [catId, subId] = txnMoveTarget.split(':')
    const isUncategorize = catId === 'uncategorize'
    let totalUpdated = 0
    const descriptions = []
    try {
      for (const txnId of selectedTxns) {
        const res = await api.post('/categories/bulk/', {
          action: isUncategorize ? 'uncategorize_transaction' : 'recategorize_transaction',
          transaction_id: txnId,
          ...(isUncategorize ? {} : { to_category_id: catId, to_subcategory_id: subId || undefined }),
        })
        totalUpdated += res.updated || 0
        if (res.description) descriptions.push(res.description)
      }
      const uniqueDescs = [...new Set(descriptions)]
      const descLabel = uniqueDescs.length === 1 ? `"${uniqueDescs[0]}"` : `${uniqueDescs.length} descricoes`
      showToast(`${totalUpdated} transacoes atualizadas (${descLabel})`)
      setSelectedTxns(new Set())
      setTxnMoveTarget('')
      invalidate()
    } catch (err) {
      showToast('Erro ao recategorizar: ' + (err.message || ''), true)
    } finally {
      setSaving(false)
    }
  }, [selectedTxns, txnMoveTarget, showToast, invalidate])

  // Create category
  const handleCreateCategory = useCallback(async () => {
    if (!newCatName.trim()) return
    setSaving(true)
    try {
      await api.post('/categories/bulk/', { action: 'create_category', name: newCatName.trim() })
      showToast(`Categoria "${newCatName.trim()}" criada`)
      setAddingCategory(false)
      setNewCatName('')
      invalidate()
    } catch (err) {
      showToast(err.data?.error || err.message || 'Erro', true)
    } finally {
      setSaving(false)
    }
  }, [newCatName, showToast, invalidate])

  // Create subcategory
  const handleCreateSubcategory = useCallback(async () => {
    if (!addingSubTo || !newSubName.trim()) return
    setSaving(true)
    try {
      await api.post('/categories/bulk/', { action: 'create_subcategory', category_id: addingSubTo, name: newSubName.trim() })
      showToast(`Subcategoria "${newSubName.trim()}" criada`)
      setAddingSubTo(null)
      setNewSubName('')
      invalidate()
    } catch (err) {
      showToast(err.data?.error || err.message || 'Erro', true)
    } finally {
      setSaving(false)
    }
  }, [addingSubTo, newSubName, showToast, invalidate])

  // Delete category (moves transactions to uncategorized)
  const handleDeleteCategory = useCallback(async (catId, catName) => {
    if (!confirm(`Excluir categoria "${catName}"? Transacoes serao movidas para "nao categorizado".`)) return
    setSaving(true)
    try {
      const res = await api.post('/categories/bulk/', { action: 'delete_category', category_id: catId })
      const uncatMsg = res.uncategorized > 0 ? ` (${res.uncategorized} transacoes descategorizadas)` : ''
      showToast(`Categoria "${catName}" excluida${uncatMsg}`)
      setSelection(null)
      invalidate()
    } catch (err) {
      showToast(err.data?.error || err.message || 'Erro', true)
    } finally {
      setSaving(false)
    }
  }, [showToast, invalidate])

  // Delete subcategory (clears subcategory from transactions)
  const handleDeleteSubcategory = useCallback(async (subId, subName) => {
    if (!confirm(`Excluir subcategoria "${subName}"?`)) return
    setSaving(true)
    try {
      const res = await api.post('/categories/bulk/', { action: 'delete_subcategory', subcategory_id: subId })
      const uncatMsg = res.uncategorized > 0 ? ` (${res.uncategorized} transacoes atualizadas)` : ''
      showToast(`Subcategoria "${subName}" excluida${uncatMsg}`)
      setSelection(null)
      invalidate()
    } catch (err) {
      showToast(err.data?.error || err.message || 'Erro', true)
    } finally {
      setSaving(false)
    }
  }, [showToast, invalidate])

  // Build flat target list for move-to dropdowns
  const allTargets = useMemo(() => {
    const targets = [{ value: 'uncategorize:', label: 'Nao categorizado' }]
    for (const cat of categories) {
      for (const sub of cat.subcategories) {
        if (selection?.type === 'sub' && sub.id === selection.subId) continue
        targets.push({
          value: sub.id,
          label: `${cat.name} > ${sub.name}`,
        })
      }
    }
    targets.sort((a, b) => a.label.localeCompare(b.label))
    return targets
  }, [categories, selection])

  const uncatTargets = useMemo(() => {
    const targets = []
    for (const cat of categories) {
      targets.push({ value: `${cat.id}:`, label: cat.name })
      for (const sub of cat.subcategories) {
        targets.push({ value: `${cat.id}:${sub.id}`, label: `${cat.name} > ${sub.name}` })
      }
    }
    return targets
  }, [categories])

  // For individual txn recategorization: cat:sub targets
  const txnTargets = useMemo(() => {
    const targets = [{ value: 'uncategorize:', label: 'Nao categorizado' }]
    for (const cat of categories) {
      targets.push({ value: `${cat.id}:`, label: cat.name })
      for (const sub of cat.subcategories) {
        targets.push({ value: `${cat.id}:${sub.id}`, label: `  ${cat.name} > ${sub.name}` })
      }
    }
    return targets
  }, [categories])

  const selectedPluggy = useMemo(() => {
    if (!selection) return []
    if (selection.type === 'sub') {
      const cat = categories.find(c => c.id === selection.catId)
      const sub = cat?.subcategories.find(s => s.id === selection.subId)
      return sub?.pluggy_mappings || []
    }
    if (selection.type === 'cat_nosub') {
      const cat = categories.find(c => c.id === selection.catId)
      return (cat?.pluggy_mappings || []).filter(p => !p.subcategory_id)
    }
    return []
  }, [selection, categories])

  const toggleTxnSelect = useCallback((txnId) => {
    setSelectedTxns(prev => {
      const next = new Set(prev)
      if (next.has(txnId)) next.delete(txnId)
      else next.add(txnId)
      return next
    })
  }, [])

  if (isLoading) {
    return <div className={styles.loading}>Carregando categorias...</div>
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <h3 className={styles.title}>Gerenciador de Categorias</h3>
        <div className={styles.tabBar}>
          <button
            className={`${styles.tabBtn} ${tab === 'categories' ? styles.tabBtnActive : ''}`}
            onClick={() => setTab('categories')}
          >
            Categorias
          </button>
          <button
            className={`${styles.tabBtn} ${tab === 'pluggy' ? styles.tabBtnActive : ''}`}
            onClick={() => setTab('pluggy')}
          >
            Pluggy Mappings
          </button>
        </div>
        {tab === 'categories' && (
          <div className={styles.stats}>
            <span className={styles.stat}><span className={styles.statNum}>{categories.length}</span> categorias</span>
            <span className={styles.stat}><span className={styles.statNum}>{totalSubs}</span> subcategorias</span>
            <span className={styles.stat}><span className={styles.statNum}>{totalTxns}</span> transacoes</span>
            {uncategorizedCount > 0 && (
              <span className={styles.stat} style={{ color: 'var(--color-orange)' }}>
                <span className={styles.statNum}>{uncategorizedCount}</span> sem categoria
              </span>
            )}
          </div>
        )}
        {tab === 'pluggy' && (
          <div className={styles.stats}>
            <span className={styles.stat}><span className={styles.statNum}>{pluggyMappings?.length || 0}</span> mapeamentos</span>
          </div>
        )}
      </div>

      {toast && (
        <div className={`${styles.toast} ${toast.isError ? styles.toastError : ''}`}>
          {toast.msg}
        </div>
      )}

      {/* Pluggy Mappings Tab */}
      {tab === 'pluggy' && (
        <div className={styles.pluggyPanel}>
          {pluggyLoading && <div className={styles.loading}>Carregando mapeamentos...</div>}
          {!pluggyLoading && pluggyMappings && (
            <table className={styles.pluggyTable}>
              <thead>
                <tr>
                  <th>Pluggy ID</th>
                  <th>Pluggy Categoria</th>
                  <th>Vault Categoria</th>
                  <th>Vault Subcategoria</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {pluggyMappings.map((m) => {
                  const isEditing = editingMapping === m.id
                  return (
                    <tr key={m.id} className={isEditing ? styles.pluggyRowEditing : ''}>
                      <td className={styles.pluggyId}>{m.pluggy_category_id}</td>
                      <td>{m.pluggy_category_name}</td>
                      <td>
                        {isEditing ? (
                          <select
                            className={styles.pluggySelect}
                            value={mappingEdit.category_id}
                            onChange={(e) => {
                              setMappingEdit({ category_id: e.target.value, subcategory_id: '' })
                            }}
                          >
                            <option value="">-- Nenhuma --</option>
                            {categories.map(c => (
                              <option key={c.id} value={c.id}>{c.name}</option>
                            ))}
                          </select>
                        ) : (
                          <span>{m.category_name || '\u2014'}</span>
                        )}
                      </td>
                      <td>
                        {isEditing ? (
                          <select
                            className={styles.pluggySelect}
                            value={mappingEdit.subcategory_id}
                            onChange={(e) => setMappingEdit(prev => ({ ...prev, subcategory_id: e.target.value }))}
                          >
                            <option value="">-- Nenhuma --</option>
                            {(categories.find(c => c.id === mappingEdit.category_id)?.subcategories || []).map(s => (
                              <option key={s.id} value={s.id}>{s.name}</option>
                            ))}
                          </select>
                        ) : (
                          <span>{m.subcategory_name || '\u2014'}</span>
                        )}
                      </td>
                      <td>
                        {isEditing ? (
                          <div className={styles.pluggyActions}>
                            <button className={styles.pluggySave} onClick={() => handleSaveMapping(m.id)} disabled={saving}>
                              Salvar
                            </button>
                            <button className={styles.pluggyCancel} onClick={() => setEditingMapping(null)}>
                              {'\u00d7'}
                            </button>
                          </div>
                        ) : (
                          <button
                            className={styles.pluggyEditBtn}
                            onClick={() => {
                              setEditingMapping(m.id)
                              setMappingEdit({
                                category_id: m.category || '',
                                subcategory_id: m.subcategory || '',
                              })
                            }}
                          >
                            Editar
                          </button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Category Panels */}
      {tab === 'categories' && <div className={styles.panels}>
        {/* Left: Category tree */}
        <div className={styles.treePanel}>
          <div className={styles.searchBar}>
            <input
              className={styles.searchInput}
              type="text"
              placeholder="Buscar categoria, subcategoria ou Pluggy..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className={styles.treeList}>
            {filteredCategories.map((cat) => {
              const isExpanded = expandedCats.has(cat.id) || !!search
              const pluggyCount = cat.pluggy_mappings?.length || 0
              const isCatSelected = selection?.type === 'cat_nosub' && selection.catId === cat.id
              return (
                <div key={cat.id}>
                  <div
                    className={`${styles.catRow} ${isCatSelected ? styles.catRowSelected : ''}`}
                    onClick={() => {
                      toggleExpand(cat.id)
                      handleSelect('cat', cat.id, null, cat.name, null)
                    }}
                  >
                    <button className={styles.catExpandBtn}>
                      {isExpanded ? '\u25BE' : '\u25B8'}
                    </button>
                    <span className={styles.catName}>{cat.name}</span>
                    {pluggyCount > 0 && (
                      <span className={styles.catPluggy}>{pluggyCount} Pluggy</span>
                    )}
                    <span className={styles.catCount}>{cat.transaction_count}</span>
                    <button
                      className={styles.treeAddBtn}
                      title="Adicionar subcategoria"
                      onClick={(e) => { e.stopPropagation(); setAddingSubTo(addingSubTo === cat.id ? null : cat.id); setNewSubName('') }}
                    >+</button>
                    <button
                      className={styles.treeDeleteBtn}
                      title="Excluir categoria"
                      onClick={(e) => { e.stopPropagation(); handleDeleteCategory(cat.id, cat.name) }}
                    >{'\u00d7'}</button>
                  </div>

                  {/* Add subcategory inline */}
                  {addingSubTo === cat.id && (
                    <div className={styles.inlineAdd}>
                      <input
                        className={styles.inlineAddInput}
                        placeholder="Nome da subcategoria..."
                        value={newSubName}
                        onChange={(e) => setNewSubName(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleCreateSubcategory()
                          if (e.key === 'Escape') { setAddingSubTo(null); setNewSubName('') }
                        }}
                        autoFocus
                      />
                      <button className={styles.inlineAddSave} onClick={handleCreateSubcategory} disabled={saving || !newSubName.trim()}>
                        Criar
                      </button>
                      <button className={styles.inlineAddCancel} onClick={() => { setAddingSubTo(null); setNewSubName('') }}>
                        {'\u00d7'}
                      </button>
                    </div>
                  )}

                  {isExpanded && (
                    <>
                      {cat.no_subcategory_count > 0 && (
                        <div
                          className={`${styles.noSubRow} ${isCatSelected ? styles.subRowSelected : ''}`}
                          onClick={(e) => {
                            e.stopPropagation()
                            handleSelect('cat_nosub', cat.id, null, cat.name, null)
                          }}
                        >
                          <span className={styles.subConnector}>{'\u2514'}</span>
                          <span className={styles.subName}>(sem subcategoria)</span>
                          <span className={styles.subCount}>{cat.no_subcategory_count}</span>
                        </div>
                      )}
                      {cat.subcategories.map((sub) => {
                        const isSelected = selection?.type === 'sub' && selection.subId === sub.id
                        const subPluggy = sub.pluggy_mappings || []
                        return (
                          <div
                            key={sub.id}
                            className={`${styles.subRow} ${isSelected ? styles.subRowSelected : ''}`}
                            onClick={(e) => {
                              e.stopPropagation()
                              handleSelect('sub', cat.id, sub.id, cat.name, sub.name)
                            }}
                          >
                            <span className={styles.subConnector}>{'\u2514'}</span>
                            <span className={styles.subName}>{sub.name}</span>
                            {subPluggy.length > 0 && (
                              <span className={styles.subPluggy} title={subPluggy.map(p => p.pluggy_name).join(', ')}>
                                {subPluggy[0].pluggy_name}
                              </span>
                            )}
                            <span className={styles.subCount}>{sub.transaction_count}</span>
                            <button
                              className={styles.treeDeleteBtn}
                              title="Excluir subcategoria"
                              onClick={(e) => { e.stopPropagation(); handleDeleteSubcategory(sub.id, sub.name) }}
                            >{'\u00d7'}</button>
                          </div>
                        )
                      })}
                    </>
                  )}
                </div>
              )
            })}

          </div>

          {/* Frozen footer */}
          <div className={styles.treeFooter}>
            {!addingCategory ? (
              <div className={styles.addCatRow} onClick={() => setAddingCategory(true)}>
                + Nova categoria
              </div>
            ) : (
              <div className={styles.inlineAdd}>
                <input
                  className={styles.inlineAddInput}
                  placeholder="Nome da categoria..."
                  value={newCatName}
                  onChange={(e) => setNewCatName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleCreateCategory()
                    if (e.key === 'Escape') { setAddingCategory(false); setNewCatName('') }
                  }}
                  autoFocus
                />
                <button className={styles.inlineAddSave} onClick={handleCreateCategory} disabled={saving || !newCatName.trim()}>
                  Criar
                </button>
                <button className={styles.inlineAddCancel} onClick={() => { setAddingCategory(false); setNewCatName('') }}>
                  {'\u00d7'}
                </button>
              </div>
            )}
            <div
              className={`${styles.uncatRow} ${selection?.type === 'uncat' ? styles.uncatRowSelected : ''}`}
              onClick={() => handleSelect('uncat', null, null, 'Nao categorizado', null)}
            >
              Nao categorizado
              <span className={styles.catCount}>{uncategorizedCount}</span>
            </div>
          </div>
        </div>

        {/* Right: Detail panel */}
        <div className={styles.detailPanel}>
          {!selection ? (
            <div className={styles.emptyDetail}>
              Selecione uma categoria ou subcategoria para ver transacoes e opcoes de edicao
            </div>
          ) : (
            <>
              {/* Header */}
              <div className={styles.detailHeader}>
                <div className={styles.detailTitle}>
                  {selection.type === 'uncat'
                    ? 'Nao categorizado'
                    : selection.type === 'cat'
                      ? selection.catName
                      : selection.type === 'cat_nosub'
                        ? `${selection.catName} (sem subcategoria)`
                        : `${selection.catName} > ${selection.subName}`
                  }
                </div>
                <div className={styles.detailSubtitle}>
                  {detailTotal} transacoes{detailTotalPages > 1 ? ` (pag ${detailPage}/${detailTotalPages})` : ''}
                </div>
                {selectedPluggy.length > 0 && (
                  <div className={styles.detailPluggyInfo}>
                    Pluggy:
                    {selectedPluggy.map((p, i) => (
                      <span key={i} className={styles.pluggyTag}>{p.pluggy_name}</span>
                    ))}
                  </div>
                )}
              </div>

              {/* Bulk actions */}
              <div className={styles.actionsBar}>
                {(selection.type === 'sub' || selection.type === 'cat_nosub' || selection.type === 'cat') && (
                  <button className={styles.actionBtn} onClick={startRename} disabled={saving}>
                    Renomear
                  </button>
                )}
                <button className={styles.actionBtn} onClick={() => { setMoving(!moving); setMoveTarget('') }} disabled={saving}>
                  {moving ? 'Cancelar' : 'Mover tudo'}
                </button>
                {selection.type === 'sub' && moving && (
                  <button className={styles.actionBtn} onClick={handleMerge} disabled={saving || !moveTarget}>
                    Mesclar
                  </button>
                )}
                {selection.type === 'sub' && selection.subId && (
                  <button
                    className={styles.actionBtnDanger}
                    onClick={() => handleDeleteSubcategory(selection.subId, selection.subName)}
                    disabled={saving}
                  >
                    Excluir
                  </button>
                )}
              </div>

              {/* Rename input */}
              {renaming && (
                <div className={styles.renameRow}>
                  <input
                    className={styles.renameInput}
                    value={renameValue}
                    onChange={(e) => setRenameValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleRename()
                      if (e.key === 'Escape') setRenaming(null)
                    }}
                    autoFocus
                  />
                  <button className={styles.renameSave} onClick={handleRename} disabled={saving || !renameValue.trim() || renameValue === renaming.name}>
                    Salvar
                  </button>
                  <button className={styles.renameCancel} onClick={() => setRenaming(null)}>
                    {'\u00d7'}
                  </button>
                </div>
              )}

              {/* Move-to selector (bulk) */}
              {moving && (
                <div className={styles.moveSection}>
                  <span className={styles.moveLabel}>
                    {selection.type === 'sub' ? 'Mover transacoes para:' : selection.type === 'uncat' ? 'Categorizar como:' : 'Atribuir subcategoria:'}
                  </span>
                  <select
                    className={styles.moveSelect}
                    value={moveTarget}
                    onChange={(e) => setMoveTarget(e.target.value)}
                  >
                    <option value="">Selecione...</option>
                    {(selection.type === 'uncat' ? uncatTargets : allTargets).map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                  <button
                    className={styles.moveConfirm}
                    onClick={handleMove}
                    disabled={saving || !moveTarget}
                  >
                    {saving ? '...' : 'Confirmar'}
                  </button>
                </div>
              )}

              {/* Individual transaction recategorization */}
              {selectedTxns.size > 0 && (
                <div className={styles.txnRecatBar}>
                  <span className={styles.txnRecatLabel}>
                    {selectedTxns.size} selecionada{selectedTxns.size > 1 ? 's' : ''} — mover para:
                  </span>
                  <select
                    className={styles.moveSelect}
                    value={txnMoveTarget}
                    onChange={(e) => setTxnMoveTarget(e.target.value)}
                  >
                    <option value="">Selecione...</option>
                    {txnTargets.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                  <button
                    className={styles.moveConfirm}
                    onClick={handleRecategorizeTxns}
                    disabled={saving || !txnMoveTarget}
                  >
                    {saving ? '...' : 'Aplicar'}
                  </button>
                  <span className={styles.txnRecatHint}>
                    Todas as transacoes com mesma descricao serao atualizadas
                  </span>
                </div>
              )}

              {/* Transaction preview */}
              <div className={styles.txnList}>
                {txnsLoading && <div className={styles.emptyDetail}>Carregando...</div>}
                {!txnsLoading && sampleTxns?.transactions?.map((txn) => (
                  <div
                    key={txn.id}
                    className={`${styles.txnRow} ${selectedTxns.has(txn.id) ? styles.txnRowSelected : ''}`}
                    onClick={() => toggleTxnSelect(txn.id)}
                  >
                    <input
                      type="checkbox"
                      className={styles.txnCheck}
                      checked={selectedTxns.has(txn.id)}
                      onChange={() => toggleTxnSelect(txn.id)}
                      onClick={(e) => e.stopPropagation()}
                    />
                    <span className={styles.txnDate}>{new Date(txn.date + 'T00:00:00').toLocaleDateString('pt-BR')}</span>
                    <span className={styles.txnDesc} title={txn.description}>
                      {txn.installment_total > 1
                        ? txn.description.replace(/\s*-?\s*[Pp]arcela\s*\d+\/\d+\s*$/, '').replace(/\s*\d+\/\d+\s*$/, '')
                        : txn.description}
                      {txn.installment_total > 1 && (
                        <span className={styles.installmentBadge}>
                          {txn.installment_total}x parcelas
                        </span>
                      )}
                    </span>
                    <span className={txn.amount >= 0 ? styles.txnAmtPos : styles.txnAmtNeg}>
                      R$ {fmt(txn.amount)}
                    </span>
                  </div>
                ))}
                {!txnsLoading && (!sampleTxns?.transactions || sampleTxns.transactions.length === 0) && (
                  <div className={styles.emptyDetail}>Nenhuma transacao</div>
                )}
              </div>

              {/* Detail pagination */}
              {detailTotalPages > 1 && (
                <div className={styles.detailPagination}>
                  <button disabled={detailPage <= 1} onClick={() => setDetailPage(p => p - 1)}>&laquo;</button>
                  <span>{detailPage} / {detailTotalPages}</span>
                  <button disabled={detailPage >= detailTotalPages} onClick={() => setDetailPage(p => p + 1)}>&raquo;</button>
                </div>
              )}
            </>
          )}
        </div>
      </div>}

      {/* All Transactions Table */}
      {tab === 'categories' && <TransactionsTable categories={categories} />}
    </div>
  )
}

function TransactionsTable({ categories }) {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebounce(search, 300)
  const [catFilter, setCatFilter] = useState('')
  const [subFilter, setSubFilter] = useState('')
  const [accountFilter, setAccountFilter] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [uncatFilter, setUncatFilter] = useState(false)
  const [page, setPage] = useState(1)
  const [selectedTxns, setSelectedTxns] = useState(new Set())
  const [moveTarget, setMoveTarget] = useState('')
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState(null)
  const pageSize = 50

  // Reset page when filters change
  useEffect(() => { setPage(1) }, [debouncedSearch, catFilter, subFilter, accountFilter, uncatFilter, dateFrom, dateTo])

  const queryParams = useMemo(() => {
    const p = new URLSearchParams()
    if (debouncedSearch) p.set('search', debouncedSearch)
    if (uncatFilter) p.set('uncategorized', '1')
    else if (catFilter) {
      p.set('category_id', catFilter)
      if (subFilter) p.set('subcategory_id', subFilter)
    }
    if (accountFilter) p.set('account_id', accountFilter)
    if (dateFrom) p.set('date_from', dateFrom)
    if (dateTo) p.set('date_to', dateTo)
    p.set('page', page)
    p.set('page_size', pageSize)
    return p.toString()
  }, [debouncedSearch, catFilter, subFilter, accountFilter, uncatFilter, dateFrom, dateTo, page])

  const { data, isLoading } = useQuery({
    queryKey: ['all-transactions', queryParams],
    queryFn: () => api.get(`/categories/bulk/?${queryParams}`),
    staleTime: 10000,
    keepPreviousData: true,
  })

  const txns = data?.transactions || []
  const total = data?.total || 0
  const accounts = data?.accounts || []
  const totalPages = Math.ceil(total / pageSize)

  const subcatsForFilter = useMemo(() => {
    if (!catFilter) return []
    const cat = categories.find(c => c.id === catFilter)
    return cat?.subcategories || []
  }, [catFilter, categories])

  const txnTargets = useMemo(() => {
    const targets = [{ value: 'uncategorize:', label: 'Nao categorizado' }]
    for (const cat of categories) {
      targets.push({ value: `${cat.id}:`, label: cat.name })
      for (const sub of cat.subcategories) {
        targets.push({ value: `${cat.id}:${sub.id}`, label: `  ${cat.name} > ${sub.name}` })
      }
    }
    return targets
  }, [categories])

  const showToast = useCallback((msg, isError) => {
    setToast({ msg, isError })
    setTimeout(() => setToast(null), 4000)
  }, [])

  const invalidate = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['all-transactions'] })
    queryClient.invalidateQueries({ queryKey: ['category-tree'] })
    queryClient.invalidateQueries({ queryKey: ['category-sample'] })
  }, [queryClient])

  const toggleTxn = useCallback((id) => {
    setSelectedTxns(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id); else next.add(id)
      return next
    })
  }, [])

  const handleRecategorize = useCallback(async () => {
    if (selectedTxns.size === 0 || !moveTarget) return
    setSaving(true)
    const [catId, subId] = moveTarget.split(':')
    const isUncategorize = catId === 'uncategorize'
    let totalUpdated = 0
    try {
      for (const txnId of selectedTxns) {
        const res = await api.post('/categories/bulk/', {
          action: isUncategorize ? 'uncategorize_transaction' : 'recategorize_transaction',
          transaction_id: txnId,
          ...(isUncategorize ? {} : { to_category_id: catId, to_subcategory_id: subId || undefined }),
        })
        totalUpdated += res.updated || 0
      }
      showToast(`${totalUpdated} transacoes atualizadas`)
      setSelectedTxns(new Set())
      setMoveTarget('')
      invalidate()
    } catch (err) {
      showToast('Erro: ' + (err.data?.error || err.message || ''), true)
    } finally {
      setSaving(false)
    }
  }, [selectedTxns, moveTarget, showToast, invalidate])

  const selectAll = useCallback(() => {
    if (selectedTxns.size === txns.length) setSelectedTxns(new Set())
    else setSelectedTxns(new Set(txns.map(t => t.id)))
  }, [selectedTxns, txns])

  return (
    <div className={styles.allTxnSection}>
      <h3 className={styles.allTxnTitle}>TODAS AS TRANSACOES</h3>

      {toast && (
        <div className={`${styles.toast} ${toast.isError ? styles.toastError : ''}`}>
          {toast.msg}
        </div>
      )}

      {/* Filters row */}
      <div className={styles.allTxnFilters}>
        <input
          className={styles.allTxnSearch}
          type="text"
          placeholder="Buscar descricao..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className={styles.allTxnSelect}
          value={uncatFilter ? '__uncat__' : catFilter}
          onChange={(e) => {
            if (e.target.value === '__uncat__') {
              setUncatFilter(true); setCatFilter(''); setSubFilter('')
            } else {
              setUncatFilter(false); setCatFilter(e.target.value); setSubFilter('')
            }
          }}
        >
          <option value="">Todas categorias</option>
          <option value="__uncat__">Sem categoria</option>
          {categories.map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
        <select
          className={styles.allTxnSelect}
          value={subFilter}
          onChange={(e) => setSubFilter(e.target.value)}
          disabled={!catFilter}
        >
          <option value="">Todas subcategorias</option>
          {subcatsForFilter.map(s => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        <select
          className={styles.allTxnSelect}
          value={accountFilter}
          onChange={(e) => setAccountFilter(e.target.value)}
        >
          <option value="">Todas contas</option>
          {accounts.map(a => (
            <option key={a.id} value={a.id}>{a.name}</option>
          ))}
        </select>
        <input
          type="date"
          className={styles.allTxnDateInput}
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          title="Data inicial"
        />
        <span className={styles.allTxnDateSep}>-</span>
        <input
          type="date"
          className={styles.allTxnDateInput}
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          title="Data final"
        />
        <span className={styles.allTxnCount}>{total} resultado{total !== 1 ? 's' : ''}</span>
      </div>

      {/* Selection action bar */}
      {selectedTxns.size > 0 && (
        <div className={styles.txnRecatBar}>
          <span className={styles.txnRecatLabel}>
            {selectedTxns.size} selecionada{selectedTxns.size > 1 ? 's' : ''}:
          </span>
          <select
            className={styles.moveSelect}
            value={moveTarget}
            onChange={(e) => setMoveTarget(e.target.value)}
          >
            <option value="">Mover para...</option>
            {txnTargets.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
          <button
            className={styles.moveConfirm}
            onClick={handleRecategorize}
            disabled={saving || !moveTarget}
          >
            {saving ? '...' : 'Aplicar'}
          </button>
          <span className={styles.txnRecatHint}>Parcelas e descricoes iguais atualizadas automaticamente</span>
        </div>
      )}

      {/* Table */}
      <div className={styles.allTxnTableWrap}>
        <table className={styles.allTxnTable}>
          <thead>
            <tr>
              <th className={styles.allTxnThCheck}>
                <input type="checkbox" onChange={selectAll} checked={txns.length > 0 && selectedTxns.size === txns.length} />
              </th>
              <th className={styles.allTxnThDate}>Data</th>
              <th className={styles.allTxnThDesc}>Descricao</th>
              <th className={styles.allTxnThCat}>Categoria</th>
              <th className={styles.allTxnThAcct}>Conta</th>
              <th className={styles.allTxnThAmt}>Valor</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr><td colSpan={6} className={styles.allTxnEmpty}>Carregando...</td></tr>
            )}
            {!isLoading && txns.length === 0 && (
              <tr><td colSpan={6} className={styles.allTxnEmpty}>Nenhuma transacao encontrada</td></tr>
            )}
            {!isLoading && txns.map((txn) => (
              <tr
                key={txn.id}
                className={`${styles.allTxnTr} ${selectedTxns.has(txn.id) ? styles.allTxnTrSelected : ''}`}
                onClick={() => toggleTxn(txn.id)}
              >
                <td className={styles.allTxnTdCheck}>
                  <input
                    type="checkbox"
                    checked={selectedTxns.has(txn.id)}
                    onChange={() => toggleTxn(txn.id)}
                    onClick={(e) => e.stopPropagation()}
                  />
                </td>
                <td className={styles.allTxnTdDate}>
                  {new Date(txn.date + 'T00:00:00').toLocaleDateString('pt-BR')}
                </td>
                <td className={styles.allTxnTdDesc}>
                  {txn.installment_total > 1
                    ? txn.description.replace(/\s*-?\s*[Pp]arcela\s*\d+\/\d+\s*$/, '').replace(/\s*\d+\/\d+\s*$/, '')
                    : txn.description}
                  {txn.installment_total > 1 && (
                    <span className={styles.installmentBadge}>{txn.installment_total}x</span>
                  )}
                </td>
                <td className={styles.allTxnTdCat}>
                  {txn.category_name
                    ? (txn.subcategory_name ? `${txn.category_name} > ${txn.subcategory_name}` : txn.category_name)
                    : <span className={styles.allTxnNocat}>—</span>
                  }
                </td>
                <td className={styles.allTxnTdAcct}>{txn.account}</td>
                <td className={txn.amount >= 0 ? styles.txnAmtPos : styles.txnAmtNeg}>
                  R$ {fmt(txn.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className={styles.allTxnPagination}>
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>&laquo; Anterior</button>
          <span>{page} / {totalPages}</span>
          <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Proxima &raquo;</button>
        </div>
      )}
    </div>
  )
}

export default CategoryManager
