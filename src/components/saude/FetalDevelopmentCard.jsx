/**
 * FetalDevelopmentCard — illustration of the fetus at the current week,
 * size comparison, and weekly developmental milestones + expected symptoms.
 */
import { useMemo } from 'react'
import styles from './saude-widgets.module.css'
import { weeksFromDum, formatWeeks } from './checkpoints'
import { fetalDataForWeek, symptomsForWeek } from './fetalWeeks'
import FetalIllustration from './FetalIllustration'

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
