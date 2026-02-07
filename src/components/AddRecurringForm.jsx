import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useMonth } from '../context/MonthContext'
import api from '../api/client'
import styles from './AddRecurringForm.module.css'

/**
 * AddRecurringForm — inline form for adding custom one-off recurring items.
 * Appears below header when "Adicionar" is clicked.
 *
 * Props:
 *   onClose - callback to hide the form
 */
function AddRecurringForm({ onClose }) {
  const { selectedMonth } = useMonth()
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [type, setType] = useState('Fixo')
  const [amount, setAmount] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!name.trim() || !amount) return

    setSaving(true)
    try {
      await api.post('/analytics/recurring/custom/', {
        month_str: selectedMonth,
        name: name.trim(),
        category_type: type,
        expected_amount: parseFloat(amount),
      })
      queryClient.invalidateQueries({ queryKey: ['analytics-recurring'] })
      queryClient.invalidateQueries({ queryKey: ['analytics-metricas'] })
      onClose()
    } catch (err) {
      console.error('Failed to add custom recurring:', err)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <input
        className={styles.input}
        type="text"
        placeholder="Nome do item"
        value={name}
        onChange={(e) => setName(e.target.value)}
        autoFocus
      />
      <select
        className={styles.select}
        value={type}
        onChange={(e) => setType(e.target.value)}
      >
        <option value="Fixo">Fixo</option>
        <option value="Variavel">Variável</option>
        <option value="Income">Entrada</option>
        <option value="Investimento">Investimento</option>
      </select>
      <div className={styles.amountWrap}>
        <span className={styles.prefix}>R$</span>
        <input
          className={styles.amountInput}
          type="number"
          placeholder="0"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          step="0.01"
          min="0"
        />
      </div>
      <button
        className={styles.saveBtn}
        type="submit"
        disabled={saving || !name.trim() || !amount}
      >
        {saving ? '...' : 'Salvar'}
      </button>
      <button
        className={styles.cancelBtn}
        type="button"
        onClick={onClose}
      >
        Cancelar
      </button>
    </form>
  )
}

export default AddRecurringForm
