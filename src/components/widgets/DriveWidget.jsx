import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../../api/client'
import { WidgetSettingsPanel, SettingsGearButton, SettingsField, settingsStyles as ss } from './WidgetSettingsPanel'

const DEFAULT_CONFIG = { account_email: '', query: '', maxItems: 10, view: 'recent' }

const MIME_ICONS = {
  'application/vnd.google-apps.spreadsheet': { icon: '\u{1F4CA}', label: 'Planilha' },
  'application/vnd.google-apps.document':    { icon: '\u{1F4DD}', label: 'Documento' },
  'application/vnd.google-apps.presentation':{ icon: '\u{1F4CA}', label: 'Apresentacao' },
  'application/vnd.google-apps.folder':      { icon: '\u{1F4C1}', label: 'Pasta' },
  'application/pdf':                         { icon: '\u{1F4C4}', label: 'PDF' },
  'image/':                                  { icon: '\u{1F5BC}', label: 'Imagem' },
  'video/':                                  { icon: '\u{1F3AC}', label: 'Video' },
}

function getFileIcon(mimeType) {
  if (!mimeType) return '\u{1F4C4}'
  const exact = MIME_ICONS[mimeType]
  if (exact) return exact.icon
  for (const [prefix, val] of Object.entries(MIME_ICONS)) {
    if (mimeType.startsWith(prefix)) return val.icon
  }
  return '\u{1F4C4}'
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
  list: {
    flex: 1,
    overflow: 'auto',
    minHeight: 0,
  },
  row: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '7px 12px',
    borderBottom: '1px solid var(--color-border)',
    cursor: 'pointer',
    textDecoration: 'none',
    color: 'inherit',
    transition: 'background 0.1s',
  },
  icon: {
    fontSize: '1rem',
    flexShrink: 0,
    width: 22,
    textAlign: 'center',
  },
  content: {
    flex: 1,
    minWidth: 0,
  },
  fileName: {
    fontSize: '0.8rem',
    fontWeight: 500,
    color: 'var(--color-text)',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  owner: {
    fontSize: '0.7rem',
    color: 'var(--color-text-secondary)',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  time: {
    fontSize: '0.68rem',
    color: 'var(--color-text-secondary)',
    flexShrink: 0,
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

export default function DriveWidget({ config, onConfigChange }) {
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
    queryKey: ['drive-files', activeEmail, cfg.query, cfg.maxItems, cfg.view],
    queryFn: () => {
      const params = new URLSearchParams()
      if (cfg.query) params.set('name', cfg.query)
      params.set('limit', String(cfg.maxItems))
      if (activeEmail) params.set('account_email', activeEmail)
      return api.get(`/google/drive/files/?${params}`)
    },
    staleTime: 60000,
    enabled: !!activeEmail,
  })

  const files = data?.files || []

  const update = (patch) => onConfigChange({ ...cfg, ...patch })

  return (
    <div style={s.wrap}>
      <div style={s.header}>
        <div style={s.headerLeft}>
          <span>Arquivos</span>
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
        <SettingsField label="Buscar por nome">
          <input
            type="text"
            style={ss.input}
            value={cfg.query}
            onChange={(e) => update({ query: e.target.value })}
            placeholder="Filtrar arquivos..."
          />
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
        ) : files.length === 0 ? (
          <div style={s.empty}>Nenhum arquivo encontrado</div>
        ) : (
          files.map((file) => (
            <a
              key={file.id}
              href={file.url}
              target="_blank"
              rel="noopener noreferrer"
              style={s.row}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-bg)' }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent' }}
            >
              <span style={s.icon}>{getFileIcon(file.mime_type)}</span>
              <div style={s.content}>
                <div style={s.fileName}>{file.name}</div>
                {file.owner && <div style={s.owner}>{file.owner}</div>}
              </div>
              {file.modified && <span style={s.time}>{timeAgo(file.modified)}</span>}
            </a>
          ))
        )}
      </div>
    </div>
  )
}
