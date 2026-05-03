/**
 * ClinicalReportCard — 5-layer diagnostic model with findings per layer.
 * Shows the clinical reasoning for the chronic hip pain investigation.
 */
import styles from './saude-widgets.module.css'

export default function ClinicalReportCard({ report, observations }) {
  if (!report) return null
  const dataFmt = report.data.split('-').reverse().join('/')

  return (
    <div className={styles.clinicalCard}>
      <div className={styles.widgetLabel}>Relatório clínico · {report.modelo} · {dataFmt}</div>

      <div className={styles.layersGrid}>
        {report.camadas.map(camada => (
          <div key={camada.id} className={styles.layerCard} style={{ '--layer-color': camada.cor }}>
            <div className={styles.layerHeader}>
              <span className={styles.layerTitle}>{camada.titulo}</span>
            </div>
            <ul className={styles.layerFindings}>
              {camada.achados.map((a, i) => <li key={i}>{a}</li>)}
            </ul>
          </div>
        ))}
      </div>

      {observations && observations.length > 0 && (
      <div className={styles.observationsBlock}>
        <h3 className={styles.observationsTitle}>Pontos de observação</h3>
        <div className={styles.observationsGrid}>
          {observations.map((o, i) => (
            <div key={i} className={styles.observationCard} data-priority={o.prioridade}>
              <div className={styles.observationHeader}>
                <span className={styles.observationTitle}>{o.titulo}</span>
                <span className={styles.observationPriority} data-priority={o.prioridade}>
                  {o.prioridade}
                </span>
              </div>
              <div className={styles.observationText}>{o.texto}</div>
            </div>
          ))}
        </div>
      </div>
      )}
    </div>
  )
}
