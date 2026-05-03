/**
 * Brazilian Ministério da Saúde prenatal schedule (Caderneta da Gestante 2023)
 * + extras for high-risk context (G6PD carrier, idade materna, etc.)
 *
 * Each checkpoint has:
 *   - id: stable identifier
 *   - week: target gestational week (or [start, end] range)
 *   - label: display name
 *   - kind: 'consulta' | 'exame_lab' | 'usg' | 'vacina' | 'rotina'
 *   - critical: true if missing this has clinical impact
 *   - notes: optional context
 */

export const CHECKPOINTS = [
  // ── 1º trimestre ──
  { id: '1a-consulta', week: [6, 12], label: '1ª consulta pré-natal', kind: 'consulta', critical: true },
  { id: 'usg-datacao', week: [7, 12], label: 'USG datação', kind: 'usg', critical: true,
    notes: 'Define DUM/IG corrigida' },
  { id: 'lab-1tri', week: [8, 12], label: 'Painel laboratorial 1º tri', kind: 'exame_lab', critical: true,
    notes: 'Hemograma, tipagem sg + Coombs, glicemia jejum, TSH, sorologias (HIV, sífilis, HepB/C, toxo, rubéola, CMV), urina + urocultura' },
  { id: 'usg-morfo-1', week: [11, 13.6], label: 'USG morfológica 1º tri', kind: 'usg', critical: true,
    notes: 'TN, osso nasal, doppler ducto venoso (rastreio cromossomopatias)' },

  // ── Aconselhamento genético G6PD (Palmer) ──
  { id: 'aconselhamento-g6pd', week: [10, 16], label: 'Aconselhamento genético G6PD', kind: 'consulta', critical: false,
    notes: 'Padrão X-recessivo: 50% chance menino afetado, 50% menina portadora. Avaliar teste pré-natal não invasivo.' },

  // ── 2º trimestre ──
  { id: 'consulta-mensal-2tri', week: [16], label: 'Consulta pré-natal mensal', kind: 'consulta', critical: true },
  { id: 'usg-morfo-2', week: [18, 22], label: 'USG morfológica 2º tri', kind: 'usg', critical: true,
    notes: 'Anatomia fetal completa, sexo, placenta, líquido amniótico' },
  { id: 'totg', week: [24, 28], label: 'TOTG (teste tolerância glicose)', kind: 'exame_lab', critical: true,
    notes: 'Diagnóstico de DMG (diabetes gestacional)' },
  { id: 'eco-fetal', week: [24, 28], label: 'Ecocardiograma fetal', kind: 'usg', critical: false,
    notes: 'Indicado se rastreio 1º tri alterado, idade materna avançada, diabetes' },
  { id: 'coombs-anti-d', week: [28], label: 'Coombs indireto + Anti-D (se Rh-)', kind: 'exame_lab', critical: true,
    notes: 'Imunoglobulina anti-D se gestante Rh negativo' },
  { id: 'mobilograma-start', week: [28], label: 'Iniciar mobilograma diário', kind: 'rotina', critical: true,
    notes: '10 movimentos/2h pós-refeição. Procurar atendimento se < 6 movimentos/2h.' },

  // ── 3º trimestre ──
  { id: 'consulta-quinzenal', week: [32], label: 'Consultas quinzenais', kind: 'consulta', critical: true },
  { id: 'lab-3tri', week: [32, 34], label: 'Painel laboratorial 3º tri', kind: 'exame_lab', critical: true,
    notes: 'Hemograma, sorologias (HIV, sífilis, HepB), urina, glicemia, Coombs (se Rh-)' },
  { id: 'gbs', week: [35, 37], label: 'Cultura Strep B (GBS)', kind: 'exame_lab', critical: true,
    notes: 'Swab vaginal/retal — define profilaxia antibiótica intra-parto' },
  { id: 'usg-3tri', week: [36, 40], label: 'USG perfil biofísico', kind: 'usg', critical: false,
    notes: 'Avaliação fetal, líquido amniótico, posição' },
  { id: 'consulta-semanal', week: [37], label: 'Consultas semanais', kind: 'consulta', critical: true },
  { id: 'plano-parto', week: [34, 38], label: 'Plano de parto + escolha hospital', kind: 'rotina', critical: true },

  // ── Vacinas ──
  { id: 'vac-dtpa', week: [20, 36], label: 'Vacina dTpa (coqueluche)', kind: 'vacina', critical: true,
    notes: 'Idealmente 27-36 sem. Protege RN nos primeiros meses.' },
  { id: 'vac-influenza', week: [12, 38], label: 'Vacina influenza', kind: 'vacina', critical: true,
    notes: 'Em campanha sazonal (abril-maio BR)' },
  { id: 'vac-covid', week: [12, 38], label: 'Vacina COVID-19', kind: 'vacina', critical: false,
    notes: 'Conforme calendário vigente' },
  { id: 'vac-hepb', week: [12, 30], label: 'Vacina Hepatite B (3 doses)', kind: 'vacina', critical: false,
    notes: 'Se não vacinada previamente' },
]

const KIND_META = {
  consulta:  { label: 'Consulta', color: '#5b8bc4', short: 'CON' },
  exame_lab: { label: 'Exame',    color: '#c47e3a', short: 'LAB' },
  usg:       { label: 'USG',      color: '#7a5fa6', short: 'USG' },
  vacina:    { label: 'Vacina',   color: '#5fa67a', short: 'VAC' },
  rotina:    { label: 'Rotina',   color: '#8a8a8a', short: 'ROT' },
}

export function getKindMeta(kind) {
  return KIND_META[kind] || KIND_META.rotina
}

/**
 * Compute checkpoint status given current gestational week (in decimal weeks).
 * Returns: 'overdue' | 'current' | 'upcoming' | 'completed'
 *
 * `completed` only set if there's a matching completion record (e.g. a
 * HealthExam matching the checkpoint id). For now we infer:
 *   - overdue: currentWeek > range_end (and not completed)
 *   - current: currentWeek between range_start and range_end
 *   - upcoming: currentWeek < range_start
 */
export function checkpointStatus(checkpoint, currentWeek, completedIds = new Set()) {
  if (completedIds.has(checkpoint.id)) return 'completed'
  if (currentWeek == null) return 'upcoming'
  const w = checkpoint.week
  const [start, end] = Array.isArray(w) ? w : [w, w]
  if (currentWeek > end) return 'overdue'
  if (currentWeek >= start) return 'current'
  return 'upcoming'
}

/**
 * Decimal weeks since DUM (e.g. 18.4 = 18w + ~3d).
 * Returns null if no DUM.
 */
export function weeksFromDum(dum) {
  if (!dum) return null
  const dumDate = typeof dum === 'string' ? new Date(dum) : dum
  const today = new Date()
  const diffMs = today - dumDate
  return diffMs / (1000 * 60 * 60 * 24 * 7)
}

/**
 * Format decimal weeks as "Xw + Yd" (Brazilian standard notation)
 */
export function formatWeeks(decimalWeeks) {
  if (decimalWeeks == null) return '—'
  const weeks = Math.floor(decimalWeeks)
  const days = Math.floor((decimalWeeks - weeks) * 7)
  return `${weeks}s + ${days}d`
}

/**
 * Naegele: DPP = DUM + 280 days
 */
export function computeDpp(dum) {
  if (!dum) return null
  const dumDate = typeof dum === 'string' ? new Date(dum) : new Date(dum)
  return new Date(dumDate.getTime() + 280 * 24 * 60 * 60 * 1000)
}
