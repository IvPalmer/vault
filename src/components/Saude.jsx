/**
 * Saude.jsx — advanced multi-widget health dashboard.
 *
 * Tabs (always visible regardless of current profile):
 *   - Eu      → currently logged-in profile's exams + vitals
 *   - {other} → partner profile's exams + vitals (auto-detected)
 *   - Família → shared pregnancy + cross-profile family view
 *
 * Family layout:
 *   - Hero: arc gauge + DPP countdown
 *   - Next action card + Cobertura widget
 *   - Pregnancy timeline (40-week gantt with checkpoints)
 *   - Checkpoints list (vertical, by trimester)
 *
 * Personal (Eu / outro) layout:
 *   - Recent exams widget (5 most recent, grouped by year list below)
 *   - Vitals sparklines
 *   - Full exam history grouped by year
 */
import { useState, useMemo, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useProfile } from '../context/ProfileContext'
import api, { API_BASE_URL } from '../api/client'
import styles from './Saude.module.css'
import widgetStyles from './saude/saude-widgets.module.css'
import PregnancyHero from './saude/PregnancyHero'
import PregnancyTimeline from './saude/PregnancyTimeline'
import PregnancyCheckpoints from './saude/PregnancyCheckpoints'
import NextActionWidget from './saude/NextActionWidget'
import CoberturaWidget from './saude/CoberturaWidget'
import ExamsRecentWidget from './saude/ExamsRecentWidget'
import AddExamForm from './saude/AddExamForm'
import MobilogramaWidget from './saude/MobilogramaWidget'
import FetalDevelopmentCard from './saude/FetalDevelopmentCard'
import BabyImplicationsSection from './saude/BabyImplicationsSection'
import CarenciaExamConflictWidget from './saude/CarenciaExamConflictWidget'
import LabPanelDashboard from './saude/LabPanelDashboard'
import HipImagingCard from './saude/HipImagingCard'
import ClinicalReportCard from './saude/ClinicalReportCard'
import MealPlanCard from './saude/MealPlanCard'
import GlucoseLogCard from './saude/GlucoseLogCard'
import ShoppingListCard from './saude/ShoppingListCard'
import CursosView from './saude/CursosView'
import EnxovalView from './saude/EnxovalView'
// Health content (clinical report, glucose log, meal plan, shopping list, hip
// imaging) is fetched from /saude/content/ — see HealthContent in models.py.
// It used to be hardcoded here, which compiled real medical records into the
// public SPA bundle, served before any auth ran.
import { useLabPanel } from './saude/useLabPanel'

const EXAM_TYPE_LABELS = {
  hemograma: 'Hemograma', bioquimica: 'Bioquímica', hormonal: 'Hormonal',
  sorologia: 'Sorologia', urina: 'Urina', genetico: 'Genético',
  imagem_rx: 'Raio-X', imagem_us: 'Ultrassom', imagem_ct: 'Tomografia',
  imagem_rm: 'Ressonância', densitometria: 'Densitometria', cardio: 'Cardio',
  outro: 'Outro',
}

function formatDate(iso) {
  if (!iso) return '—'
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

// Exam videos stream through the same same-origin proxy as the courses
// (reliable regardless of Drive's preview transcoding). See CursosView.
const examStreamUrl = (id) => `${API_BASE_URL}/google/drive/stream/${id}/`

function ExamRow({ exam }) {
  // A static /exam-media/ URL (served by nginx with native byte-range support)
  // takes precedence — reliable playback; otherwise fall back to the Drive
  // stream proxy by file id.
  const videoUrl = exam.valores?.video_url || null
  const videoDriveId = exam.valores?.video_drive_id || null
  const videoSrc = videoUrl || (videoDriveId ? examStreamUrl(videoDriveId) : null)
  // Player hints, not lab values — keep them out of the value chips.
  const HIDDEN_KEYS = new Set(['video_url', 'video_drive_id'])
  const valoresAll = exam.valores
    ? Object.entries(exam.valores).filter(([k]) => !HIDDEN_KEYS.has(k))
    : []
  const valoresEntries = valoresAll.slice(0, 4)
  return (
    <div className={styles.examRow}>
      <div className={styles.examMain}>
        <div className={styles.examTopLine}>
          <span className={styles.examTipo}>{exam.tipo_label || EXAM_TYPE_LABELS[exam.tipo] || exam.tipo}</span>
          <span className={styles.examData}>{formatDate(exam.data)}</span>
        </div>
        <div className={styles.examNome}>{exam.nome}</div>
        {(exam.medico || exam.laboratorio) && (
          <div className={styles.examMeta}>
            {exam.medico && <span>{exam.medico}</span>}
            {exam.medico && exam.laboratorio && <span> · </span>}
            {exam.laboratorio && <span>{exam.laboratorio}</span>}
          </div>
        )}
        {valoresEntries.length > 0 && (
          <div className={styles.examValores}>
            {valoresEntries.map(([k, v]) => (
              <span key={k} className={styles.examValor}>
                <strong>{k}:</strong> {String(v)}
              </span>
            ))}
            {valoresAll.length > 4 && (
              <span className={styles.examValor}>+{valoresAll.length - 4}</span>
            )}
          </div>
        )}
        {exam.notes && <div className={styles.examNotes}>{exam.notes}</div>}
        {videoSrc && (
          <video
            key={videoSrc}
            src={videoSrc}
            controls
            playsInline
            preload="metadata"
            style={{ width: '100%', maxWidth: 560, marginTop: 10, borderRadius: 8, background: '#000', display: 'block' }}
          />
        )}
      </div>
      {exam.arquivo_path && (() => {
        // arquivo_path can be (a) a https:// URL (Drive, etc.) — works on any
        // device, or (b) a legacy local path that only resolves via file://
        // when we're on Palmer's Mac AND the browser is on a local origin.
        const path = exam.arquivo_path
        const isUrl = /^https?:\/\//i.test(path)

        if (isUrl) {
          return (
            <a
              className={styles.examFile}
              href={path}
              target="_blank"
              rel="noreferrer"
              title="Abrir anexo"
            >
              PDF
            </a>
          )
        }

        const host = (typeof window !== 'undefined' && window.location.hostname) || ''
        const ua = (typeof navigator !== 'undefined' && navigator.userAgent) || ''
        const plat = (typeof navigator !== 'undefined' && navigator.platform) || ''
        const isMacUA = /Macintosh/.test(ua) && !/iPad|iPhone|iPod/.test(ua)
        const isMacPlat = /Mac/i.test(plat) && (navigator.maxTouchPoints || 0) < 2
        const isLocalHost = host === 'localhost'
          || host === '127.0.0.1'
          || host.endsWith('.ts.net')
        const isLocalMac = isMacUA && isMacPlat && isLocalHost
        if (!isLocalMac) {
          return (
            <span
              className={`${styles.examFile} ${styles.examFileDisabled}`}
              title="Arquivo local (legado) — apenas no Mac do Palmer"
              aria-disabled="true"
            >
              PDF
            </span>
          )
        }
        return (
          <a
            className={styles.examFile}
            href={`file://${path.startsWith('/') ? path : '/Users/palmer/Documents/' + path}`}
            target="_blank"
            rel="noreferrer"
            title="Abrir arquivo local"
          >
            PDF
          </a>
        )
      })()}
    </div>
  )
}

/**
 * PersonalView — shared layout used by both Eu and {other} tabs.
 * Renders exam list + vitals scoped to the given profile_id.
 */
function PersonalView({ profileId, profileName }) {
  const [adding, setAdding] = useState(false)
  // Sub-tab inside the profile view. Default = Resumo (clinical narrative).
  // Painel = full lab panel only. Histórico = full exam list.
  const [subTab, setSubTab] = useState('resumo')

  const { data: exams = [], isLoading: examsLoading } = useQuery({
    queryKey: ['health-exams', profileId],
    queryFn: () => api.get(`/saude/exams/${profileId ? `?profile_id=${profileId}` : ''}`),
    enabled: !!profileId,
  })
  const { data: vitals = [] } = useQuery({
    queryKey: ['vital-readings', profileId],
    queryFn: () => api.get(`/saude/vitals/${profileId ? `?profile_id=${profileId}` : ''}`),
    enabled: !!profileId,
  })
  // {slug: payload} — clinical_report, observations, hip_imaging, glucose_log,
  // meal_plan, shopping_list. Absent slugs just mean the card doesn't render.
  const { data: healthContent = {} } = useQuery({
    queryKey: ['health-content', profileId],
    queryFn: () => api.get(`/saude/content/${profileId ? `?profile_id=${profileId}` : ''}`),
    enabled: !!profileId,
  })

  const examsByYear = useMemo(() => {
    const grouped = {}
    for (const e of exams) {
      const year = e.data?.slice(0, 4) || 'sem data'
      if (!grouped[year]) grouped[year] = []
      grouped[year].push(e)
    }
    return Object.entries(grouped).sort(([a], [b]) => b.localeCompare(a))
  }, [exams])

  // isPalmer is gone: the cards it gated (clinical report, hip imaging) now key
  // off whether the profile actually has that content, not off their name.
  const isRafa = profileName?.toLowerCase().includes('rafa')

  // DB-driven lab panel. The old hardcoded fallbacks are gone: LabMarker rows
  // are the source (Palmer 34, Rafa 105), so the fallback never fired — it just
  // shipped the panels to anyone who downloaded the bundle.
  const { panel: livePanel, source: panelSource } = useLabPanel(profileId, null)

  // Nutrição tab only exists for Rafa. If user switches profile while on it,
  // fall back to Resumo so the panel doesn't render empty.
  useEffect(() => {
    if (subTab === 'nutricao' && !isRafa) setSubTab('resumo')
  }, [isRafa, subTab])

  return (
    <div className={styles.tabContent}>
      <div className={styles.subTabs} role="tablist" aria-label="Seções de saúde">
        <button
          id="saude-subtab-resumo"
          role="tab"
          aria-selected={subTab === 'resumo'}
          aria-controls="saude-subpanel-resumo"
          tabIndex={subTab === 'resumo' ? 0 : -1}
          className={subTab === 'resumo' ? styles.subTabActive : styles.subTab}
          onClick={() => setSubTab('resumo')}
        >
          Resumo
        </button>
        <button
          id="saude-subtab-painel"
          role="tab"
          aria-selected={subTab === 'painel'}
          aria-controls="saude-subpanel-painel"
          tabIndex={subTab === 'painel' ? 0 : -1}
          className={subTab === 'painel' ? styles.subTabActive : styles.subTab}
          onClick={() => setSubTab('painel')}
        >
          Painel laboratorial
        </button>
        {isRafa && (
          <button
            id="saude-subtab-nutricao"
            role="tab"
            aria-selected={subTab === 'nutricao'}
            aria-controls="saude-subpanel-nutricao"
            tabIndex={subTab === 'nutricao' ? 0 : -1}
            className={subTab === 'nutricao' ? styles.subTabActive : styles.subTab}
            onClick={() => setSubTab('nutricao')}
          >
            Nutrição
          </button>
        )}
        <button
          id="saude-subtab-historico"
          role="tab"
          aria-selected={subTab === 'historico'}
          aria-controls="saude-subpanel-historico"
          tabIndex={subTab === 'historico' ? 0 : -1}
          className={subTab === 'historico' ? styles.subTabActive : styles.subTab}
          onClick={() => setSubTab('historico')}
        >
          Histórico <span className={styles.subTabCount}>{exams.length}</span>
        </button>
      </div>

      {subTab === 'resumo' && (
        <div
          id="saude-subpanel-resumo"
          role="tabpanel"
          aria-labelledby="saude-subtab-resumo"
        >
          {/* Clinical synthesis dashboard — primary focus of the page.
              Gated on the content existing rather than on the profile's name:
              same result for Palmer/Rafa, and nothing to render for anyone else. */}
          {healthContent.clinical_report && (
            <ClinicalReportCard
              report={healthContent.clinical_report}
              observations={healthContent.observations}
            />
          )}

          {/* Secondary row: recent exams + vitals (vitals only if present) */}
          <div className={vitals.length > 0 ? styles.gridTwoCol : styles.gridOneCol}>
            <ExamsRecentWidget exams={exams} title={`Últimos exames de ${profileName}`} limit={3} />
            {vitals.length > 0 && (
              <div className={widgetStyles.examsWidget}>
                <div className={widgetStyles.widgetLabel}>Vitais recentes</div>
                <div className={widgetStyles.examsList}>
                  {vitals.slice(0, 8).map(v => (
                    <div key={v.id} className={widgetStyles.examMini}>
                      <span className={widgetStyles.examMiniChip} style={{ background: '#5b8bc4' }}>
                        {v.tipo_label || v.tipo}
                      </span>
                      <div className={widgetStyles.examMiniBody}>
                        <div className={widgetStyles.examMiniName}>{v.valor}</div>
                      </div>
                      <span className={widgetStyles.examMiniDate}>{formatDate(v.data)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {healthContent.hip_imaging && <HipImagingCard data={healthContent.hip_imaging} />}
        </div>
      )}

      {subTab === 'nutricao' && isRafa && (
        <div
          id="saude-subpanel-nutricao"
          role="tabpanel"
          aria-labelledby="saude-subtab-nutricao"
          className={styles.tabContent}
        >
          <MealPlanCard plan={healthContent.meal_plan} />
          <GlucoseLogCard log={healthContent.glucose_log} />
          <ShoppingListCard list={healthContent.shopping_list} />
        </div>
      )}

      {subTab === 'painel' && (
        <div
          id="saude-subpanel-painel"
          role="tabpanel"
          aria-labelledby="saude-subtab-painel"
        >
          <LabPanelDashboard panel={livePanel} source={panelSource} />
        </div>
      )}

      {subTab === 'historico' && (
        <section
          id="saude-subpanel-historico"
          role="tabpanel"
          aria-labelledby="saude-subtab-historico"
          className={styles.section}
        >
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Histórico completo · exames</h2>
            <span className={styles.sectionCount}>{exams.length}</span>
            <button className={widgetStyles.addBtn} onClick={() => setAdding(true)}>+ Adicionar exame</button>
          </div>
          {examsLoading ? (
            <div className={styles.empty}>Carregando…</div>
          ) : exams.length === 0 ? (
            <div className={styles.empty}>
              Nenhum exame cadastrado para {profileName}. Use o admin Django.
            </div>
          ) : (
            examsByYear.map(([year, list]) => (
              <div key={year} className={styles.yearGroup}>
                <h3 className={styles.yearTitle}>{year}</h3>
                <div className={styles.examList}>
                  {list.map(e => <ExamRow key={e.id} exam={e} />)}
                </div>
              </div>
            ))
          )}
        </section>
      )}

      {adding && (
        <AddExamForm profileId={profileId} profileName={profileName} onClose={() => setAdding(false)} />
      )}
    </div>
  )
}

/**
 * FamiliaView — pregnancy-centric dashboard with checkpoints, cobertura, hero gauge.
 */
function FamiliaView() {
  const [adding, setAdding] = useState(false)
  const [famTab, setFamTab] = useState('acompanhamento')
  const { data: pregnancies = [], isLoading } = useQuery({
    queryKey: ['pregnancies-shared'],
    queryFn: () => api.get('/saude/pregnancies/'),
  })
  const ativa = pregnancies.find(p => p.status === 'ativa')
  const completedSet = useMemo(() => new Set(ativa?.completed_checkpoint_ids || []), [ativa])

  // Baby implications are the gestante's lab findings — fetched, not hardcoded.
  // Same queryKey as PersonalView, so react-query serves it from cache there.
  const gestanteId = ativa?.gestante
  const { data: famContent = {} } = useQuery({
    queryKey: ['health-content', gestanteId],
    queryFn: () => api.get(`/saude/content/?profile_id=${gestanteId}`),
    enabled: !!gestanteId,
  })

  return (
    <div className={styles.tabContent}>
      <div className={styles.subTabs} role="tablist" aria-label="Seções da família">
        <button
          id="fam-subtab-acompanhamento"
          role="tab"
          aria-selected={famTab === 'acompanhamento'}
          aria-controls="fam-subpanel-acompanhamento"
          tabIndex={famTab === 'acompanhamento' ? 0 : -1}
          className={famTab === 'acompanhamento' ? styles.subTabActive : styles.subTab}
          onClick={() => setFamTab('acompanhamento')}
        >
          Acompanhamento
        </button>
        <button
          id="fam-subtab-enxoval"
          role="tab"
          aria-selected={famTab === 'enxoval'}
          aria-controls="fam-subpanel-enxoval"
          tabIndex={famTab === 'enxoval' ? 0 : -1}
          className={famTab === 'enxoval' ? styles.subTabActive : styles.subTab}
          onClick={() => setFamTab('enxoval')}
        >
          Enxoval
        </button>
        <button
          id="fam-subtab-cursos"
          role="tab"
          aria-selected={famTab === 'cursos'}
          aria-controls="fam-subpanel-cursos"
          tabIndex={famTab === 'cursos' ? 0 : -1}
          className={famTab === 'cursos' ? styles.subTabActive : styles.subTab}
          onClick={() => setFamTab('cursos')}
        >
          Cursos
        </button>
      </div>

      {famTab === 'enxoval' && (
        <div id="fam-subpanel-enxoval" role="tabpanel" aria-labelledby="fam-subtab-enxoval">
          <EnxovalView pregnancy={ativa} />
        </div>
      )}

      {famTab === 'cursos' && (
        <div id="fam-subpanel-cursos" role="tabpanel" aria-labelledby="fam-subtab-cursos">
          <CursosView />
        </div>
      )}

      {famTab === 'acompanhamento' && (
        <div id="fam-subpanel-acompanhamento" role="tabpanel" aria-labelledby="fam-subtab-acompanhamento">
        {isLoading ? (
          <div className={styles.empty}>Carregando…</div>
        ) : !ativa ? (
          <div className={styles.empty}>
            Nenhuma gestação ativa registrada. Use o admin Django para cadastrar.
          </div>
        ) : (
          <>
            <div className={styles.heroRow}>
        <div className={styles.heroLeft}>
          <div className={styles.familyTitle}>Gestação · {ativa.gestante_name}</div>
          <div className={styles.familyMeta}>
            Confirmada em {formatDate(ativa.confirmada_em)}
            {ativa.dum && ` · DUM ${formatDate(ativa.dum)}`}
          </div>
          <PregnancyHero pregnancy={ativa} />
        </div>
        <FetalDevelopmentCard pregnancy={ativa} />
        <div className={styles.heroRight}>
          <NextActionWidget pregnancy={ativa} completedIds={completedSet} />
          <CoberturaWidget pregnancy={ativa} />
        </div>
      </div>

      <CarenciaExamConflictWidget pregnancy={ativa} />

      <BabyImplicationsSection items={famContent.baby_implications} />

      {/* Linha do tempo horizontal recolhida — duplica conteúdo dos
         checkpoints abaixo. Disponível sob demanda. */}
      <details className={styles.timelineAccordion}>
        <summary>Linha do tempo gestacional · 0–40 semanas</summary>
        <PregnancyTimeline pregnancy={ativa} completedIds={completedSet} />
      </details>

      <div className={styles.gridTwoCol}>
        <MobilogramaWidget pregnancy={ativa} profileId={ativa.gestante} />
      </div>

      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Checkpoints pré-natais — Ministério da Saúde</h2>
          <span className={styles.sectionCount}>{completedSet.size} concluídos</span>
          <button className={widgetStyles.addBtn} onClick={() => setAdding(true)}>+ Registrar exame/consulta</button>
        </div>
        <PregnancyCheckpoints pregnancy={ativa} completedIds={completedSet} />
      </section>

      {adding && (
        <AddExamForm
          profileId={ativa.gestante}
          profileName={ativa.gestante_name}
          pregnancyId={ativa.id}
          onClose={() => setAdding(false)}
        />
      )}

      {pregnancies.length > 1 && (
        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Histórico de gestações</h2>
            <span className={styles.sectionCount}>{pregnancies.length}</span>
          </div>
          <div className={styles.pregnancyList}>
            {pregnancies.filter(p => p !== ativa).map(p => (
              <div key={p.id} className={styles.pregnancyCard}>
                <div className={styles.pregnancyHeader}>
                  <div>
                    <div className={styles.pregnancyTitle}>Gestação · {p.gestante_name}</div>
                    <div className={styles.pregnancyMeta}>
                      Confirmada em {formatDate(p.confirmada_em)}
                    </div>
                  </div>
                  <div className={styles.pregnancyStatus} data-status={p.status}>{p.status}</div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
          </>
        )}
        </div>
      )}
    </div>
  )
}

export default function Saude() {
  const { currentProfile, profiles = [] } = useProfile()
  const [tab, setTab] = useState('eu')

  // Pick the "other" profile (anyone that isn't the current one).
  const otherProfile = useMemo(() => {
    if (!currentProfile) return null
    return profiles.find(p => p.id !== currentProfile.id) || null
  }, [currentProfile, profiles])

  if (!currentProfile) {
    return <div className={styles.saudePage}><div className={styles.empty}>Carregando perfil…</div></div>
  }

  return (
    <div className={styles.saudePage}>
      <div className={styles.headerBar}>
        <h1 className={styles.title}>Saúde</h1>
        <div className={styles.tabs}>
          <button
            className={tab === 'eu' ? styles.tabActive : styles.tab}
            onClick={() => setTab('eu')}
          >
            {currentProfile.name}
          </button>
          {otherProfile && (
            <button
              className={tab === 'other' ? styles.tabActive : styles.tab}
              onClick={() => setTab('other')}
            >
              {otherProfile.name}
            </button>
          )}
          <button
            className={tab === 'familia' ? styles.tabActive : styles.tab}
            onClick={() => setTab('familia')}
          >
            Família
          </button>
        </div>
      </div>

      {tab === 'eu' && <PersonalView profileId={currentProfile.id} profileName={currentProfile.name} />}
      {tab === 'other' && otherProfile && <PersonalView profileId={otherProfile.id} profileName={otherProfile.name} />}
      {tab === 'familia' && <FamiliaView />}
    </div>
  )
}
