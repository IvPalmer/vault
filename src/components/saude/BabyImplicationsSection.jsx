/**
 * BabyImplicationsSection — synthesizes findings from both Palmer's and
 * Rafa's exams that have direct or potential impact on the pregnancy or
 * neonate. Lives in the Família tab.
 *
 * Each implication may declare `marker_refs` linking it to specific
 * LabMarker rows in the DB. The section fetches markers for both
 * profiles and renders live value chips inside the relevant cards.
 */
import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../../api/client'
import styles from './saude-widgets.module.css'
import { BABY_IMPLICATIONS, PRIORIDADE_LABEL } from './babyImplications'

function fmtValue(v) {
  if (v === null || v === undefined) return '—'
  const n = parseFloat(v)
  if (isNaN(n)) return v
  // Smart formatting: integers stay integer, decimals get up to 2 places
  if (Math.abs(n) >= 1000) return n.toLocaleString('pt-BR')
  if (Number.isInteger(n)) return n.toString()
  return n.toLocaleString('pt-BR', { maximumFractionDigits: 2 })
}

function fmtDate(iso) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y.slice(2)}`
}

function MarkerChip({ marker }) {
  if (!marker) return null
  const value = marker.value !== null && marker.value !== undefined
    ? fmtValue(marker.value)
    : marker.value_text || '—'
  return (
    <div className={styles.implMarkerChip} data-status={marker.status}>
      <span className={styles.implMarkerChipLabel}>{marker.label}</span>
      <span className={styles.implMarkerChipValue}>{value}{marker.unit && ` ${marker.unit}`}</span>
      <span className={styles.implMarkerChipMeta}>
        {marker.status} · {fmtDate(marker.exam_data)}
      </span>
    </div>
  )
}

function ImplicationCard({ item, expanded, onToggle, markerMap }) {
  // Resolve marker_refs to actual marker objects from the map
  const liveMarkers = useMemo(() => {
    if (!item.marker_refs || !markerMap) return []
    return item.marker_refs
      .map(ref => markerMap.get(`${ref.profile}/${ref.category}.${ref.key}`))
      .filter(Boolean)
  }, [item.marker_refs, markerMap])

  return (
    <div className={styles.implCard} data-priority={item.prioridade}>
      <button className={styles.implHeader} onClick={onToggle}>
        <div className={styles.implHeaderLeft}>
          <span className={styles.implCategoria}>{item.categoria}</span>
          <span className={styles.implTitulo}>{item.titulo}</span>
        </div>
        <div className={styles.implHeaderRight}>
          {liveMarkers.length > 0 && (
            <span className={styles.implLiveBadge} title="Valores ao vivo do banco">
              {liveMarkers.length} live
            </span>
          )}
          <span className={styles.implPrioridade} data-priority={item.prioridade}>
            {PRIORIDADE_LABEL[item.prioridade]}
          </span>
          <span className={styles.implChevron}>{expanded ? '−' : '+'}</span>
        </div>
      </button>

      {expanded && (
        <div className={styles.implBody}>
          <div className={styles.implOrigem}>Fonte: {item.origem}</div>
          <div className={styles.implResumo}>{item.resumo}</div>

          {liveMarkers.length > 0 && (
            <div className={styles.implMarkersBlock}>
              <div className={styles.implMarkersTitle}>Valores atuais (banco)</div>
              <div className={styles.implMarkersGrid}>
                {liveMarkers.map(m => <MarkerChip key={m.id} marker={m} />)}
              </div>
            </div>
          )}

          {item.cenarios && (
            <div className={styles.implScenarios}>
              <div className={styles.implScenarioTitle}>Cenários de herança</div>
              <div className={styles.implScenariosGrid}>
                {item.cenarios.map((c, i) => (
                  <div key={i} className={styles.implScenario}>
                    <div className={styles.implScenarioLabel}>{c.label}</div>
                    {c.probabilidade && <div className={styles.implScenarioProb}>{c.probabilidade}</div>}
                    {c.filho_homem && (
                      <div className={styles.implScenarioOutcome}>
                        <strong>Filho:</strong> {c.filho_homem}
                      </div>
                    )}
                    {c.filha_mulher && (
                      <div className={styles.implScenarioOutcome}>
                        <strong>Filha:</strong> {c.filha_mulher}
                      </div>
                    )}
                    {c.impacto && <div className={styles.implScenarioOutcome}>{c.impacto}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className={styles.implActionTitle}>Ações concretas</div>
          <ul className={styles.implActions}>
            {item.acoes.map((a, i) => <li key={i}>{a}</li>)}
          </ul>

          {item.evitar && (
            <div className={styles.implEvitar}>
              <div className={styles.implEvitarTitle}>{item.evitar.titulo}</div>
              <ul className={styles.implEvitarList}>
                {item.evitar.itens.map((it, i) => <li key={i}>{it}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function BabyImplicationsSection() {
  // All items collapsed by default. User opens only what they need.
  // Previously expanded all `alta` items, producing 9 simultaneously-open
  // verbose cards that made the page impossible to scan.
  const [expanded, setExpanded] = useState(new Set())

  // Fetch profiles to map names -> ids.
  // Note: api.get() returns parsed JSON directly (no .data wrapper).
  const { data: profiles = [] } = useQuery({
    queryKey: ['profiles'],
    queryFn: async () => (await api.get('/profiles/')) || [],
    staleTime: 60_000,
  })

  const profileByName = useMemo(() => {
    const m = new Map()
    for (const p of profiles) m.set(p.name?.toLowerCase(), p)
    return m
  }, [profiles])

  const palmer = profileByName.get('palmer')
  const rafa = profileByName.get('rafa')

  // Fetch lab markers for both profiles in parallel
  const { data: palmerMarkers = [] } = useQuery({
    queryKey: ['lab-markers', palmer?.id],
    queryFn: async () => {
      if (!palmer?.id) return []
      return (await api.get(`/saude/lab-markers/?profile_id=${palmer.id}`)) || []
    },
    enabled: !!palmer?.id,
  })

  const { data: rafaMarkers = [] } = useQuery({
    queryKey: ['lab-markers', rafa?.id],
    queryFn: async () => {
      if (!rafa?.id) return []
      return (await api.get(`/saude/lab-markers/?profile_id=${rafa.id}`)) || []
    },
    enabled: !!rafa?.id,
  })

  // Build map: "palmer/inflamatorio.pcr" -> marker (most recent)
  // Backend already orders by exam.data desc, so first occurrence is latest
  const markerMap = useMemo(() => {
    const m = new Map()
    for (const mk of palmerMarkers) {
      const k = `palmer/${mk.category_slug}.${mk.key}`
      if (!m.has(k)) m.set(k, mk)
    }
    for (const mk of rafaMarkers) {
      const k = `rafa/${mk.category_slug}.${mk.key}`
      if (!m.has(k)) m.set(k, mk)
    }
    return m
  }, [palmerMarkers, rafaMarkers])

  const toggle = (id) => {
    setExpanded(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const grouped = BABY_IMPLICATIONS.reduce((acc, item) => {
    if (!acc[item.prioridade]) acc[item.prioridade] = []
    acc[item.prioridade].push(item)
    return acc
  }, {})

  const order = ['alta', 'media', 'baixa']

  // Count of items with at least one live marker resolved
  const linkedCount = BABY_IMPLICATIONS.filter(i =>
    i.marker_refs && i.marker_refs.some(r => markerMap.get(`${r.profile}/${r.category}.${r.key}`))
  ).length

  // Render strategy:
  //  - "Alta" priority: visible by default, cards collapsed
  //  - "Média" + "Baixa": wrapped in <details> so they don't dominate scroll
  const altaItems = grouped.alta || []
  const mediaItems = grouped.media || []
  const baixaItems = grouped.baixa || []

  return (
    <div className={styles.implSection}>
      <div className={styles.implSectionHeader}>
        <h2 className={styles.implSectionTitle}>Implicações para o bebê — síntese cruzada</h2>
        <div className={styles.implSectionDesc}>
          Achados de ambos os perfis (Palmer + Rafa) com impacto direto ou potencial na gestação ou no neonato.
          {linkedCount > 0 && (
            <span className={styles.implSectionDescBadge}>
              {' · '}{linkedCount} {linkedCount === 1 ? 'item' : 'itens'} com valores ao vivo do banco
            </span>
          )}
        </div>
      </div>

      {altaItems.length > 0 && (
        <div className={styles.implPrioGroup}>
          <div className={styles.implPrioHeader}>
            {PRIORIDADE_LABEL.alta} ({altaItems.length})
          </div>
          <div className={styles.implList}>
            {altaItems.map(item => (
              <ImplicationCard
                key={item.id}
                item={item}
                expanded={expanded.has(item.id)}
                onToggle={() => toggle(item.id)}
                markerMap={markerMap}
              />
            ))}
          </div>
        </div>
      )}

      {(mediaItems.length > 0 || baixaItems.length > 0) && (
        <details className={styles.implSecondaryAccordion}>
          <summary>
            Resolvidos e baixa prioridade · {mediaItems.length + baixaItems.length}
            <span className={styles.implAccordionHint}>ver detalhes</span>
          </summary>
          <div className={styles.implSecondaryBody}>
            {mediaItems.length > 0 && (
              <div className={styles.implPrioGroup}>
                <div className={styles.implPrioHeader}>
                  {PRIORIDADE_LABEL.media} ({mediaItems.length})
                </div>
                <div className={styles.implList}>
                  {mediaItems.map(item => (
                    <ImplicationCard
                      key={item.id}
                      item={item}
                      expanded={expanded.has(item.id)}
                      onToggle={() => toggle(item.id)}
                      markerMap={markerMap}
                    />
                  ))}
                </div>
              </div>
            )}
            {baixaItems.length > 0 && (
              <div className={styles.implPrioGroup}>
                <div className={styles.implPrioHeader}>
                  {PRIORIDADE_LABEL.baixa} ({baixaItems.length})
                </div>
                <div className={styles.implList}>
                  {baixaItems.map(item => (
                    <ImplicationCard
                      key={item.id}
                      item={item}
                      expanded={expanded.has(item.id)}
                      onToggle={() => toggle(item.id)}
                      markerMap={markerMap}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        </details>
      )}
    </div>
  )
}
