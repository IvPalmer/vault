/**
 * Mapa do Enxoval — evidence-based layette + maternity-bag + paperwork map.
 *
 * Content grounded on:
 *   - SBP Nota de Alerta "Recomendações AAP sono seguro" (berço, SIDS)
 *   - Ministério da Saúde — Caderneta da Gestante (mala, documentos)
 *   - NHS "What to buy for your newborn baby" (quantidades de roupa)
 *   - ANS / Lei 9.656/98 art. 12 — inclusão do RN no plano em 30 dias
 *   - Resolução CONTRAN 819/2021 — bebê conforto obrigatório
 *   - ANOREG — registro civil de nascimento (prazos)
 *
 * Each category:
 *   - id, title, icon
 *   - buyWindow: [startWeek, endWeek] gestational weeks when this should be
 *     bought/done; null = pós-parto (deadline-driven, see item notes)
 *   - items: { id, label, qty?, note?, critical?, group? }
 *   - avoid: informational "do NOT buy/use" list (não marcável)
 *   - sourceIds: keys into SOURCES
 *
 * Check-state is NOT here — it lives in a FamilyNote (shared between the two
 * profiles) managed by EnxovalView.
 */

export const SOURCES = {
  'sbp-sono': {
    label: 'SBP — Nota de Alerta: sono seguro (recomendações AAP)',
    url: 'https://www.sbp.com.br/fileadmin/user_upload/23990b-NotaAlerta-Recomend_AAP_SonoSeguro_1ano.pdf',
  },
  'ms-caderneta': {
    label: 'Ministério da Saúde — Caderneta da Gestante',
    url: 'https://bvsms.saude.gov.br/bvs/publicacoes/caderneta_gestante_4ed.pdf',
  },
  'nhs-buy': {
    label: 'NHS — What to buy for your newborn baby',
    url: 'https://www.nhs.uk/best-start-in-life/pregnancy/preparing-for-labour-and-birth/what-to-buy-for-your-newborn-baby/',
  },
  'ans-rn': {
    label: 'Lei 9.656/98 art. 12 — RN coberto 30 dias; inclusão sem carência',
    url: 'https://www.planalto.gov.br/ccivil_03/leis/l9656compilado.htm',
  },
  'contran-819': {
    label: 'Resolução CONTRAN 819/2021 — dispositivo de retenção infantil',
    url: 'https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-contran/resolucoes/Resolucao8192021.pdf',
  },
  'guias-quantidades': {
    label: 'Guias BR de quantidades (Sou Mãe, Vestindo Crianças, Huggies) — consumo real de fralda/algodão',
    url: 'https://www.soumae.org/lista-completa-de-enxoval-para-bebe/',
  },
  'anoreg-registro': {
    label: 'ANOREG — Registro civil de nascimento',
    url: 'https://www.anoreg.org.br/site/atos-extrajudiciais/registro-civil/nascimento/',
  },
}

export const ENXOVAL_CATEGORIES = [
  // ── Roupinhas ────────────────────────────────────────────
  {
    id: 'roupas',
    title: 'Roupinhas · RN e P',
    icon: '👶',
    buyWindow: [24, 32],
    intro: 'Bebê de janeiro/fevereiro em Brasília = calor. Priorize algodão leve. '
      + 'RN dura semanas — compre pouco RN e mais P/M.',
    items: [
      { id: 'body-mc', label: 'Body manga curta', qty: 'RN: 4–6 · P: 6–8', critical: true,
        note: 'Algodão. RN suja 2–3 trocas de roupa por dia — e o tamanho RN dura só 2–3 semanas.' },
      { id: 'macacao', label: 'Macacão/sleepsuit leve', qty: 'RN: 3–4 · P: 5–6', critical: true,
        note: 'Abertura frontal facilita troca noturna.' },
      { id: 'mijao', label: 'Mijão/culote', qty: '4–6 por tamanho' },
      { id: 'casaquinho', label: 'Casaquinho leve de algodão', qty: '2',
        note: 'Ar-condicionado / noites mais frescas.' },
      { id: 'meias', label: 'Meias', qty: '4–6 pares' },
      { id: 'luva-touca-rn', label: 'Touca de saída da maternidade', qty: '1–2' },
      { id: 'panos-boca', label: 'Panos de boca / fraldas de pano', qty: '10–12', critical: true,
        note: 'Multiuso: golfada, apoio, sombra. É dos itens mais usados do enxoval.' },
      { id: 'babador', label: 'Babadores', qty: '3–4' },
      { id: 'manta-leve', label: 'Manta leve de algodão', qty: '2' },
      { id: 'saida-maternidade', label: 'Saída de maternidade', qty: '1' },
      { id: 'lavar-roupas', label: 'Lavar tudo antes do uso (sabão neutro/coco)', critical: true,
        note: 'Lavar até semana ~36. Remover etiquetas que coçam.' },
    ],
    avoid: [
      'Estocar muitas peças RN — bebês de +3,5 kg pulam direto pro P.',
      'Tecidos sintéticos que abafam (bebê de verão).',
      'Roupas com laços/cordões soltos perto do pescoço.',
    ],
    sourceIds: ['nhs-buy', 'guias-quantidades'],
  },

  // ── Quarto & sono seguro ─────────────────────────────────
  {
    id: 'sono',
    title: 'Quarto & sono seguro',
    icon: '🛏️',
    buyWindow: [24, 32],
    intro: 'A regra SBP/AAP: berço LIVRE. Colchão firme, lençol bem esticado e '
      + 'nada mais dentro do berço no 1º ano.',
    items: [
      { id: 'berco', label: 'Berço certificado Inmetro', qty: '1', critical: true,
        note: 'Grades com espaçamento 4,5–6,5 cm, tinta atóxica.' },
      { id: 'colchao', label: 'Colchão firme no tamanho EXATO do berço', qty: '1', critical: true,
        note: 'Sem frestas nas laterais. Firme = reduz risco de SMSL (morte súbita).' },
      { id: 'lencol', label: 'Lençol de elástico', qty: '3–4', critical: true },
      { id: 'protetor-impermeavel', label: 'Protetor de colchão impermeável', qty: '1–2' },
      { id: 'saco-dormir', label: 'Saco de dormir leve (TOG baixo)', qty: '2',
        note: 'Substitui coberta solta — recomendação SBP. Verão: tecido leve.' },
      { id: 'quarto-compartilhado', label: 'Definir onde o berço fica no quarto do casal', critical: true,
        note: 'SBP: mesmo quarto dos pais (berço próprio) por 6–12 meses.' },
      { id: 'baba-eletronica', label: 'Babá eletrônica (opcional)', qty: '1' },
      { id: 'comoda-trocador', label: 'Cômoda ou espaço de trocador', qty: '1' },
      { id: 'luz-noturna', label: 'Luz noturna fraca (trocas/mamadas)', qty: '1' },
    ],
    avoid: [
      'Travesseiro (nenhum tipo, nem "anatômico") antes de 12 meses — SBP.',
      'Protetor de berço / kit berço acolchoado — risco de sufocação.',
      'Cobertas e edredons soltos, bichos de pelúcia dentro do berço.',
      'Dormir em bebê conforto, carrinho ou sofá como rotina.',
    ],
    sourceIds: ['sbp-sono'],
  },

  // ── Banho & higiene ──────────────────────────────────────
  {
    id: 'banho',
    title: 'Banho & higiene',
    icon: '🛁',
    buyWindow: [28, 34],
    items: [
      { id: 'banheira', label: 'Banheira (com ou sem suporte)', qty: '1', critical: true },
      { id: 'toalha-capuz', label: 'Toalha com capuz macia', qty: '3–4' },
      { id: 'sabonete-liquido', label: 'Sabonete líquido neutro de glicerina', qty: '1',
        note: 'Primeiras semanas: água já basta na maior parte do corpo.' },
      { id: 'algodao', label: 'Algodão (bolas/discos)', qty: '3–4 pacotes grandes', critical: true,
        note: 'Limpeza padrão-ouro é água morna + algodão A CADA troca de fralda — gasta muito rápido.' },
      { id: 'alcool-70', label: 'Álcool 70% (coto umbilical)', qty: '1', critical: true,
        note: 'Orientação MS: limpar o coto a cada troca até cair.' },
      { id: 'pente-escova', label: 'Pente/escova macia', qty: '1' },
      { id: 'tesourinha-lixa', label: 'Tesourinha ponta redonda ou lixa', qty: '1' },
      { id: 'termometro-banho', label: 'Termômetro de banho (opcional)', qty: '1',
        note: 'Alternativa: testar com o punho (~36–37 °C).' },
    ],
    avoid: [
      'Cotonete dentro do ouvido/nariz do bebê.',
      'Perfumes e colônias nos primeiros meses.',
      'Talco — risco de aspiração (contraindicado por pediatras).',
    ],
    sourceIds: ['nhs-buy', 'ms-caderneta'],
  },

  // ── Fraldas & troca ──────────────────────────────────────
  {
    id: 'fraldas',
    title: 'Fraldas & troca',
    icon: '🧷',
    buyWindow: [28, 36],
    items: [
      { id: 'fralda-rn', label: 'Fralda descartável RN', qty: '3–5 pacotes (120–180 un)', critical: true,
        note: 'RN usa 8–12 fraldas/DIA (~240 no 1º mês), mas a fase RN dura 2–3 semanas — 120–180 un cobre sem sobrar.' },
      { id: 'fralda-p', label: 'Fralda descartável P', qty: '3–4 pacotes', 
        note: 'O grosso do estoque vai ser P/M — bom pedido de chá de bebê.' },
      { id: 'trocador-portatil', label: 'Trocador (fixo + portátil p/ bolsa)', qty: '1+1', critical: true },
      { id: 'pomada-assadura', label: 'Pomada de prevenção de assaduras', qty: '2–3', critical: true },
      { id: 'lencos-agua', label: 'Lenços umedecidos SEM perfume (ou algodão + água)', qty: '2–3 pacotes',
        note: 'Primeiras semanas: algodão com água morna é o padrão-ouro.' },
      { id: 'lixeira-tampa', label: 'Lixeira com tampa p/ fraldas', qty: '1' },
    ],
    avoid: [
      'Comprar caixas e caixas da mesma marca antes de testar na pele do bebê.',
    ],
    sourceIds: ['nhs-buy', 'guias-quantidades'],
  },

  // ── Farmacinha ───────────────────────────────────────────
  {
    id: 'farmacinha',
    title: 'Farmacinha',
    icon: '💊',
    buyWindow: [30, 36],
    intro: 'Regra de ouro: NADA de medicamento sem prescrição do pediatra. '
      + 'A farmacinha é de suporte, não de tratamento.',
    items: [
      { id: 'termometro-digital', label: 'Termômetro digital', qty: '1–2', critical: true,
        note: 'Mercúrio é proibido. Ter um de resposta rápida ajuda de madrugada.' },
      { id: 'soro-fisiologico', label: 'Soro fisiológico 0,9%', qty: '5+ flaconetes', critical: true,
        note: 'Higiene nasal e ocular.' },
      { id: 'aspirador-nasal', label: 'Aspirador nasal', qty: '1' },
      { id: 'gaze', label: 'Gazes estéreis', qty: '1 caixa' },
      { id: 'antitermico-rx', label: 'Antitérmico — SÓ o que o pediatra prescrever', critical: true,
        note: 'Deixar prescrito com dose por peso ANTES de precisar (consulta pré-natal pediátrica).' },
      { id: 'contatos-emergencia', label: 'Lista de contatos: pediatra, maternidade, SAMU 192', critical: true },
    ],
    avoid: [
      'Antitérmico/antigripal por conta própria — dose é por peso e muda rápido.',
      'Mel antes de 1 ano — risco de botulismo infantil.',
      'Termômetro de mercúrio (proibido no Brasil).',
      'G6PD na família: revisar lista de medicamentos/substâncias proibidas com o pediatra ANTES do nascimento.',
    ],
    sourceIds: ['ms-caderneta'],
  },

  // ── Amamentação ──────────────────────────────────────────
  {
    id: 'amamentacao',
    title: 'Amamentação & alimentação',
    icon: '🤱',
    buyWindow: [28, 36],
    intro: 'OMS/MS: aleitamento exclusivo até 6 meses. Compre o mínimo de '
      + 'mamadeira/bomba antes — a necessidade real só aparece depois.',
    items: [
      { id: 'sutia-amamentacao', label: 'Sutiãs de amamentação', qty: '3' },
      { id: 'absorvente-seio', label: 'Absorventes de seio', qty: '1–2 caixas' },
      { id: 'almofada-amamentacao', label: 'Almofada de amamentação (opcional)', qty: '1' },
      { id: 'pomada-lanolina', label: 'Lanolina p/ fissura mamilar', qty: '1' },
      { id: 'consultora-contato', label: 'Contato de consultora de amamentação / banco de leite', critical: true,
        note: 'Resolver ANTES do parto. Rede de bancos de leite do DF atende gratuito.' },
    ],
    avoid: [
      'Comprar bomba extratora cara antecipadamente — alugar/testar primeiro.',
      'Chupeta nas primeiras 2–4 semanas (interfere na pega) — discutir com pediatra.',
    ],
    sourceIds: ['ms-caderneta', 'nhs-buy'],
  },

  // ── Passeio & transporte ─────────────────────────────────
  {
    id: 'passeio',
    title: 'Passeio & transporte',
    icon: '🚗',
    buyWindow: [28, 36],
    items: [
      { id: 'bebe-conforto', label: 'Bebê conforto (grupo 0+, até 13 kg)', qty: '1', critical: true,
        note: 'Transporte de criança em carro exige dispositivo de retenção (CONTRAN 819/2021) — '
          + 'ou seja, a volta da maternidade já precisa dele. Instalar e testar até a semana 36: '
          + 'de costas p/ o movimento, banco traseiro.' },
      { id: 'carrinho', label: 'Carrinho de bebê (reclinável p/ RN)', qty: '1', critical: true },
      { id: 'sling', label: 'Sling / canguru ergonômico (opcional)', qty: '1',
        note: 'Posição segura: vias aéreas livres, rosto visível, "altura de beijo".' },
      { id: 'bolsa-maternidade', label: 'Bolsa de passeio (fraldas, troca, soro)', qty: '1' },
      { id: 'protetor-solar-sombrinha', label: 'Proteção solar física (sombrinha/capota)',
        note: 'Protetor solar químico só após 6 meses. Antes: sombra e roupa.' },
    ],
    avoid: [
      'Bebê conforto usado sem histórico (colisão anterior invalida) ou fora da validade.',
      'Andador — contraindicado pela SBP (acidentes + atraso motor).',
    ],
    sourceIds: ['contran-819', 'sbp-sono'],
  },

  // ── Mala da maternidade ──────────────────────────────────
  {
    id: 'mala',
    title: 'Mala da maternidade',
    icon: '🧳',
    buyWindow: [32, 36],
    intro: 'Meta: mala pronta na porta até a semana 36. Conferir a lista '
      + 'específica da maternidade escolhida — cada uma fornece itens diferentes.',
    items: [
      // Documentos
      { id: 'doc-rg-cpf', group: 'Documentos', label: 'RG + CPF da Rafa e do Palmer', critical: true },
      { id: 'doc-plano', group: 'Documentos', label: 'Carteirinha do plano + guia de internação', critical: true },
      { id: 'doc-caderneta', group: 'Documentos', label: 'Caderneta da gestante + últimos exames/USGs', critical: true,
        note: 'MS: a caderneta é o canal de comunicação com a equipe do parto.' },
      { id: 'doc-plano-parto', group: 'Documentos', label: 'Plano de parto impresso (se houver)', qty: '2 cópias' },
      // Rafa
      { id: 'mala-camisolas', group: 'Para a Rafa', label: 'Camisolas/pijamas com abertura p/ amamentar', qty: '3' },
      { id: 'mala-robe', group: 'Para a Rafa', label: 'Robe + chinelo antiderrapante', qty: '1' },
      { id: 'mala-calcinhas', group: 'Para a Rafa', label: 'Calcinhas de algodão/descartáveis pós-parto', qty: '6+' },
      { id: 'mala-absorvente-pos', group: 'Para a Rafa', label: 'Absorventes pós-parto', qty: '1–2 pacotes', critical: true },
      { id: 'mala-higiene', group: 'Para a Rafa', label: 'Nécessaire de higiene pessoal', qty: '1' },
      { id: 'mala-saida-rafa', group: 'Para a Rafa', label: 'Roupa confortável p/ alta', qty: '1' },
      // Bebê
      { id: 'mala-bebe-conjuntos', group: 'Para o bebê', label: 'Conjuntos RN + P (body, macacão, meia)', qty: '4–6', critical: true,
        note: 'Levar dos dois tamanhos — não dá pra saber o peso exato antes.' },
      { id: 'mala-bebe-manta', group: 'Para o bebê', label: 'Manta leve + touca', qty: '1–2' },
      { id: 'mala-bebe-fralda', group: 'Para o bebê', label: 'Fraldas RN', qty: '1 pacote',
        note: 'Maternidade costuma fornecer parte — conferir na visita.' },
      { id: 'mala-bebe-saida', group: 'Para o bebê', label: 'Saída de maternidade', qty: '1' },
      // Acompanhante
      { id: 'mala-acomp-roupa', group: 'Acompanhante', label: 'Trocas de roupa Palmer (2–3 dias)', qty: '2–3' },
      { id: 'mala-acomp-carregador', group: 'Acompanhante', label: 'Carregadores + power bank', qty: '1' },
      { id: 'mala-acomp-lanches', group: 'Acompanhante', label: 'Lanches + garrafa de água', qty: '—' },
      { id: 'mala-carro-teste', group: 'Acompanhante', label: 'Bebê conforto JÁ instalado no carro', critical: true },
    ],
    avoid: [],
    sourceIds: ['ms-caderneta', 'contran-819'],
  },

  // ── Documentos & burocracia pós-parto ────────────────────
  {
    id: 'docs',
    title: 'Documentos & burocracia (pós-parto)',
    icon: '📋',
    buyWindow: null,
    intro: 'Nada aqui se compra — são prazos. Os dois primeiros itens têm '
      + 'prazo legal curto e valem dinheiro/carência.',
    items: [
      { id: 'doc-dnv', label: 'Guardar a DNV (Declaração de Nascido Vivo)', critical: true,
        note: 'O hospital emite. É o documento que destrava todo o resto.' },
      { id: 'doc-registro', label: 'Registro civil em cartório — em regra, até 15 dias', critical: true,
        note: 'Certidão de nascimento gratuita; na maioria dos cartórios o CPF já sai junto '
          + '(confirmar no local). Muitas maternidades têm posto de cartório.' },
      { id: 'doc-plano-30d', label: 'Incluir bebê no plano de saúde — até 30 dias', critical: true,
        note: 'Lei 9.656/98: RN coberto nos primeiros 30 dias; inscrição nesse prazo entra sem carência. '
          + 'Depois disso podem incidir carências/regras contratuais — confirmar com a operadora. '
          + 'Não deixar pro dia 29.' },
      { id: 'doc-pezinho', label: 'Teste do pezinho — entre 3º e 5º dia de vida', critical: true,
        note: 'Dado o histórico paterno de G6PD: confirmar ANTES com o laboratório se o painel '
          + 'escolhido dosa G6PD (varia entre versões básica/ampliada/master).' },
      { id: 'doc-triagens', label: 'Triagens neonatais: orelhinha, olhinho, coraçãozinho, linguinha', critical: true,
        note: 'Normalmente ainda na maternidade — conferir na alta.' },
      { id: 'doc-vacinas-rn', label: 'BCG + Hepatite B na maternidade', critical: true },
      { id: 'doc-consulta-rn', label: '1ª consulta pediátrica — até o 5º dia de vida', critical: true,
        note: 'MS: primeira semana de saúde integral.' },
      { id: 'doc-licencas', label: 'Licença-maternidade / paternidade — dar entrada' },
    ],
    avoid: [],
    sourceIds: ['anoreg-registro', 'ans-rn', 'ms-caderneta'],
  },
]

/** Overall buy-phase hints keyed to gestational week — shown in the header. */
export const PHASE_HINTS = [
  { until: 20, text: 'Cedo demais pra comprar — fase de pesquisa e lista.' },
  { until: 24, text: 'Pós-morfológica: bom momento pra definir o que comprar.' },
  { until: 32, text: 'Janela principal de compras: roupas, quarto, banho.' },
  { until: 36, text: 'Reta final: farmacinha, mala pronta, bebê conforto instalado.' },
  { until: 42, text: 'Tudo deveria estar pronto — só repor e esperar.' },
]
