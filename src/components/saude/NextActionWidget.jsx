/**
 * NextActionWidget — picks the most urgent upcoming/overdue checkpoint and
 * surfaces it as a hero card with countdown.
 */
import { useMemo } from 'react'
import styles from './saude-widgets.module.css'
import { CHECKPOINTS, getKindMeta, checkpointStatus, weeksFromDum } from './checkpoints'

function midWeek(cp) {
  return Array.isArray(cp.week) ? (cp.week[0] + cp.week[1]) / 2 : cp.week
}
function startWeek(cp) {
  return Array.isArray(cp.week) ? cp.week[0] : cp.week
}

export default function NextActionWidget({ pregnancy, completedIds = new Set() }) {
  const decimalWeeks = useMemo(() => weeksFromDum(pregnancy?.dum), [pregnancy?.dum])

  const next = useMemo(() => {
    if (decimalWeeks == null) return null
    // Priority: overdue critical → current critical → upcoming closest
    const candidates = CHECKPOINTS
      .filter(cp => !completedIds.has(cp.id))
      .map(cp => ({ cp, status: checkpointStatus(cp, decimalWeeks, completedIds) }))
      .filter(({ status }) => status !== 'completed')

    const overdueCritical = candidates.filter(({ cp, status }) => status === 'overdue' && cp.critical)
    if (overdueCritical.length) {
      return overdueCritical.sort((a, b) => midWeek(b.cp) - midWeek(a.cp))[0]
    }
    const currentCritical = candidates.filter(({ cp, status }) => status === 'current' && cp.critical)
    if (currentCritical.length) {
      return currentCritical[0]
    }
    const upcoming = candidates
      .filter(({ status }) => status === 'upcoming' || status === 'current')
      .sort((a, b) => startWeek(a.cp) - startWeek(b.cp))
    return upcoming[0] || null
  }, [decimalWeeks, completedIds])

  if (!pregnancy) {
    return (
      <div className={styles.nextActionEmpty}>
        Sem gestação ativa.
      </div>
    )
  }

  if (decimalWeeks == null) {
    return (
      <div className={styles.nextAction} data-urgency="info">
        <div className={styles.nextActionLabel}>Próximo passo</div>
        <div className={styles.nextActionTitle}>USG datação</div>
        <div className={styles.nextActionDesc}>
          Sem DUM cadastrada. Agendar USG de datação (ideal 7–9 sem) para definir IG e DPP.
        </div>
      </div>
    )
  }

  if (!next) {
    return (
      <div className={styles.nextAction} data-urgency="ok">
        <div className={styles.nextActionLabel}>Próximo passo</div>
        <div className={styles.nextActionTitle}>Tudo em dia</div>
        <div className={styles.nextActionDesc}>Nenhum checkpoint imediato pendente.</div>
      </div>
    )
  }

  const { cp, status } = next
  const meta = getKindMeta(cp.kind)
  const targetWeek = startWeek(cp)
  const weeksUntil = targetWeek - decimalWeeks
  const daysUntil = Math.ceil(weeksUntil * 7)

  let urgency = 'info'
  let countdown = ''
  if (status === 'overdue') {
    urgency = 'urgent'
    countdown = `Atrasado em ${Math.abs(daysUntil)} dias`
  } else if (status === 'current') {
    urgency = 'now'
    countdown = 'Janela ideal — agendar agora'
  } else if (daysUntil <= 14) {
    urgency = 'soon'
    countdown = `Em ${daysUntil} dias`
  } else {
    urgency = 'info'
    countdown = `Em ${daysUntil} dias`
  }

  return (
    <div className={styles.nextAction} data-urgency={urgency}>
      <div className={styles.nextActionLabel}>
        <span className={styles.nextActionKind} style={{ background: meta.color }}>{meta.label}</span>
        <span className={styles.nextActionCountdown}>{countdown}</span>
      </div>
      <div className={styles.nextActionTitle}>{cp.label}</div>
      <div className={styles.nextActionDesc}>
        {cp.notes || `Janela: semana${Array.isArray(cp.week) && cp.week[1] != null ? `s ${cp.week[0]}–${cp.week[1]}` : Array.isArray(cp.week) ? ` ${cp.week[0]}+` : ` ${cp.week}`}.`}
      </div>
    </div>
  )
}
