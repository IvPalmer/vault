import { useState, useRef, useEffect, useCallback } from 'react'
import api from '../api/client'
import styles from './DescriptionEdit.module.css'

/**
 * DescriptionEdit — click-to-edit description with optional propagation.
 *
 * Flow:
 * 1. Click description text → enters edit mode (inline text input)
 * 2. Save new name → API renames + returns similar transactions
 * 3. If similar found → shows propagation dialog
 * 4. User confirms → propagates to selected similar transactions
 *
 * Props:
 *   transactionId - UUID
 *   description   - current description text
 *   onUpdated     - callback after save (for cache invalidation)
 */
function DescriptionEdit({ transactionId, description, onUpdated }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const [similar, setSimilar] = useState(null)  // null = no dialog, [] = dialog showing
  const [selected, setSelected] = useState(new Set())
  const [saving, setSaving] = useState(false)
  const inputRef = useRef(null)

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [editing])

  function startEditing() {
    setDraft(description || '')
    setEditing(true)
  }

  async function handleSave() {
    setEditing(false)
    const trimmed = draft.trim()
    if (!trimmed || trimmed === description) return

    try {
      // Preview rename — returns similar transactions
      const res = await api.post('/transactions/rename/', {
        transaction_id: transactionId,
        new_description: trimmed,
      })

      if (res.similar && res.similar.length > 0) {
        // Show propagation dialog
        setSimilar(res.similar)
        setSelected(new Set(res.similar.map(s => s.id)))  // All selected by default
      } else {
        // No similar — just refresh
        if (onUpdated) onUpdated()
      }
    } catch (err) {
      console.error('Failed to rename:', err)
    }
  }

  async function handlePropagate() {
    setSaving(true)
    try {
      await api.post('/transactions/rename/', {
        transaction_id: transactionId,
        new_description: draft.trim(),
        transaction_ids: Array.from(selected),
        propagate: true,
      })
      setSimilar(null)
      setSelected(new Set())
      if (onUpdated) onUpdated()
    } catch (err) {
      console.error('Failed to propagate rename:', err)
    } finally {
      setSaving(false)
    }
  }

  function handleSkipPropagate() {
    setSimilar(null)
    setSelected(new Set())
    if (onUpdated) onUpdated()
  }

  function toggleSelect(id) {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') {
      handleSave()
    } else if (e.key === 'Escape') {
      setEditing(false)
    }
  }

  // Propagation dialog
  if (similar) {
    return (
      <div className={styles.dialogOverlay} onClick={(e) => {
        if (e.target === e.currentTarget) handleSkipPropagate()
      }}>
        <div className={styles.dialog}>
          <h4 className={styles.dialogTitle}>Renomear transações semelhantes?</h4>
          <p className={styles.dialogDesc}>
            Encontramos <strong>{similar.length}</strong> transações semelhantes.
            Deseja renomear todas para &quot;{draft.trim()}&quot;?
          </p>
          <div className={styles.similarList}>
            {similar.map(s => (
              <label key={s.id} className={styles.similarItem}>
                <input
                  type="checkbox"
                  checked={selected.has(s.id)}
                  onChange={() => toggleSelect(s.id)}
                />
                <span className={styles.similarDesc}>{s.description}</span>
                <span className={styles.similarMeta}>
                  {s.month_str} · R$ {Math.abs(s.amount).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </span>
              </label>
            ))}
          </div>
          <div className={styles.dialogActions}>
            <button
              className={styles.btnSecondary}
              onClick={handleSkipPropagate}
            >
              Pular
            </button>
            <button
              className={styles.btnPrimary}
              onClick={handlePropagate}
              disabled={saving || selected.size === 0}
            >
              {saving ? 'Salvando...' : `Renomear ${selected.size} transações`}
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Edit mode
  if (editing) {
    return (
      <input
        ref={inputRef}
        type="text"
        className={styles.input}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={handleSave}
        onKeyDown={handleKeyDown}
      />
    )
  }

  // Display mode
  return (
    <button
      className={styles.display}
      onClick={startEditing}
      title="Clique para renomear"
    >
      {description}
    </button>
  )
}

export default DescriptionEdit
