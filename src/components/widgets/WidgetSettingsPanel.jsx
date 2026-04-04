import { useRef, useEffect } from 'react'

const s = {
  overlay: {
    position: 'absolute',
    inset: 0,
    zIndex: 20,
    background: 'rgba(0,0,0,0.18)',
    borderRadius: 'var(--radius-md)',
    display: 'flex',
    justifyContent: 'flex-end',
    alignItems: 'flex-start',
    padding: 8,
  },
  panel: {
    background: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    boxShadow: 'var(--shadow-lg, 0 8px 24px rgba(0,0,0,0.15))',
    padding: '12px 14px',
    minWidth: 200,
    maxWidth: 280,
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
    fontSize: '0.82rem',
    color: 'var(--color-text)',
  },
  label: {
    display: 'block',
    fontSize: '0.72rem',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    color: 'var(--color-text-secondary)',
    marginBottom: 3,
  },
  select: {
    width: '100%',
    padding: '5px 8px',
    fontSize: '0.82rem',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-sm, 4px)',
    background: 'var(--color-bg)',
    color: 'var(--color-text)',
    outline: 'none',
  },
  input: {
    width: '100%',
    padding: '5px 8px',
    fontSize: '0.82rem',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-sm, 4px)',
    background: 'var(--color-bg)',
    color: 'var(--color-text)',
    outline: 'none',
    boxSizing: 'border-box',
  },
  gearBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: 2,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'var(--color-text-secondary)',
    opacity: 0.6,
    transition: 'opacity 0.15s',
    borderRadius: 4,
  },
}

export function WidgetSettingsPanel({ open, onClose, children }) {
  const panelRef = useRef(null)

  useEffect(() => {
    if (!open) return
    const handler = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open) return null

  return (
    <div style={s.overlay} onClick={onClose}>
      <div ref={panelRef} style={s.panel} onClick={(e) => e.stopPropagation()}>
        {children}
      </div>
    </div>
  )
}

export function SettingsGearButton({ onClick }) {
  return (
    <button
      onClick={(e) => { e.stopPropagation(); onClick() }}
      style={s.gearBtn}
      title="Configuracoes"
      onMouseEnter={(e) => { e.currentTarget.style.opacity = '1' }}
      onMouseLeave={(e) => { e.currentTarget.style.opacity = '0.6' }}
    >
      <svg width="15" height="15" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="10" cy="10" r="3" />
        <path d="M10 1.5v2M10 16.5v2M3.4 3.4l1.4 1.4M15.2 15.2l1.4 1.4M1.5 10h2M16.5 10h2M3.4 16.6l1.4-1.4M15.2 4.8l1.4-1.4" />
      </svg>
    </button>
  )
}

export function SettingsField({ label, children }) {
  return (
    <div>
      <span style={s.label}>{label}</span>
      {children}
    </div>
  )
}

export { s as settingsStyles }
