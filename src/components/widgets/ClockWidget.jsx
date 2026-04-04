import { useState, useEffect } from 'react'

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
}

export default function ClockWidget() {
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 60000)
    return () => clearInterval(id)
  }, [])

  const time = now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  const date = now.toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })

  return (
    <div style={s.wrap}>
      <span style={s.time}>{time}</span>
      <span style={s.date}>{date}</span>
    </div>
  )
}
