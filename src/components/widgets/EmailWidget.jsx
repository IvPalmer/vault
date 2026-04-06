import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../../api/client'
import { WidgetSettingsPanel, SettingsGearButton, SettingsField, settingsStyles as ss } from './WidgetSettingsPanel'

const DEFAULT_CONFIG = { account_email: '', query: 'is:unread', maxItems: 10 }

const QUERY_OPTIONS = [
  { label: 'Nao lidas', value: 'is:unread' },
  { label: 'Todas', value: '' },
  { label: 'Importantes', value: 'is:important' },
]

function extractSender(from) {
  if (!from) return ''
  const match = from.match(/^"?([^"<]+)"?\s*</)
  return match ? match[1].trim() : from.replace(/<.*>/, '').trim() || from
}

function timeAgo(dateStr) {
  const d = new Date(dateStr)
  const now = new Date()
  const mins = Math.floor((now - d) / 60000)
  if (mins < 1) return 'agora'
  if (mins < 60) return `${mins}min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h`
  const days = Math.floor(hrs / 24)
  if (days < 7) return `${days}d`
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
}

const s = {
  wrap: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    background: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    boxShadow: 'var(--shadow-sm)',
    overflow: 'hidden',
    position: 'relative',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '8px 30px 8px 12px',
    borderBottom: '1px solid var(--color-border)',
    minHeight: 36,
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    fontSize: '0.78rem',
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    color: 'var(--color-text-secondary)',
  },
  badge: {
    background: 'var(--color-accent, #3b82f6)',
    color: '#fff',
    fontSize: '0.68rem',
    fontWeight: 700,
    borderRadius: 10,
    padding: '1px 6px',
    lineHeight: '1.3',
  },
  list: {
    flex: 1,
    overflow: 'auto',
    minHeight: 0,
  },
  row: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: 8,
    padding: '7px 12px',
    borderBottom: '1px solid var(--color-border)',
    cursor: 'pointer',
    textDecoration: 'none',
    color: 'inherit',
    transition: 'background 0.1s',
  },
  unreadDot: {
    width: 7,
    height: 7,
    borderRadius: '50%',
    background: 'var(--color-accent, #3b82f6)',
    flexShrink: 0,
    marginTop: 5,
  },
  readDot: {
    width: 7,
    height: 7,
    borderRadius: '50%',
    background: 'transparent',
    flexShrink: 0,
    marginTop: 5,
  },
  content: {
    flex: 1,
    minWidth: 0,
  },
  sender: {
    fontSize: '0.8rem',
    fontWeight: 600,
    color: 'var(--color-text)',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  subject: {
    fontSize: '0.76rem',
    color: 'var(--color-text-secondary)',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    lineHeight: 1.3,
  },
  time: {
    fontSize: '0.68rem',
    color: 'var(--color-text-secondary)',
    flexShrink: 0,
    marginTop: 2,
    opacity: 0.7,
  },
  empty: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    color: 'var(--color-text-secondary)',
    fontSize: '0.82rem',
    fontStyle: 'italic',
    padding: 20,
    textAlign: 'center',
  },
}

export default function EmailWidget({ config, onConfigChange }) {
  const cfg = { ...DEFAULT_CONFIG, ...config }
  const [settingsOpen, setSettingsOpen] = useState(false)

  const { data: accountsData } = useQuery({
    queryKey: ['google-accounts'],
    queryFn: () => api.get('/google/accounts/'),
    staleTime: 300000,
  })
  const accounts = accountsData?.accounts || []

  const activeEmail = cfg.account_email || accounts[0]?.email || ''

  const { data, isLoading } = useQuery({
    queryKey: ['gmail-messages', activeEmail, cfg.query, cfg.maxItems],
    queryFn: () => {
      const params = new URLSearchParams()
      if (cfg.query) params.set('q', cfg.query)
      params.set('limit', String(cfg.maxItems))
      if (activeEmail) params.set('account_email', activeEmail)
      return api.get(`/google/gmail/messages/?${params}`)
    },
    staleTime: 60000,
    enabled: !!activeEmail,
  })

  const messages = data?.messages || []
  const unreadCount = messages.filter((m) => m.is_unread).length

  const update = (patch) => onConfigChange({ ...cfg, ...patch })

  return (
    <div style={s.wrap}>
      <div style={s.header}>
        <div style={s.headerLeft}>
          <span>Emails</span>
          {unreadCount > 0 && <span style={s.badge}>{unreadCount}</span>}
        </div>
        <SettingsGearButton onClick={() => setSettingsOpen(true)} />
      </div>

      <WidgetSettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)}>
        {accounts.length > 1 && (
          <SettingsField label="Conta">
            <select
              style={ss.select}
              value={cfg.account_email}
              onChange={(e) => update({ account_email: e.target.value })}
            >
              <option value="">Auto</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.email}>{a.email}</option>
              ))}
            </select>
          </SettingsField>
        )}
        <SettingsField label="Filtro">
          <select
            style={ss.select}
            value={QUERY_OPTIONS.find((o) => o.value === cfg.query) ? cfg.query : '__custom'}
            onChange={(e) => {
              if (e.target.value !== '__custom') update({ query: e.target.value })
            }}
          >
            {QUERY_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
            {!QUERY_OPTIONS.find((o) => o.value === cfg.query) && (
              <option value="__custom">Personalizado</option>
            )}
          </select>
        </SettingsField>
        <SettingsField label="Max itens">
          <select
            style={ss.select}
            value={cfg.maxItems}
            onChange={(e) => update({ maxItems: Number(e.target.value) })}
          >
            {[5, 10, 15].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </SettingsField>
      </WidgetSettingsPanel>

      <div style={s.list}>
        {!activeEmail ? (
          <div style={s.empty}>Nenhuma conta Google conectada</div>
        ) : isLoading ? (
          <div style={s.empty}>Carregando...</div>
        ) : messages.length === 0 ? (
          <div style={s.empty}>Nenhum email encontrado</div>
        ) : (
          messages.map((msg) => (
            <a
              key={msg.id}
              href={`https://mail.google.com/mail/u/0/#inbox/${msg.id}`}
              target="_blank"
              rel="noopener noreferrer"
              style={s.row}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-bg)' }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent' }}
            >
              <div style={msg.is_unread ? s.unreadDot : s.readDot} />
              <div style={s.content}>
                <div style={s.sender}>{extractSender(msg.from)}</div>
                <div style={s.subject}>{msg.subject || '(sem assunto)'}</div>
              </div>
              <span style={s.time}>{timeAgo(msg.date)}</span>
            </a>
          ))
        )}
      </div>
    </div>
  )
}
