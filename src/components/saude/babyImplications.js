/**
 * Cross-couple medical implications for the baby — synthesized from
 * Palmer's + Rafa's exams that have direct or potential impact on the
 * pregnancy or neonate.
 *
 * Each entry: title, source profile, summary, scenarios (when relevant),
 * concrete actions, drugs/triggers to avoid, priority.
 */

export const BABY_IMPLICATIONS = [
  {
    id: 'g6pd-paterno',
    titulo: 'G6PD — Palmer portador',
    origem: 'Palmer · painel laboratorial 2025-05-28 + genético 2024',
    categoria: 'Genético',
    prioridade: 'alta',
    marker_refs: [
      { profile: 'palmer', category: 'especificos', key: 'g6pd' },
    ],
    resumo: 'Palmer tem deficiência de G6PD confirmada (atividade 2.1 U/gHb · Classe III WHO). Herança ligada ao X recessiva — Palmer é XᵍY. Rafa não testada.',
    cenarios: [
      {
        label: 'Cenário esperado · Rafa XX normal',
        probabilidade: '~95%+ (assumindo sem histórico familiar)',
        filho_homem: '0% afetado',
        filha_mulher: '100% portadora obrigatória (geralmente assintomática)',
      },
      {
        label: 'Cenário pior · Rafa XᵍX portadora',
        probabilidade: 'incomum sem histórico',
        filho_homem: '50% afetado',
        filha_mulher: '50% portadora · 50% homozigota afetada',
      },
    ],
    acoes: [
      'Solicitar genotipagem G6PD da Rafa na 1ª consulta pré-natal (~R$ 200 lab privado)',
      'Avisar pediatra/neonatologista no parto sobre histórico paterno',
      'Confirmar inclusão no teste do pezinho ampliado (SUS desde 2014, cobre G6PD)',
      'Monitorar icterícia neonatal mais de perto — G6PD aumenta risco de hiperbilirrubinemia grave',
      'Se filha portadora: aconselhamento genético quando ela própria for ter filhos',
    ],
    evitar: {
      titulo: 'Fármacos a evitar no RN afetado (e na Rafa se for portadora)',
      itens: [
        'Sulfas — Bactrim, sulfadiazina, sulfasalazina',
        'Nitrofurantoína (comum em ITU — usar amoxicilina/cefalexina)',
        'Dapsona',
        'Primaquina · cloroquina (antimaláricos)',
        'Naftaleno (bolinha de cânfora — guardar roupa)',
        'Anilinas em corantes/tinturas',
        'Fava-bean (favas) — risco se ingerido',
      ],
    },
  },

  {
    id: 'pcr-paterna',
    titulo: 'PCR e VHS Palmer normalizaram (abr/2026)',
    origem: 'Palmer · follow-up DASA 2026-04-28',
    categoria: 'Resolvido',
    prioridade: 'baixa',
    marker_refs: [
      { profile: 'palmer', category: 'inflamatorio', key: 'pcr' },
      { profile: 'palmer', category: 'inflamatorio', key: 'vhs' },
    ],
    resumo: 'PCR caiu de 3.24 → 0.25 mg/dL e VHS de 17 → 14 mm/h em ~11 meses. Processo inflamatório sistêmico resolvido entre mai/2025 e abr/2026. Não há mais suspeita ativa de doença autoimune sistêmica que pudesse impactar o neonato. Manejo ortopédico (FAI/CAM) continua mas não é fator de risco gestacional.',
    acoes: [
      'Manter monitoramento periódico de PCR/VHS (semestral)',
      'Foco em manejo ortopédico (fisioterapia, posturologia) — não afeta gestação',
    ],
  },

  {
    id: 'idade-materna',
    titulo: 'Idade materna 35 anos',
    origem: 'Rafa · DOB calc 2026-05',
    categoria: 'Risco gestacional',
    prioridade: 'alta',
    resumo: 'Idade materna ≥35 é classificada como gestação tardia. Risco aumentado de cromossomopatias (T21 ~1:350 vs ~1:1100 em 25a), pré-eclâmpsia, diabetes gestacional, baixo peso. Não impede gestação saudável — exige vigilância adicional.',
    acoes: [
      'USG morfológica 1º trimestre (11–13s+6d) com TN, osso nasal, ducto venoso — janela essencial',
      'Considerar NIPT (teste pré-natal não invasivo) ~10s+ — sangue materno, sensibilidade >99% para T21/T18/T13. ~R$ 1.200–2.500 BR, raramente coberto',
      'Rastreio combinado 1º tri (PAPP-A + β-hCG livre) na USG morfológica',
      'TOTG 24–28s essencial (risco DMG aumentado)',
      'Vigilância pressórica reforçada (PA em toda consulta)',
    ],
  },

  {
    id: 'hba1c-historica',
    titulo: 'HbA1c histórica 5.7% (Rafa, 2024)',
    origem: 'Rafa · hemograma + bioquímica 2024-08-26',
    categoria: 'Risco DMG',
    prioridade: 'media',
    marker_refs: [
      { profile: 'rafa', category: 'glicemico', key: 'hba1c' },
      { profile: 'rafa', category: 'glicemico', key: 'glicose' },
    ],
    resumo: 'Em 2024, HbA1c estava 5.7% (limite pré-DM). Normalizou para 5.1% em 2025. Mas histórico é fator de risco para diabetes gestacional (DMG), que afeta crescimento fetal (macrossomia), hipoglicemia neonatal, parto distócico.',
    acoes: [
      'TOTG 75g 24–28s — não pular nem postergar',
      'Glicemia jejum 1º tri como rastreio inicial',
      'Se DMG diagnosticada: dieta + monitorização glicêmica domiciliar; insulina se dieta insuficiente',
      'Acompanhamento nutricional preventivo desde o 1º trimestre',
    ],
  },

  {
    id: 'itu-historica',
    titulo: 'Histórico de ITU (Rafa, 2024)',
    origem: 'Rafa · urina I 2024-08-26',
    categoria: 'Risco infeccioso',
    prioridade: 'media',
    resumo: 'Urina I de 2024 com leucocitúria, bacteriúria e hemoglobina+ — sugestiva de ITU/contaminação. ITU recorrente é fator independente para parto prematuro e ruptura prematura de membranas.',
    acoes: [
      'Urocultura em TODA consulta pré-natal (não apenas urina I)',
      'Tratar bacteriúria assintomática (>100k UFC) mesmo sem sintomas',
      'Antibiótico de escolha: cefalexina ou amoxicilina (G6PD-safe se filha portadora)',
      'EVITAR nitrofurantoína no 3º trimestre (risco hemólise neonatal) e em qualquer fase se filha for portadora G6PD',
    ],
  },

  {
    id: 'trombocitose-leve',
    titulo: 'Trombocitose leve (Rafa, plaquetas 464k)',
    origem: 'Rafa · hemograma 2025-05-28',
    categoria: 'Hematológico',
    prioridade: 'baixa',
    marker_refs: [
      { profile: 'rafa', category: 'hemograma', key: 'plaquetas' },
    ],
    resumo: 'Plaquetas 464k em maio/2025 (ref <450k). Aumento discreto, geralmente reativo. Importante na gestação porque trombocitose pode mascarar trombocitopenia desenvolvendo (HELLP, púrpura gestacional).',
    acoes: [
      'Repetir hemograma no 1º trimestre confirmado',
      'Hemograma + função hepática a cada trimestre',
      'Vigilância para sinais de HELLP no 3º tri (cefaleia, dor epigástrica, edema súbito)',
    ],
  },

  {
    id: 'reservas-nutricionais',
    titulo: 'Reservas nutricionais Rafa — adequadas',
    origem: 'Rafa · painel pré-gestacional 2025-05-28',
    categoria: 'Proteção',
    prioridade: 'baixa',
    marker_refs: [
      { profile: 'rafa', category: 'micronutrientes', key: 'ferritina' },
      { profile: 'rafa', category: 'micronutrientes', key: 'b12' },
      { profile: 'rafa', category: 'micronutrientes', key: 'folato' },
      { profile: 'rafa', category: 'micronutrientes', key: 'vit_d' },
    ],
    resumo: 'Ferritina 33.8 (ref >30 ideal pré-gest), B12 609, folato 23.6, vitamina D 40.8. Reservas excelentes para iniciar gestação. Reduz risco de defeito de tubo neural e anemia gestacional.',
    acoes: [
      'Manter ácido fólico 5mg/dia até 12 sem (já em curso)',
      'Sulfato ferroso profilático a partir do 2º tri (anemia gestacional fisiológica)',
      'Repetir ferritina + B12 no 3º tri',
      'Vitamina D 1000–2000 UI/dia (manutenção, considerar dose maior em meses de inverno)',
    ],
  },

  {
    id: 'tireoide-rafa',
    titulo: 'TSH adequado para 1º trimestre (Rafa)',
    origem: 'Rafa · tireoide 2025-05-28',
    categoria: 'Endócrino',
    prioridade: 'baixa',
    marker_refs: [
      { profile: 'rafa', category: 'tireoide', key: 'tsh' },
      { profile: 'rafa', category: 'tireoide', key: 't4_livre' },
      { profile: 'rafa', category: 'tireoide', key: 'anti_tpo' },
    ],
    resumo: 'TSH 0.96 µUI/mL — atende meta gestacional 1º tri (<2.5). Anti-TPO e anti-Tg negativos (sem autoimunidade). T4 livre 1.13 (normal). Reduz risco de hipotireoidismo gestacional (impacto em desenvolvimento neurológico fetal).',
    acoes: [
      'Repetir TSH + T4 livre no 1º trimestre confirmado',
      'Meta 1º tri: TSH <2.5 · 2º/3º tri: <3.0',
      'Se subir acima da meta: levotiroxina precoce (tireoide tem demanda 30–50% maior na gestação)',
    ],
  },

  {
    id: 'cobertura-amil',
    titulo: 'Carência obstétrica Amil 300d — RESOLVIDO via Proasa Rafa paralelo',
    origem: 'Áudio corretor Luiz Carvalho 04/05/2026 + Proasa adesão 06/05/2026',
    categoria: 'Cobertura assistencial',
    prioridade: 'media',
    resumo: 'Carência Amil 300d obstétrica permanece intransponível (DPP cai ~50d antes do fim). MAS Rafa reativada na Proasa ADV 300 DF em 06/05/2026 com TODAS as carências aproveitadas → cobertura obstétrica disponível imediatamente via plano paralelo. Risco mitigado. Amil mantém-se como cobertura ambulatorial principal de ambos.',
    acoes: [
      'Honorários Dra. Nahara (parto): R$ 10.000 informado pela médica',
      'Hospital mid-high Brasília (Maternidade Brasília, Anchieta, Santa Luzia): ~R$ 15-22k pacote',
      'Hospital top (DF Star / São Luiz Star): ~R$ 19-25k pacote (ref R$ 19.800 mar/2025)',
      'Reserva mínima recomendada: R$ 35-40k (cenário esperado sem UTI)',
      'Reserva ideal: R$ 50-70k (margem UTI neonatal 3-5 dias × R$ 5-10k/dia)',
      'Alternativa: manter Nova Saúde paralelo ~R$ 2-3k/mês × 8 meses = R$ 16-24k → equivale a cobertura particular E remove risco UTI (R$ 50-100k mitigado)',
      'Pré-cadastro HMIB (Hospital Materno Infantil Brasília) como rede SUS de referência (backup)',
      'Lei 9656/98 cobre apenas emergência obstétrica 24h pós-vigência (intercorrências graves, não parto eletivo)',
      'Detalhes em family/finance/projecao_parto.md',
    ],
  },
  {
    id: 'proasa-rafa-ativo',
    titulo: 'Rafa reativada Proasa ADV 300 DF — carências aproveitadas ✓',
    origem: 'Adesão confirmada 06/05/2026 via Easyplan · family/finance/proposta_proasa_easyplan.md',
    categoria: 'Cobertura assistencial',
    prioridade: 'alta',
    resumo: 'Rafa adesão confirmada Proasa ADV 300 DF (enfermaria, R$ 503,67/mês) com TODAS as carências cumpridas aproveitadas — incluindo internação obstétrica. Upgrade pra ADV 400 DF (apartamento) só viável a partir de outubro/2026. Maternidades particulares Brasília só têm apartamento pra parto, então: (a) sobe pra ADV 400 em outubro (se sem nova carência) → parto em apto coberto, OU (b) fica no ADV 300 e paga upgrade direto ao hospital ~R$ 1.500-4.500.',
    acoes: [
      'IMEDIATO: Salvar em PDF a carta de aproveitamento de carências + contrato/condições gerais ADV 300 DF',
      'Setembro/2026: Pedir Easyplan POR ESCRITO se upgrade ADV 300 → ADV 400 gera nova carência (pela RN 438/2018 não pode, mas confirmar)',
      'Outubro/2026: Efetuar upgrade pra ADV 400 DF se confirmado sem carência adicional',
      'Pré-parto: Confirmar com Maternidade Brasília se aceita ADV 400 e custo exato do upgrade enfermaria→apto (caso fique no 300)',
      'Custo total estimado: R$ 5-6k (cenário ótimo ADV 300→400) ou R$ 6-9k (ficar ADV 300 + upgrade hospital)',
      'Mensalidade conjunta agora: R$ 900 Amil + R$ 503 Proasa Rafa = R$ 1.403/mês (R$ 597 abaixo do que pagavam Nova Saúde anterior R$ 2.000)',
      'Atualizar Pregnancy.notes no Vault com plano paralelo (Amil principal + Proasa ADV 300 Rafa)',
    ],
  },
  {
    id: 'orcamento-parto',
    titulo: 'Orçamento total real — R$ 19-23k (com Proasa) vs R$ 32-39k (só Amil)',
    origem: 'Adesão Proasa 06/05/2026 · family/finance/projecao_parto.md',
    categoria: 'Financeiro',
    prioridade: 'alta',
    resumo: 'Dra. Nahara é particular fora da rede Proasa — honorários (R$ 7k consultas + R$ 10k parto = R$ 17k) são out-of-pocket sempre. Proasa cobre HOSPITAL: internação, sala de parto, equipe plantonista, UTI neonatal eventual. Total realista com Proasa: R$ 19-23k esperado (vs R$ 32-39k só Amil). Economia real R$ 13-16k esperado, R$ 50-66k se UTI necessária.',
    acoes: [
      'Out-of-pocket Dra. Nahara: 14 consultas × R$500 = R$7k + R$10k parto = R$17k total',
      'Plano Proasa cobre: hospital + internação + equipe plantão + UTI neonatal eventual',
      'Mensalidade Proasa Rafa: R$503/mês × 8 meses = R$4k (+ copay R$500-1500)',
      'Upgrade enfermaria→apto no parto (ADV 300): R$1.5-4.5k direto ao hospital — OU subir pra ADV 400 em outubro',
      'Pedir Easyplan/Proasa TABELA DE REEMBOLSO para profissionais fora da rede — pode recuperar R$2-5k dos R$17k Dra. Nahara',
      'Reserva alvo: R$25-30k em conta de liquidez (cobre gap esperado + margem)',
      'UTI neonatal coberta integralmente pela Proasa — R$50-100k de risco mitigado',
      'Detalhes em family/finance/projecao_parto.md + proposta_proasa_easyplan.md',
    ],
  },
  {
    id: 'pedidos-1tri-2026-05-05',
    titulo: '1ª consulta realizada — 14 exames + USG solicitados',
    origem: 'Dra. Nahara A. G. Torres (CRM-DF 18529, Grupo Elas) · 05/05/2026',
    categoria: 'Pré-natal · 1º trimestre',
    prioridade: 'alta',
    resumo: 'Painel laboratorial 1º tri completo (14 exames) + USG transvaginal gestacional. Hoje IG ~5+5. Receituário: Ogestan-Pré 1×/dia + sintomáticos conforme necessidade.',
    acoes: [
      'Agendar TODOS os 14 labs imediatamente — carência exames básicos = 1 dia, já cobertos pela Amil desde 29/04/2026',
      'Lab sugerido: DASA / Lab Exame (Asa Sul) — onde foram feitos os exames anteriores da Rafa',
      'USG transvaginal: 2 opções → (a) particular agora — Doctoralia Brasília tem R$ 80-250 (Dr. Bruno Souza R$80, Êxito Saúde R$80, Dr. Rafael Mendes R$100, Dr. Adervane R$130, Sergio Mattioda/Rangell Guerra R$150, Raquel Meirelles R$250); especialistas top R$ 500-700 (Dra. Tábata Longo R$650). (b) Aguardar 28/05/2026 (Amil libera) → IG estará ~8+6, ainda na janela ideal 6-9 sem',
      'Iniciar Ogestan-Pré ou Regenesis-Pré 1cp/dia hoje (vitamina pré-natal com folato + ferro)',
      'Prescrição sintomáticos: paracetamol/Buscoduo/Simeco/Dramin/Luftal/Tamarine — apenas se necessário',
      'Hidratante corpo (Mustela/Bio Oil) + FPS 60+ desde já',
    ],
  },
  {
    id: 'amil-coberturas-imediatas',
    titulo: 'Cobertura Amil já disponível para pré-natal',
    origem: 'Tabela ANS PRC 609 + áudio corretor 04/05/2026',
    categoria: 'Cobertura assistencial',
    prioridade: 'baixa',
    resumo: 'Apesar do parto não estar coberto, todo o pré-natal está. PRC 609 reduz quase tudo. Para Bronze DF: copay isento em consultas, exames, internação não-obstétrica. Terapias (fisio/fono/nutri/psico/TO) com 40% até R$60/sessão.',
    acoes: [
      'Consultas pré-natal: carência 1 dia · cobertas desde 29/04/2026',
      'Exames laboratoriais básicos: carência 1 dia · cobertos desde 29/04/2026',
      'USG (datação, morfológica, obstétrica): carência 30 dias · libera 28/05/2026',
      'TC/RM/cardio: carência 30 dias · libera 28/05/2026',
      'Internação clínica não-obstétrica: carência 60 dias · libera 27/06/2026',
      'Cirurgia day-hospital não-obstétrica: carência 60 dias · libera 27/06/2026',
      'Hemoterapia: carência 90 dias · libera 27/07/2026',
      'Psicoterapia + Nutrição (suporte gestacional/pós-parto): carência 180 dias · libera 25/10/2026',
      '(Datas exatas estão computadas em PregnancySerializer.carencias e renderizadas no widget de conflitos.)',
    ],
  },

  {
    id: 'tipagem-sanguinea',
    titulo: 'Tipagem sanguínea + Coombs — pendente para ambos',
    origem: 'Não consta nos painéis atuais',
    categoria: 'Compatibilidade',
    prioridade: 'alta',
    resumo: 'Sem tipagem ABO/Rh registrada para Rafa nem Palmer nos exames atuais. Crítico para definir risco de doença hemolítica perinatal — se Rafa for Rh- e Palmer Rh+, indica imunoglobulina anti-D na 28ª semana e pós-parto.',
    acoes: [
      'Solicitar tipagem ABO + Rh + Coombs indireto na 1ª consulta pré-natal de Rafa',
      'Solicitar tipagem ABO + Rh do Palmer (já deve constar em exames pré-operatórios antigos)',
      'Se Rafa Rh- e Palmer Rh+: imunoglobulina anti-D 300mcg na 28s + pós-parto (até 72h)',
      'Coombs indireto repetir 28s independente de tipagem',
    ],
  },

  {
    id: 'vacinacao-mae',
    titulo: 'Vacinação materna — proteção neonatal indireta',
    origem: 'Calendário MS gestante',
    categoria: 'Imunização',
    prioridade: 'alta',
    resumo: 'Vacinas maternas durante gestação criam imunidade passiva no neonato (anticorpos via placenta) — proteção crítica nos primeiros meses antes do bebê iniciar próprio calendário vacinal.',
    acoes: [
      'dTpa (coqueluche) — 27–36s · idealmente 28s · cada gestação · CRÍTICA para proteção neonatal contra coqueluche',
      'Influenza — qualquer trimestre durante campanha (abril–maio BR)',
      'COVID-19 — conforme calendário vigente, segura em qualquer trimestre',
      'Hepatite B — 3 doses se não vacinada previamente, qualquer trimestre',
      'EVITAR: tríplice viral (SCR), varicela, febre amarela durante gestação (vivas atenuadas)',
    ],
  },

  {
    id: 'exposicoes-ambientais',
    titulo: 'Exposições ambientais a evitar',
    origem: 'Diretrizes ACOG + MS',
    categoria: 'Prevenção',
    prioridade: 'media',
    resumo: 'Itens domésticos comuns que devem ser evitados ou minimizados durante a gestação.',
    acoes: [
      'Naftaleno (bolinha de cânfora) — proibido por causa do G6PD paterno + risco fetal genérico. Substituir por alternativas naturais (cravo, lavanda)',
      'Tintura de cabelo — evitar 1º tri; após 2º tri preferir vegetal sem amônia',
      'Carne crua/mal passada + leite não pasteurizado — risco toxoplasmose/listeria',
      'Gato sem vermifugação atualizada — limpar caixa de areia com luvas (toxoplasma)',
      'Álcool — abstinência total recomendada',
      'Cafeína — limitar a 200mg/dia (~1 espresso ou 2 cafés filtrados)',
      'Atum/peixe-espada e peixes grandes — limitar (mercúrio); priorizar salmão, sardinha',
    ],
  },
]

export const PRIORIDADE_LABEL = {
  alta: 'alta prioridade',
  media: 'média prioridade',
  baixa: 'baixa prioridade',
}
