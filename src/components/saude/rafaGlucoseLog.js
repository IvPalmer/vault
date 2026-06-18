/**
 * RAFA_GLUCOSE_LOG — Automonitorização de glicose capilar (gestação).
 *
 * Source: caderno manuscrito de Rafaella.
 *   1º lote (dias 1–24): fotografado em 08/06/2026 (IMG_9104–9108, 9112).
 *   2º lote (dias 25–32): fotografado em 18/06/2026 (IMG_9200, IMG_9201).
 *   "Testagem de Glicose — 15 dias" → estendida a 32 dias.
 *
 * Período: 16/05/2026 (1º dia) → 16/06/2026 (32º dia).
 * Contexto: controle pré-rastreio de DMG (diabetes mellitus gestacional,
 *   rastreio formal 24–28 sem). Liga-se à obs do plano alimentar
 *   (HbA1c 5,4 com tendência ↑) — ver RAFA_MEAL_PLAN.
 *
 * Três medições por dia quando possível: jejum, almoço (≈pós-almoço/tarde)
 *   e jantar (≈pós-jantar/noite). `null` = não medido naquele momento.
 *
 * Referências (anotadas pela própria, padrão gestacional):
 *   - Jejum: 65–95 mg/dL
 *   - 1h após refeição: < 140 mg/dL
 *   - 2h após refeição: < 120 mg/dL
 *
 * Notas de fidelidade aos registros:
 *   - 4º dia (19/05) sem registro.
 *   - 5º dia (20/05) sem jejum (só medição noturna).
 *   - Horário das medições pós-refeição é variável (≈1–2h, nem sempre anotado);
 *     usar 140/120 como referência geral, não como corte exato por janela.
 *   - Rótulos "Tarde/Almoço" mapeados para `almoco`; "Noite/Jantar" para `jantar`.
 */
export const RAFA_GLUCOSE_LOG = {
  titulo: 'Glicose capilar — automonitorização',
  fonte: 'Caderno manuscrito (IMG_9104–9108/9112 + IMG_9200/9201), fotografado 08/06 e 18/06/2026',
  periodo: { inicio: '2026-05-16', fim: '2026-06-16' },
  referencias: {
    jejum: { min: 65, max: 95, label: 'Jejum: 65–95 mg/dL' },
    pos1h: { max: 140, label: '1h após refeição: < 140 mg/dL' },
    pos2h: { max: 120, label: '2h após refeição: < 120 mg/dL' },
  },
  observacoes: [
    'Automonitorização capilar durante gestação — controle antes do rastreio formal de DMG (24–28 sem).',
    'Primeiros 3 dias com jejum acima do alvo (113 → 108 → 108); estabiliza na faixa a partir do 6º dia.',
    'Picos pós-refeição associados a refeições de carboidrato refinado / fast-food (ver lista abaixo do gráfico).',
    'Dias sem medição: 4º dia (19/05) sem registro; 5º dia (20/05) sem jejum; alguns almoços/jantares não medidos (esqueceu a máquina / vômito).',
    'Manhã do 27º dia (11/06) anômala: jejum anotado 160 e remedições 132/163/146 — confirmar com a Rafaella (provável variação de medidor/punção). Almoço do 26º dia (157) também elevado.',
    'A partir do 29º dia (13/06) a própria anotou "aqui começa pra valer" (controle alimentar mais rígido); jejuns seguintes voltam à faixa (84–94).',
  ],
  // Cada dia: jejum (número|null), almoco/jantar ({ valor, refeicao }|null).
  dias: [
    { dia: 1, data: '2026-05-16', jejum: 113,
      almoco: null,
      jantar: null,
      nota: 'Almoço: vomitou, não mediu. Jantar (acarajé): sem máquina.' },
    { dia: 2, data: '2026-05-17', jejum: 108,
      almoco: { valor: 174, refeicao: 'Arroz, feijão e farofa de ovos' },
      jantar: { valor: 127, refeicao: 'Pastel de queijo + 2 pratos de lasanha, Heineken s/ álcool' } },
    { dia: 3, data: '2026-05-18', jejum: 108,
      almoco: { valor: 119, refeicao: 'Lasanha (tarde)' },
      jantar: null },
    { dia: 4, data: '2026-05-19', jejum: null, almoco: null, jantar: null, nota: 'Sem registro neste dia.' },
    { dia: 5, data: '2026-05-20', jejum: null,
      almoco: null,
      jantar: { valor: 110, refeicao: 'Feijão, carne, tomate e couve (noite)' },
      nota: '1º exame de imagem ♥' },
    { dia: 6, data: '2026-05-21', jejum: 90,
      almoco: null,
      jantar: { valor: 85, refeicao: 'Noite' },
      nota: 'Almoço: esqueceu a máquina, não mediu após 1h.' },
    { dia: 7, data: '2026-05-22', jejum: 89,
      almoco: { valor: 128, refeicao: 'Arroz, feijão preto, carne, couve-flor, tomate' },
      jantar: { valor: 99, refeicao: 'Sopa de legumes e frango desfiado' } },
    { dia: 8, data: '2026-05-23', jejum: 88,
      almoco: { valor: 87, refeicao: 'Arroz integral, feijão preto, alcatra, salada' },
      jantar: { valor: 127, refeicao: 'Purê de abóbora, alcatra, feijão preto' } },
    { dia: 9, data: '2026-05-24', jejum: 73,
      almoco: { valor: 113, refeicao: 'Arroz integral, frango desfiado, abobrinha, abóbora' },
      jantar: { valor: 97, refeicao: 'Sopa de legumes com frango desfiado' } },
    { dia: 10, data: '2026-05-25', jejum: 86,
      almoco: null,
      jantar: { valor: 104, refeicao: 'Sopa de legumes c/ frango + 2 biscoitos diet' } },
    { dia: 11, data: '2026-05-26', jejum: 90,
      almoco: { valor: 108, refeicao: 'Arroz, feijão, alcatra (vomitou antes de acabar) — 2h depois' },
      jantar: { valor: 96, refeicao: 'Arroz, feijão, alcatra + salada' } },
    { dia: 12, data: '2026-05-27', jejum: 97,
      almoco: { valor: 116, refeicao: 'Arroz, feijão, alcatra, salada e tomate' },
      jantar: { valor: 154, refeicao: 'CHEESEBURGER + batata' } },
    { dia: 13, data: '2026-05-28', jejum: 93,
      almoco: { valor: 95, refeicao: 'Arroz, feijão, tilápia grelhada (2h depois)' },
      jantar: { valor: 98, refeicao: 'Omelete de abobrinha, salada' } },
    { dia: 14, data: '2026-05-29', jejum: 71,
      almoco: { valor: 103, refeicao: 'Arroz, feijão, tilápia, salada' },
      jantar: { valor: 104, refeicao: 'Pizza low carb (pesto, manjericão, tomate)' } },
    { dia: 15, data: '2026-05-30', jejum: 94,
      almoco: null,
      jantar: { valor: 104, refeicao: '2 fatias de pizza low carb' } },
    { dia: 16, data: '2026-05-31', jejum: 88,
      almoco: { valor: 104, refeicao: 'Brie, tomate, pão, lasanha, cheesecake' },
      jantar: { valor: 139, refeicao: "DOIS hambúrgueres Sandy's" } },
    { dia: 17, data: '2026-06-01', jejum: 100,
      almoco: { valor: 163, refeicao: 'Cuscuz c/ ovo + enroladinho de salsicha assado' },
      jantar: { valor: 121, refeicao: 'Caldinho de feijão' } },
    { dia: 18, data: '2026-06-02', jejum: 94,
      almoco: { valor: 108, refeicao: 'Arroz integral, feijão, patinho' },
      jantar: { valor: 115, refeicao: 'Muqueca de banana c/ leite de coco, arroz, torta low carb' } },
    { dia: 19, data: '2026-06-03', jejum: 88,
      almoco: { valor: 119, refeicao: 'Salada com grão de bico' },
      jantar: null },
    { dia: 20, data: '2026-06-04', jejum: 88,
      almoco: { valor: 144, refeicao: '10 pães de queijo, arroz, frango assado, abóbora, picolé' },
      jantar: { valor: 107, refeicao: 'Pão de sal/muçarela/ovo, arroz, alcatra, feijão' } },
    { dia: 21, data: '2026-06-05', jejum: 83,
      almoco: { valor: 127, refeicao: 'Arroz cateto, feijão, falafel, tomate, molho de iogurte' },
      jantar: { valor: 93, refeicao: 'Tortinha de frango desfiado e requeijão caseiro' } },
    { dia: 22, data: '2026-06-06', jejum: 88,
      almoco: { valor: 103, refeicao: 'Lasanha à bolonhesa (Spoletto)' },
      jantar: { valor: 105, refeicao: 'Macarrão de abobrinha c/ tomate cereja, alho e parmesão, patinho grelhado' } },
    { dia: 23, data: '2026-06-07', jejum: 81,
      almoco: { valor: 150, refeicao: 'Dois pratos de lasanha à bolonhesa' },
      jantar: { valor: 153, refeicao: '5 guiozas de carne + trufa zero açúcar (Cacau Show)' } },
    { dia: 24, data: '2026-06-08', jejum: 89,
      almoco: { valor: 114, refeicao: 'Hambúrguer de falafel, arroz cateto, cenoura e quiabo no leite de coco' },
      jantar: { valor: 108, refeicao: 'Hambúrguer com duas carnes' } },
    { dia: 25, data: '2026-06-09', jejum: 82,
      almoco: null,
      jantar: { valor: 104, refeicao: 'Patinho grelhado, feijão azuki e arroz cateto' },
      nota: 'Tarde: não mediu (não levou o glicosímetro pro estágio).' },
    { dia: 26, data: '2026-06-10', jejum: 99,
      almoco: { valor: 157, refeicao: 'Arroz cateto, feijão azuki, hambúrguer de grão de bico c/ molho de iogurte, salsa e cenoura' },
      jantar: { valor: 122, refeicao: 'Caldo de abóbora com linguiça de frango, leite de coco e temperos' } },
    { dia: 27, data: '2026-06-11', jejum: 160,
      almoco: { valor: 117, refeicao: 'Arroz cateto, feijão azuki, chuchu grelhado, alface, tomate e ervilha' },
      jantar: { valor: 132, refeicao: 'Sopa de abóbora e linguiça de frango' },
      nota: 'Manhã instável: jejum anotado 160; remedições na sequência 132, 163, 146 — confirmar (provável variação de medição).' },
    { dia: 28, data: '2026-06-12', jejum: 84,
      almoco: { valor: 120, refeicao: 'Arroz cateto, feijão azuki, carne vermelha grelhada, salada e tomate' },
      jantar: { valor: 154, refeicao: 'Pipoca grande + cachorro-quente (cinema)' },
      nota: 'Dia dos Namorados.' },
    { dia: 29, data: '2026-06-13', jejum: 86,
      almoco: { valor: 114, refeicao: 'Arroz vermelho, feijão azuki, patinho grelhado, alface e tomate' },
      jantar: { valor: 80, refeicao: 'Caldo de abóbora com linguiça (2h depois) + bolo de banana e farinha de amêndoas' },
      nota: '"Aqui começa pra valer" — início do controle mais rígido (anotação dela).' },
    { dia: 30, data: '2026-06-14', jejum: 85,
      almoco: { valor: 95, refeicao: 'Patinho grelhado, arroz vermelho, feijão azuki, salada (tomate e limão), sorvete zero açúcar (chocolate/pistache)' },
      jantar: { valor: 94, refeicao: 'Lasanha caseira (berinjela, carne moída, tomate, muçarela, parmesão) + 1 maçã' } },
    { dia: 31, data: '2026-06-15', jejum: 94,
      almoco: { valor: 87, refeicao: 'Lasanha caseira low carb de berinjela com muçarela + panhoca' },
      jantar: { valor: 107, refeicao: 'Lasanha caseira low carb de berinjela, castanha, pêra' } },
    { dia: 32, data: '2026-06-16', jejum: 87,
      almoco: { valor: 95, refeicao: 'Arroz vermelho, coxão mole grelhado, feijão azuki' },
      jantar: { valor: 94, refeicao: 'Jantar (refeição não anotada)' } },
  ],
}
