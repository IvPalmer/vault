import { useState, useRef, useCallback, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import api, { getProfileId } from '../api/client'
import { useProfile } from '../context/ProfileContext'
import InlineEdit from './InlineEdit'
import styles from './Settings.module.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

const TYPE_MAP = {
  Fixo: { label: 'Fixo', cls: styles.tplTypeFixo },
  Income: { label: 'Entrada', cls: styles.tplTypeIncome },
  Investimento: { label: 'Invest.', cls: styles.tplTypeInvest },
  Variavel: { label: 'Variável', cls: styles.tplTypeVariable },
}

const TYPE_OPTIONS = ['Fixo', 'Variavel', 'Income', 'Investimento']

function TemplateTypeSelector({ value, onChange }) {
  const [isOpen, setIsOpen] = useState(false)
  const t = TYPE_MAP[value] || { label: value, cls: '' }

  return (
    <div className={styles.tplTypeWrap}>
      <button
        className={`${styles.tplTypeBadge} ${t.cls}`}
        onClick={() => setIsOpen(!isOpen)}
        title="Alterar tipo"
      >
        {t.label} ▾
      </button>
      {isOpen && (
        <div className={styles.tplTypeDropdown}>
          {TYPE_OPTIONS.map((type) => {
            const ti = TYPE_MAP[type]
            return (
              <button
                key={type}
                className={`${styles.tplTypeOption} ${type === value ? styles.tplTypeOptionActive : ''}`}
                onClick={() => {
                  if (type !== value) onChange(type)
                  setIsOpen(false)
                }}
              >
                {ti.label}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}


function SalarySection({ config, projection, templates, editing, setEditing, syncing, syncResult, onSync, onSave }) {
  const [form, setForm] = useState({})
  const incomeTemplates = templates.filter(t => t.template_type === 'Income')

  const startEdit = () => {
    setForm({
      hourly_rate_usd: config?.hourly_rate_usd || 52,
      hours_per_day: config?.hours_per_day || 8,
      wise_fee_pct: config?.wise_fee_pct || 0.0091,
      wise_fee_flat: config?.wise_fee_flat || 0.46,
      tax_hold_pct: config?.tax_hold_pct || 0.08,
      advance_recoup_pct: config?.advance_recoup_pct || 0.125,
      advance_start_date: config?.advance_start_date || '',
      advance_num_cycles: config?.advance_num_cycles || 0,
      income_template_id: config?.income_template_id || '',
    })
    setEditing(true)
  }

  const fmtBrl = (v) => v != null ? `R$ ${Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}` : '—'
  const fmtUsd = (v) => v != null ? `$ ${Number(v).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}` : '—'

  const currentMonth = projection?.months?.[0]
  const nextMonth = projection?.months?.[1]

  return (
    <div className={styles.section}>
      <div className={styles.sectionHeader}>
        <div className={styles.sectionIcon}>💰</div>
        <div>
          <h2 className={styles.sectionTitle}>Projecao Salarial</h2>
          <p className={styles.sectionDesc}>
            Calculo automatico: USD/h &rarr; Wise &rarr; BRL &rarr; conta pessoal
          </p>
        </div>
        {!editing && config != null && (
          <button className={styles.sectionAction} onClick={startEdit}>Editar</button>
        )}
      </div>

      <div className={styles.sectionBody}>
        {config == null ? (
          <p className={styles.emptyMsg}>Nenhuma configuracao salarial encontrada.</p>
        ) : editing ? (
          <div className={styles.salaryForm}>
            <div className={styles.salaryFormGrid}>
              <label>
                <span>Taxa horaria (USD)</span>
                <input
                  type="number"
                  step="0.01"
                  className={styles.formInput}
                  value={form.hourly_rate_usd}
                  onChange={(e) => setForm({ ...form, hourly_rate_usd: e.target.value })}
                />
              </label>
              <label>
                <span>Horas/dia</span>
                <input
                  type="number"
                  step="0.5"
                  className={styles.formInput}
                  value={form.hours_per_day}
                  onChange={(e) => setForm({ ...form, hours_per_day: e.target.value })}
                />
              </label>
              <label>
                <span>Wise variavel (%)</span>
                <input
                  type="number"
                  step="0.01"
                  className={styles.formInput}
                  value={(form.wise_fee_pct * 100).toFixed(2)}
                  onChange={(e) => setForm({ ...form, wise_fee_pct: parseFloat(e.target.value) / 100 || 0 })}
                />
              </label>
              <label>
                <span>Wise fixa (USD)</span>
                <input
                  type="number"
                  step="0.01"
                  className={styles.formInput}
                  value={form.wise_fee_flat}
                  onChange={(e) => setForm({ ...form, wise_fee_flat: parseFloat(e.target.value) || 0 })}
                />
              </label>
              <label>
                <span>Retenção fiscal (%)</span>
                <input
                  type="number"
                  step="0.01"
                  className={styles.formInput}
                  value={(form.tax_hold_pct * 100).toFixed(0)}
                  onChange={(e) => setForm({ ...form, tax_hold_pct: parseFloat(e.target.value) / 100 || 0 })}
                />
              </label>
              <label>
                <span>Template de Entrada</span>
                <select
                  className={styles.formSelect}
                  value={form.income_template_id}
                  onChange={(e) => setForm({ ...form, income_template_id: e.target.value })}
                >
                  <option value="">— Selecionar —</option>
                  {incomeTemplates.map((t) => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>Adiantamento recoup (%)</span>
                <input
                  type="number"
                  step="0.01"
                  className={styles.formInput}
                  value={(form.advance_recoup_pct * 100).toFixed(1)}
                  onChange={(e) => setForm({ ...form, advance_recoup_pct: parseFloat(e.target.value) / 100 || 0 })}
                />
              </label>
              <label>
                <span>Inicio recoup (YYYY-MM)</span>
                <input
                  type="text"
                  className={styles.formInput}
                  value={form.advance_start_date}
                  onChange={(e) => setForm({ ...form, advance_start_date: e.target.value })}
                  placeholder="2026-02"
                />
              </label>
              <label>
                <span>Ciclos de recoup</span>
                <input
                  type="number"
                  className={styles.formInput}
                  value={form.advance_num_cycles}
                  onChange={(e) => setForm({ ...form, advance_num_cycles: parseInt(e.target.value) || 0 })}
                />
              </label>
            </div>
            <div className={styles.salaryFormActions}>
              <button className={styles.formSaveBtn} onClick={() => onSave(form)}>Salvar</button>
              <button className={styles.cancelBtn} onClick={() => setEditing(false)}>Cancelar</button>
            </div>
          </div>
        ) : (
          <>
            {/* Summary stats */}
            <div className={styles.statsGrid}>
              <div className={styles.stat}>
                <span className={styles.statValue}>{fmtUsd(config?.hourly_rate_usd)}/h</span>
                <span className={styles.statLabel}>Taxa</span>
              </div>
              <div className={styles.stat}>
                <span className={styles.statValue}>{projection?.usd_brl?.toFixed(2) || '—'}</span>
                <span className={styles.statLabel}>USD/BRL {projection?.wise_source === 'wise_api' ? '(live)' : ''}</span>
              </div>
              <div className={styles.stat}>
                <span className={styles.statValue}>{fmtBrl(currentMonth?.brl_personal)}</span>
                <span className={styles.statLabel}>Este Mes</span>
              </div>
              <div className={styles.stat}>
                <span className={styles.statValue}>{fmtBrl(nextMonth?.brl_personal)}</span>
                <span className={styles.statLabel}>Proximo</span>
              </div>
            </div>

            {/* Monthly breakdown */}
            {projection?.months && (
              <div className={styles.salaryTable}>
                <div className={styles.salaryTableHeader}>
                  <span>Mes</span>
                  <span>Dias Uteis</span>
                  <span>Bruto USD</span>
                  <span>Liquido BRL</span>
                </div>
                {projection.months.slice(0, 6).map((m) => (
                  <div key={m.month} className={styles.salaryTableRow}>
                    <span>{m.month}</span>
                    <span>{m.weekdays}</span>
                    <span>{fmtUsd(m.gross_usd)}</span>
                    <span className={styles.salaryBrl}>{fmtBrl(m.brl_personal)}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Sync button */}
            <div className={styles.importSection}>
              <button
                className={styles.importBtn}
                onClick={onSync}
                disabled={syncing}
              >
                {syncing ? 'Sincronizando...' : 'Sincronizar Projecao'}
              </button>
              <span className={styles.importHint}>
                Atualiza BudgetConfig com valores salariais projetados
              </span>
            </div>

            {syncResult && (
              <div className={syncResult.success ? styles.successMsg : styles.errorMsg}>
                {syncResult.success ? (
                  <span>Sincronizado: {syncResult.months} meses atualizados (USD/BRL {syncResult.rate})</span>
                ) : (
                  <span>Erro: {syncResult.error}</span>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}


function Settings({ onOpenWizard }) {
  const queryClient = useQueryClient()
  const fileRef = useRef(null)
  const [uploading, setUploading] = useState(false)
  const [importing, setImporting] = useState(false)
  const [uploadResult, setUploadResult] = useState(null)
  const [importResult, setImportResult] = useState(null)
  const [dragOver, setDragOver] = useState(false)

  // New template form
  const [showNewForm, setShowNewForm] = useState(false)
  const [newName, setNewName] = useState('')
  const [newType, setNewType] = useState('Fixo')
  const [newAmount, setNewAmount] = useState('')
  const [newDueDay, setNewDueDay] = useState('')
  const [newSaving, setNewSaving] = useState(false)

  // Categories management
  const [showNewCatForm, setShowNewCatForm] = useState(false)
  const [newCatName, setNewCatName] = useState('')
  const [newCatSaving, setNewCatSaving] = useState(false)
  const [expandedCat, setExpandedCat] = useState(null)
  const [newSubName, setNewSubName] = useState('')
  const [newSubSaving, setNewSubSaving] = useState(false)

  // Budget subcategory expansion
  const [expandedBudgetCat, setExpandedBudgetCat] = useState(null)

  // Profile settings
  const { profileId, currentProfile } = useProfile()
  const [allocName, setAllocName] = useState('')
  const [allocPct, setAllocPct] = useState('')
  const [allocSaving, setAllocSaving] = useState(false)

  // Account management
  const [showNewAcctForm, setShowNewAcctForm] = useState(false)
  const [newAcctName, setNewAcctName] = useState('')
  const [newAcctType, setNewAcctType] = useState('checking')
  const [newAcctClosingDay, setNewAcctClosingDay] = useState('')
  const [newAcctDueDay, setNewAcctDueDay] = useState('')
  const [newAcctSaving, setNewAcctSaving] = useState(false)

  // Salary config
  const [salaryEditing, setSalaryEditing] = useState(false)
  const [salarySyncing, setSalarySyncing] = useState(false)
  const [salarySyncResult, setSalarySyncResult] = useState(null)

  // Rename rules
  const [showNewRenameForm, setShowNewRenameForm] = useState(false)
  const [newRenameKeyword, setNewRenameKeyword] = useState('')
  const [newRenameDisplay, setNewRenameDisplay] = useState('')
  const [newRenameSaving, setNewRenameSaving] = useState(false)
  const [renameSearch, setRenameSearch] = useState('')

  const { data: status, refetch: refetchStatus } = useQuery({
    queryKey: ['import-status'],
    queryFn: () => api.get('/import/'),
  })

  // Recurring templates query
  const { data: templatesData, refetch: refetchTemplates } = useQuery({
    queryKey: ['recurring-templates'],
    queryFn: () => api.get('/analytics/recurring/templates/'),
  })

  // Profile data query
  const { data: profileData, refetch: refetchProfile } = useQuery({
    queryKey: ['profile-settings', profileId],
    queryFn: () => api.get(`/profiles/${profileId}/`),
    enabled: !!profileId,
  })

  // Accounts query
  const { data: accountsData, refetch: refetchAccounts } = useQuery({
    queryKey: ['all-accounts'],
    queryFn: () => api.get('/accounts/'),
  })

  const allAccounts = useMemo(() => {
    if (!accountsData) return []
    return Array.isArray(accountsData) ? accountsData : (accountsData.results || [])
  }, [accountsData])

  // Rename rules query
  const { data: renamesData, refetch: refetchRenames } = useQuery({
    queryKey: ['rename-rules'],
    queryFn: () => api.get('/renames/'),
  })

  const filteredRenames = useMemo(() => {
    const list = Array.isArray(renamesData) ? renamesData : (renamesData?.results || [])
    if (!renameSearch.trim()) return list.filter(r => r.is_active !== false)
    const q = renameSearch.toLowerCase().trim()
    return list.filter(r =>
      r.is_active !== false && (
        (r.keyword || '').toLowerCase().includes(q) ||
        (r.display_name || '').toLowerCase().includes(q)
      )
    )
  }, [renamesData, renameSearch])

  // Salary config + projection
  const { data: salaryConfig, refetch: refetchSalaryConfig } = useQuery({
    queryKey: ['salary-config'],
    queryFn: async () => {
      try { return await api.get('/salary/config/') }
      catch (e) { if (e.status === 404) return null; throw e }
    },
  })
  const { data: salaryProjection, refetch: refetchSalaryProjection } = useQuery({
    queryKey: ['salary-projection'],
    queryFn: async () => {
      try { return await api.get('/salary/projection/') }
      catch (e) { if (e.status === 404) return null; throw e }
    },
    enabled: salaryConfig != null,
  })

  // Bank templates query (for dynamic import instructions)
  const { data: bankTemplatesData } = useQuery({
    queryKey: ['bank-templates'],
    queryFn: () => api.get('/bank-templates/'),
  })

  const bankTemplates = useMemo(() => {
    if (!bankTemplatesData) return []
    return Array.isArray(bankTemplatesData) ? bankTemplatesData : (bankTemplatesData.results || [])
  }, [bankTemplatesData])

  const groupedBankTemplates = useMemo(() => {
    const groups = {}
    for (const tpl of bankTemplates) {
      const bank = tpl.bank_name || 'Outro'
      if (!groups[bank]) groups[bank] = []
      groups[bank].push(tpl)
    }
    return groups
  }, [bankTemplates])

  // Profile update handler
  const handleUpdateProfile = async (field, value) => {
    if (!profileId) return
    try {
      await api.patch(`/profiles/${profileId}/`, { [field]: value })
      refetchProfile()
    } catch (err) {
      console.error('Failed to update profile:', err)
    }
  }

  // Investment allocation handlers
  const investmentAllocation = useMemo(() => {
    if (!profileData?.investment_allocation) return []
    const alloc = profileData.investment_allocation
    if (typeof alloc === 'object' && !Array.isArray(alloc)) {
      return Object.entries(alloc).map(([name, pct]) => ({ name, pct }))
    }
    return Array.isArray(alloc) ? alloc : []
  }, [profileData])

  const handleSaveAllocation = async (newAlloc) => {
    if (!profileId) return
    const allocObj = {}
    for (const item of newAlloc) {
      allocObj[item.name] = item.pct
    }
    try {
      await api.patch(`/profiles/${profileId}/`, { investment_allocation: allocObj })
      refetchProfile()
    } catch (err) {
      console.error('Failed to save allocation:', err)
    }
  }

  const handleAddAllocation = async () => {
    if (!allocName.trim() || !allocPct) return
    setAllocSaving(true)
    try {
      const newAlloc = [...investmentAllocation, { name: allocName.trim(), pct: parseFloat(allocPct) }]
      await handleSaveAllocation(newAlloc)
      setAllocName('')
      setAllocPct('')
    } catch (err) {
      console.error('Failed to add allocation:', err)
    } finally {
      setAllocSaving(false)
    }
  }

  const handleRemoveAllocation = (idx) => {
    const newAlloc = investmentAllocation.filter((_, i) => i !== idx)
    handleSaveAllocation(newAlloc)
  }

  // Account handlers
  const handleCreateAccount = async (e) => {
    e.preventDefault()
    if (!newAcctName.trim()) return
    setNewAcctSaving(true)
    try {
      await api.post('/accounts/', {
        name: newAcctName.trim(),
        account_type: newAcctType,
        closing_day: newAcctClosingDay ? parseInt(newAcctClosingDay) : null,
        due_day: newAcctDueDay ? parseInt(newAcctDueDay) : null,
      })
      refetchAccounts()
      setShowNewAcctForm(false)
      setNewAcctName('')
      setNewAcctType('checking')
      setNewAcctClosingDay('')
      setNewAcctDueDay('')
    } catch (err) {
      console.error('Failed to create account:', err)
    } finally {
      setNewAcctSaving(false)
    }
  }

  const handleUpdateAccount = async (acctId, field, value) => {
    try {
      await api.patch(`/accounts/${acctId}/`, { [field]: value })
      refetchAccounts()
    } catch (err) {
      console.error('Failed to update account:', err)
    }
  }

  const handleDeleteAccount = async (acctId, name) => {
    if (!confirm(`Excluir conta "${name}"?`)) return
    try {
      await api.delete(`/accounts/${acctId}/`)
      refetchAccounts()
    } catch (err) {
      console.error('Failed to delete account:', err)
    }
  }

  // Rename rule handlers
  const handleCreateRename = async (e) => {
    e.preventDefault()
    if (!newRenameKeyword.trim() || !newRenameDisplay.trim()) return
    setNewRenameSaving(true)
    try {
      await api.post('/renames/', {
        keyword: newRenameKeyword.trim(),
        display_name: newRenameDisplay.trim(),
        is_active: true,
      })
      refetchRenames()
      setShowNewRenameForm(false)
      setNewRenameKeyword('')
      setNewRenameDisplay('')
    } catch (err) {
      console.error('Failed to create rename rule:', err)
    } finally {
      setNewRenameSaving(false)
    }
  }

  const handleUpdateRename = async (renameId, field, value) => {
    try {
      await api.patch(`/renames/${renameId}/`, { [field]: value })
      refetchRenames()
    } catch (err) {
      console.error('Failed to update rename rule:', err)
    }
  }

  const handleDeleteRename = async (renameId, keyword) => {
    if (!confirm(`Desativar regra de renomeação "${keyword}"?`)) return
    try {
      await api.patch(`/renames/${renameId}/`, { is_active: false })
      refetchRenames()
    } catch (err) {
      console.error('Failed to deactivate rename rule:', err)
    }
  }

  const handleFiles = useCallback(async (files) => {
    if (!files.length) return
    setUploading(true)
    setUploadResult(null)
    setImportResult(null)

    const formData = new FormData()
    for (const file of files) {
      formData.append('files', file)
    }

    try {
      const profileId = getProfileId()
      const headers = profileId ? { 'X-Profile-ID': profileId } : {}
      const res = await fetch(`${API_BASE}/import/?action=upload`, {
        method: 'POST',
        body: formData,
        headers,
      })
      const data = await res.json()
      if (res.ok) {
        setUploadResult({ success: true, ...data })

        // Auto-trigger incremental import after successful upload
        setImporting(true)
        try {
          const importRes = await fetch(`${API_BASE}/import/?action=incremental`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(profileId && { 'X-Profile-ID': profileId }),
            },
          })
          const importData = await importRes.json()
          setImportResult(importData)
          if (importData.success) {
            refetchStatus()
            queryClient.invalidateQueries({ queryKey: ['analytics-metricas'] })
            queryClient.invalidateQueries({ queryKey: ['months'] })
          }
        } catch (importErr) {
          setImportResult({ success: false, error: importErr.message })
        } finally {
          setImporting(false)
        }
      } else {
        setUploadResult({ success: false, error: data.error || 'Upload failed' })
      }
    } catch (err) {
      setUploadResult({ success: false, error: err.message })
    } finally {
      setUploading(false)
    }
  }, [refetchStatus, queryClient])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    handleFiles(Array.from(e.dataTransfer.files))
  }, [handleFiles])

  const handleRunImport = async () => {
    setImporting(true)
    setImportResult(null)
    try {
      const profileId = getProfileId()
      const res = await fetch(`${API_BASE}/import/?action=run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(profileId && { 'X-Profile-ID': profileId }),
        },
      })
      const data = await res.json()
      setImportResult(data)
      if (data.success) {
        refetchStatus()
        queryClient.invalidateQueries({ queryKey: ['analytics-metricas'] })
        queryClient.invalidateQueries({ queryKey: ['months'] })
      }
    } catch (err) {
      setImportResult({ success: false, error: err.message })
    } finally {
      setImporting(false)
    }
  }

  // Salary config handlers
  const handleSalarySync = async () => {
    setSalarySyncing(true)
    setSalarySyncResult(null)
    try {
      const res = await api.post('/salary/sync/')
      setSalarySyncResult({ success: true, months: res.budget_configs_upserted, rate: res.usd_brl })
      refetchSalaryProjection()
      queryClient.invalidateQueries({ queryKey: ['analytics-metricas'] })
    } catch (err) {
      setSalarySyncResult({ success: false, error: err.message })
    } finally {
      setSalarySyncing(false)
    }
  }

  const handleSalaryConfigSave = async (updates) => {
    try {
      await api.put('/salary/config/', updates)
      refetchSalaryConfig()
      refetchSalaryProjection()
      setSalaryEditing(false)
    } catch (err) {
      console.error('Failed to save salary config:', err)
    }
  }

  // Template management handlers
  const handleUpdateTemplate = async (id, field, value) => {
    try {
      await api.patch('/analytics/recurring/templates/', {
        id,
        [field]: value,
      })
      refetchTemplates()
    } catch (err) {
      console.error('Failed to update template:', err)
    }
  }

  const handleDeleteTemplate = async (id, name) => {
    if (!confirm(`Desativar template "${name}"? Meses futuros não incluirão este item.`)) return
    try {
      await api.delete('/analytics/recurring/templates/', { id })
      refetchTemplates()
    } catch (err) {
      console.error('Failed to delete template:', err)
    }
  }

  const handleCreateTemplate = async (e) => {
    e.preventDefault()
    if (!newName.trim() || !newAmount) return
    setNewSaving(true)
    try {
      await api.post('/analytics/recurring/templates/', {
        name: newName.trim(),
        template_type: newType,
        default_limit: parseFloat(newAmount),
        due_day: newDueDay ? parseInt(newDueDay) : null,
      })
      refetchTemplates()
      setShowNewForm(false)
      setNewName('')
      setNewType('Fixo')
      setNewAmount('')
      setNewDueDay('')
    } catch (err) {
      console.error('Failed to create template:', err)
    } finally {
      setNewSaving(false)
    }
  }

  // Categories + subcategories query (uses REST ViewSet)
  const { data: categoriesData, refetch: refetchCategories } = useQuery({
    queryKey: ['all-categories'],
    queryFn: () => api.get('/categories/'),
  })

  const allCategories = useMemo(() => {
    if (!categoriesData) return []
    const list = Array.isArray(categoriesData) ? categoriesData : (categoriesData.results || [])
    return list.filter((c) => c.is_active)
  }, [categoriesData])

  // Taxonomy categories = transaction classification (Variavel type)
  // Alimentação, Compras, Transporte, etc. — shown regardless of whether they have subcategories
  const taxonomyCategories = useMemo(() => {
    return allCategories
      .sort((a, b) => a.name.localeCompare(b.name, 'pt-BR'))
  }, [allCategories])

  const handleCreateCategory = async (e) => {
    e.preventDefault()
    if (!newCatName.trim()) return
    setNewCatSaving(true)
    try {
      await api.post('/categories/', {
        name: newCatName.trim(),
        category_type: 'Variavel',
        default_limit: 0,
        is_active: true,
      })
      refetchCategories()
      setShowNewCatForm(false)
      setNewCatName('')
    } catch (err) {
      console.error('Failed to create category:', err)
    } finally {
      setNewCatSaving(false)
    }
  }

  const handleUpdateCategory = async (catId, field, value) => {
    try {
      await api.patch(`/categories/${catId}/`, { [field]: value })
      refetchCategories()
    } catch (err) {
      console.error('Failed to update category:', err)
    }
  }

  const handleDeleteCategory = async (catId, name) => {
    if (!confirm(`Desativar categoria "${name}"?`)) return
    try {
      await api.patch(`/categories/${catId}/`, { is_active: false, default_limit: 0 })
      refetchCategories()
    } catch (err) {
      console.error('Failed to deactivate category:', err)
    }
  }

  const handleCreateSubcategory = async (catId) => {
    if (!newSubName.trim()) return
    setNewSubSaving(true)
    try {
      await api.post('/subcategories/', {
        name: newSubName.trim(),
        category: catId,
      })
      refetchCategories()
      setNewSubName('')
    } catch (err) {
      console.error('Failed to create subcategory:', err)
    } finally {
      setNewSubSaving(false)
    }
  }

  const handleDeleteSubcategory = async (subId, name) => {
    if (!confirm(`Excluir subcategoria "${name}"?`)) return
    try {
      await api.delete(`/subcategories/${subId}/`)
      refetchCategories()
    } catch (err) {
      console.error('Failed to delete subcategory:', err)
    }
  }

  const handleUpdateSubcategory = async (subId, field, value) => {
    try {
      await api.patch(`/subcategories/${subId}/`, { [field]: value })
      refetchCategories()
    } catch (err) {
      console.error('Failed to update subcategory:', err)
    }
  }

  const fmtSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  // Group templates by type
  const groupedTemplates = {}
  if (templatesData?.templates) {
    for (const tpl of templatesData.templates) {
      const group = tpl.template_type
      if (!groupedTemplates[group]) groupedTemplates[group] = []
      groupedTemplates[group].push(tpl)
    }
  }

  const groupOrder = ['Income', 'Fixo', 'Variavel', 'Investimento']
  const groupLabels = {
    Income: 'ENTRADAS',
    Fixo: 'GASTOS FIXOS',
    Variavel: 'GASTOS VARIÁVEIS',
    Investimento: 'INVESTIMENTOS',
  }

  const ACCT_TYPE_MAP = {
    checking: { label: 'Corrente', cls: styles.acctTypeChecking },
    credit_card: { label: 'Cartão', cls: styles.acctTypeCredit },
    manual: { label: 'Manual', cls: styles.acctTypeManual },
  }

  const BUDGET_STRATEGY_OPTIONS = [
    { value: 'percentual', label: 'Percentual da Renda' },
    { value: 'fixo', label: 'Valores Fixos' },
    { value: 'inteligente', label: 'Inteligente (baseado em extratos)' },
  ]

  // Budget summary: total income from templates vs total allocated budgets
  const totalIncome = useMemo(() => {
    if (!templatesData?.templates) return 0
    return templatesData.templates
      .filter(t => t.template_type === 'Income')
      .reduce((s, t) => s + parseFloat(t.default_limit || 0), 0)
  }, [templatesData])

  const totalAllocated = useMemo(() => {
    return taxonomyCategories.reduce((s, c) => s + parseFloat(c.default_limit || 0), 0)
  }, [taxonomyCategories])

  return (
    <div className={styles.container}>

      {/* ============================================================ */}
      {/* SETUP WIZARD BUTTON                                          */}
      {/* ============================================================ */}
      {onOpenWizard && (
        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <div className={styles.sectionIcon}>&#9881;</div>
            <div style={{ flex: 1 }}>
              <h2 className={styles.sectionTitle}>Assistente de Configuracao</h2>
              <p className={styles.sectionDesc}>
                Execute o assistente guiado para reconfigurar seu perfil, ou salve/restaure templates de configuracao.
              </p>
            </div>
            <button
              className={styles.wizardBtn}
              onClick={onOpenWizard}
            >
              Abrir Assistente
            </button>
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* SECTION 1: PROFILE SETTINGS (PERFIL)                         */}
      {/* ============================================================ */}
      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionIcon}>👤</div>
          <div>
            <h2 className={styles.sectionTitle}>Perfil</h2>
            <p className={styles.sectionDesc}>
              Configurações gerais do perfil: metas de poupança, investimentos e estratégia de orçamento.
            </p>
          </div>
        </div>

        <div className={styles.sectionBody}>
          <div className={styles.profileFields}>
            <div className={styles.profileField}>
              <span className={styles.profileFieldLabel}>Meta de Poupança (%)</span>
              <div className={styles.profileFieldValue}>
                <InlineEdit
                  value={profileData?.savings_target_pct ?? 0}
                  onSave={(val) => handleUpdateProfile('savings_target_pct', val)}
                  prefix=""
                  format="currency"
                  color="var(--color-accent)"
                  placeholder="0"
                />
              </div>
              <span className={styles.profileFieldHint}>% da renda bruta</span>
            </div>

            <div className={styles.profileField}>
              <span className={styles.profileFieldLabel}>Meta de Investimento (%)</span>
              <div className={styles.profileFieldValue}>
                <InlineEdit
                  value={profileData?.investment_target_pct ?? 0}
                  onSave={(val) => handleUpdateProfile('investment_target_pct', val)}
                  prefix=""
                  format="currency"
                  color="var(--color-accent)"
                  placeholder="0"
                />
              </div>
              <span className={styles.profileFieldHint}>% da renda bruta</span>
            </div>

            <div className={styles.profileField}>
              <span className={styles.profileFieldLabel}>Estratégia de Orçamento</span>
              <div className={styles.profileFieldValue}>
                <select
                  className={styles.formSelect}
                  value={profileData?.budget_strategy || 'percentual'}
                  onChange={(e) => handleUpdateProfile('budget_strategy', e.target.value)}
                >
                  {BUDGET_STRATEGY_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className={styles.profileField}>
              <span className={styles.profileFieldLabel}>Exibição Cartão de Crédito</span>
              <div className={styles.profileFieldValue}>
                <div className={styles.toggleSwitch}>
                  <button
                    className={`${styles.toggleOption} ${(profileData?.cc_display_mode || 'invoice') === 'invoice' ? styles.toggleOptionActive : ''}`}
                    onClick={() => handleUpdateProfile('cc_display_mode', 'invoice')}
                  >
                    Fatura
                  </button>
                  <button
                    className={`${styles.toggleOption} ${profileData?.cc_display_mode === 'transaction' ? styles.toggleOptionActive : ''}`}
                    onClick={() => handleUpdateProfile('cc_display_mode', 'transaction')}
                  >
                    Compra
                  </button>
                </div>
              </div>
              <span className={styles.profileFieldHint}>
                Fatura = mês de pagamento · Compra = mês da transação
              </span>
            </div>

            {/* Investment Allocation */}
            <div className={styles.profileField} style={{ alignItems: 'flex-start' }}>
              <span className={styles.profileFieldLabel}>Alocação de Investimentos</span>
              <div className={styles.profileFieldValue}>
                <div className={styles.itemList}>
                  {investmentAllocation.map((item, idx) => (
                    <div key={idx} className={styles.allocationRow}>
                      <span className={styles.allocationName}>{item.name}</span>
                      <div className={styles.allocationBar}>
                        <div
                          className={styles.allocationBarFill}
                          style={{ width: `${Math.min(item.pct, 100)}%` }}
                        />
                      </div>
                      <span className={styles.allocationPct}>{item.pct}%</span>
                      <button
                        className={styles.deleteBtn}
                        onClick={() => handleRemoveAllocation(idx)}
                        title="Remover"
                      >
                        {'\u00d7'}
                      </button>
                    </div>
                  ))}
                  {investmentAllocation.length === 0 && (
                    <div className={styles.emptyState}>Nenhuma alocação definida</div>
                  )}
                </div>
                <div className={styles.allocationAddRow}>
                  <input
                    className={styles.allocationInput}
                    type="text"
                    placeholder="Nome (ex: Renda Fixa)"
                    value={allocName}
                    onChange={(e) => setAllocName(e.target.value)}
                  />
                  <input
                    className={styles.allocationPctInput}
                    type="number"
                    placeholder="%"
                    value={allocPct}
                    onChange={(e) => setAllocPct(e.target.value)}
                    min="0"
                    max="100"
                  />
                  <button
                    className={styles.formSaveBtn}
                    onClick={handleAddAllocation}
                    disabled={allocSaving || !allocName.trim() || !allocPct}
                    style={{ padding: '4px 12px', fontSize: '0.72rem' }}
                  >
                    {allocSaving ? '...' : '+'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ============================================================ */}
      {/* SECTION 2: ACCOUNT MANAGEMENT (CONTAS BANCÁRIAS)             */}
      {/* ============================================================ */}
      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionIcon}>🏦</div>
          <div>
            <h2 className={styles.sectionTitle}>Contas Bancárias</h2>
            <p className={styles.sectionDesc}>
              Gerenciamento de contas: corrente, cartão de crédito e manual.
            </p>
          </div>
          <button
            className={styles.sectionAction}
            onClick={() => setShowNewAcctForm(!showNewAcctForm)}
          >
            {showNewAcctForm ? 'Cancelar' : '+ Nova'}
          </button>
        </div>

        {/* New account form */}
        {showNewAcctForm && (
          <form className={styles.inlineForm} onSubmit={handleCreateAccount}>
            <input
              className={styles.formInput}
              type="text"
              placeholder="Nome da conta"
              value={newAcctName}
              onChange={(e) => setNewAcctName(e.target.value)}
              autoFocus
            />
            <select
              className={styles.formSelect}
              value={newAcctType}
              onChange={(e) => setNewAcctType(e.target.value)}
            >
              <option value="checking">Corrente</option>
              <option value="credit_card">Cartão de Crédito</option>
              <option value="manual">Manual</option>
            </select>
            <input
              className={styles.dayInput}
              type="number"
              placeholder="Fech."
              title="Dia de fechamento"
              value={newAcctClosingDay}
              onChange={(e) => setNewAcctClosingDay(e.target.value)}
              min="1"
              max="31"
            />
            <input
              className={styles.dayInput}
              type="number"
              placeholder="Venc."
              title="Dia de vencimento"
              value={newAcctDueDay}
              onChange={(e) => setNewAcctDueDay(e.target.value)}
              min="1"
              max="31"
            />
            <button
              className={styles.formSaveBtn}
              type="submit"
              disabled={newAcctSaving || !newAcctName.trim()}
            >
              {newAcctSaving ? '...' : 'Criar'}
            </button>
          </form>
        )}

        <div className={styles.sectionBody}>
          <span className={styles.sectionCount}>
            {allAccounts.length} contas cadastradas
          </span>

          <div className={styles.itemList}>
            {allAccounts.map((acct) => {
              const typeInfo = ACCT_TYPE_MAP[acct.account_type] || { label: acct.account_type, cls: '' }
              return (
                <div key={acct.id} className={styles.acctRow}>
                  <span className={styles.acctName}>{acct.name}</span>
                  <span className={`${styles.accountTypeBadge} ${typeInfo.cls}`}>
                    {typeInfo.label}
                  </span>
                  <span className={styles.acctDetail}>
                    <span className={styles.acctDetailLabel}>Fech.</span>
                    <InlineEdit
                      value={acct.closing_day}
                      onSave={(val) => handleUpdateAccount(acct.id, 'closing_day', val)}
                      format="currency"
                      prefix=""
                      placeholder={'\u2014'}
                      color="var(--color-text-secondary)"
                    />
                  </span>
                  <span className={styles.acctDetail}>
                    <span className={styles.acctDetailLabel}>Venc.</span>
                    <InlineEdit
                      value={acct.due_day}
                      onSave={(val) => handleUpdateAccount(acct.id, 'due_day', val)}
                      format="currency"
                      prefix=""
                      placeholder={'\u2014'}
                      color="var(--color-text-secondary)"
                    />
                  </span>
                  <button
                    className={styles.deleteBtn}
                    onClick={() => handleDeleteAccount(acct.id, acct.name)}
                    title="Excluir conta"
                  >
                    {'\u00d7'}
                  </button>
                </div>
              )
            })}
            {allAccounts.length === 0 && (
              <div className={styles.emptyState}>Nenhuma conta cadastrada</div>
            )}
          </div>
        </div>
      </div>

      {/* ============================================================ */}
      {/* SECTION 3: RECURRING TEMPLATES                               */}
      {/* ============================================================ */}
      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionIcon}>📋</div>
          <div>
            <h2 className={styles.sectionTitle}>Itens Recorrentes</h2>
            <p className={styles.sectionDesc}>
              Template de itens criados automaticamente ao acessar um mês novo.
            </p>
          </div>
          <button
            className={styles.sectionAction}
            onClick={() => setShowNewForm(!showNewForm)}
          >
            {showNewForm ? 'Cancelar' : '+ Novo'}
          </button>
        </div>

        {/* New template form */}
        {showNewForm && (
          <form className={styles.inlineForm} onSubmit={handleCreateTemplate}>
            <input
              className={styles.formInput}
              type="text"
              placeholder="Nome"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              autoFocus
            />
            <select
              className={styles.formSelect}
              value={newType}
              onChange={(e) => setNewType(e.target.value)}
            >
              <option value="Fixo">Fixo</option>
              <option value="Variavel">Variável</option>
              <option value="Income">Entrada</option>
              <option value="Investimento">Investimento</option>
            </select>
            <div className={styles.amountWrap}>
              <span className={styles.amountPrefix}>R$</span>
              <input
                className={styles.amountInput}
                type="number"
                placeholder="0"
                value={newAmount}
                onChange={(e) => setNewAmount(e.target.value)}
                step="0.01"
                min="0"
              />
            </div>
            <input
              className={styles.dayInput}
              type="number"
              placeholder="Dia"
              value={newDueDay}
              onChange={(e) => setNewDueDay(e.target.value)}
              min="1"
              max="31"
            />
            <button
              className={styles.formSaveBtn}
              type="submit"
              disabled={newSaving || !newName.trim() || !newAmount}
            >
              {newSaving ? '...' : 'Criar'}
            </button>
          </form>
        )}

        <div className={styles.sectionBody}>
          <span className={styles.sectionCount}>
            {templatesData?.count || 0} itens configurados
          </span>

          {/* Template groups */}
          {groupOrder.map((groupType) => {
            const items = groupedTemplates[groupType]
            if (!items || items.length === 0) return null
            const groupTotal = items.reduce((s, t) => s + t.default_limit, 0)
            return (
              <div key={groupType} className={styles.tplGroup}>
                <div className={styles.tplGroupHeader}>
                  <span className={styles.tplGroupTitle}>{groupLabels[groupType]}</span>
                  <span className={styles.tplGroupTotal}>
                    R$ {Math.abs(groupTotal).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div className={styles.itemList}>
                  {items.map((tpl) => (
                    <div key={tpl.id} className={styles.tplRow}>
                      <span className={styles.tplDueDay}>
                        {tpl.due_day == null ? (
                          <span style={{ color: 'var(--color-text-secondary)' }}>{'\u2014'}</span>
                        ) : (
                          <InlineEdit
                            value={tpl.due_day}
                            onSave={(val) => handleUpdateTemplate(tpl.id, 'due_day', val)}
                            format="currency"
                            prefix=""
                            placeholder="\u2014"
                            color="var(--color-text-secondary)"
                          />
                        )}
                      </span>
                      <span className={styles.tplName}>
                        <InlineEdit
                          value={tpl.name}
                          onSave={(val) => handleUpdateTemplate(tpl.id, 'name', val)}
                          format="text"
                          prefix=""
                          color="var(--color-text)"
                        />
                      </span>
                      <span className={styles.tplType}>
                        <TemplateTypeSelector
                          value={tpl.template_type}
                          onChange={(val) => handleUpdateTemplate(tpl.id, 'template_type', val)}
                        />
                      </span>
                      <span className={styles.tplAmount}>
                        <InlineEdit
                          value={tpl.default_limit}
                          onSave={(val) => handleUpdateTemplate(tpl.id, 'default_limit', val)}
                          color="var(--color-text)"
                        />
                      </span>
                      <button
                        className={styles.deleteBtn}
                        onClick={() => handleDeleteTemplate(tpl.id, tpl.name)}
                        title="Desativar template"
                      >
                        {'\u00d7'}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ============================================================ */}
      {/* SECTION 4: CATEGORIES & SUBCATEGORIES (taxonomy only)        */}
      {/* ============================================================ */}
      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionIcon}>🏷️</div>
          <div>
            <h2 className={styles.sectionTitle}>Categorias & Subcategorias</h2>
            <p className={styles.sectionDesc}>
              Taxonomia de classificação de transações. Clique no ▸ para ver e adicionar subcategorias.
            </p>
          </div>
          <button
            className={styles.sectionAction}
            onClick={() => setShowNewCatForm(!showNewCatForm)}
          >
            {showNewCatForm ? 'Cancelar' : '+ Nova'}
          </button>
        </div>

        {/* New category form */}
        {showNewCatForm && (
          <form className={styles.inlineForm} onSubmit={handleCreateCategory}>
            <input
              className={styles.formInput}
              type="text"
              placeholder="Nome da categoria"
              value={newCatName}
              onChange={(e) => setNewCatName(e.target.value)}
              autoFocus
            />
            <button
              className={styles.formSaveBtn}
              type="submit"
              disabled={newCatSaving || !newCatName.trim()}
            >
              {newCatSaving ? '...' : 'Criar'}
            </button>
          </form>
        )}

        <div className={styles.sectionBody}>
          <span className={styles.sectionCount}>
            {taxonomyCategories.length} categorias · {taxonomyCategories.reduce((sum, c) => sum + (c.subcategories?.length || 0), 0)} subcategorias
          </span>

          {/* Flat alphabetical list of taxonomy categories */}
          <div className={styles.itemList}>
            {taxonomyCategories.map((cat) => {
              const isExpanded = expandedCat === cat.id
              const subCount = cat.subcategories?.length || 0
              return (
                <div key={cat.id}>
                  <div className={styles.catRow}>
                    <button
                      className={styles.catExpandBtn}
                      onClick={() => setExpandedCat(isExpanded ? null : cat.id)}
                      title={isExpanded ? 'Fechar' : 'Ver subcategorias'}
                    >
                      {isExpanded ? '▾' : '▸'}
                    </button>
                    <span className={styles.catName}>
                      <InlineEdit
                        value={cat.name}
                        onSave={(val) => handleUpdateCategory(cat.id, 'name', val)}
                        format="text"
                        prefix=""
                        color="var(--color-text)"
                      />
                    </span>
                    <span className={styles.catSubBadge}>
                      {subCount} sub
                    </span>
                    <button
                      className={styles.deleteBtn}
                      onClick={() => handleDeleteCategory(cat.id, cat.name)}
                      title="Desativar categoria"
                    >
                      {'\u00d7'}
                    </button>
                  </div>

                  {/* Subcategories (expanded) */}
                  {isExpanded && (
                    <div className={styles.subSection}>
                      {cat.subcategories?.map((sub) => (
                        <div key={sub.id} className={styles.subRow}>
                          <span className={styles.subIndent}>{'\u2514'}</span>
                          <span className={styles.subName}>{sub.name}</span>
                          <button
                            className={styles.deleteBtn}
                            onClick={() => handleDeleteSubcategory(sub.id, sub.name)}
                            title="Excluir subcategoria"
                          >
                            {'\u00d7'}
                          </button>
                        </div>
                      ))}
                      <div className={styles.subAddRow}>
                        <span className={styles.subIndent}>+</span>
                        <input
                          className={styles.subInput}
                          type="text"
                          placeholder="Nova subcategoria..."
                          value={expandedCat === cat.id ? newSubName : ''}
                          onChange={(e) => setNewSubName(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault()
                              handleCreateSubcategory(cat.id)
                            }
                          }}
                        />
                        <button
                          className={styles.formSaveBtn}
                          onClick={() => handleCreateSubcategory(cat.id)}
                          disabled={newSubSaving || !newSubName.trim()}
                          style={{ padding: '3px 10px', fontSize: '0.7rem' }}
                        >
                          {newSubSaving ? '...' : 'Adicionar'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* ============================================================ */}
      {/* SECTION 5: BUDGET & INVESTMENTS (ORÇAMENTO & INVESTIMENTOS)  */}
      {/* ============================================================ */}
      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionIcon}>💰</div>
          <div>
            <h2 className={styles.sectionTitle}>Orçamento & Investimentos</h2>
            <p className={styles.sectionDesc}>
              Resumo de orçamento alocado vs renda, limites por categoria e alocação de investimentos.
            </p>
          </div>
        </div>

        <div className={styles.sectionBody}>
          {/* Budget summary cards */}
          <div className={styles.budgetSummary}>
            <div className={styles.budgetCard}>
              <span className={styles.budgetCardValue} style={{ color: 'var(--color-green)' }}>
                R$ {Math.abs(totalIncome).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
              </span>
              <span className={styles.budgetCardLabel}>Renda Detectada</span>
            </div>
            <div className={styles.budgetCard}>
              <span className={styles.budgetCardValue} style={{ color: 'var(--color-accent)' }}>
                R$ {totalAllocated.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
              </span>
              <span className={styles.budgetCardLabel}>Orçamento Alocado</span>
            </div>
            <div className={styles.budgetCard}>
              <span
                className={styles.budgetCardValue}
                style={{ color: totalIncome - totalAllocated >= 0 ? 'var(--color-green)' : 'var(--color-red)' }}
              >
                R$ {Math.abs(totalIncome - totalAllocated).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
              </span>
              <span className={styles.budgetCardLabel}>
                {totalIncome - totalAllocated >= 0 ? 'Disponível' : 'Acima do Orçamento'}
              </span>
            </div>
          </div>

          {/* Category budget limits with subcategory expansion */}
          <h4 className={styles.subheading}>Limites por Categoria (Variável)</h4>
          <div className={styles.itemList}>
            {taxonomyCategories.map((cat) => {
              const subs = cat.subcategories || []
              const hasSubs = subs.length > 0
              const isBudgetExpanded = expandedBudgetCat === cat.id
              return (
                <div key={cat.id}>
                  <div className={styles.budgetTableRow}>
                    {hasSubs ? (
                      <button
                        className={styles.catExpandBtn}
                        onClick={() => setExpandedBudgetCat(isBudgetExpanded ? null : cat.id)}
                        title={isBudgetExpanded ? 'Fechar' : 'Ver subcategorias'}
                      >
                        {isBudgetExpanded ? '▾' : '▸'}
                      </button>
                    ) : (
                      <span style={{ width: 24, display: 'inline-block' }} />
                    )}
                    <span className={styles.budgetCatName}>{cat.name}</span>
                    <span className={styles.budgetLimit}>
                      <InlineEdit
                        value={cat.default_limit || 0}
                        onSave={(val) => handleUpdateCategory(cat.id, 'default_limit', val)}
                        color="var(--color-text)"
                      />
                    </span>
                  </div>
                  {/* Subcategory limits */}
                  {isBudgetExpanded && subs.map((sub) => (
                    <div key={sub.id} className={styles.budgetTableRow} style={{ paddingLeft: 32, opacity: 0.85 }}>
                      <span className={styles.subIndent}>{'\u2514'}</span>
                      <span className={styles.budgetCatName} style={{ fontSize: '0.82rem' }}>{sub.name}</span>
                      <span className={styles.budgetLimit}>
                        <InlineEdit
                          value={sub.default_limit || 0}
                          onSave={(val) => handleUpdateSubcategory(sub.id, 'default_limit', val)}
                          color="var(--color-text)"
                        />
                      </span>
                    </div>
                  ))}
                </div>
              )
            })}
            {taxonomyCategories.length === 0 && (
              <div className={styles.emptyState}>Nenhuma categoria variável</div>
            )}
          </div>

          {/* Investment allocation visualization */}
          {investmentAllocation.length > 0 && (
            <>
              <h4 className={styles.subheading}>Alocação de Investimentos</h4>
              <div className={styles.itemList}>
                {investmentAllocation.map((item, idx) => (
                  <div key={idx} className={styles.allocationRow}>
                    <span className={styles.allocationName}>{item.name}</span>
                    <div className={styles.allocationBar}>
                      <div
                        className={styles.allocationBarFill}
                        style={{ width: `${Math.min(item.pct, 100)}%` }}
                      />
                    </div>
                    <span className={styles.allocationPct}>{item.pct}%</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* ============================================================ */}
      {/* SECTION 6: RENAME RULES (REGRAS DE RENOMEAÇÃO)               */}
      {/* ============================================================ */}
      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionIcon}>✏️</div>
          <div>
            <h2 className={styles.sectionTitle}>Regras de Renomeação</h2>
            <p className={styles.sectionDesc}>
              Regras para renomear descrições de transações automaticamente. Quando a descrição contém a palavra-chave, o nome é substituído.
            </p>
          </div>
          <button
            className={styles.sectionAction}
            onClick={() => setShowNewRenameForm(!showNewRenameForm)}
          >
            {showNewRenameForm ? 'Cancelar' : '+ Nova'}
          </button>
        </div>

        {/* New rename rule form */}
        {showNewRenameForm && (
          <form className={styles.inlineForm} onSubmit={handleCreateRename}>
            <input
              className={styles.formInput}
              type="text"
              placeholder="Palavra-chave (ex: PIX JOAO)"
              value={newRenameKeyword}
              onChange={(e) => setNewRenameKeyword(e.target.value)}
              autoFocus
            />
            <input
              className={styles.formInput}
              type="text"
              placeholder="Nome exibido (ex: João — Aluguel)"
              value={newRenameDisplay}
              onChange={(e) => setNewRenameDisplay(e.target.value)}
            />
            <button
              className={styles.formSaveBtn}
              type="submit"
              disabled={newRenameSaving || !newRenameKeyword.trim() || !newRenameDisplay.trim()}
            >
              {newRenameSaving ? '...' : 'Criar'}
            </button>
          </form>
        )}

        <div className={styles.sectionBody}>
          {/* Search + count */}
          <div className={styles.ruleToolbar}>
            <input
              className={styles.ruleSearchInput}
              type="text"
              placeholder="Buscar regras de renomeação..."
              value={renameSearch}
              onChange={(e) => setRenameSearch(e.target.value)}
            />
            <span className={styles.sectionCount}>
              {filteredRenames.length} ativas
            </span>
          </div>

          {/* Rename rules list */}
          <div className={styles.ruleList}>
            {filteredRenames.map((rule) => (
              <div key={rule.id} className={styles.renameRow}>
                <span className={styles.renameKeyword}>
                  <InlineEdit
                    value={rule.keyword}
                    onSave={(val) => handleUpdateRename(rule.id, 'keyword', val)}
                    format="text"
                    prefix=""
                    color="var(--color-accent)"
                  />
                </span>
                <span className={styles.renameArrow}>&rarr;</span>
                <span className={styles.renameDisplay}>
                  <InlineEdit
                    value={rule.display_name}
                    onSave={(val) => handleUpdateRename(rule.id, 'display_name', val)}
                    format="text"
                    prefix=""
                    color="var(--color-text)"
                  />
                </span>
                <button
                  className={styles.deleteBtn}
                  onClick={() => handleDeleteRename(rule.id, rule.keyword)}
                  title="Desativar regra"
                >
                  {'\u00d7'}
                </button>
              </div>
            ))}
            {filteredRenames.length === 0 && (
              <div className={styles.emptyState}>
                {renameSearch ? 'Nenhuma regra encontrada' : 'Nenhuma regra de renomeação cadastrada'}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ============================================================ */}
      {/* SECTION 7: IMPORT                                            */}
      {/* ============================================================ */}
      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionIcon}>📥</div>
          <div>
            <h2 className={styles.sectionTitle}>Importar Extratos</h2>
            <p className={styles.sectionDesc}>
              Upload de extratos OFX, CSV ou TXT do Itaú.
            </p>
          </div>
        </div>

        <div className={styles.sectionBody}>
          {/* Instructions — dynamic from bank templates or fallback */}
          <div className={styles.instructions}>
            <h3>Formatos Aceitos</h3>
            {bankTemplates.length > 0 ? (
              Object.entries(groupedBankTemplates).map(([bankName, templates]) => (
                <div key={bankName} className={styles.bankGroup}>
                  <div className={styles.bankGroupTitle}>{bankName}</div>
                  <div className={styles.formatGrid}>
                    {templates.map((tpl) => (
                      <div key={tpl.id} className={styles.formatCard}>
                        {tpl.is_recommended && (
                          <div className={styles.formatBadge} data-type="best">RECOMENDADO</div>
                        )}
                        {!tpl.is_recommended && (
                          <div className={styles.formatBadge} data-type="ok">ALTERNATIVA</div>
                        )}
                        <h4>{tpl.name}</h4>
                        {tpl.import_instructions && (
                          <div className={styles.bankInstructions}>{tpl.import_instructions}</div>
                        )}
                        {tpl.file_pattern && <code>{tpl.file_pattern}</code>}
                      </div>
                    ))}
                  </div>
                </div>
              ))
            ) : (
              <div className={styles.formatGrid}>
                <div className={styles.formatCard}>
                  <div className={styles.formatBadge} data-type="best">RECOMENDADO</div>
                  <h4>Conta Corrente — OFX</h4>
                  <p>Exportar do Itau: Extrato &rarr; Exportar &rarr; OFX/Money</p>
                  <code>Extrato Conta Corrente-*.ofx</code>
                  <ul>
                    <li>Formato estruturado, sem ambiguidade</li>
                    <li>Valores com sinal correto (+/-)</li>
                    <li>Melhor cobertura de dados</li>
                  </ul>
                </div>
                <div className={styles.formatCard}>
                  <div className={styles.formatBadge} data-type="ok">ALTERNATIVA</div>
                  <h4>Conta Corrente — TXT</h4>
                  <p>Exportar do Itau: Extrato &rarr; Exportar &rarr; TXT</p>
                  <code>Extrato Conta Corrente-*.txt</code>
                  <ul>
                    <li>Funciona, mas menos preciso que OFX</li>
                    <li>Ignorado automaticamente se OFX existir</li>
                  </ul>
                </div>
                <div className={styles.formatCard}>
                  <div className={styles.formatBadge} data-type="ok">ALTERNATIVA</div>
                  <h4>Conta Corrente — PDF</h4>
                  <p>Exportar do Itau: Extrato &rarr; Salvar como PDF</p>
                  <ul>
                    <li className={styles.warn}>Nao suportado para import automatico</li>
                    <li>Use apenas para conferencia manual</li>
                  </ul>
                </div>
                <div className={styles.formatCard}>
                  <div className={styles.formatBadge} data-type="best">RECOMENDADO</div>
                  <h4>Cartao de Credito — CSV</h4>
                  <p>Exportar do Itau: Fatura &rarr; Baixar CSV</p>
                  <code>itau-master-YYYYMMDD.csv</code>
                  <code>itau-visa-YYYYMMDD.csv</code>
                  <ul>
                    <li>Renomear com prefixo <strong>itau-master-</strong> ou <strong>itau-visa-</strong></li>
                    <li>O sistema converte automaticamente para o formato interno</li>
                    <li>Formato: data, lancamento, valor (3 colunas)</li>
                  </ul>
                </div>
              </div>
            )}
          </div>

          {/* Upload zone */}
          <div
            className={`${styles.dropZone} ${dragOver ? styles.dragOver : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileRef.current?.click()}
          >
            <input
              ref={fileRef}
              type="file"
              multiple
              accept=".ofx,.csv,.txt"
              style={{ display: 'none' }}
              onChange={(e) => handleFiles(Array.from(e.target.files))}
            />
            <div className={styles.dropIcon}>
              {uploading ? '...' : '+'}
            </div>
            <p>{uploading ? 'Enviando...' : 'Arraste arquivos aqui ou clique para selecionar'}</p>
            <span className={styles.dropHint}>.ofx, .csv, .txt</span>
          </div>

          {/* Upload result */}
          {uploadResult && (
            <div className={uploadResult.success ? styles.successMsg : styles.errorMsg}>
              {uploadResult.success ? (
                <>
                  <strong>{uploadResult.uploaded} arquivo(s) enviado(s)</strong>
                  <ul>
                    {uploadResult.files?.map((f, i) => (
                      <li key={i}>{f.original} &rarr; <code>{f.saved_as}</code> ({fmtSize(f.size)})</li>
                    ))}
                  </ul>
                </>
              ) : (
                <span>Erro: {uploadResult.error}</span>
              )}
            </div>
          )}

          {/* Import button */}
          <div className={styles.importSection}>
            <button
              className={styles.importBtn}
              onClick={handleRunImport}
              disabled={importing}
            >
              {importing ? 'Importando...' : 'Reimportar Todos os Dados'}
            </button>
            <span className={styles.importHint}>
              Limpa o banco e reimporta todos os arquivos de SampleData
            </span>
          </div>

          {/* Import result */}
          {importResult && (
            <div className={importResult.success ? styles.successMsg : styles.errorMsg}>
              {importResult.success ? (
                <span>
                  Importacao concluida: <strong>{importResult.transactions}</strong> transacoes,{' '}
                  <strong>{importResult.months}</strong> meses
                  {importResult.new_transactions != null && importResult.new_transactions !== importResult.transactions && (
                    <> ({importResult.new_transactions} novas)</>
                  )}
                </span>
              ) : (
                <span>Erro na importacao: {importResult.error}</span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ============================================================ */}
      {/* SECTION 8: SALARY PROJECTION                                 */}
      {/* ============================================================ */}
      <SalarySection
        config={salaryConfig}
        projection={salaryProjection}
        templates={templatesData?.templates || []}
        editing={salaryEditing}
        setEditing={setSalaryEditing}
        syncing={salarySyncing}
        syncResult={salarySyncResult}
        onSync={handleSalarySync}
        onSave={handleSalaryConfigSave}
      />

      {/* ============================================================ */}
      {/* SECTION 9: STATUS                                            */}
      {/* ============================================================ */}
      {status && (
        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <div className={styles.sectionIcon}>📊</div>
            <div>
              <h2 className={styles.sectionTitle}>Status do Banco</h2>
              <p className={styles.sectionDesc}>
                Visão geral dos dados importados.
              </p>
            </div>
          </div>

          <div className={styles.sectionBody}>
            <div className={styles.statsGrid}>
              <div className={styles.stat}>
                <span className={styles.statValue}>{status.transactions?.toLocaleString('pt-BR')}</span>
                <span className={styles.statLabel}>Transacoes</span>
              </div>
              <div className={styles.stat}>
                <span className={styles.statValue}>{status.months}</span>
                <span className={styles.statLabel}>Meses</span>
              </div>
              <div className={styles.stat}>
                <span className={styles.statValue}>{status.earliest}</span>
                <span className={styles.statLabel}>Mais antigo</span>
              </div>
              <div className={styles.stat}>
                <span className={styles.statValue}>{status.latest}</span>
                <span className={styles.statLabel}>Mais recente</span>
              </div>
            </div>

            <h4 className={styles.subheading}>Transacoes por Conta</h4>
            <div className={styles.accountList}>
              {status.accounts && Object.entries(status.accounts).map(([name, count]) => (
                <div key={name} className={styles.accountRow}>
                  <span>{name}</span>
                  <span className={styles.accountCount}>{count.toLocaleString('pt-BR')}</span>
                </div>
              ))}
            </div>

            <h4 className={styles.subheading}>Arquivos em SampleData ({status.files?.length})</h4>
            <div className={styles.fileList}>
              {status.files?.map((f, i) => (
                <div key={i} className={styles.fileRow}>
                  <span className={styles.fileName}>{f.name}</span>
                  <span className={styles.fileSize}>{fmtSize(f.size)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Settings
