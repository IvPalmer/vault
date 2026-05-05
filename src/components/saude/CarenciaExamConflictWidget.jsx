/**
 * CarenciaExamConflictWidget — surfaces conflicts between upcoming
 * pre-natal checkpoints and Amil insurance carência clear dates.
 *
 * For each near-term checkpoint (next 60 days), compares:
 *   - exam ideal date window (computed from DUM + checkpoint.week)
 *   - carência clear date for that exam category (from pregnancy.carencias)
 *
 * Renders only checkpoints with a real conflict or partial coverage.
 */
import { useMemo } from 'react'
import styles from './saude-widgets.module.css'
import { CHECKPOINTS, getKindMeta } from './checkpoints'
import { parseLocalDate, addDays, diffDays, fmtDate, fmtDateShort, todayLocal } from './dateUtils'

/**
 * For a checkpoint with `week: [start, end]` and a DUM date, compute the
 * absolute ideal window in calendar dates.
 */
function checkpointWindow(checkpoint, dum) {
  if (!dum) return null
  const range = checkpoint.week
  const startWeek = Array.isArray(range) ? range[0] : range
  const endWeek = Array.isArray(range) && range.length > 1 ? range[1] : startWeek
  return {
    start: addDays(dum, Math.floor(startWeek * 7)),
    end: addDays(dum, Math.ceil(endWeek * 7)),
  }
}

/**
 * Classify the conflict between exam window and carência clear date.
 *
 *   - 'cleared'        — exam window starts after carência clears (no conflict)
 *   - 'partial'        — carência clears DURING exam window (partial coverage)
 *   - 'uncovered'      — carência clears AFTER exam window ends (fully uncovered)
 *   - 'no_carencia'    — no carência mapped (not insurance-relevant)
 */
function classifyConflict(window, clearDate) {
  if (!clearDate) return 'no_carencia'
  if (clearDate <= window.start) return 'cleared'
  if (clearDate >= window.end) return 'uncovered'
  return 'partial'
}

export default function CarenciaExamConflictWidget({ pregnancy }) {
  const dum = pregnancy?.dum ? parseLocalDate(pregnancy.dum) : null
  const carencias = pregnancy?.carencias

  const conflicts = useMemo(() => {
    if (!dum || !carencias) return []
    const today = todayLocal()
    const horizon = addDays(today, 60)

    const out = []
    for (const cp of CHECKPOINTS) {
      const slug = cp.carencia_slug
      if (!slug) continue
      const carencia = carencias[slug]
      if (!carencia) continue

      const window = checkpointWindow(cp, dum)
      if (!window) continue

      // Skip if exam window is far in the future or already past
      if (window.start > horizon) continue
      if (window.end < today) continue

      const clearDate = parseLocalDate(carencia.clear_date)
      const status = classifyConflict(window, clearDate)
      // Only surface non-cleared conflicts
      if (status === 'cleared' || status === 'no_carencia') continue

      out.push({
        checkpoint: cp,
        window,
        carencia,
        clearDate,
        status,
        daysToWindowStart: diffDays(window.start, today),
      })
    }

    out.sort((a, b) => a.window.start - b.window.start)
    return out
  }, [dum, carencias])

  if (!pregnancy || !dum || !carencias) return null

  if (conflicts.length === 0) {
    return (
      <div className={styles.conflictWidget} data-status="ok">
        <div className={styles.conflictHeader}>
          <span className={styles.widgetLabel}>Conflitos carência × exames</span>
          <span className={styles.conflictBadge} data-status="ok">tudo coberto próximos 60 dias</span>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.conflictWidget} data-status="warning">
      <div className={styles.conflictHeader}>
        <span className={styles.widgetLabel}>Conflitos carência × exames próximos 60 dias</span>
        <span className={styles.conflictBadge} data-status="warning">{conflicts.length} alerta{conflicts.length > 1 ? 's' : ''}</span>
      </div>

      <div className={styles.conflictList}>
        {conflicts.map(c => {
          const meta = getKindMeta(c.checkpoint.kind)
          return (
            <div key={c.checkpoint.id} className={styles.conflictRow} data-status={c.status}>
              <div className={styles.conflictRowHeader}>
                <span className={styles.conflictKind} style={{ background: meta.color }}>{meta.short}</span>
                <span className={styles.conflictTitle}>{c.checkpoint.label}</span>
                <span className={styles.conflictStatusPill} data-status={c.status}>
                  {c.status === 'uncovered' ? 'sem cobertura' : 'cobertura parcial'}
                </span>
              </div>
              <div className={styles.conflictDetails}>
                <div>
                  <span className={styles.conflictLabel}>Janela ideal:</span>{' '}
                  <strong>{fmtDateShort(c.window.start)} – {fmtDateShort(c.window.end)}</strong>
                  {' · sem '}
                  <strong>{c.checkpoint.week[0]}–{c.checkpoint.week[1] || c.checkpoint.week[0]}</strong>
                </div>
                <div>
                  <span className={styles.conflictLabel}>Amil libera:</span>{' '}
                  <strong>{fmtDate(c.clearDate)}</strong>
                  {' · '}
                  {c.carencia.label} ({c.carencia.days} dias)
                </div>
                {c.status === 'uncovered' && (
                  <div className={styles.conflictAction}>
                    Janela inteira fora da cobertura. Opção: agendar particular ou aguardar carência terminar (perde a janela ideal).
                  </div>
                )}
                {c.status === 'partial' && (
                  <div className={styles.conflictAction}>
                    Carência libera no meio da janela. Opção A: particular antes de {fmtDateShort(c.clearDate)}. Opção B: agendar Amil entre {fmtDateShort(c.clearDate)} e {fmtDateShort(c.window.end)}.
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
