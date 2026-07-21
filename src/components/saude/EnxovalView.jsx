/**
 * EnxovalView — interactive "Mapa do Enxoval" for the Família tab.
 *
 * What the R$27 PDF funnels sell, but living inside Vault:
 *   - evidence-based checklist (SBP, MS, NHS, ANS, CONTRAN — see enxovalData)
 *   - aware of the CURRENT gestational week: each category gets a buy-window
 *     status (agora / futuro / atrasado / feito) like the prenatal checkpoints
 *   - shared check-state between the two profiles, synced cross-device
 *
 * Persistence: one FamilyNote (title = NOTE_TITLE) holding a JSON blob
 * { v, checked: {itemId: true}, custom: [{id, cat, label}] }. FamilyNotes are
 * household-shared and full-CRUD, so no backend change is needed. Home.jsx
 * hides "__"-prefixed titles from the bulletin board. Writes are debounced
 * whole-blob upserts — last write wins, fine for a two-person household.
 */
import { useState, useMemo, useEffect, useRef, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../../api/client'
import { ENXOVAL_CATEGORIES, SOURCES, PHASE_HINTS } from './enxovalData'
import { weeksFromDum, formatWeeks } from './checkpoints'
import styles from './enxoval.module.css'

const NOTE_TITLE = '__enxoval_state__'
const EMPTY_STATE = { v: 1, checked: {}, custom: [] }

function parseState(note) {
  if (!note?.content) return EMPTY_STATE
  try {
    const parsed = JSON.parse(note.content)
    const checked = parsed.checked && typeof parsed.checked === 'object' && !Array.isArray(parsed.checked)
      ? parsed.checked : {}
    const custom = (Array.isArray(parsed.custom) ? parsed.custom : []).filter(c =>
      c && typeof c.id === 'string' && typeof c.cat === 'string' && typeof c.label === 'string')
    return { v: 1, checked, custom }
  } catch {
    return EMPTY_STATE
  }
}

function customId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return `c-${crypto.randomUUID()}`
  return `c-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

function categoryStatus(cat, currentWeek, done, total, pregnancyStatus) {
  if (total > 0 && done === total) return 'completed'
  // Deadline-driven (docs) categories go live once the baby is born.
  if (!cat.buyWindow) return pregnancyStatus === 'finalizada' ? 'current' : 'posparto'
  if (currentWeek == null) return 'upcoming'
  const [start, end] = cat.buyWindow
  if (currentWeek > end) return 'overdue'
  if (currentWeek >= start) return 'current'
  return 'upcoming'
}

const STATUS_LABEL = {
  completed: 'feito',
  current: 'agora',
  upcoming: 'futuro',
  overdue: 'atrasado',
  posparto: 'pós-parto',
}

export default function EnxovalView({ pregnancy }) {
  const queryClient = useQueryClient()
  const currentWeek = useMemo(() => weeksFromDum(pregnancy?.dum), [pregnancy?.dum])

  const { data: notes = [], isLoading } = useQuery({
    queryKey: ['home-notes'],
    queryFn: () => api.get('/home/notes/'),
  })
  const notesList = notes.results || notes
  // Deterministic canonical pick if duplicates ever exist: oldest first.
  const stateNote = useMemo(() => {
    const candidates = (notesList.filter?.(n => n.title === NOTE_TITLE) || [])
    candidates.sort((a, b) => (a.created_at || '').localeCompare(b.created_at || ''))
    return candidates[0] || null
  }, [notesList])

  // Local state is the source of truth while editing; server writes are
  // debounced whole-blob upserts (see saveSoon). While clean (no pending
  // edit/save), re-hydrate from the server so the other profile's checks
  // show up without a reload.
  const [state, setState] = useState(null)
  const noteIdRef = useRef(null)
  const dirtyRef = useRef(false)
  useEffect(() => {
    if (isLoading || dirtyRef.current) return
    if (stateNote) noteIdRef.current = stateNote.id
    setState(prev => {
      const server = parseState(stateNote)
      if (prev !== null && JSON.stringify(prev) === JSON.stringify(server)) return prev
      return server
    })
  }, [isLoading, stateNote])

  const saveTimer = useRef(null)
  const savingRef = useRef(Promise.resolve())
  const pendingRef = useRef(null)

  const doSave = useCallback((blob) => {
    // Chain writes so a create finishes (and yields its id) before any patch.
    savingRef.current = savingRef.current.then(async () => {
      const body = { title: NOTE_TITLE, content: JSON.stringify(blob), pinned: false }
      try {
        if (!noteIdRef.current) {
          // Anti-duplicata: another device may have created the note since we
          // loaded — re-check by fresh GET before POSTing a new one.
          const fresh = await api.get('/home/notes/')
          const list = fresh.results || fresh
          const existing = (list.filter?.(n => n.title === NOTE_TITLE) || [])
            .sort((a, b) => (a.created_at || '').localeCompare(b.created_at || ''))[0]
          if (existing) noteIdRef.current = existing.id
        }
        if (noteIdRef.current) {
          await api.patch(`/home/notes/${noteIdRef.current}/`, body)
        } else {
          const created = await api.post('/home/notes/', { ...body, author_name: 'Vault' })
          noteIdRef.current = created?.id || null
        }
        if (pendingRef.current === blob) {
          pendingRef.current = null
          dirtyRef.current = false
        }
        queryClient.invalidateQueries({ queryKey: ['home-notes'] })
      } catch (e) {
        console.error('enxoval: falha ao salvar estado', e)
      }
    })
  }, [queryClient])

  const saveSoon = useCallback((next) => {
    dirtyRef.current = true
    pendingRef.current = next
    clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(() => doSave(next), 600)
  }, [doSave])

  // Flush (not drop) any pending edit when the component unmounts —
  // e.g. switching to another sub-tab within the debounce window.
  useEffect(() => () => {
    clearTimeout(saveTimer.current)
    if (pendingRef.current) doSave(pendingRef.current)
  }, [doSave])

  const update = useCallback((updater) => {
    setState(prev => {
      const next = updater(prev || EMPTY_STATE)
      saveSoon(next)
      return next
    })
  }, [saveSoon])

  const toggleItem = (id) => update(s => {
    const checked = { ...s.checked }
    if (checked[id]) delete checked[id]
    else checked[id] = true
    return { ...s, checked }
  })

  const addCustom = (catId, label) => update(s => ({
    ...s,
    custom: [...s.custom, { id: customId(), cat: catId, label }],
  }))

  const removeCustom = (id) => update(s => {
    const checked = { ...s.checked }
    delete checked[id]
    return { ...s, checked, custom: s.custom.filter(c => c.id !== id) }
  })

  const [filter, setFilter] = useState('todos') // todos | pendentes | essenciais
  const [expanded, setExpanded] = useState(null) // null = auto by status

  const checked = state?.checked || {}
  const custom = state?.custom || []

  // Per-category rows (base + custom) and progress.
  const cats = useMemo(() => ENXOVAL_CATEGORIES.map(cat => {
    const customItems = custom
      .filter(c => c.cat === cat.id)
      .map(c => ({ id: c.id, label: c.label, isCustom: true }))
    const all = [...cat.items, ...customItems]
    const done = all.filter(i => checked[i.id]).length
    const status = categoryStatus(cat, currentWeek, done, all.length, pregnancy?.status)
    return { ...cat, all, done, total: all.length, status }
  }), [custom, checked, currentWeek, pregnancy?.status])

  const totalDone = cats.reduce((a, c) => a + c.done, 0)
  const totalItems = cats.reduce((a, c) => a + c.total, 0)
  const pct = totalItems ? Math.round((totalDone / totalItems) * 100) : 0
  const phase = PHASE_HINTS.find(p => currentWeek != null && currentWeek < p.until)

  const isOpen = (cat) =>
    expanded ? expanded.has(cat.id) : (cat.status === 'current' || cat.status === 'overdue')
  const toggleOpen = (cat) => {
    const base = expanded || new Set(cats.filter(isOpen).map(c => c.id))
    const next = new Set(base)
    if (next.has(cat.id)) next.delete(cat.id)
    else next.add(cat.id)
    setExpanded(next)
  }

  if (state === null) {
    return <div className={styles.loading}>Carregando mapa do enxoval…</div>
  }

  return (
    <div className={styles.enxoval}>
      {/* ── Header: progress + week phase ── */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.headerTitle}>Mapa do Enxoval</div>
          <div className={styles.headerSub}>
            {currentWeek != null && <>Semana <strong>{formatWeeks(currentWeek)}</strong> · </>}
            {phase?.text || 'Checklist compartilhado do casal.'}
          </div>
        </div>
        <div className={styles.headerProgress}>
          <div className={styles.progressNum}>{totalDone}<span>/{totalItems}</span></div>
          <div className={styles.progressBar}>
            <div className={styles.progressFill} style={{ width: `${pct}%` }} />
          </div>
          <div className={styles.progressPct}>{pct}% pronto</div>
        </div>
      </div>

      {/* ── Filters ── */}
      <div className={styles.filters} role="group" aria-label="Filtro de itens">
        {[['todos', 'Todos'], ['pendentes', 'Pendentes'], ['essenciais', 'Essenciais']].map(([key, label]) => (
          <button
            key={key}
            className={filter === key ? styles.filterActive : styles.filter}
            aria-pressed={filter === key}
            onClick={() => setFilter(key)}
          >
            {label}
          </button>
        ))}
      </div>

      {/* ── Categories ── */}
      {cats.map(cat => {
        const open = isOpen(cat)
        const visible = cat.all.filter(item => {
          if (filter === 'pendentes') return !checked[item.id]
          if (filter === 'essenciais') return item.critical
          return true
        })
        let lastGroup = null
        return (
          <section key={cat.id} className={styles.card} data-status={cat.status}>
            <button
              className={styles.cardHead}
              onClick={() => toggleOpen(cat)}
              aria-expanded={open}
            >
              <span className={styles.cardIcon} aria-hidden="true">{cat.icon}</span>
              <span className={styles.cardTitleWrap}>
                <span className={styles.cardTitle}>{cat.title}</span>
                <span className={styles.cardMeta}>
                  {cat.done}/{cat.total}
                  {cat.buyWindow && <> · comprar entre as semanas {cat.buyWindow[0]}–{cat.buyWindow[1]}</>}
                </span>
              </span>
              <span className={styles.cardProgressBar}>
                <span
                  className={styles.cardProgressFill}
                  style={{ width: `${cat.total ? (cat.done / cat.total) * 100 : 0}%` }}
                />
              </span>
              <span className={styles.statusPill} data-status={cat.status}>
                {STATUS_LABEL[cat.status]}
              </span>
              <span className={styles.chevron} data-open={open} aria-hidden="true">▾</span>
            </button>

            {open && (
              <div className={styles.cardBody}>
                {cat.intro && <p className={styles.catIntro}>{cat.intro}</p>}

                {visible.length === 0 && (
                  <div className={styles.emptyFilter}>Nada aqui com esse filtro.</div>
                )}

                <ul className={styles.itemList}>
                  {visible.map(item => {
                    const showGroup = item.group && item.group !== lastGroup
                    lastGroup = item.group || lastGroup
                    return (
                      <li key={item.id}>
                        {showGroup && <div className={styles.groupHead}>{item.group}</div>}
                        <div className={styles.itemRow}>
                          <label className={styles.item} data-checked={!!checked[item.id]}>
                            <input
                              type="checkbox"
                              checked={!!checked[item.id]}
                              onChange={() => toggleItem(item.id)}
                            />
                            <span className={styles.itemBody}>
                              <span className={styles.itemLabel}>
                                {item.label}
                                {item.qty && <span className={styles.qty}>{item.qty}</span>}
                                {item.critical && <span className={styles.critical}>essencial</span>}
                              </span>
                              {item.note && <span className={styles.itemNote}>{item.note}</span>}
                            </span>
                          </label>
                          {item.isCustom && (
                            <button
                              type="button"
                              className={styles.removeCustom}
                              aria-label={`Remover item ${item.label}`}
                              onClick={() => removeCustom(item.id)}
                            >
                              ×
                            </button>
                          )}
                        </div>
                      </li>
                    )
                  })}
                </ul>

                <AddCustomForm onAdd={(label) => addCustom(cat.id, label)} />

                {cat.avoid?.length > 0 && (
                  <div className={styles.avoidBox}>
                    <div className={styles.avoidTitle}>⚠ Evitar</div>
                    <ul>
                      {cat.avoid.map((a, i) => <li key={i}>{a}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </section>
        )
      })}

      {/* ── Sources ── */}
      <div className={styles.sources}>
        <div className={styles.sourcesTitle}>Fontes</div>
        <ul>
          {Object.entries(SOURCES).map(([id, s]) => (
            <li key={id}>
              <a href={s.url} target="_blank" rel="noreferrer">{s.label} ↗</a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

function AddCustomForm({ onAdd }) {
  const [value, setValue] = useState('')
  const submit = (e) => {
    e.preventDefault()
    const label = value.trim()
    if (!label) return
    onAdd(label)
    setValue('')
  }
  return (
    <form className={styles.addForm} onSubmit={submit}>
      <input
        type="text"
        value={value}
        placeholder="Adicionar item…"
        aria-label="Novo item da categoria"
        onChange={(e) => setValue(e.target.value)}
        maxLength={120}
      />
      <button type="submit" aria-label="Adicionar item" disabled={!value.trim()}>+</button>
    </form>
  )
}
