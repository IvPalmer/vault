import { useState, useRef, useEffect } from 'react'
import styles from './MetricCard.module.css'

function MetricCard({ label, value, subtitle, color = 'var(--color-text)', tooltip, progress }) {
  const [showTip, setShowTip] = useState(false)
  const tipRef = useRef(null)
  const btnRef = useRef(null)

  // Close tooltip on click outside
  useEffect(() => {
    if (!showTip) return
    function handleClick(e) {
      if (tipRef.current && !tipRef.current.contains(e.target) &&
          btnRef.current && !btnRef.current.contains(e.target)) {
        setShowTip(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [showTip])

  return (
    <div className={styles.card}>
      {tooltip && (
        <button
          ref={btnRef}
          className={styles.infoBtn}
          onClick={(e) => { e.stopPropagation(); setShowTip(!showTip) }}
          title="O que significa?"
        >
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="8" cy="8" r="7" />
            <path d="M6.5 6.5a1.5 1.5 0 1 1 2.12 1.38c-.44.26-.62.6-.62 1.12" strokeLinecap="round" />
            <circle cx="8" cy="11.5" r="0.5" fill="currentColor" stroke="none" />
          </svg>
        </button>
      )}
      {showTip && tooltip && (
        <div ref={tipRef} className={styles.tooltip}>
          {tooltip}
        </div>
      )}
      <div className={styles.value} style={{ color }}>{value}</div>
      <div className={styles.label}>{label}</div>
      {subtitle && <div className={styles.subtitle}>{subtitle}</div>}
      {progress != null && (
        <div className={styles.progressBar}>
          <div
            className={styles.progressFill}
            style={{
              width: `${Math.min(progress, 100)}%`,
              background: progress > 100 ? 'var(--color-red)' : color,
            }}
          />
        </div>
      )}
    </div>
  )
}

export default MetricCard
