import styles from './Skeleton.module.css'

/**
 * Skeleton loading placeholder.
 * Props:
 *   variant: 'card' | 'row' | 'text' | 'chart'
 *   count: number of skeletons to render (default 1)
 *   height: custom height (e.g., '200px')
 */
function Skeleton({ variant = 'text', count = 1, height }) {
  const items = Array.from({ length: count }, (_, i) => i)

  if (variant === 'card') {
    return (
      <div className={styles.cardGrid}>
        {items.map(i => (
          <div key={i} className={styles.card}>
            <div className={`${styles.line} ${styles.lineShort}`} />
            <div className={`${styles.line} ${styles.lineMedium}`} />
            <div className={`${styles.line} ${styles.lineFull}`} />
          </div>
        ))}
      </div>
    )
  }

  if (variant === 'chart') {
    return (
      <div className={styles.chart} style={height ? { height } : undefined}>
        <div className={styles.shimmer} />
      </div>
    )
  }

  if (variant === 'row') {
    return (
      <div className={styles.rows}>
        {items.map(i => (
          <div key={i} className={styles.row}>
            <div className={`${styles.line} ${styles.lineFull}`} />
          </div>
        ))}
      </div>
    )
  }

  // Default: text lines
  return (
    <div className={styles.textBlock}>
      {items.map(i => (
        <div
          key={i}
          className={`${styles.line} ${i % 3 === 0 ? styles.lineShort : i % 3 === 1 ? styles.lineMedium : styles.lineFull}`}
        />
      ))}
    </div>
  )
}

export default Skeleton
