import { useState, useEffect } from 'react'
import { WidgetSettingsPanel, SettingsGearButton, SettingsField, settingsStyles as ss } from './WidgetSettingsPanel'

const s = {
  wrap: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    boxShadow: 'var(--shadow-sm)',
    gap: 4,
    position: 'relative',
  },
  time: {
    fontSize: '2rem',
    fontWeight: 800,
    color: 'var(--color-text)',
    lineHeight: 1,
    fontVariantNumeric: 'tabular-nums',
  },
  date: {
    fontSize: '0.72rem',
    fontWeight: 600,
    color: 'var(--color-text-secondary)',
    textTransform: 'capitalize',
  },
  gear: {
    position: 'absolute',
    top: 4,
    right: 28,
  },
}

export default function ClockWidget({ config, onConfigChange }) {
  const [now, setNow] = useState(new Date())
  const [settingsOpen, setSettingsOpen] = useState(false)
  const showSeconds = config?.showSeconds || false
  const hour12 = config?.hour12 || false
  const showDate = config?.showDate !== false

  useEffect(() => {
    const interval = showSeconds ? 1000 : 60000
    const id = setInterval(() => setNow(new Date()), interval)
    return () => clearInterval(id)
  }, [showSeconds])

  const update = (patch) => onConfigChange?.({ ...config, ...patch })

  const time = now.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
    ...(showSeconds && { second: '2-digit' }),
    hour12,
  })
  const date = now.toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })

  return (
    <div style={s.wrap}>
      {onConfigChange && (
        <div style={s.gear}>
          <SettingsGearButton onClick={() => setSettingsOpen(true)} />
        </div>
      )}

      <WidgetSettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)}>
        <SettingsField label="Formato">
          <select style={ss.select} value={hour12 ? '12' : '24'} onChange={(e) => update({ hour12: e.target.value === '12' })}>
            <option value="24">24 horas</option>
            <option value="12">12 horas (AM/PM)</option>
          </select>
        </SettingsField>
        <SettingsField label="Segundos">
          <select style={ss.select} value={showSeconds ? 'yes' : 'no'} onChange={(e) => update({ showSeconds: e.target.value === 'yes' })}>
            <option value="no">Ocultar</option>
            <option value="yes">Mostrar</option>
          </select>
        </SettingsField>
        <SettingsField label="Data">
          <select style={ss.select} value={showDate ? 'yes' : 'no'} onChange={(e) => update({ showDate: e.target.value === 'yes' })}>
            <option value="yes">Mostrar</option>
            <option value="no">Ocultar</option>
          </select>
        </SettingsField>
      </WidgetSettingsPanel>

      <span style={s.time}>{time}</span>
      {showDate && <span style={s.date}>{date}</span>}
    </div>
  )
}
