/**
 * Rafa's clinical reference data.
 *
 * RAFA_LAB_PANEL is the *current* panel (now: 1º trimestre gestacional, 2026-05-06).
 * RAFA_LAB_PANEL_PREGESTACIONAL preserves the 2025-05-28 baseline as historical
 * reference — kept for the markers Dra. Nahara did not re-request (lipídios,
 * hormônios sexuais, função renal/hepática completa, coagulação).
 *
 * Sources:
 *   - 2026-05-06 painel 1º T (DASA Asa Sul, solicitante Dra. Nahara Alves Gomes Torres)
 *   - 2025-05-28 painel pré-gestacional (DASA · solicitante Dr. Bruno Bezerra Silva)
 *   - 2024-08-26 hemograma + glicemia + lipídios (Lapac/DB)
 */

export const RAFA_LAB_PANEL = {
  data_coleta: '2026-05-06',
  laboratorio: 'DASA · Exame Medicina Diagnóstica · Asa Sul',
  contexto: 'Painel 1º trimestre — IG ~5+6 sem (DUM 28/03/2026). Solicitante Dra. Nahara Alves Gomes Torres (CRM-DF 18529).',
  idade_coleta: 35,

  categorias: [
    {
      id: 'hemograma',
      nome: 'Hemograma',
      markers: [
        { key: 'hemacias', label: 'Hemácias', value: 4.25, unit: '10⁶/µL', ref_min: 3.8, ref_max: 4.8, status: 'normal' },
        { key: 'hemoglobina', label: 'Hemoglobina', value: 13.0, unit: 'g/dL', ref_min: 12.0, ref_max: 15.0, status: 'normal' },
        { key: 'hematocrito', label: 'Hematócrito', value: 38.5, unit: '%', ref_min: 36.0, ref_max: 46.0, status: 'normal' },
        { key: 'vcm', label: 'VCM', value: 90.7, unit: 'fL', ref_min: 83.0, ref_max: 101.0, status: 'normal' },
        { key: 'hcm', label: 'HCM', value: 30.6, unit: 'pg', ref_min: 27.0, ref_max: 32.0, status: 'normal' },
        { key: 'chcm', label: 'CHCM', value: 33.8, unit: 'g/dL', ref_min: 31.0, ref_max: 35.0, status: 'normal' },
        { key: 'rdw', label: 'RDW', value: 12.7, unit: '%', ref_min: 11.6, ref_max: 14.0, status: 'normal' },
        { key: 'leucocitos', label: 'Leucócitos', value: 10830, unit: '/µL', ref_min: 4000, ref_max: 10000, status: 'limite_superior',
          obs: 'Leucocitose discreta fisiológica da gestação. Sem desvio à esquerda.' },
        { key: 'neutrofilos', label: 'Neutrófilos', value: 8047, unit: '/µL', ref_min: 1800, ref_max: 7800, status: 'limite_superior',
          obs: 'Neutrofilia fisiológica gestacional (74,3%).' },
        { key: 'linfocitos', label: 'Linfócitos', value: 1809, unit: '/µL', ref_min: 1000, ref_max: 3000, status: 'normal' },
        { key: 'monocitos', label: 'Monócitos', value: 856, unit: '/µL', ref_min: 200, ref_max: 1000, status: 'normal' },
        { key: 'eosinofilos', label: 'Eosinófilos', value: 87, unit: '/µL', ref_min: 20, ref_max: 500, status: 'normal' },
        { key: 'basofilos', label: 'Basófilos', value: 32, unit: '/µL', ref_min: 20, ref_max: 100, status: 'normal' },
        { key: 'plaquetas', label: 'Plaquetas', value: 396000, unit: '/µL', ref_min: 150000, ref_max: 450000, status: 'normal',
          obs: 'Normalizou (era 464k em 2025).' },
        { key: 'vpm', label: 'VPM', value: 9.6, unit: 'fL', ref_min: 9.2, ref_max: 12.8, status: 'normal' },
      ],
    },
    {
      id: 'tipagem',
      nome: 'Tipagem sanguínea',
      markers: [
        { key: 'grupo_abo', label: 'Grupo ABO', value_text: 'O', unit: '', status: 'normal' },
        { key: 'fator_rh', label: 'Fator Rh', value_text: 'Positivo', unit: '', status: 'normal',
          obs: 'Rh positivo — sem necessidade de imunoglobulina anti-D na 28ª semana ou pós-parto.' },
        { key: 'coombs_indireto', label: 'Coombs indireto', value_text: 'Negativo', unit: '', status: 'normal' },
      ],
    },
    {
      id: 'glicemia',
      nome: 'Metabolismo glicêmico',
      markers: [
        { key: 'glicose', label: 'Glicemia jejum', value: 94, unit: 'mg/dL', ref_min: 70, ref_max: 99, status: 'normal' },
        { key: 'hba1c', label: 'HbA1c', value: 5.4, unit: '%', ref_max: 5.7, status: 'normal',
          obs: 'Tendência ↑ leve (5.1 → 5.4 em 1 ano). Reforça importância do TOTG 24-28s.' },
        { key: 'gme', label: 'Glicose média estimada', value: 107, unit: 'mg/dL', status: 'normal' },
        { key: 'insulina', label: 'Insulina basal', value: 4.9, unit: 'µUI/mL', ref_min: 2.5, ref_max: 13.1, status: 'normal' },
        { key: 'homa_ir', label: 'HOMA-IR', value: 1.13, unit: '', ref_max: 2.7, status: 'normal' },
      ],
    },
    {
      id: 'tireoide',
      nome: 'Função tireoide',
      markers: [
        { key: 'tsh', label: 'TSH ultrassensível', value: 0.56, unit: 'µUI/mL', ref_min: 0.10, ref_max: 3.60, status: 'normal',
          obs: 'Faixa 1º trimestre gestacional. Caiu de 0,96 (2025) — esperado pela supressão pelo hCG.' },
        { key: 't4_livre', label: 'T4 livre', value: 1.37, unit: 'ng/dL', ref_min: 0.70, ref_max: 1.90, status: 'normal' },
      ],
    },
    {
      id: 'micronutrientes',
      nome: 'Ferro e vitaminas',
      markers: [
        { key: 'ferro', label: 'Ferro sérico', value: 143, unit: 'µg/dL', ref_min: 33, ref_max: 193, status: 'normal',
          obs: 'Subiu de 110 (2025) → 143.' },
        { key: 'ferritina', label: 'Ferritina', value: 58.4, unit: 'ng/mL', ref_min: 13, ref_max: 150, status: 'normal',
          obs: 'Reservas adequadas. Subiu de 33,8 (2025) → 58,4 — boa base para expansão de volume.' },
        { key: 'b12', label: 'Vitamina B-12', value: 453, unit: 'pg/mL', ref_min: 245, ref_max: 985, status: 'normal' },
        { key: 'vit_d', label: '25-OH Vitamina D', value: null, value_text: 'Pendente', unit: 'ng/mL', status: 'pendente',
          obs: 'Solicitada por Dra. Nahara mas não coletada — autorização Amil aguardando. Coletar avulsa.' },
      ],
    },
    {
      id: 'sorologias',
      nome: 'Sorologias infecciosas',
      markers: [
        { key: 'hiv', label: 'HIV 1/2 (p24+Ac, 4ª gen)', value: 0.06, value_text: 'Não reagente', unit: 'índice', status: 'normal' },
        { key: 'htlv', label: 'HTLV I/II', value: 0.10, value_text: 'Não reagente', unit: 'índice', status: 'normal' },
        { key: 'sifilis', label: 'Sífilis (CMIA Anti-T.pallidum)', value: 0.03, value_text: 'Não reagente', unit: 'índice', status: 'normal' },
        { key: 'hbsag', label: 'HBsAg', value: 0.32, value_text: 'Não reagente', unit: 'índice', status: 'normal',
          obs: 'Sem infecção pelo HBV.' },
        { key: 'anti_hbs', label: 'Anti-HBs', value: 2.0, value_text: '<2,0', unit: 'mUI/mL', ref_min: 10, status: 'baixo',
          obs: 'Sem proteção contra hepatite B (<10 mUI/mL). Indica vacinação durante a gestação (Engerix-B, esquema acelerado 0/1/2 ou 0/1/6, segura SBIM).' },
        { key: 'anti_hcv', label: 'Hepatite C (Anti-HCV)', value: 0.07, value_text: 'Não reagente', unit: 'índice', status: 'normal' },
        { key: 'rubeola_igg', label: 'Rubéola IgG', value: 90.5, unit: 'UI/mL', ref_min: 10.0, status: 'normal',
          obs: 'Imune (reagente). Protege o feto.' },
        { key: 'rubeola_igm', label: 'Rubéola IgM', value: 0.12, value_text: 'Não reagente', unit: 'index', status: 'normal' },
        { key: 'cmv_igg', label: 'Citomegalovírus IgG', value: 147.0, unit: 'UA/mL', ref_min: 6.0, status: 'normal',
          obs: 'Infecção passada — imune. Reduz drasticamente risco de transmissão vertical.' },
        { key: 'cmv_igm', label: 'Citomegalovírus IgM', value: 0.13, value_text: 'Não reagente', unit: 'index', status: 'normal' },
        { key: 'toxo_igg', label: 'Toxoplasmose IgG', value: 0.2, value_text: '<0,2', unit: 'UI/mL', ref_min: 1.6, status: 'baixo',
          obs: 'SUSCETÍVEL. Sem imunidade prévia. Reforço de prevenção alimentar/ambiental + repetir sorologia a cada trimestre (~ago/2026 e ~nov/2026).' },
        { key: 'toxo_igm', label: 'Toxoplasmose IgM', value: 0.06, value_text: 'Não reagente', unit: 'index', status: 'normal' },
      ],
    },
    {
      id: 'urinario',
      nome: 'Trato urinário',
      markers: [
        { key: 'densidade', label: 'Urina I — densidade', value: 1.016, unit: '', ref_min: 1.003, ref_max: 1.035, status: 'normal' },
        { key: 'ph', label: 'Urina I — pH', value: 6.5, unit: '', ref_min: 5, ref_max: 7.5, status: 'normal' },
        { key: 'proteina', label: 'Urina I — proteína', value_text: 'Não reagente', unit: '', status: 'normal' },
        { key: 'glicose_urina', label: 'Urina I — glicose', value_text: 'Não reagente', unit: '', status: 'normal' },
        { key: 'cetonicos', label: 'Urina I — corpos cetônicos', value_text: 'Não reagente', unit: '', status: 'normal' },
        { key: 'nitrito', label: 'Urina I — nitrito', value_text: 'Não reagente', unit: '', status: 'normal' },
        { key: 'hemoglobina_urina', label: 'Urina I — hemoglobina', value_text: 'Não reagente', unit: '', status: 'normal' },
        { key: 'leucocitos_urina', label: 'Urina I — leucócitos', value: 7400, unit: '/mL', ref_max: 25000, status: 'normal' },
        { key: 'hemacias_urina', label: 'Urina I — hemácias', value: 7800, unit: '/mL', ref_max: 23000, status: 'normal' },
        { key: 'bacterias', label: 'Urina I — bactérias', value_text: '<1.200', unit: '/µL', ref_max: 1200, status: 'normal' },
        { key: 'urocultura', label: 'Urocultura jato médio', value_text: 'Negativa', unit: '', status: 'normal',
          obs: 'ITU/bacteriúria assintomática descartada. Repetir cada trimestre — histórico de 2024.' },
      ],
    },
  ],
}

/**
 * Pre-gestational baseline (2025-05-28) — preserved for markers Dra. Nahara
 * did not re-request in the 1º T panel: lipídios, hormônios sexuais, função
 * renal e hepática completa, coagulação.
 */
export const RAFA_LAB_PANEL_PREGESTACIONAL = {
  data_coleta: '2025-05-28',
  laboratorio: 'DASA · Laboratório Exame',
  contexto: 'Painel pré-gestacional completo — solicitante Dr. Bruno Bezerra Silva',
  idade_coleta: 34,

  categorias: [
    {
      id: 'lipidios',
      nome: 'Perfil lipídico (2025-05-28)',
      markers: [
        { key: 'colesterol_total', label: 'Colesterol total', value: 223, unit: 'mg/dL', ref_max: 190, status: 'alto',
          obs: 'Limítrofe alto. Aumento fisiológico esperado durante gestação. Reavaliar pós-parto.' },
        { key: 'hdl', label: 'HDL', value: 62, unit: 'mg/dL', ref_min: 40, status: 'normal' },
        { key: 'ldl', label: 'LDL', value: 143, unit: 'mg/dL', ref_max: 130, status: 'limite_superior' },
        { key: 'trigliceres', label: 'Triglicérides', value: 74, unit: 'mg/dL', ref_max: 150, status: 'normal' },
        { key: 'vldl', label: 'VLDL', value: 18, unit: 'mg/dL', status: 'normal' },
        { key: 'apo_a', label: 'Apo A', value: 162, unit: 'mg/dL', ref_min: 108, ref_max: 225, status: 'normal' },
        { key: 'apo_b', label: 'Apo B', value: 103, unit: 'mg/dL', ref_min: 60, ref_max: 117, status: 'normal' },
        { key: 'lp_a', label: 'Lipoproteína(a)', value: 29.7, unit: 'nmol/L', ref_max: 75, status: 'normal' },
      ],
    },
    {
      id: 'hormonios_sexuais',
      nome: 'Hormônios sexuais pré-gestacional (2025-05-28)',
      markers: [
        { key: 'estradiol', label: 'Estradiol', value: 261, unit: 'pg/mL', status: 'normal',
          obs: 'Coleta sem fase informada' },
        { key: 'fsh', label: 'FSH', value: 5.4, unit: 'mUI/mL', status: 'normal' },
        { key: 'prolactina', label: 'Prolactina', value: 13.2, unit: 'ng/mL', ref_min: 4.8, ref_max: 23.3, status: 'normal' },
        { key: 'testo_total', label: 'Testosterona total', value: 28.3, unit: 'ng/dL', status: 'normal' },
        { key: 'testo_livre', label: 'Testosterona livre', value: 0.18, unit: 'ng/dL', status: 'normal' },
        { key: 'testo_biod', label: 'Testosterona biodisponível', value: 4.32, unit: 'ng/dL', status: 'normal' },
        { key: 'dht', label: 'DHT', value: 69.4, unit: 'pg/mL', status: 'normal' },
      ],
    },
    {
      id: 'renal',
      nome: 'Função renal e eletrólitos (2025-05-28)',
      markers: [
        { key: 'creatinina', label: 'Creatinina', value: 0.68, unit: 'mg/dL', ref_min: 0.50, ref_max: 1.00, status: 'normal' },
        { key: 'sodio', label: 'Sódio', value: 137, unit: 'mmol/L', ref_min: 136, ref_max: 145, status: 'normal' },
        { key: 'potassio', label: 'Potássio', value: 4.9, unit: 'mmol/L', ref_min: 3.5, ref_max: 5.1, status: 'normal' },
        { key: 'calcio', label: 'Cálcio total', value: 9.7, unit: 'mg/dL', ref_min: 8.6, ref_max: 10.0, status: 'normal' },
        { key: 'calcio_ionico', label: 'Cálcio iônico', value: 1.15, unit: 'mmol/L', ref_min: 1.05, ref_max: 1.30, status: 'normal' },
        { key: 'fosforo', label: 'Fósforo', value: 4.2, unit: 'mg/dL', ref_min: 2.5, ref_max: 4.5, status: 'normal' },
      ],
    },
    {
      id: 'hepatica',
      nome: 'Função hepática (2025-05-28)',
      markers: [
        { key: 'tgo', label: 'TGO/AST', value: 20, unit: 'U/L', ref_max: 32, status: 'normal' },
        { key: 'tgp', label: 'TGP/ALT', value: 21, unit: 'U/L', ref_max: 33, status: 'normal' },
        { key: 'ggt', label: 'Gama-GT', value: 13, unit: 'U/L', ref_max: 40, status: 'normal' },
        { key: 'fa', label: 'Fosfatase alcalina', value: 43, unit: 'U/L', ref_min: 35, ref_max: 105, status: 'normal' },
        { key: 'bili_total', label: 'Bilirrubina total', value: 0.30, unit: 'mg/dL', ref_max: 1.20, status: 'normal' },
        { key: 'ptn_total', label: 'Proteínas totais', value: 7.9, unit: 'g/dL', ref_min: 6.4, ref_max: 8.3, status: 'normal' },
        { key: 'albumina', label: 'Albumina', value: 5.1, unit: 'g/dL', ref_min: 3.5, ref_max: 5.2, status: 'normal' },
      ],
    },
    {
      id: 'tireoide_extra_2025',
      nome: 'Tireoide — autoimunidade (2025-05-28)',
      markers: [
        { key: 'anti_tpo', label: 'Anti-TPO', value: 11.1, unit: 'UI/mL', ref_max: 35, status: 'normal' },
        { key: 'anti_tg', label: 'Anti-tireoglobulina', value: 17.6, unit: 'UI/mL', ref_max: 115, status: 'normal' },
      ],
    },
    {
      id: 'micronutrientes_extra_2025',
      nome: 'Folato / homocisteína / D-dímero (2025-05-28)',
      markers: [
        { key: 'transferrina', label: 'Transferrina', value: 286, unit: 'mg/dL', ref_min: 200, ref_max: 360, status: 'normal' },
        { key: 'folato', label: 'Ácido fólico', value: 23.6, unit: 'ng/mL', ref_min: 5.38, status: 'normal' },
        { key: 'homocisteina', label: 'Homocisteína', value: 5.53, unit: 'µmol/L', ref_min: 4.44, ref_max: 13.56, status: 'normal' },
        { key: 'vit_d_2025', label: '25-OH Vitamina D (2025)', value: 40.8, unit: 'ng/mL', ref_min: 30, ref_max: 60, status: 'normal',
          obs: 'Repetir na gestação atual — pedido aguardando autorização Amil.' },
        { key: 'd_dimero', label: 'D-dímero', value: 220, unit: 'ng/mL FEU', ref_max: 500, status: 'normal' },
      ],
    },
  ],
}

export const RAFA_OBSERVATIONS = [
  {
    titulo: '⚠️ Hepatite B — sem proteção vacinal',
    texto: 'Anti-HBs <2,0 mUI/mL (precisa ≥10 para proteção). HBsAg negativo confirma ausência de infecção. Discutir esquema acelerado de vacinação durante a gestação na 2ª consulta — Engerix-B 0/1/2 ou 0/1/6 meses. Vacina considerada segura pela SBIM/CDC durante gestação.',
    prioridade: 'alta',
  },
  {
    titulo: '⚠️ Toxoplasmose — suscetível (sem imunidade)',
    texto: 'IgG <0,2 UI/mL (não reagente), IgM negativo. Sem imunidade prévia. Repetir IgG/IgM trimestralmente (~ago/2026 e ~nov/2026). Reforçar prevenção: carne MUITO bem passada, lavar verduras com hipoclorito, congelar carnes >24h a −12°C antes de cozinhar, luvas em jardinagem, evitar contato direto com fezes de gato (caixa de areia delega para Palmer ou com luvas+lavagem).',
    prioridade: 'alta',
  },
  {
    titulo: '📋 Vitamina D pendente',
    texto: 'Não consta no laudo de 06/05/2026 — estava no painel solicitado mas aguardava autorização Amil. Em 2025 estava 40,8 ng/mL (ótimo). Coletar avulsa para confirmar status atual. Deficiência de vit D associada a pré-eclâmpsia e DMG.',
    prioridade: 'media',
  },
  {
    titulo: 'HbA1c em tendência leve de alta (5,1 → 5,4)',
    texto: 'Ainda dentro do normal (<5,7%), mas subiu 0,3 pontos em 1 ano. TOTG 75g entre 24-28 sem é especialmente importante. Histórico: 2024 estava em 5,7% (limite pré-DM), normalizou em 2025, agora subindo ligeiramente.',
    prioridade: 'media',
  },
  {
    titulo: '✅ Imunidades confirmadas: rubéola e CMV',
    texto: 'Rubéola IgG 90,5 UI/mL (imune). CMV IgG 147 UA/mL + IgM negativo (infecção passada, imune). Riscos verticais para esses dois agentes reduzidos drasticamente.',
    prioridade: 'baixa',
  },
  {
    titulo: '✅ Tipagem O Rh Positivo — sem necessidade de anti-D',
    texto: 'Coombs indireto negativo, fator Rh positivo. Sem necessidade de imunoglobulina anti-D na 28ª semana nem pós-parto. Risco de DHRN nulo.',
    prioridade: 'baixa',
  },
  {
    titulo: '✅ Plaquetas normalizaram (464k → 396k)',
    texto: 'Trombocitose leve de 2025 era reativa — agora dentro da referência. Não exige mais monitoramento específico.',
    prioridade: 'baixa',
  },
  {
    titulo: '✅ Sem ITU/bacteriúria atual',
    texto: 'Urocultura negativa, urina I normal. Histórico de 2024 sugeria ITU/contaminação. Repetir urocultura a cada trimestre como rotina pré-natal. Se tratar futuramente: evitar nitrofurantoína (Palmer G6PD deficiente).',
    prioridade: 'baixa',
  },
  {
    titulo: '✅ Reservas de ferro/B12 adequadas e em alta',
    texto: 'Ferritina 33,8 → 58,4 ng/mL (↑), ferro 110 → 143 µg/dL (↑), B12 453 pg/mL. Boa base para a expansão de volume sanguíneo do 2º/3º trimestre. Manter Ogestan-Pré ou Regenesis-Pré.',
    prioridade: 'baixa',
  },
  {
    titulo: 'TSH gestacional: bem dentro do alvo',
    texto: 'TSH 0,56 µUI/mL (faixa 1º T: 0,10–3,60). Caiu de 0,96 em 2025 — esperado pela supressão pelo hCG. T4L 1,37 ng/dL normal. Repetir TSH ~12 sem (~junho/2026) para confirmar estabilização pós-pico hCG.',
    prioridade: 'baixa',
  },
]

/**
 * Pre-natal "diagnostic model" — forward-looking risk/protection map for this
 * pregnancy. Updated after 1º T painel (2026-05-06) confirmed several findings.
 */
export const RAFA_PREGNANCY_REPORT = {
  modelo: 'Mapa de risco / proteção gestacional',
  data: '2026-05-10',

  sintese: {
    headline: 'Gestação 1º trimestre — 2 pendências críticas',
    subtitle: 'Hepatite B sem proteção vacinal + suscetibilidade à toxoplasmose. Vit D insuficiente (19 ng/mL — em tratamento). Cobertura do parto resolvida.',
  },

  acoes: [
    { titulo: 'Vacinar Hepatite B (esquema acelerado 0/1/2 ou 0/1/6)', prazo: '2ª consulta', prioridade: 'alta', porque: 'Anti-HBs <2,0 mUI/mL (sem proteção). Vacina segura na gestação (SBIM).' },
    { titulo: 'Prevenção toxoplasmose ativa', prazo: 'contínuo', prioridade: 'alta', porque: 'IgG não reagente — Rafa suscetível. Carne bem passada, hipoclorito em verduras, Palmer cuida da caixa de areia.' },
    { titulo: 'Suplementar Vit D (insuficiência detectada)', prazo: 'em tratamento', prioridade: 'media', porque: '25-OH 19 ng/mL (13/05/2026) — abaixo de 30 ng/mL. Risco de pré-eclâmpsia/DMG. Repetir em ~8-12 semanas.' },
    { titulo: 'TOTG 75g entre 24-28 semanas', prazo: 'ago–set/2026', prioridade: 'media', porque: 'HbA1c em tendência leve de alta (5,1 → 5,4).' },
    { titulo: 'Repetir sorologia toxoplasmose IgG/IgM', prazo: '2º T (ago) e 3º T (nov)', prioridade: 'media', porque: 'Vigilância de seroconversão.' },
  ],

  mudancas: [
    { titulo: 'Cobertura do parto resolvida — segunda cobertura/parto privado contratado', direcao: 'positivo', data: 'mai/2026' },
    { titulo: 'Vit D coletada (13/05) — 19 ng/mL, insuficiência detectada e em tratamento', direcao: 'neutro', data: 'mai/2026' },
    { titulo: 'Tipagem O Rh+ confirmada — sem necessidade de anti-D', direcao: 'positivo', data: 'mai/2026' },
    { titulo: 'Imunidade à rubéola e CMV confirmadas', direcao: 'positivo', data: 'mai/2026' },
    { titulo: 'HIV, HCV, HBV, HTLV, sífilis: todos não reagentes', direcao: 'positivo', data: 'mai/2026' },
    { titulo: 'Plaquetas normalizaram (464k → 396k)', direcao: 'positivo', data: 'mai/2026' },
    { titulo: 'Reservas de ferro e ferritina em alta', direcao: 'positivo', data: 'mai/2026' },
  ],

  camadas: [
    {
      id: 'protecao_atual',
      titulo: 'Proteção atual (confirmada pelo painel 1º T)',
      cor: '#5fa67a',
      achados: [
        'Tipagem O Rh Positivo — sem necessidade de imunoglobulina anti-D na 28ª semana nem pós-parto',
        'Coombs indireto negativo — risco de DHRN nulo',
        'Imunidade à rubéola confirmada (IgG 90,5 UI/mL)',
        'Imunidade ao CMV (IgG 147 UA/mL, IgM negativo — infecção passada)',
        'HIV, HCV, HBV (HBsAg), HTLV e sífilis: todos não reagentes',
        'Tireoide com TSH 0,56 — dentro da faixa gestacional 1º T (anti-TPO/anti-Tg negativos em 2025)',
        'Reservas de ferro (143 µg/dL) e ferritina (58,4 ng/mL) adequadas e crescendo desde 2025',
        'Vitamina B12 453 pg/mL — suficiente. Folato ótimo em 2025; mantido com Ogestan-Pré',
        'Sem ITU/bacteriúria — urocultura negativa, urina I normal',
        'Hemograma e plaquetas normais — trombocitose leve de 2025 normalizou (464k → 396k)',
        'Sem resistência insulínica (HOMA-IR 1,13) e glicemia normal',
      ],
    },
    {
      id: 'acoes_necessarias',
      titulo: 'Ações necessárias (decorrentes do painel)',
      cor: '#b43c3c',
      achados: [
        '⚠️ VACINAÇÃO HEPATITE B: Anti-HBs <2,0 mUI/mL (sem proteção). Discutir esquema acelerado durante gestação na 2ª consulta — Engerix-B 0/1/2 ou 0/1/6 meses (segura SBIM).',
        '⚠️ PREVENÇÃO TOXOPLASMOSE: IgG não reagente — Rafa é suscetível. Carne MUITO bem passada, lavar verduras com hipoclorito, congelar carnes >24h a −12°C, luvas em jardinagem, Palmer cuida da caixa de areia do gato.',
        '⚠️ REPETIR SOROLOGIA TOXOPLASMOSE: IgG/IgM em ~agosto/2026 (2º T) e ~novembro/2026 (3º T).',
        '📋 Coletar VITAMINA D (25-OH) — não veio no painel (autorização Amil pendente). Em 2025 estava 40,8 (ótimo) — confirmar manutenção.',
        '🗓️ TSH reflexo ~12 sem (~junho/2026) — confirmar estabilização pós-pico hCG.',
        '🗓️ TOTG 75g entre 24-28 sem — HbA1c 5,1 → 5,4 reforça a importância do rastreio DMG.',
      ],
    },
    {
      id: 'monitorar',
      titulo: 'Pontos a monitorar',
      cor: '#c47e3a',
      achados: [
        'HbA1c em tendência leve de alta (5,7 em 2024 → 5,1 em 2025 → 5,4 em 2026) — ainda normal, mas TOTG 24-28s essencial',
        'Colesterol total 223 e LDL 143 em 2025 — não re-medido neste painel. Esperar aumento fisiológico na gestação. Reavaliar pós-parto, não tratar com estatina durante.',
        'Histórico de ITU em 2024 — urocultura mensal/trimestral como rotina (atualmente negativa). Se tratar: evitar nitrofurantoína (Palmer G6PD)',
        'Leucocitose leve (10.830) e neutrofilia (8.047) — fisiológicas da gestação, sem desvio à esquerda. Monitorar trajetória, sem ação imediata.',
      ],
    },
    {
      id: 'risco_g6pd',
      titulo: 'G6PD (Palmer portador)',
      cor: '#7a5fa6',
      achados: [
        'Herança X-recessiva — Palmer XᵍY (afetado), Rafa não testada',
        'Cenário esperado (Rafa XX normal): 0% filho afetado, 100% filha portadora obrigatória (assintomática)',
        'Cenário pior (Rafa XᵍX portadora — incomum): 50% filho afetado, 50% filha portadora',
        'Solicitar genotipagem G6PD da Rafa para definir cenário real — não estava no painel 1º T da Dra. Nahara, discutir inclusão',
        'Triagem neonatal SUS (teste do pezinho ampliado) já detecta G6PD no RN',
        'Lista de fármacos a evitar no RN afetado: sulfas, dapsona, nitrofurantoína, primaquina, naftaleno',
      ],
    },
    {
      id: 'cobertura',
      titulo: 'Cobertura assistencial',
      cor: '#b43c3c',
      achados: [
        'Plano: Amil 702 PME · Bronze DF · PRC 609 · vigência ~28/04/2026',
        'Carência obstétrica 300 dias DEFINITIVAMENTE IRREDUCÍVEL (corretor 04/05/2026)',
        'Fim carência ~21/02/2027 vs DPP estimada ~02/01/2027 → gap de ~50 dias',
        'Pré-natal coberto integralmente — painel 1º T pago pela Amil (carência 1 dia exames básicos)',
        'Vitamina D ainda aguardando autorização Amil',
        'USG transvaginal datação agendada para 18/05/2026 (após carência 30d USG)',
        'Plano B mandatório para parto: rede particular Brasília ou HMIB (SUS)',
        'Reserva financeira recomendada: R$ 30-50k mínimo, R$ 80-100k considerando UTI neonatal',
      ],
    },
  ],
}
