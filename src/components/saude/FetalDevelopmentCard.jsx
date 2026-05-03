/**
 * FetalDevelopmentCard — illustration of the fetus at the current week,
 * size comparison, and weekly developmental milestones + expected symptoms.
 */
import { useMemo } from 'react'
import styles from './saude-widgets.module.css'
import { weeksFromDum, formatWeeks } from './checkpoints'
import { fetalDataForWeek, symptomsForWeek } from './fetalWeeks'

/**
 * Stylized SVG fetus that scales with gestational week. The outline grows
 * from a small dot at week 4 to a curled-up infant by week 40.
 */
function FetalIllustration({ week }) {
  // Scale from 0.3 (early) to 1 (term)
  const scale = Math.min(1, Math.max(0.25, (week - 4) / 36))
  // Curl factor — earlier weeks more "curled"; later weeks more elongated
  const isEmbryo = week < 10

  return (
    <svg viewBox="0 0 240 200" className={styles.fetalSvg} aria-label={`Feto em ${week} semanas`}>
      <defs>
        <radialGradient id="amnioGrad" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="rgba(196,126,58,0.05)" />
          <stop offset="100%" stopColor="rgba(196,126,58,0.18)" />
        </radialGradient>
        <linearGradient id="fetusGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#e8b48a" />
          <stop offset="100%" stopColor="#c47e3a" />
        </linearGradient>
      </defs>

      {/* Amniotic sac */}
      <ellipse cx="120" cy="100" rx="105" ry="88" fill="url(#amnioGrad)" stroke="rgba(196,126,58,0.3)" strokeWidth="1" strokeDasharray="3 4" />

      {/* Umbilical cord */}
      <path d="M 120 12 Q 100 50, 110 80 T 115 110" stroke="rgba(180, 90, 40, 0.4)" strokeWidth="2" fill="none" strokeLinecap="round" />

      {/* Fetus */}
      <g transform={`translate(120, 105) scale(${scale}) translate(-120, -105)`}>
        {isEmbryo ? (
          // Embryo: comma-shaped curl
          <path
            d="M 95 95 Q 80 70, 110 65 Q 145 60, 145 95 Q 145 125, 125 130 Q 105 132, 95 115 Z"
            fill="url(#fetusGrad)"
            stroke="rgba(120, 60, 20, 0.5)"
            strokeWidth="1.5"
          />
        ) : (
          // Fetus: head + body + curled limbs
          <>
            {/* Head */}
            <ellipse cx="118" cy="78" rx="32" ry="34" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.5)" strokeWidth="1.5" />
            {/* Body (curled) */}
            <path
              d="M 100 100 Q 80 130, 105 152 Q 130 165, 145 145 Q 155 125, 142 105 Z"
              fill="url(#fetusGrad)"
              stroke="rgba(120, 60, 20, 0.5)"
              strokeWidth="1.5"
            />
            {/* Arm hint */}
            <path d="M 100 110 Q 90 122, 100 138" stroke="rgba(120, 60, 20, 0.5)" strokeWidth="1.5" fill="none" strokeLinecap="round" />
            {/* Leg hint (curled) */}
            <path d="M 130 155 Q 115 170, 100 158" stroke="rgba(120, 60, 20, 0.5)" strokeWidth="1.5" fill="none" strokeLinecap="round" />
            {/* Eye hint (visible after ~16w) */}
            {week >= 16 && <circle cx="108" cy="76" r="2" fill="rgba(60, 30, 10, 0.7)" />}
          </>
        )}
      </g>
    </svg>
  )
}

export default function FetalDevelopmentCard({ pregnancy }) {
  const decimalWeeks = useMemo(() => weeksFromDum(pregnancy?.dum), [pregnancy?.dum])
  const data = useMemo(() => fetalDataForWeek(decimalWeeks), [decimalWeeks])
  const symptoms = useMemo(() => symptomsForWeek(decimalWeeks), [decimalWeeks])

  if (!data) {
    return (
      <div className={styles.fetalCard}>
        <div className={styles.widgetLabel}>Desenvolvimento do bebê</div>
        <div className={styles.fetalEmpty}>Aguardando DUM para mostrar evolução.</div>
      </div>
    )
  }

  return (
    <div className={styles.fetalCard}>
      <div className={styles.fetalHeader}>
        <div className={styles.widgetLabel}>Desenvolvimento · {formatWeeks(decimalWeeks)}</div>
        <div className={styles.fetalCompareEmoji}>{data.emoji}</div>
      </div>

      <div className={styles.fetalIllustrationWrap}>
        <FetalIllustration week={data.week} />
      </div>

      <div className={styles.fetalCompareTitle}>do tamanho de um(a) <strong>{data.compare}</strong></div>
      <div className={styles.fetalSizeRow}>
        <div className={styles.fetalSizeBlock}>
          <div className={styles.fetalSizeNum}>{data.size_cm} <span>cm</span></div>
          <div className={styles.fetalSizeLabel}>cabeça-pés</div>
        </div>
        <div className={styles.fetalSizeBlock}>
          <div className={styles.fetalSizeNum}>{data.weight_g >= 1000 ? `${(data.weight_g / 1000).toFixed(2)} kg` : `${data.weight_g} g`}</div>
          <div className={styles.fetalSizeLabel}>peso aprox</div>
        </div>
      </div>

      <div className={styles.fetalMilestoneTitle}>Esta semana</div>
      <div className={styles.fetalMilestoneText}>{data.milestones}</div>

      {symptoms.length > 0 && (
        <>
          <div className={styles.fetalMilestoneTitle}>Sintomas comuns nesta fase</div>
          <ul className={styles.fetalSymptoms}>
            {symptoms.map((s, i) => <li key={i}>{s}</li>)}
          </ul>
        </>
      )}
    </div>
  )
}
