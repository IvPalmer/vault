/**
 * PregnancyHero — arc gauge + DPP countdown center.
 *
 * Pattern 1.3 from research: 270° SVG arc showing IG/40w with current-week
 * pulse marker. Center displays IG (XwYd) + DPP date + days remaining.
 */
import { useMemo } from 'react'
import styles from './saude-widgets.module.css'
import { weeksFromDum, formatWeeks, computeDpp } from './checkpoints'

const SIZE = 220
const STROKE = 14
const CENTER = SIZE / 2
const RADIUS = (SIZE - STROKE) / 2 - 8
// 270° arc: starts at 135° (bottom-left), ends at 405° (45°, bottom-right)
const ARC_START = 135 * (Math.PI / 180)
const ARC_END = 405 * (Math.PI / 180)
const ARC_TOTAL_RAD = ARC_END - ARC_START

function polar(angleRad, r = RADIUS) {
  return [CENTER + r * Math.cos(angleRad), CENTER + r * Math.sin(angleRad)]
}

function arcPath(startRad, endRad, r = RADIUS) {
  const [sx, sy] = polar(startRad, r)
  const [ex, ey] = polar(endRad, r)
  const large = endRad - startRad > Math.PI ? 1 : 0
  return `M ${sx} ${sy} A ${r} ${r} 0 ${large} 1 ${ex} ${ey}`
}

export default function PregnancyHero({ pregnancy }) {
  const { decimalWeeks, dpp, daysToDpp, progressPct } = useMemo(() => {
    const dum = pregnancy?.dum
    const w = weeksFromDum(dum)
    const dppDate = pregnancy?.dpp ? new Date(pregnancy.dpp) : computeDpp(dum)
    const days = dppDate ? Math.ceil((dppDate - new Date()) / (1000 * 60 * 60 * 24)) : null
    const pct = w != null ? Math.min(1, Math.max(0, w / 40)) : 0
    return { decimalWeeks: w, dpp: dppDate, daysToDpp: days, progressPct: pct }
  }, [pregnancy?.dum, pregnancy?.dpp])

  const progressRad = ARC_START + ARC_TOTAL_RAD * progressPct
  const [markerX, markerY] = polar(progressRad)

  // Trimester boundary angles
  const t1End = ARC_START + ARC_TOTAL_RAD * (13 / 40)
  const t2End = ARC_START + ARC_TOTAL_RAD * (27 / 40)

  return (
    <div className={styles.hero}>
      <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`} className={styles.heroSvg}>
        {/* Background track */}
        <path
          d={arcPath(ARC_START, ARC_END)}
          stroke="rgba(0,0,0,0.06)"
          strokeWidth={STROKE}
          fill="none"
          strokeLinecap="round"
        />
        {/* Trimester segments (subtle) */}
        <path d={arcPath(ARC_START, t1End)} stroke="rgba(91,139,196,0.18)" strokeWidth={STROKE} fill="none" strokeLinecap="round" />
        <path d={arcPath(t1End, t2End)} stroke="rgba(122,95,166,0.18)" strokeWidth={STROKE} fill="none" strokeLinecap="round" />
        <path d={arcPath(t2End, ARC_END)} stroke="rgba(196,126,58,0.18)" strokeWidth={STROKE} fill="none" strokeLinecap="round" />

        {/* Progress arc */}
        {decimalWeeks != null && (
          <path
            d={arcPath(ARC_START, progressRad)}
            stroke="var(--accent, #c47e3a)"
            strokeWidth={STROKE}
            fill="none"
            strokeLinecap="round"
          />
        )}

        {/* Trimester tick marks */}
        {[t1End, t2End].map((a, i) => {
          const [x1, y1] = polar(a, RADIUS - STROKE / 2 - 2)
          const [x2, y2] = polar(a, RADIUS + STROKE / 2 + 2)
          return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="rgba(0,0,0,0.3)" strokeWidth={1} />
        })}

        {/* Current week pulse marker */}
        {decimalWeeks != null && (
          <>
            <circle cx={markerX} cy={markerY} r={STROKE / 2 + 6} fill="var(--accent, #c47e3a)" opacity={0.25}>
              <animate attributeName="r" values={`${STROKE/2 + 4};${STROKE/2 + 14};${STROKE/2 + 4}`} dur="1.8s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.4;0;0.4" dur="1.8s" repeatCount="indefinite" />
            </circle>
            <circle cx={markerX} cy={markerY} r={STROKE / 2 + 2} fill="var(--accent, #c47e3a)" stroke="#fff" strokeWidth={3} />
          </>
        )}

        {/* Trimester labels — positioned outside the arc to avoid overlap with center IG */}
        <text x={CENTER - 80} y={SIZE - 4} fontSize="9" fontWeight="600" fill="rgba(91,139,196,0.7)" textAnchor="middle" letterSpacing="0.06em">T1</text>
        <text x={CENTER + 80} y={SIZE - 4} fontSize="9" fontWeight="600" fill="rgba(196,126,58,0.8)" textAnchor="middle" letterSpacing="0.06em">T3</text>
        <text x={CENTER} y={SIZE - 4} fontSize="9" fontWeight="600" fill="rgba(122,95,166,0.7)" textAnchor="middle" letterSpacing="0.06em">T2</text>
      </svg>

      {/* Center content (absolutely positioned) */}
      <div className={styles.heroCenter}>
        <div className={styles.heroIg}>{formatWeeks(decimalWeeks)}</div>
        <div className={styles.heroIgLabel}>idade gestacional</div>
        {dpp && (
          <>
            <div className={styles.heroDpp}>
              {dpp.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })}
            </div>
            <div className={styles.heroDppLabel}>
              {daysToDpp > 0 ? `${daysToDpp} dias até DPP` : daysToDpp === 0 ? 'DPP hoje' : `${Math.abs(daysToDpp)} dias após DPP`}
            </div>
          </>
        )}
        {!dpp && <div className={styles.heroDppLabel}>DPP pendente — aguardando USG datação</div>}
      </div>
    </div>
  )
}
