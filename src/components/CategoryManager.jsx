import { useState, useMemo, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'
import styles from './CategoryManager.module.css'

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function CategoryManager() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [expandedCats, setExpandedCats] = useState(new Set())
  const [selection, setSelection] = useState(null) // { type: 'sub'|'cat_nosub'|'uncat', catId, subId, catName, subName }
  const [renaming, setRenaming] = useState(null) // { id, name, type: 'sub'|'cat' }
  const [renameValue, setRenameValue] = useState('')
  const [moving, setMoving] = useState(false)
  const [moveTarget, setMoveTarget] = useState('')
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState(null)
  const [tab, setTab] = useState('categories') // 'categories' | 'pluggy'
  const [editingMapping, setEditingMapping] = useState(null) // mapping id being edited
  const [mappingEdit, setMappingEdit] = useState({ category_id: '', subcategory_id: '' })

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

  const { data: sampleTxns, isLoading: txnsLoading } = useQuery({
    queryKey: ['category-sample', selection?.type, selection?.catId, selection?.subId],
    queryFn: () => api.post('/categories/bulk/', {
      action: 'get_sample_transactions',
      subcategory_id: selection?.type === 'sub' ? selection.subId : undefined,
      category_id: selection?.type === 'cat_nosub' ? selection.catId : undefined,
      uncategorized: selection?.type === 'uncat' ? true : undefined,
      limit: 30,
    }),
    enabled: !!selection,
    staleTime: 5000,
  })

  const categories = treeData?.categories || []
  const uncategorizedCount = treeData?.uncategorized_count || 0

  const totalTxns = useMemo(() => {
    return categories.reduce((sum, c) => sum + c.transaction_count, 0) + uncategorizedCount
  }, [categories, uncategorizedCount])

  const totalSubs = useMemo(() => {
    return categories.reduce((sum, c) => sum + c.subcategories.length, 0)
  }, [categories])

  // Filter categories by search
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
    setTimeout(() => setToast(null), 3000)
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
  }, [])

  // Rename
  const startRename = useCallback(() => {
    if (!selection) return
    if (selection.type === 'sub') {
      setRenaming({ id: selection.subId, name: selection.subName, type: 'sub' })
      setRenameValue(selection.subName)
    } else if (selection.type === 'cat_nosub') {
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

  // Move / reassign
  const handleMove = useCallback(async () => {
    if (!selection || !moveTarget) return
    setSaving(true)
    try {
      if (selection.type === 'sub') {
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
        // moveTarget is "catId:subId" or "catId:"
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

  // Build flat list of all subcategories for move-to dropdown
  const allTargets = useMemo(() => {
    const targets = []
    for (const cat of categories) {
      for (const sub of cat.subcategories) {
        if (selection?.type === 'sub' && sub.id === selection.subId) continue
        targets.push({
          value: sub.id,
          label: `${cat.name} > ${sub.name}`,
          catName: cat.name,
          subName: sub.name,
        })
      }
    }
    targets.sort((a, b) => a.label.localeCompare(b.label))
    return targets
  }, [categories, selection])

  // For uncategorized, allow selecting category + subcategory
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

  // Detail panel: Pluggy mappings for selected item
  const selectedPluggy = useMemo(() => {
    if (!selection) return []
    if (selection.type === 'sub') {
      const cat = categories.find(c => c.id === selection.catId)
      const sub = cat?.subcategories.find(s => s.id === selection.subId)
      return sub?.pluggy_mappings || []
    }
    if (selection.type === 'cat_nosub') {
      const cat = categories.find(c => c.id === selection.catId)
      // Show pluggy mappings that point to this category but no subcategory
      return (cat?.pluggy_mappings || []).filter(p => !p.subcategory_id)
    }
    return []
  }, [selection, categories])

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
                          <span>{m.category_name || '—'}</span>
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
                          <span>{m.subcategory_name || '—'}</span>
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
              return (
                <div key={cat.id}>
                  <div
                    className={`${styles.catRow} ${selection?.type === 'cat_nosub' && selection.catId === cat.id ? styles.catRowSelected : ''}`}
                    onClick={() => {
                      toggleExpand(cat.id)
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
                  </div>

                  {isExpanded && (
                    <>
                      {cat.no_subcategory_count > 0 && (
                        <div
                          className={`${styles.noSubRow} ${selection?.type === 'cat_nosub' && selection.catId === cat.id ? styles.subRowSelected : ''}`}
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
                          </div>
                        )
                      })}
                    </>
                  )}
                </div>
              )
            })}

            {/* Uncategorized */}
            {uncategorizedCount > 0 && (
              <div
                className={`${styles.uncatRow} ${selection?.type === 'uncat' ? styles.uncatRowSelected : ''}`}
                onClick={() => handleSelect('uncat', null, null, 'Nao categorizado', null)}
              >
                Nao categorizado
                <span className={styles.catCount}>{uncategorizedCount}</span>
              </div>
            )}
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
                    : selection.type === 'cat_nosub'
                      ? `${selection.catName} (sem subcategoria)`
                      : `${selection.catName} > ${selection.subName}`
                  }
                </div>
                <div className={styles.detailSubtitle}>
                  {sampleTxns?.transactions?.length || 0} transacoes recentes
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

              {/* Actions */}
              <div className={styles.actionsBar}>
                {(selection.type === 'sub' || selection.type === 'cat_nosub') && (
                  <button className={styles.actionBtn} onClick={startRename} disabled={saving}>
                    Renomear
                  </button>
                )}
                <button className={styles.actionBtn} onClick={() => { setMoving(!moving); setMoveTarget('') }} disabled={saving}>
                  {moving ? 'Cancelar' : 'Mover para...'}
                </button>
                {selection.type === 'sub' && moving && (
                  <button className={styles.actionBtn} onClick={handleMerge} disabled={saving || !moveTarget}>
                    Mesclar
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

              {/* Move-to selector */}
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

              {/* Transaction preview */}
              <div className={styles.txnList}>
                {txnsLoading && <div className={styles.emptyDetail}>Carregando...</div>}
                {!txnsLoading && sampleTxns?.transactions?.map((txn) => (
                  <div key={txn.id} className={styles.txnRow}>
                    <span className={styles.txnDate}>{new Date(txn.date + 'T00:00:00').toLocaleDateString('pt-BR')}</span>
                    <span className={styles.txnDesc} title={txn.description}>{txn.description}</span>
                    <span className={txn.amount >= 0 ? styles.txnAmtPos : styles.txnAmtNeg}>
                      R$ {fmt(txn.amount)}
                    </span>
                  </div>
                ))}
                {!txnsLoading && (!sampleTxns?.transactions || sampleTxns.transactions.length === 0) && (
                  <div className={styles.emptyDetail}>Nenhuma transacao</div>
                )}
              </div>
            </>
          )}
        </div>
      </div>}
    </div>
  )
}

export default CategoryManager
