import { useState, useRef, useEffect } from 'react'
import styles from './InlineEdit.module.css'

/**
 * Safely evaluate a math expression (supports +, -, *, /, parentheses).
 * Returns the result or NaN if invalid.
 */
function evalFormula(expr) {
  const cleaned = expr.replace(/\s/g, '').replace(/,/g, '.')
  // Only allow digits, decimal points, operators, and parentheses
  if (!/^[\d.+\-*/()]+$/.test(cleaned)) return NaN
  try {
    // Use Function constructor to evaluate (safe since we validated the charset)
    const result = new Function(`return (${cleaned})`)()
    return typeof result === 'number' && isFinite(result) ? result : NaN
  } catch {
    return NaN
  }
}

/**
 * InlineEdit — click-to-edit pattern for amounts and text.
 * Currency mode supports formula expressions (e.g., "1500 + 1800" evaluates to 3300).
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
    let newVal
    if (format === 'currency') {
      // Try formula evaluation first (e.g., "1500 + 1800")
      newVal = evalFormula(trimmed)
      if (isNaN(newVal)) return
      // Round to 2 decimal places
      newVal = Math.round(newVal * 100) / 100
    } else {
      newVal = trimmed
    }
    // Use tolerance for numeric comparison to avoid floating-point issues
    const changed = typeof newVal === 'number' && typeof value === 'number'
      ? Math.abs(newVal - value) > 0.001
      : newVal !== value
    if (changed) {
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
          type="text"
          inputMode={format === 'currency' ? 'decimal' : 'text'}
          className={styles.input}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={handleSave}
          onKeyDown={handleKeyDown}
          placeholder={format === 'currency' ? 'ex: 1500 + 1800' : ''}
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
