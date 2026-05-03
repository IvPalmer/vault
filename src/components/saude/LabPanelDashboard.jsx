/**
 * LabPanelDashboard — comprehensive lab markers grouped by category.
 * Each marker shown as a card with value, unit, ref range, status color.
 */
import styles from './saude-widgets.module.css'
import { PALMER_LAB_PANEL } from './palmerHealthData'

const STATUS_COLORS = {
  normal:           { bg: 'rgba(70, 140, 90, 0.08)', border: 'rgba(70, 140, 90, 0.3)', dot: '#468c5a', label: 'normal' },
  alto:             { bg: 'rgba(180, 60, 60, 0.07)', border: 'rgba(180, 60, 60, 0.35)', dot: '#b43c3c', label: 'alto' },
  baixo:            { bg: 'rgba(91, 139, 196, 0.08)', border: 'rgba(91, 139, 196, 0.35)', dot: '#5b8bc4', label: 'baixo' },
  limite_superior:  { bg: 'rgba(196, 126, 58, 0.08)', border: 'rgba(196, 126, 58, 0.35)', dot: '#c47e3a', label: 'limite ↑' },
  limite_inferior:  { bg: 'rgba(196, 126, 58, 0.08)', border: 'rgba(196, 126, 58, 0.35)', dot: '#c47e3a', label: 'limite ↓' },
}

function fmtRef(m) {
  const min = m.ref_min
  const max = m.ref_max
  if (min != null && max != null) return `${min}–${max} ${m.unit}`
  if (max != null) return `< ${max} ${m.unit}`
  if (min != null) return `> ${min} ${m.unit}`
  return ''
}

function fmtValue(v, unit) {
  if (typeof v === 'number') {
    if (v >= 1000) return v.toLocaleString('pt-BR')
    if (Number.isInteger(v)) return String(v)
    return v.toFixed(2).replace('.', ',')
  }
  return String(v)
}

function MarkerCard({ marker }) {
  const status = STATUS_COLORS[marker.status] || STATUS_COLORS.normal
  return (
    <div
      className={styles.markerCard}
      style={{ background: status.bg, borderColor: status.border }}
    >
      <div className={styles.markerLabel}>{marker.label}</div>
      <div className={styles.markerValueRow}>
        <span className={styles.markerValue}>{fmtValue(marker.value, marker.unit)}</span>
        <span className={styles.markerUnit}>{marker.unit}</span>
      </div>
      <div className={styles.markerFooter}>
        <span className={styles.markerStatusDot} style={{ background: status.dot }} />
        <span className={styles.markerStatusLabel}>{status.label}</span>
        {fmtRef(marker) && <span className={styles.markerRef}>ref: {fmtRef(marker)}</span>}
      </div>
      {marker.obs && (
        <div className={styles.markerObs}>{marker.obs}</div>
      )}
    </div>
  )
}

export default function LabPanelDashboard() {
  const panel = PALMER_LAB_PANEL
  const dataFmt = panel.data_coleta.split('-').reverse().join('/')

  return (
    <div className={styles.labPanel}>
      <div className={styles.labHeader}>
        <div>
          <div className={styles.widgetLabel}>Painel laboratorial completo</div>
          <div className={styles.labMeta}>{panel.laboratorio} · {dataFmt} · {panel.contexto}</div>
        </div>
      </div>

      {panel.categorias.map(cat => (
        <div key={cat.id} className={styles.labCategory}>
          <h3 className={styles.labCategoryTitle}>{cat.nome}</h3>
          <div className={styles.markerGrid}>
            {cat.markers.map(m => <MarkerCard key={m.key} marker={m} />)}
          </div>
        </div>
      ))}
    </div>
  )
}
