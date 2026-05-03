/**
 * ExamsRecentWidget — list of latest exams with type chip and value preview.
 */
import { useMemo } from 'react'
import styles from './saude-widgets.module.css'
import { getKindMeta } from './checkpoints'

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

function tipoColor(tipo) {
  if (tipo === 'hemograma' || tipo === 'bioquimica' || tipo === 'hormonal' || tipo === 'sorologia' || tipo === 'urina') {
    return getKindMeta('exame_lab').color
  }
  if (tipo?.startsWith('imagem_')) return getKindMeta('usg').color
  if (tipo === 'genetico') return getKindMeta('vacina').color
  return getKindMeta('rotina').color
}

export default function ExamsRecentWidget({ exams = [], limit = 5, title = 'Exames recentes' }) {
  const recent = useMemo(() => {
    return [...exams]
      .sort((a, b) => (b.data || '').localeCompare(a.data || ''))
      .slice(0, limit)
  }, [exams, limit])

  return (
    <div className={styles.examsWidget}>
      <div className={styles.widgetLabel}>{title}</div>
      {recent.length === 0 ? (
        <div className={styles.examsEmpty}>Nenhum exame cadastrado.</div>
      ) : (
        <div className={styles.examsList}>
          {recent.map(e => {
            const valoresEntries = e.valores ? Object.entries(e.valores).slice(0, 2) : []
            return (
              <div key={e.id} className={styles.examMini}>
                <span className={styles.examMiniChip} style={{ background: tipoColor(e.tipo) }}>
                  {EXAM_TYPE_LABELS[e.tipo] || e.tipo}
                </span>
                <div className={styles.examMiniBody}>
                  <div className={styles.examMiniName}>{e.nome}</div>
                  {valoresEntries.length > 0 && (
                    <div className={styles.examMiniValores}>
                      {valoresEntries.map(([k, v]) => (
                        <span key={k}><strong>{k}:</strong> {String(v)}</span>
                      ))}
                    </div>
                  )}
                </div>
                <span className={styles.examMiniDate}>{formatDate(e.data)}</span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
