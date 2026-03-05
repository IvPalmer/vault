import { useState, useRef, useEffect } from 'react'
import styles from './InlineEdit.module.css'

/**
 * Safely evaluate a math expression (supports +, -, *, /, parentheses).
 * Uses a recursive descent parser instead of eval/new Function for CSP safety.
 * Returns the result or NaN if invalid.
 */
function evalFormula(expr) {
  const cleaned = expr.replace(/\s/g, '').replace(/,/g, '.')
  if (!/^[\d.+\-*/()]+$/.test(cleaned)) return NaN
  try {
    let pos = 0
    const peek = () => cleaned[pos]
    const consume = (ch) => { if (cleaned[pos] === ch) pos++; else throw new Error('parse') }

    function parseExpr() {
      let left = parseTerm()
      while (peek() === '+' || peek() === '-') {
        const op = cleaned[pos++]
        const right = parseTerm()
        left = op === '+' ? left + right : left - right
      }
      return left
    }
    function parseTerm() {
      let left = parseFactor()
      while (peek() === '*' || peek() === '/') {
        const op = cleaned[pos++]
        const right = parseFactor()
        left = op === '*' ? left * right : left / right
      }
      return left
    }
    function parseFactor() {
      if (peek() === '(') { consume('('); const val = parseExpr(); consume(')'); return val }
      if (peek() === '-') { pos++; return -parseFactor() }
      const start = pos
      while (pos < cleaned.length && /[\d.]/.test(cleaned[pos])) pos++
      if (pos === start) throw new Error('parse')
      return parseFloat(cleaned.slice(start, pos))
    }

    const result = parseExpr()
    if (pos !== cleaned.length) return NaN
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
