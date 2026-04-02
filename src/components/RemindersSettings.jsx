/**
 * RemindersSettings.jsx — Apple Reminders sidecar status + setup.
 *
 * Checks if the local sidecar is running (localhost:5177).
 * If running: shows available reminder lists.
 * If not: shows setup instructions with one-click install.
 */
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
  const { data, isLoading } = useQuery({
    queryKey: ['sidecar-status'],
    queryFn: checkSidecar,
    staleTime: 10000,
    refetchInterval: 15000,
  })

  const connected = data?.connected || false
  const lists = data?.lists || []

  const handleSetup = () => {
    // Open Terminal with the setup command
    const cmd = `curl -sL http://${window.location.hostname}:5175/sidecar-setup.sh | bash`
    // Copy to clipboard and show instructions
    navigator.clipboard.writeText(cmd).then(() => {
      alert(
        'Comando copiado! Cole no Terminal:\n\n' + cmd + '\n\n' +
        'Isso vai instalar e iniciar o sidecar de Lembretes automaticamente.'
      )
    }).catch(() => {
      prompt('Copie e cole no Terminal:', cmd)
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
                color: 'var(--color-green, #34C759)',
                fontWeight: 600,
              }}>
                localhost:{5177}
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
            <p style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', margin: '0 0 1rem' }}>
              O sidecar conecta seus Lembretes do Apple ao Vault.
              Cada Mac precisa rodar seu proprio sidecar para ver seus lembretes pessoais.
            </p>
            <button
              className={styles.btnConnect}
              onClick={handleSetup}
              style={{ borderStyle: 'solid' }}
            >
              Configurar Lembretes neste Mac
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
