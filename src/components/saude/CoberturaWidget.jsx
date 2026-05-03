/**
 * CoberturaWidget — obstetric coverage countdown vs DPP risk visualization.
 */
import styles from './saude-widgets.module.css'

function formatDate(d) {
  if (!d) return '—'
  const dt = typeof d === 'string' ? new Date(d) : d
  return dt.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
}

export default function CoberturaWidget({ pregnancy }) {
  const cobertura = pregnancy?.cobertura_parto
  if (!cobertura) {
    return <div className={styles.coberturaEmpty}>Cobertura: dados insuficientes</div>
  }

  const { status, plano, fim_carencia, dias_descoberto } = cobertura

  if (status === 'pending') {
    return (
      <div className={styles.coberturaWidget} data-status="pending">
        <div className={styles.widgetLabel}>Cobertura obstétrica</div>
        <div className={styles.coberturaTitleSmall}>Aguardando dados</div>
        <div className={styles.coberturaDesc}>
          Confirme DPP (USG datação) e data de início da vigência do plano para calcular cobertura.
        </div>
      </div>
    )
  }

  if (status === 'ok') {
    return (
      <div className={styles.coberturaWidget} data-status="ok">
        <div className={styles.widgetLabel}>Cobertura obstétrica ✅</div>
        <div className={styles.coberturaTitleSmall}>{plano}</div>
        <div className={styles.coberturaDesc}>
          Carência cumprida em {formatDate(fim_carencia)}. Parto coberto pelo plano.
        </div>
      </div>
    )
  }

  // risco
  const dpp = pregnancy?.dpp ? new Date(pregnancy.dpp) : null
  const fim = new Date(fim_carencia)
  const inicio = pregnancy?.plano_vigencia_inicio ? new Date(pregnancy.plano_vigencia_inicio) : null
  const totalDays = inicio ? (fim - inicio) / (1000 * 60 * 60 * 24) : 300
  const todayDays = inicio ? (new Date() - inicio) / (1000 * 60 * 60 * 24) : 0
  const carenciaPct = Math.min(100, Math.max(0, (todayDays / totalDays) * 100))
  const dppPct = dpp && inicio ? Math.min(100, Math.max(0, ((dpp - inicio) / (1000 * 60 * 60 * 24) / totalDays) * 100)) : null

  return (
    <div className={styles.coberturaWidget} data-status="risco">
      <div className={styles.widgetLabel}>⚠️ Risco de cobertura</div>
      <div className={styles.coberturaTitleSmall}>{plano}</div>
      <div className={styles.coberturaBarOuter}>
        <div className={styles.coberturaBarInner} style={{ width: `${carenciaPct}%` }} />
        {dppPct != null && (
          <div className={styles.coberturaDppMarker} style={{ left: `${dppPct}%` }} title="DPP">
            <span className={styles.coberturaDppLabel}>DPP</span>
          </div>
        )}
      </div>
      <div className={styles.coberturaTimeline}>
        <span>Início: {formatDate(inicio)}</span>
        <span>Fim carência: {formatDate(fim)}</span>
      </div>
      <div className={styles.coberturaDesc}>
        DPP cai <strong>{dias_descoberto} dias</strong> antes do fim da carência. Negociar redução com Amil ou preparar plano B.
      </div>
    </div>
  )
}
