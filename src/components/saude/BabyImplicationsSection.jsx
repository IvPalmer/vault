/**
 * BabyImplicationsSection — synthesizes findings from both Palmer's and
 * Rafa's exams that have direct or potential impact on the pregnancy or
 * neonate. Lives in the Família tab.
 */
import { useState } from 'react'
import styles from './saude-widgets.module.css'
import { BABY_IMPLICATIONS, PRIORIDADE_LABEL } from './babyImplications'

function ImplicationCard({ item, expanded, onToggle }) {
  return (
    <div className={styles.implCard} data-priority={item.prioridade}>
      <button className={styles.implHeader} onClick={onToggle}>
        <div className={styles.implHeaderLeft}>
          <span className={styles.implCategoria}>{item.categoria}</span>
          <span className={styles.implTitulo}>{item.titulo}</span>
        </div>
        <div className={styles.implHeaderRight}>
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
  // Default-expanded items: high-priority ones
  const defaultExpanded = new Set(BABY_IMPLICATIONS.filter(i => i.prioridade === 'alta').map(i => i.id))
  const [expanded, setExpanded] = useState(defaultExpanded)

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

  return (
    <div className={styles.implSection}>
      <div className={styles.implSectionHeader}>
        <h2 className={styles.implSectionTitle}>Implicações para o bebê — síntese cruzada</h2>
        <div className={styles.implSectionDesc}>
          Achados de ambos os perfis (Palmer + Rafa) com impacto direto ou potencial na gestação ou no neonato. Itens de alta prioridade abertos por padrão.
        </div>
      </div>

      {order.map(prio => grouped[prio] && (
        <div key={prio} className={styles.implPrioGroup}>
          <div className={styles.implPrioHeader}>
            {PRIORIDADE_LABEL[prio]} ({grouped[prio].length})
          </div>
          <div className={styles.implList}>
            {grouped[prio].map(item => (
              <ImplicationCard
                key={item.id}
                item={item}
                expanded={expanded.has(item.id)}
                onToggle={() => toggle(item.id)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
