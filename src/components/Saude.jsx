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
import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useProfile } from '../context/ProfileContext'
import api from '../api/client'
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

function ExamRow({ exam }) {
  const valoresEntries = exam.valores ? Object.entries(exam.valores).slice(0, 4) : []
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
            {Object.keys(exam.valores || {}).length > 4 && (
              <span className={styles.examValor}>+{Object.keys(exam.valores).length - 4}</span>
            )}
          </div>
        )}
        {exam.notes && <div className={styles.examNotes}>{exam.notes}</div>}
      </div>
      {exam.arquivo_path && (
        <a
          className={styles.examFile}
          href={`file://${exam.arquivo_path.startsWith('/') ? exam.arquivo_path : '/Users/palmer/Documents/' + exam.arquivo_path}`}
          target="_blank"
          rel="noreferrer"
          title="Abrir arquivo local"
        >
          📄
        </a>
      )}
    </div>
  )
}

/**
 * PersonalView — shared layout used by both Eu and {other} tabs.
 * Renders exam list + vitals scoped to the given profile_id.
 */
function PersonalView({ profileId, profileName }) {
  const [adding, setAdding] = useState(false)
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

  const examsByYear = useMemo(() => {
    const grouped = {}
    for (const e of exams) {
      const year = e.data?.slice(0, 4) || 'sem data'
      if (!grouped[year]) grouped[year] = []
      grouped[year].push(e)
    }
    return Object.entries(grouped).sort(([a], [b]) => b.localeCompare(a))
  }, [exams])

  return (
    <div className={styles.tabContent}>
      <div className={styles.gridTwoCol}>
        <ExamsRecentWidget exams={exams} title={`${profileName} · últimos exames`} limit={5} />
        <div className={widgetStyles.examsWidget}>
          <div className={widgetStyles.widgetLabel}>Vitais recentes</div>
          {vitals.length === 0 ? (
            <div className={widgetStyles.examsEmpty}>Nenhuma leitura de vitais ainda.</div>
          ) : (
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
          )}
        </div>
      </div>

      <section className={styles.section}>
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
  const { data: pregnancies = [], isLoading } = useQuery({
    queryKey: ['pregnancies-shared'],
    queryFn: () => api.get('/saude/pregnancies/'),
  })
  const ativa = pregnancies.find(p => p.status === 'ativa')
  const completedSet = useMemo(() => new Set(ativa?.completed_checkpoint_ids || []), [ativa])

  if (isLoading) return <div className={styles.empty}>Carregando…</div>
  if (!ativa) {
    return (
      <div className={styles.empty}>
        Nenhuma gestação ativa registrada. Use o admin Django para cadastrar.
      </div>
    )
  }

  return (
    <div className={styles.tabContent}>
      <div className={styles.heroRow}>
        <div className={styles.heroLeft}>
          <div className={styles.familyTitle}>Gestação · {ativa.gestante_name}</div>
          <div className={styles.familyMeta}>
            Confirmada em {formatDate(ativa.confirmada_em)}
            {ativa.dum && ` · DUM ${formatDate(ativa.dum)}`}
          </div>
          <PregnancyHero pregnancy={ativa} />
        </div>
        <div className={styles.heroRight}>
          <NextActionWidget pregnancy={ativa} completedIds={completedSet} />
          <CoberturaWidget pregnancy={ativa} />
        </div>
      </div>

      <PregnancyTimeline pregnancy={ativa} completedIds={completedSet} />

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
