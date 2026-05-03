/**
 * Fetal development by gestational week.
 *
 * Each entry has size_cm + weight_g + comparison (BR cultural reference,
 * "do tamanho de um abacate") + key milestones in PT-BR.
 *
 * Sources: ACOG, MS Caderneta da Gestante, Mayo Clinic week-by-week.
 */

export const WEEKS = {
  4:  { compare: 'semente de papoula', emoji: '🌱', size_cm: 0.1,  weight_g: 0.4,
        milestones: 'Implantação no útero. Tubo neural começa a se formar.' },
  5:  { compare: 'grão de arroz',      emoji: '🌾', size_cm: 0.2,  weight_g: 0.5,
        milestones: 'Tubo neural se fecha. Coração primitivo começa a se formar.' },
  6:  { compare: 'lentilha',            emoji: '🫘', size_cm: 0.6,  weight_g: 1,
        milestones: 'Coração começa a bater (~110 bpm). Brotos de braços e pernas aparecem.' },
  7:  { compare: 'mirtilo',             emoji: '🫐', size_cm: 1.0,  weight_g: 2,
        milestones: 'Cérebro se desenvolvendo rapidamente. Mãos e pés se formam.' },
  8:  { compare: 'feijão',              emoji: '🫘', size_cm: 1.6,  weight_g: 3,
        milestones: 'Dedos das mãos e pés começam a aparecer. Embrião agora "feto".' },
  9:  { compare: 'cereja',              emoji: '🍒', size_cm: 2.3,  weight_g: 5,
        milestones: 'Movimentos espontâneos começam (não sentidos pela mãe ainda).' },
  10: { compare: 'morango',             emoji: '🍓', size_cm: 3.1,  weight_g: 7,
        milestones: 'Órgãos vitais formados. Unhas começam a crescer.' },
  11: { compare: 'limão pequeno',       emoji: '🍋', size_cm: 4.1,  weight_g: 14,
        milestones: 'Ossos começam a endurecer. Genitália se diferencia.' },
  12: { compare: 'ameixa',              emoji: '🟣', size_cm: 5.4,  weight_g: 14,
        milestones: 'Reflexos aparecem. Pode chupar o polegar. 1ª USG morfológica em breve.' },
  13: { compare: 'pêssego',             emoji: '🍑', size_cm: 7.4,  weight_g: 23,
        milestones: 'Cordas vocais formadas. Fim do 1º trimestre — risco de aborto cai bastante.' },
  14: { compare: 'maçã pequena',        emoji: '🍎', size_cm: 8.7,  weight_g: 43,
        milestones: 'Pode fazer caretas, franzir testa. Pelos finos (lanugo) começam.' },
  15: { compare: 'laranja',             emoji: '🍊', size_cm: 10.1, weight_g: 70,
        milestones: 'Reflexo respiratório com líquido amniótico. Pele ainda translúcida.' },
  16: { compare: 'abacate',             emoji: '🥑', size_cm: 11.6, weight_g: 100,
        milestones: 'Começa a ouvir sons. Pode mover olhos.' },
  17: { compare: 'cebola',              emoji: '🧅', size_cm: 13.0, weight_g: 140,
        milestones: 'Gordura subcutânea começa a se formar. Esqueleto se solidifica.' },
  18: { compare: 'batata-doce',         emoji: '🍠', size_cm: 14.2, weight_g: 190,
        milestones: 'Pode bocejar e soluçar. Janela ideal: USG morfológica 2º tri (18–22s).' },
  19: { compare: 'manga',               emoji: '🥭', size_cm: 15.3, weight_g: 240,
        milestones: 'Vernix caseosa cobre a pele. Cabelo da cabeça crescendo.' },
  20: { compare: 'banana',              emoji: '🍌', size_cm: 16.4, weight_g: 300,
        milestones: 'Metade da gestação. Movimentos perceptíveis pela mãe (quickening).' },
  21: { compare: 'cenoura',             emoji: '🥕', size_cm: 26.7, weight_g: 360,
        milestones: 'Medula óssea produz células sanguíneas. Movimentos coordenados.' },
  22: { compare: 'abóbora pequena',     emoji: '🎃', size_cm: 27.8, weight_g: 430,
        milestones: 'Papilas gustativas se desenvolvem. Dorme 12–14h por dia.' },
  23: { compare: 'berinjela',           emoji: '🍆', size_cm: 28.9, weight_g: 500,
        milestones: 'Pulmões em desenvolvimento. Audição clara — pode reconhecer voz.' },
  24: { compare: 'milho',               emoji: '🌽', size_cm: 30.0, weight_g: 600,
        milestones: 'Marco de viabilidade extra-uterina (com UTI neonatal).' },
  25: { compare: 'nabo',                emoji: '🥔', size_cm: 34.6, weight_g: 660,
        milestones: 'Textura da pele se desenvolve. Cabelo ganha cor.' },
  26: { compare: 'pepino',              emoji: '🥒', size_cm: 35.6, weight_g: 760,
        milestones: 'Olhos começam a abrir. TOTG (24–28s) e ecocardio fetal nessa janela.' },
  27: { compare: 'couve-flor',          emoji: '🥬', size_cm: 36.6, weight_g: 875,
        milestones: 'Padrões de sono REM. Cérebro muito ativo.' },
  28: { compare: 'beringela grande',    emoji: '🍆', size_cm: 37.6, weight_g: 1005,
        milestones: 'Início 3º trimestre. Mobilograma diário a partir de agora. Anti-D se Rh-.' },
  29: { compare: 'abóbora butternut',   emoji: '🎃', size_cm: 38.6, weight_g: 1150,
        milestones: 'Músculos e pulmões maturando. Posição definida (cabeça pra baixo idealmente).' },
  30: { compare: 'melão honeydew',      emoji: '🍈', size_cm: 39.9, weight_g: 1320,
        milestones: 'Surfactante pulmonar começa a ser produzido em quantidade.' },
  31: { compare: 'coco',                emoji: '🥥', size_cm: 41.1, weight_g: 1500,
        milestones: 'Ganho de peso acelerado. Pode ver luz através da parede uterina.' },
  32: { compare: 'aspargos',            emoji: '🌿', size_cm: 42.4, weight_g: 1700,
        milestones: 'Unhas crescem. Sistema imunológico maturando.' },
  33: { compare: 'abacaxi',             emoji: '🍍', size_cm: 43.7, weight_g: 1900,
        milestones: 'Detecta luz e escuridão. Painel laboratorial 3º tri.' },
  34: { compare: 'melão cantaloupe',    emoji: '🍈', size_cm: 45.0, weight_g: 2150,
        milestones: 'Pulmões quase maduros. Plano de parto + escolha hospital.' },
  35: { compare: 'melão honeydew gde',  emoji: '🍈', size_cm: 46.2, weight_g: 2400,
        milestones: 'Cultura GBS (35–37s). Cérebro continua maturando rápido.' },
  36: { compare: 'alface romana',       emoji: '🥬', size_cm: 47.4, weight_g: 2620,
        milestones: 'Gordura subcutânea acumula. "Lightening" — bebê desce na pelve.' },
  37: { compare: 'acelga',              emoji: '🌿', size_cm: 48.6, weight_g: 2860,
        milestones: 'Termo precoce. Pulmões prontos para o ambiente externo.' },
  38: { compare: 'alho-poró',           emoji: '🌿', size_cm: 49.8, weight_g: 3080,
        milestones: 'Vernix começa a sair. Bebê com aparência de recém-nascido.' },
  39: { compare: 'melancia pequena',    emoji: '🍉', size_cm: 50.7, weight_g: 3290,
        milestones: 'Termo. Parto pode ocorrer a qualquer momento.' },
  40: { compare: 'abóbora moranga',     emoji: '🎃', size_cm: 51.2, weight_g: 3460,
        milestones: 'Data provável do parto. ~5% nascem exatamente na DPP.' },
}

/**
 * Get fetal data for the closest available week (clamped to 4–40).
 */
export function fetalDataForWeek(decimalWeek) {
  if (decimalWeek == null) return null
  const w = Math.max(4, Math.min(40, Math.floor(decimalWeek)))
  return { week: w, ...WEEKS[w] }
}

/**
 * Common symptoms expected at this gestational stage.
 * Returns array of strings.
 */
export function symptomsForWeek(decimalWeek) {
  if (decimalWeek == null) return []
  const w = Math.floor(decimalWeek)
  if (w < 4) return ['Pré-implantação — sem sintomas detectáveis']
  if (w <= 8) return [
    'Náuseas matinais (pico 6–9 sem)',
    'Fadiga acentuada',
    'Sensibilidade mamária',
    'Micção frequente',
    'Aversão ou desejo por alimentos',
  ]
  if (w <= 13) return [
    'Náuseas começam a melhorar',
    'Fadiga ainda presente',
    'Constipação possível',
    'Mudanças de humor',
    'Aumento de volume sanguíneo',
  ]
  if (w <= 20) return [
    'Náuseas geralmente passam',
    'Energia retorna ("lua de mel" gestacional)',
    'Pele radiante (efeito hormonal)',
    'Possível dor lombar leve',
    'Quickening — primeiros movimentos perceptíveis (~18–22s)',
  ]
  if (w <= 27) return [
    'Movimentos fetais regulares',
    'Dor lombar e ciática possíveis',
    'Edema leve em pés',
    'Azia/refluxo ocasional',
    'Contrações Braxton-Hicks ocasionais',
  ]
  if (w <= 34) return [
    'Falta de ar (útero pressiona diafragma)',
    'Edema em pés e mãos',
    'Dificuldade para dormir',
    'Câimbras nas pernas',
    'Contrações Braxton-Hicks mais frequentes',
  ]
  return [
    'Bebê desce ("lightening") — alívio respiratório',
    'Pressão pélvica aumenta',
    'Contrações Braxton-Hicks regulares',
    'Possível perda do tampão mucoso',
    'Sinais de trabalho de parto possíveis a qualquer momento',
  ]
}
