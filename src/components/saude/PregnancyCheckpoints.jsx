/**
 * PregnancyCheckpoints — vertical list grouped by trimester with status pills.
 */
import { useMemo } from 'react'
import styles from './saude-widgets.module.css'
import { CHECKPOINTS, getKindMeta, checkpointStatus, weeksFromDum } from './checkpoints'

function checkpointStartWeek(cp) {
  return Array.isArray(cp.week) ? cp.week[0] : cp.week
}

const STATUS_LABEL = {
  completed: 'feito',
  current: 'agora',
  upcoming: 'futuro',
  overdue: 'atrasado',
}

export default function PregnancyCheckpoints({ pregnancy, completedIds = new Set() }) {
  const decimalWeeks = useMemo(() => weeksFromDum(pregnancy?.dum), [pregnancy?.dum])

  const grouped = useMemo(() => {
    const t = { 1: [], 2: [], 3: [] }
    const sorted = [...CHECKPOINTS].sort((a, b) => checkpointStartWeek(a) - checkpointStartWeek(b))
    for (const cp of sorted) {
      const w = checkpointStartWeek(cp)
      const tri = w < 14 ? 1 : w < 28 ? 2 : 3
      t[tri].push(cp)
    }
    return t
  }, [])

  return (
    <div className={styles.checkpointsWidget}>
      {[1, 2, 3].map(tri => (
        <div key={tri} className={styles.triGroup}>
          <div className={styles.triHeader}>{tri}º trimestre</div>
          <div className={styles.triList}>
            {grouped[tri].map(cp => {
              const status = checkpointStatus(cp, decimalWeeks, completedIds)
              const meta = getKindMeta(cp.kind)
              return (
                <div key={cp.id} className={styles.checkpointRow} data-status={status}>
                  <div className={styles.checkpointIcon} style={{ background: meta.color }}>
                    {status === 'completed' ? '✓' : meta.icon}
                  </div>
                  <div className={styles.checkpointBody}>
                    <div className={styles.checkpointLabel}>{cp.label}</div>
                    <div className={styles.checkpointMeta}>
                      sem {Array.isArray(cp.week) ? (cp.week[1] != null ? `${cp.week[0]}-${cp.week[1]}` : `${cp.week[0]}+`) : cp.week}
                      {cp.critical && <span className={styles.criticalTag}>essencial</span>}
                    </div>
                  </div>
                  <div className={styles.checkpointStatus} data-status={status}>
                    {STATUS_LABEL[status]}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
