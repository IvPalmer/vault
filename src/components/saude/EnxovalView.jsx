/**
 * EnxovalView — "Mapa do Enxoval da Laura" na aba Família.
 *
 * Os dados vêm de enxovalData.js, que é GERADO a partir da mesma fonte que
 * produz o PDF entregue à família (scratchpad/enxoval/modules.py). App e PDF
 * não divergem: mudou o conteúdo, roda-se o export e os dois acompanham.
 *
 * Cada módulo traz blocos de tipos diferentes — checklist, tabela, linha do
 * tempo, caixa de destaque, caixa "evitar" — e cada item tem sua ilustração.
 * O módulo ganha status pela janela de compra em semanas gestacionais.
 *
 * Persistência: um FamilyNote (title = NOTE_TITLE) com um blob JSON
 * { v, checked: {itemId: true}, custom: [{id, cat, label}] }. FamilyNotes são
 * compartilhados na casa e têm CRUD completo, então nada muda no backend.
 * Home.jsx esconde títulos com prefixo "__". Escritas são upserts do blob
 * inteiro, com debounce — last write wins, suficiente para duas pessoas.
 */
import { useState, useMemo, useEffect, useRef, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../../api/client'
import { MODULES, ICONS, SPOTS, SOURCES, PAL } from './enxovalData'
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

function moduleStatus(mod, currentWeek, done, total, pregnancyStatus) {
  // Módulo-guia (inIndex false) vale a gestação inteira, não é pós-parto.
  if (mod.inIndex === false) return 'current'
  if (total > 0 && done === total) return 'completed'
  // Sem janela de compra = prazos, que só ficam "agora" depois do parto.
  if (!mod.buyWindow) return pregnancyStatus === 'finalizada' ? 'current' : 'posparto'
  if (currentWeek == null) return 'upcoming'
  const [start, end] = mod.buyWindow
  if (currentWeek > end) return 'overdue'
  if (currentWeek >= start) return 'current'
  return 'upcoming'
}

const STATUS_LABEL = {
  completed: 'feito', current: 'agora', upcoming: 'futuro',
  overdue: 'atrasado', posparto: 'pós-parto',
}

/** SVG vindo dos dados — conteúdo nosso, gerado no build, nunca de terceiros. */
function Art({ svg, className }) {
  if (!svg) return null
  return <span className={className} dangerouslySetInnerHTML={{ __html: svg }} />
}

export default function EnxovalView({ pregnancy }) {
  const queryClient = useQueryClient()
  const currentWeek = useMemo(() => weeksFromDum(pregnancy?.dum), [pregnancy?.dum])

  const { data: notes = [], isLoading } = useQuery({
    queryKey: ['home-notes'],
    queryFn: () => api.get('/home/notes/'),
  })
  const notesList = notes.results || notes
  const stateNote = useMemo(() => {
    const candidates = (notesList.filter?.(n => n.title === NOTE_TITLE) || [])
    candidates.sort((a, b) => (a.created_at || '').localeCompare(b.created_at || ''))
    return candidates[0] || null
  }, [notesList])

  const [state, setState] = useState(null)
  const noteIdRef = useRef(null)
  const dirtyRef = useRef(false)
  useEffect(() => {
    if (isLoading || dirtyRef.current) return
    noteIdRef.current = stateNote ? stateNote.id : null
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
    savingRef.current = savingRef.current.then(async () => {
      const body = { title: NOTE_TITLE, content: JSON.stringify(blob), pinned: false }
      try {
        if (!noteIdRef.current) {
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
        // Sem retry automático, mas destravamos a re-hidratação: manter
        // dirtyRef em true cegaria esta aba para as edições do outro perfil
        // pelo resto da sessão.
        console.error('enxoval: falha ao salvar estado', e)
        if (pendingRef.current === blob) {
          pendingRef.current = null
          dirtyRef.current = false
        }
      }
    })
  }, [queryClient])

  const saveSoon = useCallback((next) => {
    dirtyRef.current = true
    pendingRef.current = next
    clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(() => doSave(next), 600)
  }, [doSave])

  useEffect(() => () => {
    clearTimeout(saveTimer.current)
    if (pendingRef.current) doSave(pendingRef.current)
  }, [doSave])

  const update = useCallback((updater) => {
    setState(prev => {
      const next = updater(prev || EMPTY_STATE)
      // agenda fora do updater: o React pode reexecutá-lo
      queueMicrotask(() => saveSoon(next))
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
    ...s, custom: [...s.custom, { id: customId(), cat: catId, label }],
  }))

  const removeCustom = (id) => update(s => {
    const checked = { ...s.checked }
    delete checked[id]
    return { ...s, checked, custom: s.custom.filter(c => c.id !== id) }
  })

  const [filter, setFilter] = useState('todos')
  const [expanded, setExpanded] = useState(null)

  const checked = state?.checked || {}
  const custom = state?.custom || []

  // Itens de um módulo = os do conteúdo + os que o casal adicionou.
  const mods = useMemo(() => MODULES.map(mod => {
    const base = []
    for (const b of mod.blocks) {
      if (b.kind === 'items') base.push(...b.items)
      else if (b.kind === 'groups') b.groups.forEach(g => base.push(...g.items))
    }
    const extra = custom.filter(c => c.cat === mod.id)
      .map(c => ({ id: c.id, label: c.label, isCustom: true, icon: 'check' }))
    const all = [...base, ...extra]
    const done = all.filter(i => checked[i.id]).length
    return {
      ...mod, extra, done, total: all.length,
      status: moduleStatus(mod, currentWeek, done, all.length, pregnancy?.status),
    }
  }), [custom, checked, currentWeek, pregnancy?.status])

  const totalDone = mods.reduce((a, m) => a + m.done, 0)
  const totalItems = mods.reduce((a, m) => a + m.total, 0)
  const pct = totalItems ? Math.round((totalDone / totalItems) * 100) : 0

  const isOpen = (mod) =>
    expanded ? expanded.has(mod.id) : (mod.status === 'current' || mod.status === 'overdue')
  const toggleOpen = (mod) => {
    const base = expanded || new Set(mods.filter(isOpen).map(m => m.id))
    const next = new Set(base)
    if (next.has(mod.id)) next.delete(mod.id)
    else next.add(mod.id)
    setExpanded(next)
  }

  const keep = (it) => {
    if (filter === 'pendentes') return !checked[it.id]
    if (filter === 'essenciais') return it.ess
    return true
  }

  if (state === null) {
    return <div className={styles.loading}>Carregando mapa do enxoval…</div>
  }

  const renderItem = (it, pal) => (
    <div key={it.id} className={styles.itemRow}>
      <label className={styles.item} data-checked={!!checked[it.id]}>
        <input type="checkbox" checked={!!checked[it.id]} onChange={() => toggleItem(it.id)} />
        <Art svg={ICONS[it.icon]} className={styles.itemArt} />
        <span className={styles.itemBody}>
          <span className={styles.itemLabel}>
            {it.label}
            {it.qty && (
              <span className={styles.qty} style={{ background: pal.tint, color: pal.deep }}>
                {it.qty}
              </span>
            )}
            {it.ess && <span className={styles.critical} style={{ color: pal.deep }}>essencial</span>}
          </span>
          {it.note && <span className={styles.itemNote}>{it.note}</span>}
        </span>
      </label>
      {it.isCustom && (
        <button type="button" className={styles.removeCustom}
          aria-label={`Remover item ${it.label}`} onClick={() => removeCustom(it.id)}>×</button>
      )}
    </div>
  )

  const renderBlock = (b, k, pal) => {
    switch (b.kind) {
      case 'intro':
        return <p key={k} className={styles.blockIntro}>{b.text}</p>
      case 'items': {
        const vis = b.items.filter(keep)
        if (!vis.length) return null
        return <div key={k} className={styles.itemList}>{vis.map(it => renderItem(it, pal))}</div>
      }
      case 'groups':
        return (
          <div key={k}>
            {b.groups.map(g => {
              const vis = g.items.filter(keep)
              if (!vis.length) return null
              return (
                <div key={g.name}>
                  <div className={styles.groupChip} style={{ background: pal.tint, color: pal.deep }}>
                    {g.name}
                  </div>
                  <div className={styles.itemList}>{vis.map(it => renderItem(it, pal))}</div>
                </div>
              )
            })}
          </div>
        )
      case 'table':
        return (
          <div key={k} className={styles.tableWrap}>
            {b.title && <div className={styles.tableTitle} style={{ color: pal.deep }}>{b.title}</div>}
            <table className={styles.table}>
              <thead><tr style={{ background: pal.tint }}>
                {b.head.map(h => <th key={h}>{h}</th>)}
              </tr></thead>
              <tbody>
                {b.rows.map((r, ri) => <tr key={ri}>{r.map((c, ci) => <td key={ci}>{c}</td>)}</tr>)}
              </tbody>
            </table>
            {b.note && <div className={styles.tableNote}>{b.note}</div>}
          </div>
        )
      case 'timeline':
        return (
          <div key={k} className={styles.timeline}>
            {b.rows.map((r, ri) => {
              const hp = r.hot ? PAL.terra : PAL.blue
              return (
                <div key={ri} className={styles.tlRow}>
                  <span className={styles.tlWhen} style={{ background: hp.tint, color: hp.deep }}>
                    {r.when}
                  </span>
                  <div className={styles.tlWhat} dangerouslySetInnerHTML={{ __html: r.what }} />
                </div>
              )
            })}
          </div>
        )
      case 'tip':
        return (
          <div key={k} className={styles.tip} style={{ background: pal.tint, borderColor: pal.mid }}>
            <div className={styles.tipTitle} style={{ color: pal.deep }}>{b.title}</div>
            <div className={styles.tipBody} dangerouslySetInnerHTML={{ __html: b.body }} />
          </div>
        )
      case 'avoid':
        return (
          <div key={k} className={styles.avoid}>
            <div className={styles.avoidTitle}>✕ &nbsp;{b.title || 'melhor evitar'}</div>
            <ul>{b.items.map((a, ai) => <li key={ai}>{a}</li>)}</ul>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div className={styles.enxoval}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.headerTitle}>Mapa do Enxoval da Laura</div>
          <div className={styles.headerSub}>
            {currentWeek != null && <>Semana <strong>{formatWeeks(currentWeek)}</strong> · </>}
            {MODULES.length} módulos · mesma fonte do PDF da família
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

      <div className={styles.filters} role="group" aria-label="Filtro de itens">
        {[['todos', 'Todos'], ['pendentes', 'Pendentes'], ['essenciais', 'Essenciais']].map(([key, label]) => (
          <button key={key} className={filter === key ? styles.filterActive : styles.filter}
            aria-pressed={filter === key} onClick={() => setFilter(key)}>{label}</button>
        ))}
      </div>

      {mods.map(mod => {
        const pal = PAL[mod.pal] || PAL.terra
        const open = isOpen(mod)
        return (
          <section key={mod.id} className={styles.card} data-status={mod.status}>
            <button className={styles.cardHead} onClick={() => toggleOpen(mod)} aria-expanded={open}
              style={{ background: open ? pal.tint : undefined }}>
              <Art svg={SPOTS[mod.spot]} className={styles.cardArt} />
              <span className={styles.cardTitleWrap}>
                <span className={styles.cardNum} style={{ color: pal.deep }}>{mod.num}</span>
                <span className={styles.cardTitle}>{mod.title}</span>
                <span className={styles.cardMeta}>{mod.done}/{mod.total} · {mod.win}</span>
              </span>
              <span className={styles.statusPill} data-status={mod.status}>
                {STATUS_LABEL[mod.status]}
              </span>
              <span className={styles.chevron} data-open={open} aria-hidden="true">▾</span>
            </button>

            {open && (
              <div className={styles.cardBody}>
                {mod.intro && <p className={styles.catIntro}>{mod.intro}</p>}
                {mod.blocks.map((b, k) => renderBlock(b, k, pal))}
                {mod.total > 0 && mod.done === mod.total && filter === 'pendentes' && (
                  <div className={styles.emptyFilter}>Tudo marcado neste módulo. 🎉</div>
                )}
                {mod.extra.length > 0 && (
                  <div className={styles.itemList}>{mod.extra.filter(keep).map(it => renderItem(it, pal))}</div>
                )}
                <AddCustomForm onAdd={(label) => addCustom(mod.id, label)} />
              </div>
            )}
          </section>
        )
      })}

      <div className={styles.sources}>
        <div className={styles.sourcesTitle}>Fontes</div>
        <ul>{SOURCES.map((s, i) => <li key={i}>{s}</li>)}</ul>
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
      <input type="text" value={value} placeholder="Adicionar item…"
        aria-label="Novo item do módulo" onChange={(e) => setValue(e.target.value)} maxLength={120} />
      <button type="submit" aria-label="Adicionar item" disabled={!value.trim()}>+</button>
    </form>
  )
}
