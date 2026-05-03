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
    titulo: 'PCR cronicamente elevada — Palmer',
    origem: 'Palmer · painel laboratorial 2025-05-28',
    categoria: 'Investigação parental',
    prioridade: 'media',
    resumo: 'PCR ultrassensível 3.24 mg/dL (ref <0.5) — 23× o basal de 2019. VHS 17 (ref <8). Investigação reumatológica em curso. Não afeta diretamente o feto, mas se for doença autoimune sistêmica subjacente (espondiloartrite, artrite reativa), pode haver implicações no parto e no neonato.',
    acoes: [
      'Concluir investigação (HLA-B27, FAN, fator reumatoide) antes do parto',
      'Compartilhar resultados com obstetra — ajustar conduta se diagnóstico autoimune',
      'Revisar medicações pós-diagnóstico para compatibilidade com lactação',
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
    resumo: 'TSH 0.96 µUI/mL — atende meta gestacional 1º tri (<2.5). Anti-TPO e anti-Tg negativos (sem autoimunidade). T4 livre 1.13 (normal). Reduz risco de hipotireoidismo gestacional (impacto em desenvolvimento neurológico fetal).',
    acoes: [
      'Repetir TSH + T4 livre no 1º trimestre confirmado',
      'Meta 1º tri: TSH <2.5 · 2º/3º tri: <3.0',
      'Se subir acima da meta: levotiroxina precoce (tireoide tem demanda 30–50% maior na gestação)',
    ],
  },

  {
    id: 'cobertura-amil',
    titulo: 'Carência obstétrica Amil 702 PME · 300 dias',
    origem: 'Contrato Amil + corretor (PRC 609)',
    categoria: 'Cobertura assistencial',
    prioridade: 'alta',
    resumo: 'Vigência iniciou ~28/04/2026. Carência obstétrica de 300 dias termina ~21/02/2027. DPP estimada ~02/01/2027 — parto cai ~50 dias antes do fim da carência.',
    acoes: [
      'Negociação ativa com corretor para redução obstétrica (cláusula 7.4 do contrato)',
      'Plano B documentado em family/pregnancy/alerta_carencia.md',
      'Reserva financeira mínima R$ 30–50k (ideal R$ 80–100k considerando UTI neonatal)',
      'Pré-cadastro HMIB (Hospital Materno Infantil Brasília) como rede SUS de referência',
      'Lei 9656/98 cobre emergência obstétrica 24h pós-vigência (intercorrências, não parto eletivo)',
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
