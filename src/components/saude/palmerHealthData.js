/**
 * Palmer's clinical reference data, sourced from the standalone painel
 * (PAINEL_FINAL_CONSOLIDADO.html) generated 2025-09-XX.
 *
 * Until we move all of this into HealthExam.valores JSON via seed_health,
 * the dashboard reads from this file. After full migration to DB, this
 * becomes a fallback or seed source only.
 */

export const PALMER_LAB_PANEL = {
  data_coleta: '2025-05-28',  // most-recent panel
  laboratorio: 'Sabin Brasília',
  contexto: 'Painel pré-investigação ortopédica/sistêmica',

  categorias: [
    {
      id: 'hormonios_sexuais',
      nome: 'Hormônios sexuais',
      markers: [
        { key: 'testo_total', label: 'Testosterona total', value: 541, unit: 'ng/dL', ref_min: 264, ref_max: 916, status: 'normal' },
        { key: 'testo_livre', label: 'Testosterona livre', value: 12.92, unit: 'pg/mL', ref_min: 8.7, ref_max: 25.1, status: 'normal' },
        { key: 'shbg', label: 'SHBG', value: 26.70, unit: 'nmol/L', ref_min: 24.4, ref_max: 122.0, status: 'limite_inferior',
          obs: 'Próximo ao limite inferior — biodisponibilidade adequada' },
      ],
    },
    {
      id: 'tireoide',
      nome: 'Função tireoide',
      markers: [
        { key: 'tsh', label: 'TSH', value: 2.02, unit: 'mIU/L', ref_min: 0.40, ref_max: 4.00, status: 'normal' },
        { key: 't4_livre', label: 'T4 livre', value: 1.00, unit: 'ng/dL', ref_min: 0.93, ref_max: 1.70, status: 'normal' },
        { key: 'anti_tpo', label: 'Anti-TPO', value: 11.0, unit: 'UI/mL', ref_max: 35, status: 'normal' },
      ],
    },
    {
      id: 'cortisol',
      nome: 'Eixo adrenal',
      markers: [
        { key: 'cortisol_am', label: 'Cortisol matinal', value: 5.0, unit: 'µg/dL', ref_min: 6.2, ref_max: 18.0, status: 'baixo',
          obs: 'Baixo — investigar fadiga adrenal/insuficiência. Repetir em jejum, 8h da manhã.' },
      ],
    },
    {
      id: 'glicemia',
      nome: 'Metabolismo glicêmico',
      markers: [
        { key: 'glicose', label: 'Glicemia jejum', value: 86, unit: 'mg/dL', ref_min: 70, ref_max: 100, status: 'normal' },
        { key: 'hba1c', label: 'HbA1c', value: 4.8, unit: '%', ref_max: 5.7, status: 'normal' },
        { key: 'homa_ir', label: 'HOMA-IR', value: 1.65, unit: '', ref_max: 2.0, status: 'normal' },
      ],
    },
    {
      id: 'lipidios',
      nome: 'Perfil lipídico',
      markers: [
        { key: 'colesterol_total', label: 'Colesterol total', value: 247, unit: 'mg/dL', ref_max: 190, status: 'alto' },
        { key: 'ldl', label: 'LDL', value: 176, unit: 'mg/dL', ref_max: 130, status: 'alto' },
        { key: 'apo_b', label: 'Apo B', value: 135, unit: 'mg/dL', ref_min: 66, ref_max: 133, status: 'alto',
          obs: 'Marcador mais preciso de risco cardiovascular que LDL isolado' },
        { key: 'fibrinogenio', label: 'Fibrinogênio', value: 380, unit: 'mg/dL', ref_min: 200, ref_max: 400, status: 'limite_superior' },
      ],
    },
    {
      id: 'hemograma',
      nome: 'Hemograma',
      markers: [
        { key: 'hemoglobina', label: 'Hemoglobina', value: 15.7, unit: 'g/dL', ref_min: 12.0, ref_max: 16.0, status: 'normal' },
        { key: 'hematocrito', label: 'Hematócrito', value: 46.3, unit: '%', ref_min: 36, ref_max: 46, status: 'limite_superior' },
        { key: 'leucocitos', label: 'Leucócitos', value: 6020, unit: '/µL', ref_min: 4500, ref_max: 11000, status: 'normal' },
        { key: 'plaquetas', label: 'Plaquetas', value: 262000, unit: '/µL', ref_min: 150000, ref_max: 400000, status: 'normal' },
      ],
    },
    {
      id: 'renal',
      nome: 'Função renal',
      markers: [
        { key: 'creatinina', label: 'Creatinina', value: 1.07, unit: 'mg/dL', ref_min: 0.6, ref_max: 1.2, status: 'normal' },
        { key: 'egfr', label: 'eGFR', value: 90, unit: 'mL/min/1.73m²', ref_min: 90, status: 'normal',
          obs: '>90 mL/min/1.73m² — função preservada' },
        { key: 'ureia', label: 'Uréia', value: 34, unit: 'mg/dL', ref_min: 15, ref_max: 45, status: 'normal' },
      ],
    },
    {
      id: 'hepatica',
      nome: 'Função hepática',
      markers: [
        { key: 'tgo', label: 'TGO/AST', value: 29, unit: 'U/L', ref_max: 33, status: 'normal' },
        { key: 'tgp', label: 'TGP/ALT', value: 26, unit: 'U/L', ref_max: 32, status: 'normal' },
        { key: 'ggt', label: 'GGT', value: 19, unit: 'U/L', ref_max: 55, status: 'normal' },
        { key: 'fa', label: 'Fosfatase alcalina', value: 96, unit: 'U/L', ref_min: 30, ref_max: 120, status: 'normal' },
      ],
    },
    {
      id: 'coagulacao',
      nome: 'Coagulação',
      markers: [
        { key: 'tp', label: 'TP', value: 12.7, unit: 's', ref_min: 11, ref_max: 13.5, status: 'normal' },
        { key: 'inr', label: 'INR', value: 1.00, unit: '', ref_min: 0.80, ref_max: 1.10, status: 'normal' },
        { key: 'ttpa', label: 'TTPA', value: 37.7, unit: 's', ref_min: 24, ref_max: 36, status: 'limite_superior',
          obs: 'Levemente elevado — repetir e investigar se persistir' },
        { key: 'd_dimero', label: 'D-dímero', value: 120, unit: 'ng/mL', ref_max: 250, status: 'normal' },
      ],
    },
    {
      id: 'inflamatorio',
      nome: 'Marcadores inflamatórios',
      markers: [
        { key: 'pcr', label: 'PCR ultrassensível', value: 3.24, unit: 'mg/dL', ref_max: 0.5, status: 'alto',
          obs: 'Aumento de 23× vs basal de 2019 (0.14). Investigação inflamatória/quadril.' },
        { key: 'vhs', label: 'VHS', value: 17, unit: 'mm/h', ref_max: 8, status: 'alto' },
      ],
    },
    {
      id: 'especificos',
      nome: 'Marcadores específicos',
      markers: [
        { key: 'g6pd', label: 'G6PD (atividade)', value: 2.1, unit: 'U/gHb', ref_min: 2.2, status: 'baixo',
          obs: 'Deficiência confirmada — Classe III (WHO). Padrão X-recessivo. Evitar gatilhos hemolíticos.' },
        { key: 'vitamina_d', label: '25-OH Vitamina D', value: 36.6, unit: 'ng/mL', ref_min: 30, ref_max: 100, status: 'normal' },
      ],
    },
  ],
}

export const PALMER_HIP_IMAGING = {
  data: '2025-09-12',
  modalidade: 'Tomografia computadorizada de quadris',
  achado_principal: 'Morfologia tipo CAM bilateral com α-angle elevado e LCEA reduzido bilateralmente. Entesopatia AIIS esquerda. Atrofia de glúteo mínimo esquerdo. Varicocele crônica E.',

  measurements: [
    {
      categoria: 'Asfericidade femoral',
      ref_text: '<10% considerado normal',
      esquerdo: 19.4,
      direito: 16.8,
      unit: '%',
      status: 'alto_bilateral',
      esquerdo_status: 'alto',
      direito_status: 'alto',
    },
    {
      categoria: 'Pontos de deformidade >2mm',
      ref_text: '<5% considerado normal',
      esquerdo: 11.5,
      direito: 10.0,
      unit: '%',
      status: 'alto_bilateral',
      esquerdo_status: 'alto',
      direito_status: 'alto',
    },
    {
      categoria: 'Protrusão acetabular',
      ref_text: '<2-3mm normal',
      esquerdo: 4.6,
      direito: 4.0,
      unit: 'mm',
      status: 'alto_bilateral',
      esquerdo_status: 'alto',
      direito_status: 'alto',
    },
    {
      categoria: 'LCEA (Lateral Center-Edge Angle)',
      ref_text: '25–40° normal · <25° displásico',
      esquerdo: 19.3,
      direito: 15.7,
      unit: '°',
      status: 'baixo_bilateral',
      esquerdo_status: 'baixo',
      direito_status: 'baixo',
    },
    {
      categoria: 'α-angle lateral (CAM)',
      ref_text: '<55° normal',
      esquerdo: 68,
      direito: null,
      unit: '°',
      status: 'alto',
      esquerdo_status: 'alto',
    },
  ],
}

export const PALMER_DENSITOMETRIA = {
  data: '2024-08-14',
  bmd: 1.321,
  bmd_unit: 'g/cm²',
  t_score: 1.2,
  z_score: null,
  gordura_corporal_pct: 30.0,
  massa_magra_apendicular: 7.97,
  massa_magra_apendicular_unit: 'kg/m²',
  status: 'normal',
}

export const PALMER_CLINICAL_REPORT = {
  modelo: 'Diagnóstico em 5 camadas',
  data: '2025-09-15',

  camadas: [
    {
      id: 'estrutural',
      titulo: 'Estrutural',
      icone: '🦴',
      cor: '#7a5fa6',
      achados: [
        'CAM-type FAI (Femoroacetabular Impingement) bilateral',
        'α-angle 68° lateral (E) — pinçamento femoral',
        'LCEA 19.3°/15.7° (E/D) — instabilidade acetabular',
        'Protrusão acetabular bilateral (4.6 mm E, 4.0 mm D)',
        'Asfericidade femoral elevada bilateral',
      ],
    },
    {
      id: 'tecido_mole',
      titulo: 'Tecido mole',
      icone: '💪',
      cor: '#c47e3a',
      achados: [
        'Atrofia de glúteo mínimo esquerdo',
        'Edema na espinha ilíaca antero-inferior (EIAI/AIIS) E',
        'Entesopatia da AIIS esquerda',
        'Varicocele esquerda crônica (desde adolescência)',
      ],
    },
    {
      id: 'inflamatorio',
      titulo: 'Inflamatório',
      icone: '🔥',
      cor: '#b43c3c',
      achados: [
        'PCR ultrassensível 3.24 mg/dL (ref <0.5) — 23× basal de 2019',
        'VHS 17 mm/h (ref <8)',
        'Padrão sugestivo de processo inflamatório crônico de baixo grau',
        'Investigar artrite reativa, espondiloartrite, doença sistêmica',
      ],
    },
    {
      id: 'neuropatico',
      titulo: 'Neuropático',
      icone: '⚡',
      cor: '#5b8bc4',
      achados: [
        'Avaliação especializada em curso',
        'Possível componente neuropático na dor crônica',
        'Necessária eletroneuromiografia se persistir',
      ],
    },
    {
      id: 'sensibilizacao_central',
      titulo: 'Sensibilização central',
      icone: '🧠',
      cor: '#5fa67a',
      achados: [
        'Comorbidades em investigação',
        'Padrão de dor crônica sugere envolvimento do SNC',
        'Avaliar com escalas (Central Sensitization Inventory)',
      ],
    },
  ],
}

export const PALMER_OBSERVATIONS = [
  {
    titulo: 'Cortisol matinal baixo',
    texto: 'Cortisol 5.0 µg/dL abaixo da referência (6.2–18.0). Repetir coleta em jejum estrito às 8h. Se confirmado, investigar insuficiência adrenal — relação com fadiga crônica relatada.',
    prioridade: 'alta',
  },
  {
    titulo: 'Dislipidemia a tratar',
    texto: 'LDL 176 e Apo B 135 acima do alvo. Indicado intervenção dietética + reavaliação 3 meses. Se persistir, considerar estatina. Risco cardiovascular adicional pela G6PD (estatinas geralmente seguras, evitar nitrofuranos/sulfas em outras situações).',
    prioridade: 'media',
  },
  {
    titulo: 'PCR cronicamente elevada',
    texto: 'Aumento de 23× vs basal 2019. Investigação reumatológica em andamento. HLA-B27, FAN, fator reumatoide indicados se ainda não feitos.',
    prioridade: 'alta',
  },
  {
    titulo: 'G6PD — gravidez Rafa',
    texto: 'Padrão X-recessivo: se feto masculino, 50% chance de afetado. Aconselhamento genético + avaliação de teste pré-natal não invasivo. Fármacos a evitar no neonato: sulfas, nitrofurantoína, primaquina, dapsona, naftaleno.',
    prioridade: 'alta',
  },
  {
    titulo: 'TTPA levemente elevado',
    texto: 'TTPA 37.7s (ref 24–36). Repetir e considerar painel de coagulação completo (fator VIII, IX, anticoagulante lúpico) se persistir.',
    prioridade: 'baixa',
  },
]
