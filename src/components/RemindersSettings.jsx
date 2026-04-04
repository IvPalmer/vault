/**
 * RemindersSettings.jsx — Apple Reminders sidecar status + setup.
 *
 * Checks if the local sidecar is running (localhost:5177).
 * If running: shows available reminder lists.
 * If not: shows setup script with copy button.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import styles from './CalendarSettings.module.css'

const SIDECAR_URL = 'http://localhost:5177'

async function checkSidecar() {
  try {
    const res = await fetch(`${SIDECAR_URL}/api/home/reminders/lists/?all=true`, {
      signal: AbortSignal.timeout(3000),
    })
    if (!res.ok) return { connected: false }
    const data = await res.json()
    return { connected: true, lists: data.lists || [] }
  } catch {
    return { connected: false }
  }
}

export default function RemindersSettings() {
  const [copied, setCopied] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['sidecar-status'],
    queryFn: checkSidecar,
    staleTime: 10000,
    refetchInterval: 15000,
  })

  const connected = data?.connected || false
  const lists = data?.lists || []

  const setupCmd = `curl -fsSL ${window.location.origin}/reminders-setup.sh | bash`

  const handleCopy = () => {
    navigator.clipboard.writeText(setupCmd).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 3000)
    }).catch(() => {
      window.prompt('Copie o comando:', setupCmd)
    })
  }

  return (
    <div className={styles.section}>
      <h2 className={styles.title}>Lembretes (Apple)</h2>

      {isLoading && <p className={styles.muted}>Verificando conexao...</p>}

      {!isLoading && connected && (
        <div className={styles.accountCard}>
          <div className={styles.accountHeader}>
            <div className={styles.accountInfo}>
              <span className={styles.accountEmail}>Sidecar conectado</span>
              <span style={{
                fontSize: '0.7rem',
                color: '#34C759',
                fontWeight: 600,
              }}>
                localhost:5177
              </span>
            </div>
          </div>
          <div className={styles.calendarList}>
            {lists.map((name) => (
              <div key={name} className={styles.calendarRow}>
                <div className={styles.calendarDot} style={{ backgroundColor: 'var(--color-accent)' }} />
                <span className={styles.calendarName}>{name}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {!isLoading && !connected && (
        <div className={styles.accountCard}>
          <div style={{ padding: '0.5rem 0' }}>
            <p style={{ fontSize: '0.85rem', color: 'var(--color-text)', margin: '0 0 0.5rem' }}>
              O sidecar de Lembretes nao esta rodando neste Mac.
            </p>
            <p style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', margin: '0 0 0.75rem' }}>
              Cada Mac precisa rodar seu proprio sidecar para conectar seus Lembretes do Apple ao Vault.
              Abra o Terminal e execute o comando abaixo:
            </p>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: 'var(--color-bg)',
              border: '1px solid var(--color-border)',
              borderRadius: '6px',
              padding: '10px 12px',
              marginBottom: '8px',
            }}>
              <code style={{
                flex: 1,
                fontSize: '0.72rem',
                fontFamily: "'SF Mono', 'Fira Code', monospace",
                color: 'var(--color-text)',
                wordBreak: 'break-all',
              }}>
                {setupCmd}
              </code>
              <button
                onClick={handleCopy}
                className={styles.btnSmall}
                style={{ flexShrink: 0, minWidth: '70px' }}
              >
                {copied ? 'Copiado!' : 'Copiar'}
              </button>
            </div>
            <p style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)', margin: 0 }}>
              O script baixa, compila e inicia o sidecar automaticamente.
              Apos rodar, atualize esta pagina.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
