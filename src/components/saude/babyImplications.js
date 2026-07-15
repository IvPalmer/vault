/**
 * Priority labels for BabyImplicationsSection.
 *
 * The implications themselves (BABY_IMPLICATIONS) used to live here as a
 * hardcoded array. Each entry carried real lab values, lab names and dates
 * (HbA1c readings, fasting glucose, HOMA-IR, collection dates) — which
 * compiled a person's medical history into the public SPA bundle, served
 * before any app-level auth ran. They now come from /saude/content/
 * (slug: baby_implications). Only these generic labels stay in source.
 */
export const PRIORIDADE_LABEL = {
  alta: 'alta prioridade',
  media: 'média prioridade',
  baixa: 'baixa prioridade',
}
