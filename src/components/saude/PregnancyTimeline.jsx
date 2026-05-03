/**
 * PregnancyTimeline — horizontal 0-40 week gantt with trimester bands and
 * checkpoint pins. Pattern 1.1 + 1.5 from research (multi-track on hover detail).
 */
import { useMemo, useState } from 'react'
import styles from './saude-widgets.module.css'
import { CHECKPOINTS, getKindMeta, checkpointStatus, weeksFromDum } from './checkpoints'

const TOTAL_WEEKS = 42  // a touch beyond 40 for visual breathing room
const T1_END = 13.6
const T2_END = 27.6

function checkpointMidWeek(cp) {
  const w = cp.week
  return Array.isArray(w) ? (w[0] + w[1]) / 2 : w
}

export default function PregnancyTimeline({ pregnancy, completedIds = new Set() }) {
  const [hovered, setHovered] = useState(null)

  const decimalWeeks = useMemo(() => weeksFromDum(pregnancy?.dum), [pregnancy?.dum])

  const pctOfWeek = (w) => Math.min(100, Math.max(0, (w / TOTAL_WEEKS) * 100))

  return (
    <div className={styles.timelineWrap}>
      <div className={styles.timelineHeader}>
        <div className={styles.timelineTitle}>Linha do tempo · 0–40 semanas</div>
        <div className={styles.timelineLegend}>
          {['consulta', 'exame_lab', 'usg', 'vacina'].map(k => {
            const m = getKindMeta(k)
            return (
              <span key={k} className={styles.legendItem}>
                <span className={styles.legendDot} style={{ background: m.color }} />
                {m.label}
              </span>
            )
          })}
        </div>
      </div>

      <div className={styles.timelineBody}>
        {/* Trimester bands */}
        <div className={styles.trimesterBand} style={{ left: 0, width: `${pctOfWeek(T1_END)}%`, background: 'rgba(91,139,196,0.08)' }}>
          <span className={styles.trimesterLabel}>1º trimestre</span>
        </div>
        <div className={styles.trimesterBand} style={{ left: `${pctOfWeek(T1_END)}%`, width: `${pctOfWeek(T2_END) - pctOfWeek(T1_END)}%`, background: 'rgba(122,95,166,0.08)' }}>
          <span className={styles.trimesterLabel}>2º trimestre</span>
        </div>
        <div className={styles.trimesterBand} style={{ left: `${pctOfWeek(T2_END)}%`, width: `${pctOfWeek(40) - pctOfWeek(T2_END)}%`, background: 'rgba(196,126,58,0.08)' }}>
          <span className={styles.trimesterLabel}>3º trimestre</span>
        </div>

        {/* Week ruler */}
        <div className={styles.weekRuler}>
          {[4, 8, 12, 16, 20, 24, 28, 32, 36, 40].map(w => (
            <div key={w} className={styles.weekTick} style={{ left: `${pctOfWeek(w)}%` }}>
              <div className={styles.weekTickLine} />
              <div className={styles.weekTickLabel}>{w}</div>
            </div>
          ))}
        </div>

        {/* Current week marker */}
        {decimalWeeks != null && decimalWeeks > 0 && (
          <div className={styles.currentMarker} style={{ left: `${pctOfWeek(decimalWeeks)}%` }}>
            <div className={styles.currentMarkerLine} />
            <div className={styles.currentMarkerLabel}>
              {Math.floor(decimalWeeks)}s + {Math.floor((decimalWeeks - Math.floor(decimalWeeks)) * 7)}d
            </div>
          </div>
        )}

        {/* Checkpoint pins */}
        <div className={styles.checkpointTrack}>
          {CHECKPOINTS.map(cp => {
            const w = checkpointMidWeek(cp)
            const status = checkpointStatus(cp, decimalWeeks, completedIds)
            const meta = getKindMeta(cp.kind)
            return (
              <div
                key={cp.id}
                className={styles.checkpointPin}
                data-status={status}
                style={{ left: `${pctOfWeek(w)}%`, '--cp-color': meta.color }}
                onMouseEnter={() => setHovered(cp.id)}
                onMouseLeave={() => setHovered(null)}
              >
                <div className={styles.checkpointDot}>{status === 'completed' ? '✓' : meta.icon}</div>
                {hovered === cp.id && (
                  <div className={styles.checkpointTooltip}>
                    <div className={styles.tooltipTitle}>{cp.label}</div>
                    <div className={styles.tooltipMeta}>
                      {meta.label} · semana {Array.isArray(cp.week) ? (cp.week[1] != null ? `${cp.week[0]}-${cp.week[1]}` : `${cp.week[0]}+`) : cp.week}
                      {' · '}
                      <span data-status={status} className={styles.tooltipStatus}>
                        {status === 'completed' ? 'feito' : status === 'overdue' ? 'atrasado' : status === 'current' ? 'agora' : 'futuro'}
                      </span>
                    </div>
                    {cp.notes && <div className={styles.tooltipNotes}>{cp.notes}</div>}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
