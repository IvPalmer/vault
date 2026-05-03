/**
 * Rafa's clinical reference data, sourced from:
 *   - Hemograma + painel consolidado 2025-05-28 (DASA / Lab Exame)
 *   - Hemograma + glicemia + lipídios 2024-08-26 (Lapac/DB)
 *   - Vit D / D-dímero / Lp(a) 2025-05-28 (DASA)
 */

export const RAFA_LAB_PANEL = {
  data_coleta: '2025-05-28',
  laboratorio: 'DASA · Laboratório Exame',
  contexto: 'Painel pré-gestacional completo — solicitante Dr. Bruno Bezerra Silva',
  idade_coleta: 34,

  categorias: [
    {
      id: 'hemograma',
      nome: 'Hemograma',
      markers: [
        { key: 'hemacias', label: 'Hemácias', value: 4.59, unit: 'milhões/µL', ref_min: 3.8, ref_max: 4.8, status: 'normal' },
        { key: 'hemoglobina', label: 'Hemoglobina', value: 14.6, unit: 'g/dL', ref_min: 12.0, ref_max: 15.0, status: 'normal' },
        { key: 'hematocrito', label: 'Hematócrito', value: 42.8, unit: '%', ref_min: 36.0, ref_max: 46.0, status: 'normal' },
        { key: 'vcm', label: 'VCM', value: 93.3, unit: 'fL', ref_min: 83.0, ref_max: 101.0, status: 'normal' },
        { key: 'hcm', label: 'HCM', value: 31.8, unit: 'pg', ref_min: 27.0, ref_max: 32.0, status: 'normal' },
        { key: 'chcm', label: 'CHCM', value: 34.1, unit: 'g/dL', ref_min: 31.0, ref_max: 35.0, status: 'normal' },
        { key: 'rdw', label: 'RDW', value: 13.0, unit: '%', ref_min: 11.6, ref_max: 14.0, status: 'normal' },
        { key: 'leucocitos', label: 'Leucócitos', value: 7470, unit: '/µL', ref_min: 4000, ref_max: 10000, status: 'normal' },
        { key: 'linfocitos', label: 'Linfócitos', value: 30.6, unit: '%', ref_min: 20, ref_max: 40, status: 'normal' },
        { key: 'monocitos', label: 'Monócitos', value: 7.9, unit: '%', ref_min: 2.0, ref_max: 10.0, status: 'normal' },
        { key: 'eosinofilos', label: 'Eosinófilos', value: 3.0, unit: '%', ref_min: 1.0, ref_max: 6.0, status: 'normal' },
        { key: 'basofilos', label: 'Basófilos', value: 0.6, unit: '%', ref_min: 0, ref_max: 2.0, status: 'normal' },
        { key: 'plaquetas', label: 'Plaquetas', value: 464000, unit: '/µL', ref_min: 150000, ref_max: 450000, status: 'alto',
          obs: 'Trombocitose leve (acima de 450k). Geralmente reativa — monitorar na gestação.' },
        { key: 'vpm', label: 'VPM', value: 9.7, unit: 'fL', ref_min: 9.2, ref_max: 12.8, status: 'normal' },
      ],
    },
    {
      id: 'glicemia',
      nome: 'Metabolismo glicêmico',
      markers: [
        { key: 'glicose', label: 'Glicemia jejum', value: 81, unit: 'mg/dL', ref_min: 70, ref_max: 99, status: 'normal' },
        { key: 'hba1c', label: 'HbA1c', value: 5.1, unit: '%', ref_max: 5.7, status: 'normal',
          obs: '2024 estava 5.7% (limite pré-DM). Normalizou em 2025.' },
        { key: 'insulina', label: 'Insulina', value: 5.3, unit: 'µUI/mL', ref_min: 2.5, ref_max: 13.1, status: 'normal' },
        { key: 'homa_ir', label: 'HOMA-IR', value: 1.06, unit: '', ref_max: 2.7, status: 'normal' },
      ],
    },
    {
      id: 'lipidios',
      nome: 'Perfil lipídico',
      markers: [
        { key: 'colesterol_total', label: 'Colesterol total', value: 223, unit: 'mg/dL', ref_max: 190, status: 'alto',
          obs: 'Limítrofe alto. Aumento fisiológico esperado durante gestação (placenta).' },
        { key: 'hdl', label: 'HDL', value: 62, unit: 'mg/dL', ref_min: 40, status: 'normal' },
        { key: 'ldl', label: 'LDL', value: 143, unit: 'mg/dL', ref_max: 130, status: 'limite_superior' },
        { key: 'trigliceres', label: 'Triglicérides', value: 74, unit: 'mg/dL', ref_max: 150, status: 'normal' },
        { key: 'vldl', label: 'VLDL', value: 18, unit: 'mg/dL', status: 'normal' },
        { key: 'apo_a', label: 'Apo A', value: 162, unit: 'mg/dL', ref_min: 108, ref_max: 225, status: 'normal' },
        { key: 'apo_b', label: 'Apo B', value: 103, unit: 'mg/dL', ref_min: 60, ref_max: 117, status: 'normal' },
        { key: 'lp_a', label: 'Lipoproteína(a)', value: 29.7, unit: 'nmol/L', ref_max: 75, status: 'normal',
          obs: 'Risco cardiovascular adicional — bom estar baixo' },
      ],
    },
    {
      id: 'tireoide',
      nome: 'Função tireoide',
      markers: [
        { key: 'tsh', label: 'TSH ultrassensível', value: 0.96, unit: 'µUI/mL', ref_min: 0.40, ref_max: 4.30, status: 'normal',
          obs: 'Janela TSH gestacional 1º tri ideal: <2.5 — atual está adequado' },
        { key: 't4_livre', label: 'T4 livre', value: 1.13, unit: 'ng/dL', ref_min: 0.93, ref_max: 1.70, status: 'normal' },
        { key: 'anti_tpo', label: 'Anti-TPO', value: 11.1, unit: 'UI/mL', ref_max: 35, status: 'normal' },
        { key: 'anti_tg', label: 'Anti-tireoglobulina', value: 17.6, unit: 'UI/mL', ref_max: 115, status: 'normal' },
      ],
    },
    {
      id: 'hormonios_sexuais',
      nome: 'Hormônios sexuais (pré-gestacional)',
      markers: [
        { key: 'estradiol', label: 'Estradiol', value: 261, unit: 'pg/mL', status: 'normal',
          obs: 'Depende fase ciclo — coleta sem fase informada' },
        { key: 'fsh', label: 'FSH', value: 5.4, unit: 'mUI/mL', status: 'normal' },
        { key: 'prolactina', label: 'Prolactina', value: 13.2, unit: 'ng/mL', ref_min: 4.8, ref_max: 23.3, status: 'normal' },
        { key: 'testo_total', label: 'Testosterona total', value: 28.3, unit: 'ng/dL', status: 'normal' },
        { key: 'testo_livre', label: 'Testosterona livre', value: 0.18, unit: 'ng/dL', status: 'normal' },
        { key: 'testo_biod', label: 'Testosterona biodisponível', value: 4.32, unit: 'ng/dL', status: 'normal' },
        { key: 'dht', label: 'DHT', value: 69.4, unit: 'pg/mL', status: 'normal' },
      ],
    },
    {
      id: 'cortisol',
      nome: 'Eixo adrenal',
      markers: [
        { key: 'cortisol_am', label: 'Cortisol matinal', value: 8.0, unit: 'µg/dL', ref_min: 6.2, ref_max: 18.0, status: 'normal' },
      ],
    },
    {
      id: 'renal',
      nome: 'Função renal e eletrólitos',
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
      nome: 'Função hepática',
      markers: [
        { key: 'tgo', label: 'TGO/AST', value: 20, unit: 'U/L', ref_max: 32, status: 'normal' },
        { key: 'tgp', label: 'TGP/ALT', value: 21, unit: 'U/L', ref_max: 33, status: 'normal' },
        { key: 'ggt', label: 'Gama-GT', value: 13, unit: 'U/L', ref_max: 40, status: 'normal' },
        { key: 'fa', label: 'Fosfatase alcalina', value: 43, unit: 'U/L', ref_min: 35, ref_max: 105, status: 'normal' },
        { key: 'bili_total', label: 'Bilirrubina total', value: 0.30, unit: 'mg/dL', ref_max: 1.20, status: 'normal' },
        { key: 'bili_direta', label: 'Bilirrubina direta', value: 0.10, unit: 'mg/dL', ref_max: 0.30, status: 'normal' },
        { key: 'bili_indireta', label: 'Bilirrubina indireta', value: 0.20, unit: 'mg/dL', ref_min: 0.10, ref_max: 1.00, status: 'normal' },
        { key: 'ptn_total', label: 'Proteínas totais', value: 7.9, unit: 'g/dL', ref_min: 6.4, ref_max: 8.3, status: 'normal' },
        { key: 'albumina', label: 'Albumina', value: 5.1, unit: 'g/dL', ref_min: 3.5, ref_max: 5.2, status: 'normal' },
      ],
    },
    {
      id: 'micronutrientes',
      nome: 'Ferro / vitaminas (pré-natal)',
      markers: [
        { key: 'ferro', label: 'Ferro sérico', value: 110, unit: 'µg/dL', ref_min: 33, ref_max: 193, status: 'normal' },
        { key: 'ferritina', label: 'Ferritina', value: 33.8, unit: 'ng/mL', ref_min: 13, ref_max: 150, status: 'normal',
          obs: 'Ideal pré-gestacional > 30. Reservas adequadas.' },
        { key: 'transferrina', label: 'Transferrina', value: 286, unit: 'mg/dL', ref_min: 200, ref_max: 360, status: 'normal' },
        { key: 'b12', label: 'Vitamina B-12', value: 609, unit: 'pg/mL', ref_min: 245, ref_max: 985, status: 'normal' },
        { key: 'folato', label: 'Ácido fólico', value: 23.6, unit: 'ng/mL', ref_min: 5.38, status: 'normal',
          obs: 'Crítico na gestação para tubo neural — níveis ótimos.' },
        { key: 'homocisteina', label: 'Homocisteína', value: 5.53, unit: 'µmol/L', ref_min: 4.44, ref_max: 13.56, status: 'normal' },
        { key: 'vit_d', label: '25-OH Vitamina D', value: 40.8, unit: 'ng/mL', ref_min: 30, ref_max: 60, status: 'normal' },
      ],
    },
    {
      id: 'coagulacao',
      nome: 'Coagulação',
      markers: [
        { key: 'd_dimero', label: 'D-dímero', value: 220, unit: 'ng/mL FEU', ref_max: 500, status: 'normal',
          obs: 'Aumenta fisiologicamente na gestação — basal pré-gestacional.' },
      ],
    },
  ],
}

export const RAFA_OBSERVATIONS = [
  {
    titulo: 'Trombocitose leve (plaquetas 464k)',
    texto: 'Acima de 450k em maio/2025. Geralmente reativa (estresse, inflamação leve, exercício). Repetir hemograma no 1º trimestre. Investigar se persistir ou aumentar.',
    prioridade: 'media',
  },
  {
    titulo: 'Dislipidemia limítrofe pré-gestacional',
    texto: 'Colesterol total 223 e LDL 143 acima do ideal antes da gestação. Aumento fisiológico esperado durante gravidez (placenta usa colesterol). Reavaliar no pós-parto — não tratar com estatina durante gestação.',
    prioridade: 'baixa',
  },
  {
    titulo: 'Reservas de ferro/B12/folato adequadas',
    texto: 'Ferritina 33.8, B12 609, folato 23.6, vitamina D 40.8 — todos em níveis ótimos para iniciar a gestação. Manter suplementação multivitamínica + ácido fólico 5mg/dia até 12 sem (já em curso).',
    prioridade: 'baixa',
  },
  {
    titulo: 'TSH adequado para 1º trimestre',
    texto: 'TSH 0.96 atende meta gestacional do 1º tri (<2.5 µUI/mL). Repetir no 1º trimestre confirmado e ajustar se necessário (anti-TPO negativo é tranquilizador).',
    prioridade: 'baixa',
  },
  {
    titulo: 'Histórico ITU 2024',
    texto: 'Urina I de 2024 sugestiva de ITU/contaminação (hemoglobina+, leucocitúria, bacteriúria). ITU recorrente é fator de risco para parto prematuro — solicitar urocultura em toda consulta pré-natal.',
    prioridade: 'media',
  },
  {
    titulo: 'HbA1c 5.7% em 2024 → 5.1% em 2025',
    texto: 'Em 2024 estava no limite de pré-DM (5.7%). Normalizou em 2025. Mas há histórico — TOTG 24-28s é especialmente importante para investigar diabetes gestacional.',
    prioridade: 'media',
  },
]

/**
 * Pre-natal "diagnostic model" — not a clinical 5-layer like Palmer's hip case,
 * but a forward-looking risk/protection map for this pregnancy.
 */
export const RAFA_PREGNANCY_REPORT = {
  modelo: 'Mapa de risco / proteção gestacional',
  data: '2026-05-02',

  camadas: [
    {
      id: 'protecao_atual',
      titulo: 'Proteção atual',
      cor: '#5fa67a',
      achados: [
        'Reservas de ferro, B12, folato e vitamina D em níveis ótimos',
        'TSH adequado para 1º trimestre (<2.5)',
        'Tireoide sem autoimunidade (anti-TPO e anti-Tg negativos)',
        'Função renal e hepática normais',
        'Anti-TPO negativo — risco baixo de hipotireoidismo gestacional',
      ],
    },
    {
      id: 'monitorar',
      titulo: 'Pontos a monitorar',
      cor: '#c47e3a',
      achados: [
        'Plaquetas 464k em maio/2025 — repetir no 1º trimestre',
        'Histórico HbA1c 5.7% em 2024 — TOTG 24-28s essencial',
        'Histórico de ITU em 2024 — urocultura mensal',
        'Colesterol limítrofe — monitorar mas não tratar na gestação',
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
        'Solicitar genotipagem G6PD da Rafa para definir cenário real',
        'Triagem neonatal SUS (teste do pezinho ampliado) já detecta G6PD no RN',
        'Lista de fármacos a evitar no RN afetado: sulfas, dapsona, nitrofurantoína, primaquina, naftaleno',
      ],
    },
    {
      id: 'cobertura',
      titulo: 'Cobertura assistencial',
      cor: '#b43c3c',
      achados: [
        'Carência obstétrica Amil 702 PME (PRC 609): 300 dias',
        'DPP estimada cai antes do fim da carência',
        'Plano B documentado em family/pregnancy/alerta_carencia.md',
        'Negociação ativa com corretor para redução obstétrica',
      ],
    },
  ],
}
