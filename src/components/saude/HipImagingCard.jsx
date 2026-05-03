/**
 * HipImagingCard — bilateral hip measurements (Palmer's CT 2025-09-12).
 * Side-by-side comparison left vs right with status indicators.
 */
import styles from './saude-widgets.module.css'
import { PALMER_HIP_IMAGING } from './palmerHealthData'

const STATUS_COLOR = {
  alto: '#b43c3c',
  baixo: '#5b8bc4',
  normal: '#468c5a',
}

export default function HipImagingCard() {
  const data = PALMER_HIP_IMAGING
  const dataFmt = data.data.split('-').reverse().join('/')

  return (
    <div className={styles.hipCard}>
      <div className={styles.widgetLabel}>{data.modalidade} · {dataFmt}</div>
      <div className={styles.hipFinding}>{data.achado_principal}</div>

      <div className={styles.hipTable}>
        <div className={styles.hipTableHeader}>
          <span></span>
          <span>Esquerdo</span>
          <span>Direito</span>
          <span>Referência</span>
        </div>
        {data.measurements.map((m, i) => (
          <div key={i} className={styles.hipRow}>
            <div className={styles.hipCategoryName}>{m.categoria}</div>
            <div className={styles.hipValueCell}>
              {m.esquerdo != null ? (
                <>
                  <span className={styles.hipValue} style={{ color: STATUS_COLOR[m.esquerdo_status] || '#2a2724' }}>
                    {m.esquerdo}{m.unit}
                  </span>
                </>
              ) : <span className={styles.hipDash}>—</span>}
            </div>
            <div className={styles.hipValueCell}>
              {m.direito != null ? (
                <span className={styles.hipValue} style={{ color: STATUS_COLOR[m.direito_status] || '#2a2724' }}>
                  {m.direito}{m.unit}
                </span>
              ) : <span className={styles.hipDash}>—</span>}
            </div>
            <div className={styles.hipRef}>{m.ref_text}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
