/**
 * ClinicalReportCard — clinical synthesis dashboard.
 *
 * Replaced the previous "5 colored cards in a row + 5 observation cards" layout
 * (which read like a flat clinical memo) with a triage-focused composition:
 *
 *   1. Status hero — synthesis headline + subtitle + primary CTA
 *   2. Próximas ações — ranked actionable list (max 5)
 *   3. Mudanças recentes — what improved / resolved
 *   4. Raciocínio clínico — collapsed accordion containing the original
 *      camada breakdown (Estrutural/Tecido mole/...) for who wants the depth
 *
 * `observations` (slug: observations, from /saude/content/) renders as a small
 * "Pontos adicionais" tail when there are items not surfaced in acoes/mudancas.
 */
import styles from './saude-widgets.module.css'

function ArrowIcon({ direction = 'right' }) {
  const rot = { up: -90, down: 90, right: 0 }[direction] || 0
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
         style={{ transform: `rotate(${rot}deg)`, flexShrink: 0 }}>
      <line x1="5" y1="12" x2="19" y2="12" />
      <polyline points="12 5 19 12 12 19" />
    </svg>
  )
}

function CheckIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
      <polyline points="20 6 9 17 4 12" />
    </svg>
  )
}

function AcaoRow({ acao }) {
  return (
    <li className={styles.acaoRow} data-priority={acao.prioridade}>
      <div className={styles.acaoMain}>
        <div className={styles.acaoTitulo}>{acao.titulo}</div>
        {acao.porque && <div className={styles.acaoPorque}>{acao.porque}</div>}
      </div>
      <div className={styles.acaoMeta}>
        {acao.prazo && <span className={styles.acaoPrazo}>{acao.prazo}</span>}
        <span className={styles.acaoPrioridade} data-priority={acao.prioridade}>
          {acao.prioridade}
        </span>
      </div>
    </li>
  )
}

function MudancaRow({ m }) {
  const direcao = m.direcao || 'positivo'
  return (
    <li className={styles.mudancaRow} data-direcao={direcao}>
      <span className={styles.mudancaIcon} aria-hidden="true">
        {direcao === 'positivo' && <CheckIcon />}
        {direcao === 'negativo' && <ArrowIcon direction="down" />}
        {direcao === 'neutro' && <ArrowIcon direction="right" />}
      </span>
      <div className={styles.mudancaBody}>
        <span className={styles.mudancaTitulo}>{m.titulo}</span>
        {m.data && <span className={styles.mudancaData}>{m.data}</span>}
      </div>
    </li>
  )
}

export default function ClinicalReportCard({ report, observations }) {
  if (!report) return null
  const dataFmt = report.data?.split('-').reverse().join('/')

  const sintese = report.sintese
  const acoes = report.acoes || []
  const mudancas = report.mudancas || []

  return (
    <section className={styles.clinicalCard}>
      {sintese ? (
        <header className={styles.statusHero}>
          <div className={styles.statusHeroMain}>
            <div className={styles.statusEyebrow}>
              {report.modelo} · {dataFmt}
            </div>
            <h2 className={styles.statusHeadline}>{sintese.headline}</h2>
            {sintese.subtitle && (
              <p className={styles.statusSubtitle}>{sintese.subtitle}</p>
            )}
          </div>
          {sintese.cta && (
            <a
              href={sintese.cta.href}
              target="_blank"
              rel="noopener"
              className={styles.statusCta}
            >
              {sintese.cta.label}
              <ArrowIcon direction="right" />
            </a>
          )}
        </header>
      ) : (
        <div className={styles.widgetLabel}>Relatório clínico · {report.modelo} · {dataFmt}</div>
      )}

      <div className={styles.dashGrid}>
        {acoes.length > 0 && (
          <div className={styles.dashCol}>
            <h3 className={styles.dashColTitle}>Próximas ações</h3>
            <ol className={styles.acoesList}>
              {acoes.map((a, i) => <AcaoRow key={i} acao={a} />)}
            </ol>
          </div>
        )}

        {mudancas.length > 0 && (
          <div className={styles.dashCol}>
            <h3 className={styles.dashColTitle}>Mudanças recentes</h3>
            <ul className={styles.mudancasList}>
              {mudancas.map((m, i) => <MudancaRow key={i} m={m} />)}
            </ul>
          </div>
        )}
      </div>

      {report.camadas && report.camadas.length > 0 && (
        <details className={styles.reasoningAccordion}>
          <summary>
            <span>Raciocínio clínico · {report.camadas.length} camadas</span>
            <span className={styles.accordionHint}>ver detalhes</span>
          </summary>
          <div className={styles.reasoningBody}>
            {report.camadas.map(camada => (
              <div key={camada.id} className={styles.reasoningLayer}>
                <div className={styles.reasoningLayerHeader}>
                  <span
                    className={styles.reasoningLayerDot}
                    style={{ background: camada.cor }}
                    aria-hidden="true"
                  />
                  <h4 className={styles.reasoningLayerTitle}>{camada.titulo}</h4>
                </div>
                <ul className={styles.reasoningLayerFindings}>
                  {camada.achados.map((a, i) => <li key={i}>{a}</li>)}
                </ul>
              </div>
            ))}
          </div>
        </details>
      )}

      {/* "Pontos adicionais" (observations) removed from Resumo — content
         overlaps with acoes/mudancas. Kept as data export for the printable
         report (relatorio-palmer.html) and the full audit trail. */}
    </section>
  )
}
