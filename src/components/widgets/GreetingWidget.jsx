import { useProfile } from '../../context/ProfileContext'

const s = {
  wrap: {
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    padding: '0 20px',
    background: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    boxShadow: 'var(--shadow-sm)',
    gap: 12,
  },
  greeting: {
    fontSize: '1.1rem',
    fontWeight: 700,
    color: 'var(--color-text)',
  },
  date: {
    fontSize: '0.78rem',
    color: 'var(--color-text-secondary)',
    marginLeft: 'auto',
  },
}

function getGreeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Bom dia'
  if (h < 18) return 'Boa tarde'
  return 'Boa noite'
}

export default function GreetingWidget() {
  const { currentProfile } = useProfile()
  const name = currentProfile?.name || ''
  const date = new Date().toLocaleDateString('pt-BR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })

  return (
    <div style={s.wrap}>
      <span style={s.greeting}>{getGreeting()}, {name}</span>
      <span style={s.date}>{date}</span>
    </div>
  )
}
