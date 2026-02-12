import { useReducer, useCallback, useMemo, useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'
import { useProfile } from '../context/ProfileContext'
import styles from './SetupWizard.module.css'

// ── Constants ──────────────────────────────────────────────────
const TOTAL_STEPS = 10

const FALLBACK_ORDER = [
  'entradas_atuais', 'entradas_projetadas', 'a_entrar', 'a_pagar',
  'dias_fechamento', 'gastos_atuais', 'gastos_projetados', 'gastos_fixos',
  'gastos_variaveis', 'diario_max', 'fatura_master', 'fatura_visa',
  'parcelas', 'saldo_projetado', 'saude', 'meta_poupanca',
]

const CARD_LABELS = {
  entradas_atuais: 'Entradas Atuais',
  entradas_projetadas: 'Entradas Projetadas',
  gastos_atuais: 'Gastos Atuais',
  gastos_projetados: 'Gastos Projetados',
  saldo_projetado: 'Saldo Projetado',
  saldo_conta: 'Saldo em Conta',
  a_entrar: 'A Entrar',
  a_pagar: 'A Pagar',
  gastos_fixos: 'Gastos Fixos',
  gastos_variaveis: 'Gastos Variaveis',
  parcelas: 'Parcelas',
  dias_fechamento: 'Dias ate Fechamento',
  diario_max: 'Gasto Diario Recomendado',
  saude: 'Saude do Mes',
  meta_poupanca: 'Meta Poupanca',
  fatura_master: 'Fatura Mastercard',
  fatura_visa: 'Fatura Visa',
}

const ACCT_TYPE_LABELS = {
  checking: 'Conta Corrente',
  credit_card: 'Cartao de Credito',
}

const STEP_TITLES = {
  1: 'Dados do Perfil',
  2: 'Selecionar Bancos',
  3: 'Configurar Cartoes',
  4: 'Modo de Visualizacao',
  5: 'Itens Recorrentes',
  6: 'Categorias & Orcamento',
  7: 'Regras de Renomeacao',
  8: 'Regras de Categorizacao',
  9: 'Cartoes do Dashboard',
  10: 'Revisao',
}

// ── Reducer ────────────────────────────────────────────────────
const initialState = {
  step: 1,
  wizardMode: 'new', // 'new' | 'edit' | 'template'
  showModeSelection: false,
  loadedTemplateId: null,
  profileName: '',
  selectedTemplates: [],
  cardConfigs: {},
  ccDisplayMode: 'invoice',
  recurringSource: null,
  recurringItems: [],
  categorySource: null,
  categories: [],
  budgetLimits: [],
  savingsTarget: 20,
  investmentTarget: 10,
  investmentAllocation: [],
  renameRules: [],
  categorizationRules: [],
  cardOrder: [...FALLBACK_ORDER],
  hiddenCards: [],
}

function reducer(state, action) {
  switch (action.type) {
    case 'SET_STEP':
      return { ...state, step: action.payload }
    case 'NEXT_STEP':
      return { ...state, step: Math.min(state.step + 1, TOTAL_STEPS) }
    case 'PREV_STEP':
      return { ...state, step: Math.max(state.step - 1, 1) }
    case 'SET_WIZARD_MODE':
      return { ...state, wizardMode: action.payload }
    case 'SET_SHOW_MODE_SELECTION':
      return { ...state, showModeSelection: action.payload }
    case 'SET_PROFILE_NAME':
      return { ...state, profileName: action.payload }
    case 'TOGGLE_TEMPLATE': {
      const tpl = action.payload
      const exists = state.selectedTemplates.find(t => t.id === tpl.id)
      const selectedTemplates = exists
        ? state.selectedTemplates.filter(t => t.id !== tpl.id)
        : [...state.selectedTemplates, tpl]
      const cardConfigs = { ...state.cardConfigs }
      if (!exists && tpl.account_type === 'credit_card') {
        cardConfigs[tpl.id] = {
          closing_day: tpl.default_closing_day || 1,
          due_day: tpl.default_due_day || 10,
          credit_limit: '',
          display_name: tpl.display_name || tpl.bank_name,
        }
      } else if (exists) {
        delete cardConfigs[tpl.id]
      }
      return { ...state, selectedTemplates, cardConfigs }
    }
    case 'SET_CARD_CONFIG':
      return {
        ...state,
        cardConfigs: {
          ...state.cardConfigs,
          [action.payload.id]: {
            ...state.cardConfigs[action.payload.id],
            ...action.payload.data,
          },
        },
      }
    case 'SET_CC_DISPLAY_MODE':
      return { ...state, ccDisplayMode: action.payload }
    case 'SET_RECURRING_SOURCE':
      return { ...state, recurringSource: action.payload }
    case 'SET_RECURRING_ITEMS':
      return { ...state, recurringItems: action.payload }
    case 'TOGGLE_RECURRING_ITEM': {
      const items = state.recurringItems.map((item, i) =>
        i === action.payload ? { ...item, included: !item.included } : item
      )
      return { ...state, recurringItems: items }
    }
    case 'UPDATE_RECURRING_ITEM': {
      const items = state.recurringItems.map((item, i) =>
        i === action.payload.index ? { ...item, ...action.payload.data } : item
      )
      return { ...state, recurringItems: items }
    }
    case 'SET_CATEGORY_SOURCE':
      return { ...state, categorySource: action.payload }
    case 'SET_CATEGORIES':
      return { ...state, categories: action.payload }
    case 'SET_BUDGET_LIMITS':
      return { ...state, budgetLimits: action.payload }
    case 'UPDATE_BUDGET_LIMIT': {
      const limits = state.budgetLimits.map((b, i) =>
        i === action.payload.index ? { ...b, suggested_limit: action.payload.value } : b
      )
      return { ...state, budgetLimits: limits }
    }
    case 'SET_SAVINGS_TARGET':
      return { ...state, savingsTarget: action.payload }
    case 'SET_INVESTMENT_TARGET':
      return { ...state, investmentTarget: action.payload }
    case 'SET_INVESTMENT_ALLOCATION':
      return { ...state, investmentAllocation: action.payload }
    case 'ADD_ALLOCATION':
      return {
        ...state,
        investmentAllocation: [...state.investmentAllocation, action.payload],
      }
    case 'REMOVE_ALLOCATION':
      return {
        ...state,
        investmentAllocation: state.investmentAllocation.filter((_, i) => i !== action.payload),
      }
    case 'UPDATE_ALLOCATION': {
      const alloc = state.investmentAllocation.map((a, i) =>
        i === action.payload.index ? { ...a, ...action.payload.data } : a
      )
      return { ...state, investmentAllocation: alloc }
    }
    case 'SET_RENAME_RULES':
      return { ...state, renameRules: action.payload }
    case 'ADD_RENAME_RULE':
      return { ...state, renameRules: [...state.renameRules, action.payload] }
    case 'REMOVE_RENAME_RULE':
      return { ...state, renameRules: state.renameRules.filter((_, i) => i !== action.payload) }
    case 'UPDATE_RENAME_RULE': {
      const rules = state.renameRules.map((r, i) =>
        i === action.payload.index ? { ...r, ...action.payload.data } : r
      )
      return { ...state, renameRules: rules }
    }
    case 'SET_CATEGORIZATION_RULES':
      return { ...state, categorizationRules: action.payload }
    case 'ADD_CATEGORIZATION_RULE':
      return { ...state, categorizationRules: [...state.categorizationRules, action.payload] }
    case 'REMOVE_CATEGORIZATION_RULE':
      return { ...state, categorizationRules: state.categorizationRules.filter((_, i) => i !== action.payload) }
    case 'UPDATE_CATEGORIZATION_RULE': {
      const rules = state.categorizationRules.map((r, i) =>
        i === action.payload.index ? { ...r, ...action.payload.data } : r
      )
      return { ...state, categorizationRules: rules }
    }
    case 'SET_CARD_ORDER':
      return { ...state, cardOrder: action.payload }
    case 'TOGGLE_HIDDEN_CARD': {
      const card = action.payload
      const hidden = state.hiddenCards.includes(card)
        ? state.hiddenCards.filter(c => c !== card)
        : [...state.hiddenCards, card]
      return { ...state, hiddenCards: hidden }
    }
    case 'MOVE_CARD': {
      const { index, direction } = action.payload
      const order = [...state.cardOrder]
      const newIndex = index + direction
      if (newIndex < 0 || newIndex >= order.length) return state
      ;[order[index], order[newIndex]] = [order[newIndex], order[index]]
      return { ...state, cardOrder: order }
    }
    case 'LOAD_TEMPLATE': {
      // Load full wizard state from a SetupTemplate's template_data
      const td = action.payload
      return {
        ...state,
        wizardMode: 'template',
        loadedTemplateId: td._templateId || null,
        selectedTemplates: [], // Templates use bank_accounts, not selectedTemplates
        cardConfigs: {},
        ccDisplayMode: td.cc_display_mode || 'invoice',
        recurringSource: td.recurring_templates?.length > 0 ? 'template' : null,
        recurringItems: (td.recurring_templates || []).map(r => ({ ...r, included: true })),
        categorySource: td.categories?.length > 0 ? 'template' : null,
        categories: (td.categories || []).map(c => typeof c === 'string' ? c : c.name),
        budgetLimits: (td.categories || []).filter(c => typeof c === 'object').map(c => ({
          category: c.name,
          avg_monthly: 0,
          suggested_limit: c.limit || 0,
        })),
        savingsTarget: td.savings_target_pct || 20,
        investmentTarget: td.investment_target_pct || 10,
        investmentAllocation: Array.isArray(td.investment_allocation)
          ? td.investment_allocation
          : Object.entries(td.investment_allocation || {}).map(([name, percentage]) => ({ name, percentage })),
        renameRules: td.rename_rules || [],
        categorizationRules: td.categorization_rules || [],
        cardOrder: td.metricas_config?.card_order || [...FALLBACK_ORDER],
        hiddenCards: td.metricas_config?.hidden_cards || [],
      }
    }
    case 'LOAD_EXISTING_CONFIG': {
      // Load from ProfileSetupStateView response for edit mode
      const cfg = action.payload
      return {
        ...state,
        wizardMode: 'edit',
        profileName: cfg.name || '',
        selectedTemplates: [],
        cardConfigs: {},
        ccDisplayMode: cfg.cc_display_mode || 'invoice',
        recurringSource: cfg.recurring_templates?.length > 0 ? 'existing' : null,
        recurringItems: (cfg.recurring_templates || []).map(r => ({ ...r, included: true })),
        categorySource: cfg.categories?.length > 0 ? 'existing' : null,
        categories: (cfg.categories || []).map(c => typeof c === 'string' ? c : c.name),
        budgetLimits: (cfg.categories || []).filter(c => typeof c === 'object').map(c => ({
          category: c.name,
          avg_monthly: 0,
          suggested_limit: c.limit || 0,
        })),
        savingsTarget: cfg.savings_target_pct || 20,
        investmentTarget: cfg.investment_target_pct || 10,
        investmentAllocation: Array.isArray(cfg.investment_allocation)
          ? cfg.investment_allocation
          : Object.entries(cfg.investment_allocation || {}).map(([name, percentage]) => ({ name, percentage })),
        renameRules: cfg.rename_rules || [],
        categorizationRules: cfg.categorization_rules || [],
        cardOrder: cfg.metricas_config?.card_order || [...FALLBACK_ORDER],
        hiddenCards: cfg.metricas_config?.hidden_cards || [],
      }
    }
    case 'RESET_STATE':
      return { ...initialState, wizardMode: state.wizardMode, showModeSelection: false }
    default:
      return state
  }
}

// ── Helper: Build submission payload ──────────────────────────
function buildPayload(state) {
  // Transform frontend wizard state into backend-expected format
  const bankAccounts = state.selectedTemplates.map(tpl => {
    const config = state.cardConfigs[tpl.id] || {}
    return {
      bank_template_id: tpl.id,
      display_name: config.display_name || tpl.display_name || tpl.bank_name,
      account_type: tpl.account_type,
      closing_day: config.closing_day || tpl.default_closing_day || null,
      due_day: config.due_day || tpl.default_due_day || null,
      credit_limit: config.credit_limit ? parseFloat(config.credit_limit) : null,
    }
  })

  const recurringTemplates = state.recurringItems
    .filter(r => r.included)
    .map(r => ({
      name: r.name,
      type: r.type || r.template_type || 'Fixo',
      amount: parseFloat(r.amount || r.default_limit || 0),
      due_day: r.due_day || null,
    }))

  const categories = state.budgetLimits.length > 0
    ? state.budgetLimits.map(b => ({
        name: b.category || b.name,
        type: b.type || 'Variavel',
        limit: parseFloat(b.suggested_limit || 0),
        due_day: b.due_day || null,
      }))
    : state.categories.map(c => ({
        name: typeof c === 'string' ? c : c.name,
        type: typeof c === 'object' ? (c.type || c.category_type || 'Variavel') : 'Variavel',
        limit: typeof c === 'object' ? parseFloat(c.limit || c.default_limit || 0) : 0,
        due_day: null,
      }))

  return {
    reset_mode: state.wizardMode === 'edit',
    name: state.profileName || undefined,
    savings_target_pct: state.savingsTarget,
    investment_target_pct: state.investmentTarget,
    investment_allocation: state.investmentAllocation,
    budget_strategy: 'percentage',
    bank_accounts: bankAccounts,
    cc_display_mode: state.ccDisplayMode,
    recurring_templates: recurringTemplates,
    categories,
    rename_rules: state.renameRules.filter(r => r.keyword && r.display_name),
    categorization_rules: state.categorizationRules.filter(r => r.keyword && r.category_name),
    metricas_config: {
      card_order: state.cardOrder,
      hidden_cards: state.hiddenCards,
    },
  }
}

// ── Main Component ─────────────────────────────────────────────
export default function SetupWizard({ onClose, editMode = false }) {
  const [state, dispatch] = useReducer(reducer, {
    ...initialState,
    showModeSelection: editMode,
    wizardMode: editMode ? 'edit' : 'new',
  })
  const queryClient = useQueryClient()
  const { profiles, profileId, currentProfile } = useProfile()
  const [confirmReset, setConfirmReset] = useState(false)
  const [saveTemplateName, setSaveTemplateName] = useState('')
  const [showSaveTemplate, setShowSaveTemplate] = useState(false)

  // ── API queries ──
  const { data: bankTemplates = [], isLoading: loadingTemplates } = useQuery({
    queryKey: ['bank-templates'],
    queryFn: () => api.get('/bank-templates/'),
  })

  const [analyzeTriggered, setAnalyzeTriggered] = useState(false)
  const { data: analyzeData, isLoading: loadingAnalyze, error: analyzeError } = useQuery({
    queryKey: ['analyze-setup'],
    queryFn: () => api.get('/analytics/analyze-setup/'),
    enabled: analyzeTriggered,
    staleTime: 5 * 60 * 1000,
  })

  const { data: setupTemplates = [] } = useQuery({
    queryKey: ['setup-templates'],
    queryFn: () => api.get('/setup-templates/'),
    enabled: editMode,
  })

  // Load existing config when in edit mode
  const { data: existingConfig } = useQuery({
    queryKey: ['setup-state', profileId],
    queryFn: () => api.get(`/profiles/${profileId}/setup-state/`),
    enabled: editMode && state.wizardMode === 'edit',
  })

  // Pre-fill from existing config
  const prevConfigRef = useRef(null)
  useEffect(() => {
    if (existingConfig && existingConfig !== prevConfigRef.current && state.wizardMode === 'edit' && !state.showModeSelection) {
      prevConfigRef.current = existingConfig
      dispatch({ type: 'LOAD_EXISTING_CONFIG', payload: existingConfig })
    }
  }, [existingConfig, state.wizardMode, state.showModeSelection])

  // ── Submit mutation ──
  const submitMutation = useMutation({
    mutationFn: (payload) => api.post(`/profiles/${profileId}/setup/`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] })
      queryClient.invalidateQueries({ queryKey: ['metricas'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      queryClient.invalidateQueries({ queryKey: ['recurring-templates'] })
      queryClient.invalidateQueries({ queryKey: ['renames'] })
      queryClient.invalidateQueries({ queryKey: ['rules'] })
      onClose()
    },
  })

  // Save template mutation
  const saveTemplateMutation = useMutation({
    mutationFn: (payload) => api.post(`/profiles/${profileId}/export-setup/`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['setup-templates'] })
      setShowSaveTemplate(false)
      setSaveTemplateName('')
    },
  })

  // ── Grouped bank templates ──
  const groupedTemplates = useMemo(() => {
    const groups = {}
    const list = Array.isArray(bankTemplates) ? bankTemplates : bankTemplates?.results || []
    for (const t of list) {
      const key = t.bank_name || 'Outros'
      if (!groups[key]) groups[key] = []
      groups[key].push(t)
    }
    return groups
  }, [bankTemplates])

  // CC templates from selection
  const ccTemplates = useMemo(
    () => state.selectedTemplates.filter(t => t.account_type === 'credit_card'),
    [state.selectedTemplates]
  )

  // ── Handlers ──
  const handleNext = useCallback(() => {
    if (state.step === 4) {
      setAnalyzeTriggered(true)
    }
    dispatch({ type: 'NEXT_STEP' })
  }, [state.step])

  const handleSmartRecurring = useCallback(() => {
    dispatch({ type: 'SET_RECURRING_SOURCE', payload: 'smart' })
    setAnalyzeTriggered(true)
    if (analyzeData?.recurring_items) {
      dispatch({
        type: 'SET_RECURRING_ITEMS',
        payload: analyzeData.recurring_items.map(r => ({ ...r, included: true })),
      })
    }
  }, [analyzeData])

  const handleSmartCategories = useCallback(() => {
    dispatch({ type: 'SET_CATEGORY_SOURCE', payload: 'smart' })
    setAnalyzeTriggered(true)
    if (analyzeData?.budget_analysis) {
      dispatch({ type: 'SET_BUDGET_LIMITS', payload: analyzeData.budget_analysis })
    }
    if (analyzeData?.categories) {
      dispatch({ type: 'SET_CATEGORIES', payload: analyzeData.categories })
    }
  }, [analyzeData])

  // When analyze data arrives, update state if source is 'smart'
  const prevAnalyzeRef = useRef(null)
  useEffect(() => {
    if (analyzeData && analyzeData !== prevAnalyzeRef.current) {
      prevAnalyzeRef.current = analyzeData
      if (state.recurringSource === 'smart' && analyzeData.recurring_items && state.recurringItems.length === 0) {
        dispatch({
          type: 'SET_RECURRING_ITEMS',
          payload: analyzeData.recurring_items.map(r => ({ ...r, included: true })),
        })
      }
      if (state.categorySource === 'smart' && analyzeData.budget_analysis && state.budgetLimits.length === 0) {
        dispatch({ type: 'SET_BUDGET_LIMITS', payload: analyzeData.budget_analysis })
      }
      if (state.categorySource === 'smart' && analyzeData.categories && state.categories.length === 0) {
        dispatch({ type: 'SET_CATEGORIES', payload: analyzeData.categories })
      }
    }
  }, [analyzeData, state.recurringSource, state.categorySource, state.recurringItems.length, state.budgetLimits.length, state.categories.length])

  const handleSubmit = useCallback(() => {
    const payload = buildPayload(state)
    submitMutation.mutate(payload)
  }, [state, submitMutation])

  const handleSaveTemplate = useCallback(() => {
    saveTemplateMutation.mutate({
      name: saveTemplateName || `${currentProfile?.name || 'Profile'} Config`,
      description: `Saved from wizard on ${new Date().toLocaleDateString('pt-BR')}`,
    })
  }, [saveTemplateName, currentProfile, saveTemplateMutation])

  const handleLoadTemplate = useCallback((template) => {
    dispatch({
      type: 'LOAD_TEMPLATE',
      payload: { ...template.template_data, _templateId: template.id },
    })
    dispatch({ type: 'SET_SHOW_MODE_SELECTION', payload: false })
  }, [])

  const handleStartEdit = useCallback(() => {
    if (!confirmReset) {
      setConfirmReset(true)
      return
    }
    dispatch({ type: 'SET_WIZARD_MODE', payload: 'edit' })
    dispatch({ type: 'SET_SHOW_MODE_SELECTION', payload: false })
    setConfirmReset(false)
  }, [confirmReset])

  const handleStartNew = useCallback(() => {
    dispatch({ type: 'SET_WIZARD_MODE', payload: 'new' })
    dispatch({ type: 'SET_SHOW_MODE_SELECTION', payload: false })
  }, [])

  const canNext = useMemo(() => {
    switch (state.step) {
      case 1: return state.profileName.trim().length > 0 || state.wizardMode === 'edit'
      case 2: return state.selectedTemplates.length > 0 || state.wizardMode === 'edit' || state.wizardMode === 'template'
      default: return true
    }
  }, [state.step, state.profileName, state.selectedTemplates, state.wizardMode])

  // ── Mode Selection Screen ──
  if (state.showModeSelection) {
    const templateList = Array.isArray(setupTemplates) ? setupTemplates : setupTemplates?.results || []
    return (
      <div className={styles.overlay}>
        <div className={styles.progressBar}>
          <div className={styles.progressFill} style={{ width: '0%' }} />
        </div>
        <div className={styles.body}>
          <div className={styles.content}>
            <div className={styles.stepLabel}>Assistente de Configuracao</div>
            <h1 className={styles.stepTitle}>Como deseja configurar?</h1>
            <p className={styles.stepDesc}>
              Escolha como deseja configurar seu perfil. Voce pode reconfigurar do zero,
              carregar um template salvo, ou apenas revisar as configuracoes atuais.
            </p>

            <div className={styles.sourceGrid}>
              <div
                className={`${styles.sourceCard} ${confirmReset ? styles.sourceCardActive : ''}`}
                onClick={handleStartEdit}
              >
                <div className={styles.sourceIcon}>&#128260;</div>
                <div className={styles.sourceTitle}>Reconfigurar</div>
                <div className={styles.sourceDesc}>
                  {confirmReset
                    ? 'Clique novamente para confirmar. Dados atuais serao substituidos.'
                    : 'Reconfigura o perfil do zero com o assistente completo'}
                </div>
              </div>

              <div className={styles.sourceCard} onClick={handleStartNew}>
                <div className={styles.sourceIcon}>&#10024;</div>
                <div className={styles.sourceTitle}>Configurar Novo</div>
                <div className={styles.sourceDesc}>Inicia uma configuracao limpa sem afetar dados existentes</div>
              </div>

              <div className={styles.sourceCard} onClick={onClose}>
                <div className={styles.sourceIcon}>&#128473;</div>
                <div className={styles.sourceTitle}>Fechar</div>
                <div className={styles.sourceDesc}>Voltar para as configuracoes sem alterar nada</div>
              </div>
            </div>

            {/* Saved templates */}
            {templateList.length > 0 && (
              <>
                <div className={styles.bankGroupTitle} style={{ marginTop: 32 }}>
                  Templates Salvos
                </div>
                <div className={styles.cardGrid}>
                  {templateList.map(tpl => (
                    <div
                      key={tpl.id}
                      className={styles.selectCard}
                      onClick={() => handleLoadTemplate(tpl)}
                    >
                      <div className={styles.cardName}>{tpl.name}</div>
                      <div className={styles.cardSub}>{tpl.description || 'Sem descricao'}</div>
                      <div className={styles.cardSub} style={{ marginTop: 4, fontSize: '0.68rem' }}>
                        {new Date(tpl.updated_at || tpl.created_at).toLocaleDateString('pt-BR')}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>

        <div className={styles.nav}>
          <button className={styles.navBack} onClick={onClose}>Cancelar</button>
          <div />
          <div />
        </div>
      </div>
    )
  }

  // ── Render Steps ──
  return (
    <div className={styles.overlay}>
      <div className={styles.progressBar}>
        <div
          className={styles.progressFill}
          style={{ width: `${(state.step / TOTAL_STEPS) * 100}%` }}
        />
      </div>

      <div className={styles.body}>
        <div className={styles.content}>
          {state.step === 1 && <Step1 state={state} dispatch={dispatch} />}
          {state.step === 2 && (
            <Step2
              state={state}
              dispatch={dispatch}
              groupedTemplates={groupedTemplates}
              loading={loadingTemplates}
            />
          )}
          {state.step === 3 && <Step3 state={state} dispatch={dispatch} ccTemplates={ccTemplates} />}
          {state.step === 4 && <Step4 state={state} dispatch={dispatch} />}
          {state.step === 5 && (
            <Step5
              state={state}
              dispatch={dispatch}
              profiles={profiles}
              onSmartSelect={handleSmartRecurring}
              loading={loadingAnalyze && state.recurringSource === 'smart'}
              error={analyzeError}
            />
          )}
          {state.step === 6 && (
            <Step6
              state={state}
              dispatch={dispatch}
              onSmartSelect={handleSmartCategories}
              loading={loadingAnalyze && state.categorySource === 'smart'}
              error={analyzeError}
            />
          )}
          {state.step === 7 && <Step7Rename state={state} dispatch={dispatch} />}
          {state.step === 8 && (
            <Step8Categorize
              state={state}
              dispatch={dispatch}
              categories={state.categories}
              budgetLimits={state.budgetLimits}
            />
          )}
          {state.step === 9 && <Step9Cards state={state} dispatch={dispatch} />}
          {state.step === 10 && (
            <Step10Review
              state={state}
              onSubmit={handleSubmit}
              submitting={submitMutation.isPending}
              error={submitMutation.error}
              onSaveTemplate={() => setShowSaveTemplate(true)}
              showSaveTemplate={showSaveTemplate}
              saveTemplateName={saveTemplateName}
              onSaveTemplateNameChange={setSaveTemplateName}
              onConfirmSaveTemplate={handleSaveTemplate}
              savingTemplate={saveTemplateMutation.isPending}
            />
          )}
        </div>
      </div>

      {/* Bottom nav */}
      <div className={styles.nav}>
        <button
          className={styles.navBack}
          onClick={() => {
            if (state.step === 1 && editMode) {
              dispatch({ type: 'SET_SHOW_MODE_SELECTION', payload: true })
            } else {
              dispatch({ type: 'PREV_STEP' })
            }
          }}
          disabled={state.step === 1 && !editMode}
        >
          {state.step === 1 && editMode ? 'Modos' : 'Voltar'}
        </button>

        <div className={styles.dots}>
          {Array.from({ length: TOTAL_STEPS }, (_, i) => (
            <div
              key={i}
              className={`${styles.dot} ${
                i + 1 === state.step ? styles.dotActive : i + 1 < state.step ? styles.dotDone : ''
              }`}
            />
          ))}
        </div>

        <div className={styles.navRight}>
          {state.step >= 5 && state.step <= 8 && (
            <button className={styles.skipLink} onClick={handleNext}>
              Pular
            </button>
          )}
          {state.step < TOTAL_STEPS ? (
            <button className={styles.navNext} onClick={handleNext} disabled={!canNext}>
              Proximo
            </button>
          ) : (
            <button
              className={styles.navNext}
              onClick={handleSubmit}
              disabled={submitMutation.isPending}
            >
              {submitMutation.isPending ? 'Salvando...' : (state.wizardMode === 'edit' ? 'Reconfigurar' : 'Criar Perfil')}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Step 1: Profile Basics ─────────────────────────────────────
function Step1({ state, dispatch }) {
  return (
    <>
      <div className={styles.stepLabel}>Passo 1 de {TOTAL_STEPS}</div>
      <h1 className={styles.stepTitle}>Dados do Perfil</h1>
      <p className={styles.stepDesc}>
        {state.wizardMode === 'edit'
          ? 'Confirme os dados do perfil. O nome nao sera alterado no modo edicao.'
          : 'Comece dando um nome ao seu perfil financeiro.'}
      </p>

      <div className={styles.fieldGroup}>
        <label className={styles.fieldLabel}>Nome do Perfil</label>
        <input
          className={`${styles.textInput} ${state.wizardMode === 'edit' ? styles.readOnly : ''}`}
          type="text"
          placeholder="Ex: Pessoal, Familia, Empresa..."
          value={state.profileName}
          onChange={e => dispatch({ type: 'SET_PROFILE_NAME', payload: e.target.value })}
          readOnly={state.wizardMode === 'edit'}
          autoFocus={state.wizardMode !== 'edit'}
        />
      </div>

      <div className={styles.fieldGroup}>
        <label className={styles.fieldLabel}>Moeda</label>
        <input
          className={`${styles.textInput} ${styles.readOnly}`}
          type="text"
          value="BRL (Real Brasileiro)"
          readOnly
        />
      </div>
    </>
  )
}

// ── Step 2: Bank Selection ─────────────────────────────────────
function Step2({ state, dispatch, groupedTemplates, loading }) {
  if (loading) {
    return (
      <>
        <div className={styles.stepLabel}>Passo 2 de {TOTAL_STEPS}</div>
        <h1 className={styles.stepTitle}>Selecionar Bancos</h1>
        <div className={styles.loadingWrap}>
          <div className={styles.spinner} />
          <span className={styles.loadingText}>Carregando templates bancarios...</span>
        </div>
      </>
    )
  }

  const selectedIds = new Set(state.selectedTemplates.map(t => t.id))

  return (
    <>
      <div className={styles.stepLabel}>Passo 2 de {TOTAL_STEPS}</div>
      <h1 className={styles.stepTitle}>Selecionar Bancos</h1>
      <p className={styles.stepDesc}>
        {state.wizardMode === 'edit'
          ? 'Selecione os bancos para reconfigurar. Contas existentes serao recriadas.'
          : 'Escolha os bancos e contas que deseja acompanhar neste perfil.'}
      </p>

      {Object.entries(groupedTemplates).map(([bank, templates]) => (
        <div key={bank} className={styles.bankGroup}>
          <div className={styles.bankGroupTitle}>{bank}</div>
          <div className={styles.cardGrid}>
            {templates.map(tpl => {
              const active = selectedIds.has(tpl.id)
              return (
                <div
                  key={tpl.id}
                  className={`${styles.selectCard} ${active ? styles.selectCardActive : ''}`}
                  onClick={() => dispatch({ type: 'TOGGLE_TEMPLATE', payload: tpl })}
                >
                  <div className={`${styles.cardCheck} ${active ? styles.cardCheckActive : ''}`}>
                    {active ? '\u2713' : ''}
                  </div>
                  <div className={styles.cardName}>{tpl.display_name || tpl.bank_name}</div>
                  <div className={styles.cardSub}>{ACCT_TYPE_LABELS[tpl.account_type] || tpl.account_type}</div>
                  <span
                    className={`${styles.cardBadge} ${
                      tpl.account_type === 'credit_card' ? styles.badgeCredit : styles.badgeChecking
                    }`}
                  >
                    {tpl.account_type === 'credit_card' ? 'Credito' : 'Corrente'}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </>
  )
}

// ── Step 3: CC Config ──────────────────────────────────────────
function Step3({ state, dispatch, ccTemplates }) {
  if (ccTemplates.length === 0) {
    return (
      <>
        <div className={styles.stepLabel}>Passo 3 de {TOTAL_STEPS}</div>
        <h1 className={styles.stepTitle}>Configurar Cartoes</h1>
        <p className={styles.emptyState}>
          Nenhum cartao de credito selecionado. Voce pode voltar e adicionar um, ou avancar.
        </p>
      </>
    )
  }

  return (
    <>
      <div className={styles.stepLabel}>Passo 3 de {TOTAL_STEPS}</div>
      <h1 className={styles.stepTitle}>Configurar Cartoes</h1>
      <p className={styles.stepDesc}>
        Defina os dias de fechamento e vencimento de cada cartao.
      </p>

      <div className={styles.ccConfigList}>
        {ccTemplates.map(tpl => {
          const config = state.cardConfigs[tpl.id] || {}
          return (
            <div key={tpl.id} className={styles.ccCard}>
              <div className={styles.ccCardTitle}>{config.display_name || tpl.display_name}</div>
              <div className={styles.ccCardBank}>{tpl.bank_name}</div>
              <div className={styles.ccFields}>
                <div className={styles.ccFieldGroup}>
                  <label className={styles.ccFieldLabel}>Fechamento</label>
                  <input
                    className={styles.smallInput}
                    type="number"
                    min={1}
                    max={31}
                    value={config.closing_day || ''}
                    onChange={e =>
                      dispatch({
                        type: 'SET_CARD_CONFIG',
                        payload: { id: tpl.id, data: { closing_day: parseInt(e.target.value) || '' } },
                      })
                    }
                  />
                </div>
                <div className={styles.ccFieldGroup}>
                  <label className={styles.ccFieldLabel}>Vencimento</label>
                  <input
                    className={styles.smallInput}
                    type="number"
                    min={1}
                    max={31}
                    value={config.due_day || ''}
                    onChange={e =>
                      dispatch({
                        type: 'SET_CARD_CONFIG',
                        payload: { id: tpl.id, data: { due_day: parseInt(e.target.value) || '' } },
                      })
                    }
                  />
                </div>
                <div className={styles.ccFieldGroup}>
                  <label className={styles.ccFieldLabel}>Limite (R$)</label>
                  <input
                    className={styles.amtInput}
                    type="number"
                    min={0}
                    placeholder="Opcional"
                    value={config.credit_limit || ''}
                    onChange={e =>
                      dispatch({
                        type: 'SET_CARD_CONFIG',
                        payload: { id: tpl.id, data: { credit_limit: e.target.value } },
                      })
                    }
                  />
                </div>
                <div className={styles.ccFieldGroup}>
                  <label className={styles.ccFieldLabel}>Nome</label>
                  <input
                    className={styles.textInput}
                    type="text"
                    value={config.display_name || ''}
                    onChange={e =>
                      dispatch({
                        type: 'SET_CARD_CONFIG',
                        payload: { id: tpl.id, data: { display_name: e.target.value } },
                      })
                    }
                  />
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </>
  )
}

// ── Step 4: CC Display Mode ────────────────────────────────────
function Step4({ state, dispatch }) {
  const isInvoice = state.ccDisplayMode === 'invoice'

  return (
    <>
      <div className={styles.stepLabel}>Passo 4 de {TOTAL_STEPS}</div>
      <h1 className={styles.stepTitle}>Modo de Visualizacao</h1>
      <p className={styles.stepDesc}>
        Escolha como as transacoes do cartao de credito aparecem no dashboard.
      </p>

      <div className={styles.modeGrid}>
        <div
          className={`${styles.modeCard} ${isInvoice ? styles.modeCardActive : ''}`}
          onClick={() => dispatch({ type: 'SET_CC_DISPLAY_MODE', payload: 'invoice' })}
        >
          <div className={styles.modeIcon}>&#128196;</div>
          <div className={styles.modeTitle}>Fatura</div>
          <div className={styles.modeDesc}>
            Mostra no mes atual o que voce esta PAGANDO (fatura do cartao).
            Ex: Em fevereiro vejo compras de janeiro.
          </div>
        </div>

        <div
          className={`${styles.modeCard} ${!isInvoice ? styles.modeCardActive : ''}`}
          onClick={() => dispatch({ type: 'SET_CC_DISPLAY_MODE', payload: 'transaction' })}
        >
          <div className={styles.modeIcon}>&#128722;</div>
          <div className={styles.modeTitle}>Compra</div>
          <div className={styles.modeDesc}>
            Mostra no mes atual o que voce COMPROU.
            Ex: Em fevereiro vejo compras de fevereiro.
          </div>
        </div>
      </div>

      <div className={styles.timeline}>
        <div className={styles.timelineMonth}>
          <div className={styles.timelineLabel}>Janeiro</div>
          <div className={`${styles.timelineBox} ${!isInvoice ? styles.timelineBoxHighlight : ''}`}>
            Compras de Jan
          </div>
          <div className={styles.timelineBox}>Fatura de Dez</div>
        </div>
        <div className={styles.timelineArrow}>&rarr;</div>
        <div className={styles.timelineMonth}>
          <div className={styles.timelineLabel}>Fevereiro</div>
          <div className={`${styles.timelineBox} ${!isInvoice ? styles.timelineBoxHighlight : ''}`}>
            Compras de Fev
          </div>
          <div className={`${styles.timelineBox} ${isInvoice ? styles.timelineBoxHighlight : ''}`}>
            Fatura de Jan
          </div>
        </div>
        <div className={styles.timelineArrow}>&rarr;</div>
        <div className={styles.timelineMonth}>
          <div className={styles.timelineLabel}>Marco</div>
          <div className={`${styles.timelineBox} ${!isInvoice ? styles.timelineBoxHighlight : ''}`}>
            Compras de Mar
          </div>
          <div className={`${styles.timelineBox} ${isInvoice ? styles.timelineBoxHighlight : ''}`}>
            Fatura de Fev
          </div>
        </div>
      </div>
    </>
  )
}

// ── Step 5: Recurring Items ────────────────────────────────────
function Step5({ state, dispatch, profiles, onSmartSelect, loading, error }) {
  const TYPE_BADGE = {
    Fixo: { label: 'Fixo', cls: styles.dataBadgeFixo },
    Income: { label: 'Entrada', cls: styles.dataBadgeIncome },
    Investimento: { label: 'Invest.', cls: styles.dataBadgeInvest },
    Variavel: { label: 'Variavel', cls: styles.dataBadgeVariable },
  }

  return (
    <>
      <div className={styles.stepLabel}>Passo 5 de {TOTAL_STEPS}</div>
      <h1 className={styles.stepTitle}>Itens Recorrentes</h1>
      <p className={styles.stepDesc}>
        Adicione despesas e receitas que se repetem todo mes.
      </p>

      <div className={styles.sourceGrid}>
        <div
          className={`${styles.sourceCard} ${state.recurringSource === 'smart' ? styles.sourceCardActive : ''}`}
          onClick={onSmartSelect}
        >
          <div className={styles.sourceIcon}>&#9889;</div>
          <div className={styles.sourceTitle}>Sugestao Inteligente</div>
          <div className={styles.sourceDesc}>Detecta automaticamente itens recorrentes do seu historico</div>
        </div>

        <div
          className={`${styles.sourceCard} ${state.recurringSource === 'clone' ? styles.sourceCardActive : ''}`}
          onClick={() => dispatch({ type: 'SET_RECURRING_SOURCE', payload: 'clone' })}
        >
          <div className={styles.sourceIcon}>&#128203;</div>
          <div className={styles.sourceTitle}>Copiar de Perfil</div>
          <div className={styles.sourceDesc}>Use itens de outro perfil existente</div>
        </div>

        <div
          className={`${styles.sourceCard} ${state.recurringSource === 'blank' ? styles.sourceCardActive : ''}`}
          onClick={() => {
            dispatch({ type: 'SET_RECURRING_SOURCE', payload: 'blank' })
            dispatch({ type: 'SET_RECURRING_ITEMS', payload: [] })
          }}
        >
          <div className={styles.sourceIcon}>&#128221;</div>
          <div className={styles.sourceTitle}>Comecar Vazio</div>
          <div className={styles.sourceDesc}>Configure tudo manualmente depois</div>
        </div>
      </div>

      {state.recurringSource === 'clone' && (
        <select
          className={styles.profileSelect}
          onChange={async (e) => {
            if (!e.target.value) return
            try {
              const data = await api.get(`/analytics/recurring/templates/?source_profile=${e.target.value}`)
              const items = (Array.isArray(data) ? data : data?.templates || data?.results || []).map(r => ({
                name: r.name,
                type: r.template_type || r.type || 'Fixo',
                amount: parseFloat(r.default_limit || r.amount || 0),
                due_day: r.due_day,
                included: true,
              }))
              dispatch({ type: 'SET_RECURRING_ITEMS', payload: items })
            } catch { /* ignore */ }
          }}
          defaultValue=""
        >
          <option value="">Selecione um perfil...</option>
          {(profiles || []).map(p => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
      )}

      {loading && (
        <div className={styles.loadingWrap}>
          <div className={styles.spinner} />
          <span className={styles.loadingText}>Analisando historico...</span>
        </div>
      )}

      {error && (
        <div className={styles.errorMsg}>
          Erro ao analisar dados: {error.message}
        </div>
      )}

      {state.recurringItems.length > 0 && !loading && (
        <div className={styles.dataTable}>
          <div className={styles.dataTableHead}>
            <span style={{ width: 18 }} />
            <span className={styles.dataName}>Nome</span>
            <span style={{ width: 80 }}>Tipo</span>
            <span className={styles.dataAmount}>Valor</span>
            <span className={styles.dataFreq}>Freq.</span>
            {state.recurringSource === 'smart' && <span className={styles.dataConf}>Conf.</span>}
          </div>
          {state.recurringItems.map((item, i) => {
            const badge = TYPE_BADGE[item.type] || { label: item.type, cls: '' }
            const confClass = (item.confidence || 0) >= 80
              ? styles.confHigh
              : (item.confidence || 0) >= 50
                ? styles.confMed
                : styles.confLow
            return (
              <div key={i} className={styles.dataRow}>
                <input
                  type="checkbox"
                  className={styles.dataCheck}
                  checked={item.included}
                  onChange={() => dispatch({ type: 'TOGGLE_RECURRING_ITEM', payload: i })}
                />
                <span className={styles.dataName}>{item.name}</span>
                <span style={{ width: 80 }}>
                  <span className={`${styles.dataBadge} ${badge.cls}`}>{badge.label}</span>
                </span>
                <span className={styles.dataAmount}>
                  <input
                    className={styles.amtInput}
                    type="number"
                    value={item.amount || ''}
                    onChange={e =>
                      dispatch({
                        type: 'UPDATE_RECURRING_ITEM',
                        payload: { index: i, data: { amount: parseFloat(e.target.value) || 0 } },
                      })
                    }
                    style={{ width: 90 }}
                  />
                </span>
                <span className={styles.dataFreq}>{item.frequency || 'Mensal'}</span>
                {state.recurringSource === 'smart' && (
                  <span className={`${styles.dataConf} ${confClass}`}>
                    {item.confidence || 0}%
                  </span>
                )}
              </div>
            )
          })}
        </div>
      )}

      {(state.recurringSource === 'blank' || (state.recurringSource === 'existing' && state.recurringItems.length === 0)) && (
        <p className={styles.emptyState}>
          Voce podera adicionar itens recorrentes nas configuracoes do perfil depois.
        </p>
      )}
    </>
  )
}

// ── Step 6: Categories & Budget ────────────────────────────────
function Step6({ state, dispatch, onSmartSelect, loading, error }) {
  return (
    <>
      <div className={styles.stepLabel}>Passo 6 de {TOTAL_STEPS}</div>
      <h1 className={styles.stepTitle}>Categorias & Orcamento</h1>
      <p className={styles.stepDesc}>
        Defina categorias de gastos e limites de orcamento.
      </p>

      <div className={styles.sourceGrid}>
        <div
          className={`${styles.sourceCard} ${state.categorySource === 'smart' ? styles.sourceCardActive : ''}`}
          onClick={onSmartSelect}
        >
          <div className={styles.sourceIcon}>&#9889;</div>
          <div className={styles.sourceTitle}>Sugestao Inteligente</div>
          <div className={styles.sourceDesc}>Sugere limites baseados no seu historico</div>
        </div>

        <div
          className={`${styles.sourceCard} ${state.categorySource === 'default' ? styles.sourceCardActive : ''}`}
          onClick={() => dispatch({ type: 'SET_CATEGORY_SOURCE', payload: 'default' })}
        >
          <div className={styles.sourceIcon}>&#128195;</div>
          <div className={styles.sourceTitle}>Categorias Padrao</div>
          <div className={styles.sourceDesc}>Use o conjunto padrao de categorias</div>
        </div>

        <div
          className={`${styles.sourceCard} ${state.categorySource === 'blank' ? styles.sourceCardActive : ''}`}
          onClick={() => {
            dispatch({ type: 'SET_CATEGORY_SOURCE', payload: 'blank' })
            dispatch({ type: 'SET_CATEGORIES', payload: [] })
            dispatch({ type: 'SET_BUDGET_LIMITS', payload: [] })
          }}
        >
          <div className={styles.sourceIcon}>&#128221;</div>
          <div className={styles.sourceTitle}>Comecar Vazio</div>
          <div className={styles.sourceDesc}>Configure tudo manualmente depois</div>
        </div>
      </div>

      {loading && (
        <div className={styles.loadingWrap}>
          <div className={styles.spinner} />
          <span className={styles.loadingText}>Analisando categorias...</span>
        </div>
      )}

      {error && (
        <div className={styles.errorMsg}>Erro ao analisar dados: {error.message}</div>
      )}

      {state.budgetLimits.length > 0 && !loading && (
        <div className={styles.dataTable}>
          <div className={styles.dataTableHead}>
            <span className={styles.dataColFlex}>Categoria</span>
            <span className={styles.dataColSm}>Media Mensal</span>
            <span className={styles.dataColSm}>Limite Sugerido</span>
          </div>
          {state.budgetLimits.map((b, i) => (
            <div key={i} className={styles.dataRow}>
              <span className={styles.dataColFlex}>{b.category || b.name}</span>
              <span className={styles.dataColSm} style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                R$ {(b.avg_monthly || 0).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
              </span>
              <span className={styles.dataColSm}>
                <input
                  className={styles.amtInput}
                  type="number"
                  value={b.suggested_limit || ''}
                  onChange={e =>
                    dispatch({
                      type: 'UPDATE_BUDGET_LIMIT',
                      payload: { index: i, value: parseFloat(e.target.value) || 0 },
                    })
                  }
                  style={{ width: 90 }}
                />
              </span>
            </div>
          ))}
        </div>
      )}

      {state.categorySource && state.categorySource !== 'blank' && (
        <>
          <div className={styles.targetRow}>
            <div className={styles.targetGroup}>
              <span className={styles.targetLabel}>Meta de Poupanca</span>
              <input
                className={styles.targetPct}
                type="number"
                min={0}
                max={100}
                value={state.savingsTarget}
                onChange={e => dispatch({ type: 'SET_SAVINGS_TARGET', payload: parseFloat(e.target.value) || 0 })}
              />
              <span className={styles.targetUnit}>%</span>
            </div>
            <div className={styles.targetGroup}>
              <span className={styles.targetLabel}>Meta de Investimento</span>
              <input
                className={styles.targetPct}
                type="number"
                min={0}
                max={100}
                value={state.investmentTarget}
                onChange={e => dispatch({ type: 'SET_INVESTMENT_TARGET', payload: parseFloat(e.target.value) || 0 })}
              />
              <span className={styles.targetUnit}>%</span>
            </div>
          </div>

          <div className={styles.allocSection}>
            <div className={styles.allocTitle}>Alocacao de Investimentos</div>
            {state.investmentAllocation.map((a, i) => (
              <div key={i} className={styles.allocRow}>
                <input
                  className={styles.textInput}
                  style={{ flex: 1, padding: '6px 10px', fontSize: '0.82rem' }}
                  type="text"
                  value={a.name}
                  onChange={e =>
                    dispatch({ type: 'UPDATE_ALLOCATION', payload: { index: i, data: { name: e.target.value } } })
                  }
                />
                <input
                  className={styles.targetPct}
                  type="number"
                  min={0}
                  max={100}
                  value={a.percentage}
                  onChange={e =>
                    dispatch({
                      type: 'UPDATE_ALLOCATION',
                      payload: { index: i, data: { percentage: parseFloat(e.target.value) || 0 } },
                    })
                  }
                />
                <span className={styles.targetUnit}>%</span>
                <button
                  className={styles.skipLink}
                  onClick={() => dispatch({ type: 'REMOVE_ALLOCATION', payload: i })}
                  style={{ textDecoration: 'none', color: 'var(--color-red)' }}
                >
                  &#10005;
                </button>
              </div>
            ))}
            <button
              className={styles.allocAddBtn}
              onClick={() => dispatch({ type: 'ADD_ALLOCATION', payload: { name: '', percentage: 0 } })}
            >
              + Adicionar Alocacao
            </button>
          </div>
        </>
      )}

      {state.categorySource === 'blank' && (
        <p className={styles.emptyState}>
          Voce podera configurar categorias e orcamento nas configuracoes do perfil depois.
        </p>
      )}
    </>
  )
}

// ── Step 7: Rename Rules (NEW) ─────────────────────────────────
function Step7Rename({ state, dispatch }) {
  return (
    <>
      <div className={styles.stepLabel}>Passo 7 de {TOTAL_STEPS}</div>
      <h1 className={styles.stepTitle}>Regras de Renomeacao</h1>
      <p className={styles.stepDesc}>
        Defina regras para renomear descricoes de transacoes automaticamente.
        Ex: "PIX ENVIADO CP" aparece como "PIX Enviado".
      </p>

      {state.renameRules.length > 0 && (
        <div className={styles.dataTable}>
          <div className={styles.dataTableHead}>
            <span className={styles.dataColFlex}>Palavra-chave</span>
            <span className={styles.dataColFlex}>Nome Exibido</span>
            <span style={{ width: 32 }} />
          </div>
          {state.renameRules.map((rule, i) => (
            <div key={i} className={styles.dataRow}>
              <span className={styles.dataColFlex}>
                <input
                  className={styles.textInput}
                  style={{ padding: '6px 10px', fontSize: '0.82rem' }}
                  type="text"
                  placeholder="Palavra-chave"
                  value={rule.keyword || ''}
                  onChange={e =>
                    dispatch({ type: 'UPDATE_RENAME_RULE', payload: { index: i, data: { keyword: e.target.value } } })
                  }
                />
              </span>
              <span className={styles.dataColFlex}>
                <input
                  className={styles.textInput}
                  style={{ padding: '6px 10px', fontSize: '0.82rem' }}
                  type="text"
                  placeholder="Nome exibido"
                  value={rule.display_name || ''}
                  onChange={e =>
                    dispatch({ type: 'UPDATE_RENAME_RULE', payload: { index: i, data: { display_name: e.target.value } } })
                  }
                />
              </span>
              <button
                className={styles.skipLink}
                onClick={() => dispatch({ type: 'REMOVE_RENAME_RULE', payload: i })}
                style={{ textDecoration: 'none', color: 'var(--color-red)', width: 32, textAlign: 'center' }}
              >
                &#10005;
              </button>
            </div>
          ))}
        </div>
      )}

      <button
        className={styles.allocAddBtn}
        style={{ marginTop: 16 }}
        onClick={() => dispatch({ type: 'ADD_RENAME_RULE', payload: { keyword: '', display_name: '' } })}
      >
        + Adicionar Regra
      </button>

      {state.renameRules.length === 0 && (
        <p className={styles.emptyState}>
          Nenhuma regra de renomeacao configurada. Voce pode adicionar agora ou depois nas configuracoes.
        </p>
      )}
    </>
  )
}

// ── Step 8: Categorization Rules (NEW) ─────────────────────────
function Step8Categorize({ state, dispatch, categories, budgetLimits }) {
  // Build category name list for dropdown
  const categoryNames = useMemo(() => {
    const names = new Set()
    categories.forEach(c => names.add(typeof c === 'string' ? c : c.name))
    budgetLimits.forEach(b => names.add(b.category || b.name))
    return [...names].filter(Boolean).sort()
  }, [categories, budgetLimits])

  return (
    <>
      <div className={styles.stepLabel}>Passo 8 de {TOTAL_STEPS}</div>
      <h1 className={styles.stepTitle}>Regras de Categorizacao</h1>
      <p className={styles.stepDesc}>
        Defina regras para categorizar transacoes automaticamente.
        Ex: "UBER" vai para categoria "Transporte".
      </p>

      {state.categorizationRules.length > 0 && (
        <div className={styles.dataTable}>
          <div className={styles.dataTableHead}>
            <span className={styles.dataColFlex}>Palavra-chave</span>
            <span className={styles.dataColFlex}>Categoria</span>
            <span style={{ width: 32 }} />
          </div>
          {state.categorizationRules.map((rule, i) => (
            <div key={i} className={styles.dataRow}>
              <span className={styles.dataColFlex}>
                <input
                  className={styles.textInput}
                  style={{ padding: '6px 10px', fontSize: '0.82rem' }}
                  type="text"
                  placeholder="Palavra-chave"
                  value={rule.keyword || ''}
                  onChange={e =>
                    dispatch({ type: 'UPDATE_CATEGORIZATION_RULE', payload: { index: i, data: { keyword: e.target.value } } })
                  }
                />
              </span>
              <span className={styles.dataColFlex}>
                <select
                  className={styles.profileSelect}
                  style={{ marginBottom: 0 }}
                  value={rule.category_name || ''}
                  onChange={e =>
                    dispatch({ type: 'UPDATE_CATEGORIZATION_RULE', payload: { index: i, data: { category_name: e.target.value } } })
                  }
                >
                  <option value="">Selecione...</option>
                  {categoryNames.map(name => (
                    <option key={name} value={name}>{name}</option>
                  ))}
                </select>
              </span>
              <button
                className={styles.skipLink}
                onClick={() => dispatch({ type: 'REMOVE_CATEGORIZATION_RULE', payload: i })}
                style={{ textDecoration: 'none', color: 'var(--color-red)', width: 32, textAlign: 'center' }}
              >
                &#10005;
              </button>
            </div>
          ))}
        </div>
      )}

      <button
        className={styles.allocAddBtn}
        style={{ marginTop: 16 }}
        onClick={() => dispatch({ type: 'ADD_CATEGORIZATION_RULE', payload: { keyword: '', category_name: '', priority: 0 } })}
      >
        + Adicionar Regra
      </button>

      {state.categorizationRules.length === 0 && (
        <p className={styles.emptyState}>
          Nenhuma regra de categorizacao configurada. Voce pode adicionar agora ou depois nas configuracoes.
        </p>
      )}
    </>
  )
}

// ── Step 9: Dashboard Cards ────────────────────────────────────
function Step9Cards({ state, dispatch }) {
  return (
    <>
      <div className={styles.stepLabel}>Passo 9 de {TOTAL_STEPS}</div>
      <h1 className={styles.stepTitle}>Cartoes do Dashboard</h1>
      <p className={styles.stepDesc}>
        Escolha quais metricas aparecem no dashboard e a ordem de exibicao.
      </p>

      <div className={styles.metricList}>
        {state.cardOrder.map((cardId, index) => {
          const hidden = state.hiddenCards.includes(cardId)
          return (
            <div key={cardId} className={styles.metricRow} style={hidden ? { opacity: 0.45 } : undefined}>
              <input
                type="checkbox"
                className={styles.metricCheck}
                checked={!hidden}
                onChange={() => dispatch({ type: 'TOGGLE_HIDDEN_CARD', payload: cardId })}
              />
              <span className={styles.metricLabel}>
                {CARD_LABELS[cardId] || cardId}
              </span>
              <button
                className={styles.metricMoveBtn}
                onClick={() => dispatch({ type: 'MOVE_CARD', payload: { index, direction: -1 } })}
                disabled={index === 0}
                title="Mover para cima"
              >
                &#9650;
              </button>
              <button
                className={styles.metricMoveBtn}
                onClick={() => dispatch({ type: 'MOVE_CARD', payload: { index, direction: 1 } })}
                disabled={index === state.cardOrder.length - 1}
                title="Mover para baixo"
              >
                &#9660;
              </button>
            </div>
          )
        })}
      </div>
    </>
  )
}

// ── Step 10: Review & Confirm ──────────────────────────────────
function Step10Review({
  state, onSubmit, submitting, error,
  onSaveTemplate, showSaveTemplate, saveTemplateName,
  onSaveTemplateNameChange, onConfirmSaveTemplate, savingTemplate,
}) {
  const ccCount = Object.keys(state.cardConfigs).length
  const activeRecurring = state.recurringItems.filter(r => r.included).length
  const activeCards = state.cardOrder.filter(c => !state.hiddenCards.includes(c)).length
  const validRenames = state.renameRules.filter(r => r.keyword && r.display_name).length
  const validCatRules = state.categorizationRules.filter(r => r.keyword && r.category_name).length

  return (
    <>
      <div className={styles.stepLabel}>Passo 10 de {TOTAL_STEPS}</div>
      <h1 className={styles.stepTitle}>Revisao</h1>
      <p className={styles.stepDesc}>
        {state.wizardMode === 'edit'
          ? 'Confira as configuracoes antes de reconfigurar o perfil. Dados existentes serao substituidos.'
          : 'Confira as configuracoes antes de criar o perfil.'}
      </p>

      <div className={styles.reviewSection}>
        <div className={styles.reviewTitle}>Perfil</div>
        <div className={styles.reviewCard}>
          <div className={styles.reviewRow}>
            <span className={styles.reviewLabel}>Nome</span>
            <span className={styles.reviewValue}>{state.profileName || '(sem nome)'}</span>
          </div>
          <div className={styles.reviewRow}>
            <span className={styles.reviewLabel}>Moeda</span>
            <span className={styles.reviewValue}>BRL</span>
          </div>
          {state.wizardMode === 'edit' && (
            <div className={styles.reviewRow}>
              <span className={styles.reviewLabel}>Modo</span>
              <span className={styles.reviewValue} style={{ color: 'var(--color-orange)' }}>Reconfigurar</span>
            </div>
          )}
        </div>
      </div>

      <div className={styles.reviewSection}>
        <div className={styles.reviewTitle}>Contas Bancarias</div>
        <div className={styles.reviewCard}>
          <div className={styles.reviewRow}>
            <span className={styles.reviewLabel}>Contas selecionadas</span>
            <span className={styles.reviewValueAccent}>{state.selectedTemplates.length}</span>
          </div>
          {state.selectedTemplates.map(t => (
            <div key={t.id} className={styles.reviewRow}>
              <span className={styles.reviewLabel}>{t.display_name || t.bank_name}</span>
              <span className={styles.reviewValue}>
                {t.account_type === 'credit_card' ? 'Credito' : 'Corrente'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {ccCount > 0 && (
        <div className={styles.reviewSection}>
          <div className={styles.reviewTitle}>Cartoes de Credito</div>
          <div className={styles.reviewCard}>
            <div className={styles.reviewRow}>
              <span className={styles.reviewLabel}>Cartoes configurados</span>
              <span className={styles.reviewValueAccent}>{ccCount}</span>
            </div>
            <div className={styles.reviewRow}>
              <span className={styles.reviewLabel}>Modo de visualizacao</span>
              <span className={styles.reviewValue}>
                {state.ccDisplayMode === 'invoice' ? 'Fatura' : 'Compra'}
              </span>
            </div>
          </div>
        </div>
      )}

      <div className={styles.reviewSection}>
        <div className={styles.reviewTitle}>Dados</div>
        <div className={styles.reviewCard}>
          <div className={styles.reviewRow}>
            <span className={styles.reviewLabel}>Itens recorrentes</span>
            <span className={styles.reviewValueAccent}>{activeRecurring}</span>
          </div>
          <div className={styles.reviewRow}>
            <span className={styles.reviewLabel}>Categorias</span>
            <span className={styles.reviewValueAccent}>
              {state.budgetLimits.length || state.categories.length}
            </span>
          </div>
          <div className={styles.reviewRow}>
            <span className={styles.reviewLabel}>Regras de renomeacao</span>
            <span className={styles.reviewValueAccent}>{validRenames}</span>
          </div>
          <div className={styles.reviewRow}>
            <span className={styles.reviewLabel}>Regras de categorizacao</span>
            <span className={styles.reviewValueAccent}>{validCatRules}</span>
          </div>
          <div className={styles.reviewRow}>
            <span className={styles.reviewLabel}>Meta poupanca</span>
            <span className={styles.reviewValue}>{state.savingsTarget}%</span>
          </div>
          <div className={styles.reviewRow}>
            <span className={styles.reviewLabel}>Meta investimento</span>
            <span className={styles.reviewValue}>{state.investmentTarget}%</span>
          </div>
        </div>
      </div>

      <div className={styles.reviewSection}>
        <div className={styles.reviewTitle}>Dashboard</div>
        <div className={styles.reviewCard}>
          <div className={styles.reviewRow}>
            <span className={styles.reviewLabel}>Cartoes visiveis</span>
            <span className={styles.reviewValueAccent}>{activeCards} de {state.cardOrder.length}</span>
          </div>
        </div>
      </div>

      {/* Save as template */}
      <div className={styles.reviewSection}>
        <div className={styles.reviewTitle}>Template</div>
        <div className={styles.reviewCard}>
          {!showSaveTemplate ? (
            <button
              className={styles.allocAddBtn}
              style={{ width: '100%' }}
              onClick={onSaveTemplate}
            >
              Salvar Configuracao como Template
            </button>
          ) : (
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input
                className={styles.textInput}
                style={{ flex: 1, padding: '8px 12px', fontSize: '0.85rem' }}
                type="text"
                placeholder="Nome do template..."
                value={saveTemplateName}
                onChange={e => onSaveTemplateNameChange(e.target.value)}
                autoFocus
              />
              <button
                className={styles.navNext}
                style={{ padding: '8px 16px', fontSize: '0.82rem' }}
                onClick={onConfirmSaveTemplate}
                disabled={savingTemplate}
              >
                {savingTemplate ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className={styles.errorMsg}>
          Erro ao salvar: {error.message || 'Erro desconhecido'}
        </div>
      )}
    </>
  )
}
