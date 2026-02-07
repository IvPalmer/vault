import { useState, useRef, useEffect } from 'react'
import styles from './InlineEdit.module.css'

/**
 * InlineEdit — click-to-edit pattern for amounts and text.
 *
 * Props:
 *   value       - current value (number or string)
 *   onSave      - callback(newValue) when editing completes
 *   prefix      - display prefix (e.g. "R$")
 *   format      - 'currency' | 'text' (default 'currency')
 *   color       - text color
 *   disabled    - prevent editing
 *   placeholder - hint when value is empty/zero
 */
function InlineEdit({
  value,
  onSave,
  prefix = 'R$',
  format = 'currency',
  color,
  disabled = false,
  placeholder = 'clique para editar',
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const inputRef = useRef(null)

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [editing])

  function startEditing() {
    if (disabled) return
    const displayVal = format === 'currency'
      ? (value || 0).toString()
      : (value || '').toString()
    setDraft(displayVal)
    setEditing(true)
  }

  function handleSave() {
    setEditing(false)
    const trimmed = draft.trim()
    if (!trimmed && format === 'currency') return
    const newVal = format === 'currency' ? parseFloat(trimmed) : trimmed
    if (format === 'currency' && isNaN(newVal)) return
    if (newVal !== value) {
      onSave(newVal)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') {
      handleSave()
    } else if (e.key === 'Escape') {
      setEditing(false)
    }
  }

  function formatDisplay() {
    if (format === 'currency') {
      if (value == null || value === 0) return null
      const formatted = Math.abs(value).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
      return `${prefix} ${formatted}`
    }
    return value || null
  }

  if (editing) {
    return (
      <div className={styles.editWrapper}>
        {prefix && format === 'currency' && (
          <span className={styles.prefix}>{prefix}</span>
        )}
        <input
          ref={inputRef}
          type={format === 'currency' ? 'number' : 'text'}
          className={styles.input}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={handleSave}
          onKeyDown={handleKeyDown}
          step="0.01"
        />
      </div>
    )
  }

  const displayText = formatDisplay()

  return (
    <button
      className={`${styles.display} ${disabled ? styles.disabled : ''}`}
      onClick={startEditing}
      style={{ color: color || 'var(--color-text-secondary)' }}
      title={disabled ? '' : 'Clique para editar'}
    >
      {displayText || (
        <span className={styles.placeholder}>{placeholder}</span>
      )}
    </button>
  )
}

export default InlineEdit
