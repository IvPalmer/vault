/**
 * MobilogramaWidget — kick counter for 3rd trimester (≥28w).
 *
 * Protocol (Cardiff Count-to-Ten, MS BR adopted):
 *   - 1x/dia, deitada em decúbito lateral esquerdo, pós-refeição
 *   - Contar até 10 movimentos; anotar tempo decorrido
 *   - Alerta: < 10 movimentos em 2 horas → procurar atendimento
 *
 * Records each session as a VitalReading {tipo:'mobilograma', valor:count, notes:'minutes:N'}
 */
import { useState, useEffect, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../../api/client'
import styles from './saude-widgets.module.css'
import { weeksFromDum } from './checkpoints'

const TARGET_KICKS = 10
const ALERT_MINUTES = 120

function fmtTime(elapsedMs) {
  const totalSec = Math.floor(elapsedMs / 1000)
  const m = Math.floor(totalSec / 60)
  const s = totalSec % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function fmtDate(iso) {
  if (!iso) return '—'
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

export default function MobilogramaWidget({ pregnancy, profileId }) {
  const queryClient = useQueryClient()
  const decimalWeeks = weeksFromDum(pregnancy?.dum)
  const isActive = decimalWeeks != null && decimalWeeks >= 28

  // Session state — persisted to localStorage so refreshing doesn't lose progress
  const STORAGE_KEY = `mobilograma:${pregnancy?.id || 'na'}`
  const [session, setSession] = useState(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      return raw ? JSON.parse(raw) : null
    } catch { return null }
  })
  const [, setTick] = useState(0)
  const tickRef = useRef(null)

  useEffect(() => {
    if (!session) return
    tickRef.current = setInterval(() => setTick(t => t + 1), 1000)
    return () => clearInterval(tickRef.current)
  }, [session])

  useEffect(() => {
    if (session) localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
    else localStorage.removeItem(STORAGE_KEY)
  }, [session, STORAGE_KEY])

  const { data: history = [] } = useQuery({
    queryKey: ['mobilograma', profileId],
    queryFn: () => api.get(`/saude/vitals/?profile_id=${profileId}&tipo=mobilograma`),
    enabled: !!profileId,
  })

  const saveMutation = useMutation({
    mutationFn: (payload) => api.post(`/saude/vitals/?profile_id=${profileId}`, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['mobilograma', profileId] }),
  })

  const start = () => setSession({ startedAt: Date.now(), kicks: 0 })
  const tap = () => setSession(s => s ? { ...s, kicks: Math.min(s.kicks + 1, 999) } : s)
  const reset = () => setSession(null)

  const finish = () => {
    if (!session) return
    const elapsedMin = Math.round((Date.now() - session.startedAt) / 60000)
    saveMutation.mutate({
      tipo: 'mobilograma',
      data: new Date().toISOString().slice(0, 10),
      valor: session.kicks,
      notes: `${elapsedMin} min`,
      pregnancy: pregnancy?.id || null,
    })
    setSession(null)
  }

  if (!isActive) {
    return (
      <div className={styles.mobiloEmpty}>
        <div className={styles.widgetLabel}>Mobilograma</div>
        <div className={styles.mobiloEmptyText}>
          Ativa a partir da semana 28. {decimalWeeks != null && `Hoje: ${Math.floor(decimalWeeks)}s.`}
        </div>
      </div>
    )
  }

  const elapsed = session ? Date.now() - session.startedAt : 0
  const elapsedMin = elapsed / 60000
  const progress = session ? (session.kicks / TARGET_KICKS) * 100 : 0
  const overTime = elapsedMin > ALERT_MINUTES && session && session.kicks < TARGET_KICKS

  return (
    <div className={styles.mobiloWidget}>
      <div className={styles.widgetLabel}>
        <span>Mobilograma</span>
        <span className={styles.mobiloHelp}>Meta: 10 mov em até 2h</span>
      </div>

      {!session ? (
        <button className={styles.mobiloStart} onClick={start}>
          Iniciar contagem
        </button>
      ) : (
        <>
          <div className={styles.mobiloMain}>
            <div className={styles.mobiloKicks}>
              <span className={styles.mobiloKicksNum}>{session.kicks}</span>
              <span className={styles.mobiloKicksOf}>/ {TARGET_KICKS}</span>
            </div>
            <div className={styles.mobiloTime}>
              <span>{fmtTime(elapsed)}</span>
              <span className={styles.mobiloTimeLabel}>tempo</span>
            </div>
          </div>

          <div className={styles.mobiloProgress}>
            <div className={styles.mobiloProgressFill} style={{ width: `${Math.min(100, progress)}%` }} />
          </div>

          {overTime && (
            <div className={styles.mobiloAlert}>
              ⚠️ Mais de 2h sem 10 movimentos. <strong>Procure atendimento</strong> (HMIB, urgência obstétrica Amil 4002-2200).
            </div>
          )}

          <div className={styles.mobiloActions}>
            <button className={styles.mobiloTap} onClick={tap}>+ 1 mov</button>
            <button className={styles.btnSecondary} onClick={finish} disabled={saveMutation.isPending}>
              {saveMutation.isPending ? 'Salvando…' : 'Finalizar'}
            </button>
            <button className={styles.btnGhost} onClick={reset}>Cancelar</button>
          </div>
        </>
      )}

      {history.length > 0 && (
        <div className={styles.mobiloHistory}>
          <div className={styles.mobiloHistoryTitle}>Últimas sessões</div>
          {history.slice(0, 5).map(h => (
            <div key={h.id} className={styles.mobiloHistoryRow}>
              <span>{fmtDate(h.data)}</span>
              <span><strong>{h.valor}</strong> mov</span>
              <span>{h.notes}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
