/**
 * AddExamForm — modal form for adding a HealthExam.
 *
 * Pre-fills profile_id from caller. Optional checkpoint_id dropdown so the
 * exam fulfills a specific prenatal checkpoint (e.g. "usg-datacao") and the
 * Família view auto-marks it as completed.
 */
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../api/client'
import styles from './saude-widgets.module.css'
import { CHECKPOINTS } from './checkpoints'

const EXAM_TYPES = [
  { value: 'hemograma', label: 'Hemograma' },
  { value: 'bioquimica', label: 'Bioquímica' },
  { value: 'hormonal', label: 'Hormonal' },
  { value: 'sorologia', label: 'Sorologia' },
  { value: 'urina', label: 'Urina' },
  { value: 'genetico', label: 'Genético' },
  { value: 'imagem_us', label: 'Ultrassom' },
  { value: 'imagem_rx', label: 'Raio-X' },
  { value: 'imagem_ct', label: 'Tomografia' },
  { value: 'imagem_rm', label: 'Ressonância' },
  { value: 'densitometria', label: 'Densitometria' },
  { value: 'cardio', label: 'Cardio' },
  { value: 'outro', label: 'Outro' },
]

export default function AddExamForm({ profileId, profileName, pregnancyId, onClose }) {
  const queryClient = useQueryClient()
  const [tipo, setTipo] = useState('hemograma')
  const [nome, setNome] = useState('')
  const [data, setData] = useState(new Date().toISOString().slice(0, 10))
  const [laboratorio, setLaboratorio] = useState('')
  const [medico, setMedico] = useState('')
  const [notes, setNotes] = useState('')
  const [arquivoPath, setArquivoPath] = useState('')
  const [checkpointId, setCheckpointId] = useState('')

  const mutation = useMutation({
    mutationFn: (payload) => api.post(`/saude/exams/?profile_id=${profileId}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['health-exams'] })
      queryClient.invalidateQueries({ queryKey: ['pregnancies-shared'] })
      onClose()
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    mutation.mutate({
      tipo, nome, data,
      laboratorio: laboratorio || '',
      medico: medico || '',
      notes: notes || '',
      arquivo_path: arquivoPath || '',
      pregnancy: pregnancyId || null,
      checkpoint_id: checkpointId || '',
      valores: {},
    })
  }

  return (
    <div className={styles.modalBackdrop} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h3 className={styles.modalTitle}>Novo exame · {profileName}</h3>
          <button className={styles.modalClose} onClick={onClose}>×</button>
        </div>
        <form onSubmit={handleSubmit} className={styles.modalForm}>
          <div className={styles.formRow}>
            <label>Tipo</label>
            <select value={tipo} onChange={e => setTipo(e.target.value)} required>
              {EXAM_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>

          <div className={styles.formRow}>
            <label>Nome</label>
            <input type="text" value={nome} onChange={e => setNome(e.target.value)} required placeholder="Ex: USG datação" />
          </div>

          <div className={styles.formRow}>
            <label>Data</label>
            <input type="date" value={data} onChange={e => setData(e.target.value)} required />
          </div>

          {pregnancyId && (
            <div className={styles.formRow}>
              <label>Checkpoint pré-natal</label>
              <select value={checkpointId} onChange={e => setCheckpointId(e.target.value)}>
                <option value="">— nenhum —</option>
                {CHECKPOINTS.map(cp => (
                  <option key={cp.id} value={cp.id}>{cp.label}</option>
                ))}
              </select>
              <span className={styles.formHint}>Marca o checkpoint como concluído.</span>
            </div>
          )}

          <div className={styles.formRow}>
            <label>Laboratório</label>
            <input type="text" value={laboratorio} onChange={e => setLaboratorio(e.target.value)} placeholder="Opcional" />
          </div>

          <div className={styles.formRow}>
            <label>Médico</label>
            <input type="text" value={medico} onChange={e => setMedico(e.target.value)} placeholder="Opcional" />
          </div>

          <div className={styles.formRow}>
            <label>Notas</label>
            <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={3} placeholder="Achados, conclusão..." />
          </div>

          <div className={styles.formRow}>
            <label>Arquivo (path)</label>
            <input type="text" value={arquivoPath} onChange={e => setArquivoPath(e.target.value)} placeholder="Exames/2026/.../arquivo.pdf" />
          </div>

          {mutation.isError && (
            <div className={styles.formError}>
              Erro ao salvar. Tente novamente.
            </div>
          )}

          <div className={styles.formActions}>
            <button type="button" className={styles.btnSecondary} onClick={onClose}>Cancelar</button>
            <button type="submit" className={styles.btnPrimary} disabled={mutation.isPending}>
              {mutation.isPending ? 'Salvando...' : 'Salvar exame'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
