/**
 * Saude.jsx — health module page.
 *
 * Tabs:
 *   - Eu: profile-scoped exams + vitals (Palmer sees Palmer's, Rafa sees Rafa's)
 *   - Familia: shared pregnancies + cross-profile family health context
 */
import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useProfile } from '../context/ProfileContext'
import api from '../api/client'
import styles from './Saude.module.css'

const EXAM_TYPE_LABELS = {
  hemograma: 'Hemograma',
  bioquimica: 'Bioquímica',
  hormonal: 'Hormonal',
  sorologia: 'Sorologia',
  urina: 'Urina',
  genetico: 'Genético',
  imagem_rx: 'Raio-X',
  imagem_us: 'Ultrassom',
  imagem_ct: 'Tomografia',
  imagem_rm: 'Ressonância',
  densitometria: 'Densitometria',
  cardio: 'Cardiológico',
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

function EuTab() {
  const { currentProfile } = useProfile()
  const { data: exams = [], isLoading: examsLoading } = useQuery({
    queryKey: ['health-exams', currentProfile?.id],
    queryFn: () => api.get('/saude/exams/'),
    enabled: !!currentProfile,
  })
  const { data: vitals = [] } = useQuery({
    queryKey: ['vital-readings', currentProfile?.id],
    queryFn: () => api.get('/saude/vitals/'),
    enabled: !!currentProfile,
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
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Exames</h2>
          <span className={styles.sectionCount}>{exams.length}</span>
        </div>
        {examsLoading ? (
          <div className={styles.empty}>Carregando…</div>
        ) : exams.length === 0 ? (
          <div className={styles.empty}>
            Nenhum exame cadastrado ainda. Use o admin Django ou um script de import para popular.
          </div>
        ) : (
          examsByYear.map(([year, list]) => (
            <div key={year} className={styles.yearGroup}>
              <h3 className={styles.yearTitle}>{year}</h3>
              <div className={styles.examList}>
                {list.map((e) => <ExamRow key={e.id} exam={e} />)}
              </div>
            </div>
          ))
        )}
      </section>

      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Vitais</h2>
          <span className={styles.sectionCount}>{vitals.length}</span>
        </div>
        {vitals.length === 0 ? (
          <div className={styles.empty}>Sem leituras de vitais ainda.</div>
        ) : (
          <div className={styles.vitalsList}>
            {vitals.slice(0, 20).map((v) => (
              <div key={v.id} className={styles.vitalRow}>
                <span className={styles.vitalDate}>{formatDate(v.data)}</span>
                <span className={styles.vitalTipo}>{v.tipo_label}</span>
                <span className={styles.vitalValor}>{v.valor}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

function PregnancyCard({ pregnancy }) {
  const ig = pregnancy.ig_atual_semanas
  const dias = pregnancy.dias_ate_dpp
  const progressPct = pregnancy.dum
    ? Math.min(100, Math.max(0, ((280 - (dias ?? 280)) / 280) * 100))
    : 0
  const lastConsult = pregnancy.consultations?.[0]

  return (
    <div className={styles.pregnancyCard}>
      <div className={styles.pregnancyHeader}>
        <div>
          <div className={styles.pregnancyTitle}>
            Gestação · {pregnancy.gestante_name}
          </div>
          <div className={styles.pregnancyMeta}>
            Confirmada em {formatDate(pregnancy.confirmada_em)}
            {pregnancy.dum && ` · DUM ${formatDate(pregnancy.dum)}`}
            {pregnancy.dpp && ` · DPP ${formatDate(pregnancy.dpp)}`}
          </div>
        </div>
        <div className={styles.pregnancyStatus} data-status={pregnancy.status}>
          {pregnancy.status}
        </div>
      </div>

      {pregnancy.dum && (
        <div className={styles.pregnancyTimeline}>
          <div className={styles.timelineBar}>
            <div className={styles.timelineFill} style={{ width: `${progressPct}%` }} />
          </div>
          <div className={styles.timelineLabels}>
            <span>{ig ? `IG ${ig}` : '—'}</span>
            <span>{dias != null ? `${dias} dias até DPP` : '—'}</span>
          </div>
        </div>
      )}

      {lastConsult && (
        <div className={styles.lastConsult}>
          <div className={styles.lastConsultTitle}>Última consulta · {formatDate(lastConsult.data)}</div>
          <div className={styles.lastConsultBody}>
            {lastConsult.pa_sis && <span>PA {lastConsult.pa_sis}/{lastConsult.pa_dia}</span>}
            {lastConsult.peso_kg && <span>Peso {lastConsult.peso_kg}kg</span>}
            {lastConsult.fcf_bpm && <span>FCF {lastConsult.fcf_bpm}bpm</span>}
            {lastConsult.altura_uterina_cm && <span>AU {lastConsult.altura_uterina_cm}cm</span>}
            {lastConsult.ig_semanas && <span>IG {lastConsult.ig_semanas}</span>}
          </div>
        </div>
      )}
    </div>
  )
}

function FamiliaTab() {
  const { currentProfile } = useProfile()
  const { data: pregnancies = [], isLoading } = useQuery({
    queryKey: ['pregnancies', currentProfile?.id],
    queryFn: () => api.get('/saude/pregnancies/'),
    enabled: !!currentProfile,
  })
  const activePregnancies = pregnancies.filter((p) => p.status === 'ativa')

  return (
    <div className={styles.tabContent}>
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Gestações</h2>
        </div>
        {isLoading ? (
          <div className={styles.empty}>Carregando…</div>
        ) : pregnancies.length === 0 ? (
          <div className={styles.empty}>
            Nenhuma gestação registrada. Use o admin Django para cadastrar.
          </div>
        ) : (
          <div className={styles.pregnancyList}>
            {pregnancies.map((p) => <PregnancyCard key={p.id} pregnancy={p} />)}
          </div>
        )}
      </section>

      {activePregnancies.length > 0 && (
        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Próximos passos</h2>
          </div>
          <div className={styles.tipBox}>
            Detalhes de pré-natal, marcos, mobilograma e alertas: ver
            <code> health/family/PLANO_MESTRE.md</code> no Mac.
          </div>
        </section>
      )}
    </div>
  )
}

export default function Saude() {
  const [tab, setTab] = useState('eu')
  const { currentProfile } = useProfile()

  return (
    <div className={styles.saudePage}>
      <div className={styles.headerBar}>
        <h1 className={styles.title}>Saúde · {currentProfile?.name || ''}</h1>
        <div className={styles.tabs}>
          <button
            className={tab === 'eu' ? styles.tabActive : styles.tab}
            onClick={() => setTab('eu')}
          >
            Eu
          </button>
          <button
            className={tab === 'familia' ? styles.tabActive : styles.tab}
            onClick={() => setTab('familia')}
          >
            Família
          </button>
        </div>
      </div>
      {tab === 'eu' ? <EuTab /> : <FamiliaTab />}
    </div>
  )
}
