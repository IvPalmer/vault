import styles from './MetricCard.module.css'

function MetricCard({ label, value, subtitle, color = 'var(--color-text)' }) {
  return (
    <div className={styles.card}>
      <div className={styles.value} style={{ color }}>{value}</div>
      <div className={styles.label}>{label}</div>
      {subtitle && <div className={styles.subtitle}>{subtitle}</div>}
    </div>
  )
}

export default MetricCard
