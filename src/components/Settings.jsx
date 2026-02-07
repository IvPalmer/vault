import { useState, useRef, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'
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


function Settings() {
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

  const { data: status, refetch: refetchStatus } = useQuery({
    queryKey: ['import-status'],
    queryFn: () => api.get('/import/'),
  })

  // Recurring templates query
  const { data: templatesData, refetch: refetchTemplates } = useQuery({
    queryKey: ['recurring-templates'],
    queryFn: () => api.get('/analytics/recurring/templates/'),
  })

  const handleFiles = useCallback(async (files) => {
    if (!files.length) return
    setUploading(true)
    setUploadResult(null)

    const formData = new FormData()
    for (const file of files) {
      formData.append('files', file)
    }

    try {
      const res = await fetch(`${API_BASE}/import/?action=upload`, {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()
      if (res.ok) {
        setUploadResult({ success: true, ...data })
        refetchStatus()
      } else {
        setUploadResult({ success: false, error: data.error || 'Upload failed' })
      }
    } catch (err) {
      setUploadResult({ success: false, error: err.message })
    } finally {
      setUploading(false)
    }
  }, [refetchStatus])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    handleFiles(Array.from(e.dataTransfer.files))
  }, [handleFiles])

  const handleRunImport = async () => {
    setImporting(true)
    setImportResult(null)
    try {
      const res = await fetch(`${API_BASE}/import/?action=run`, {
        method: 'POST',
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
        category_type: newType,
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

  const fmtSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  // Group templates by type
  const groupedTemplates = {}
  if (templatesData?.templates) {
    for (const tpl of templatesData.templates) {
      const group = tpl.category_type
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

  return (
    <div className={styles.container}>
      {/* ---- RECURRING TEMPLATES ---- */}
      <h2 className={styles.heading}>Itens Recorrentes (Template)</h2>
      <p className={styles.templateDesc}>
        Estes itens são automaticamente criados ao acessar um mês novo.
        Edite aqui para alterar o padrão de meses futuros.
      </p>

      <div className={styles.templateSection}>
        <div className={styles.templateHeader}>
          <span className={styles.templateCount}>
            {templatesData?.count || 0} itens configurados
          </span>
          <button
            className={styles.addTplBtn}
            onClick={() => setShowNewForm(!showNewForm)}
          >
            {showNewForm ? 'Cancelar' : '+ Novo Template'}
          </button>
        </div>

        {/* New template form */}
        {showNewForm && (
          <form className={styles.newTplForm} onSubmit={handleCreateTemplate}>
            <input
              className={styles.tplInput}
              type="text"
              placeholder="Nome"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              autoFocus
            />
            <select
              className={styles.tplSelect}
              value={newType}
              onChange={(e) => setNewType(e.target.value)}
            >
              <option value="Fixo">Fixo</option>
              <option value="Variavel">Variável</option>
              <option value="Income">Entrada</option>
              <option value="Investimento">Investimento</option>
            </select>
            <div className={styles.tplAmountWrap}>
              <span className={styles.tplPrefix}>R$</span>
              <input
                className={styles.tplAmountInput}
                type="number"
                placeholder="0"
                value={newAmount}
                onChange={(e) => setNewAmount(e.target.value)}
                step="0.01"
                min="0"
              />
            </div>
            <input
              className={styles.tplDayInput}
              type="number"
              placeholder="Dia"
              value={newDueDay}
              onChange={(e) => setNewDueDay(e.target.value)}
              min="1"
              max="31"
            />
            <button
              className={styles.tplSaveBtn}
              type="submit"
              disabled={newSaving || !newName.trim() || !newAmount}
            >
              {newSaving ? '...' : 'Criar'}
            </button>
          </form>
        )}

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
              <div className={styles.tplList}>
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
                        value={tpl.category_type}
                        onChange={(val) => handleUpdateTemplate(tpl.id, 'category_type', val)}
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
                      className={styles.tplDeleteBtn}
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

      {/* ---- IMPORT SECTION ---- */}
      <h2 className={styles.heading}>Importar Extratos</h2>

      {/* Instructions */}
      <div className={styles.instructions}>
        <h3>Formatos Aceitos</h3>
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
            </span>
          ) : (
            <span>Erro na importacao: {importResult.error}</span>
          )}
        </div>
      )}

      {/* Current status */}
      {status && (
        <div className={styles.statusSection}>
          <h3>Status Atual</h3>
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
      )}
    </div>
  )
}

export default Settings
