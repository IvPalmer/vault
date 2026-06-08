/**
 * RAFA_GLUCOSE_LOG — Automonitorização de glicose capilar (gestação).
 *
 * Source: caderno manuscrito de Rafaella, fotografado em 08/06/2026
 *   (IMG_9104–IMG_9108). "Testagem de Glicose — 15 dias" → estendida a 23 dias.
 *
 * Período: 16/05/2026 (1º dia) → 07/06/2026 (23º dia).
 * Contexto: controle pré-rastreio de DMG (diabetes mellitus gestacional,
 *   rastreio formal 24–28 sem). Liga-se à obs do plano alimentar
 *   (HbA1c 5,4 com tendência ↑) — ver RAFA_MEAL_PLAN.
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
 */
export const RAFA_GLUCOSE_LOG = {
  titulo: 'Glicose capilar — automonitorização',
  fonte: 'Caderno manuscrito (IMG_9104–9108), fotografado 08/06/2026',
  periodo: { inicio: '2026-05-16', fim: '2026-06-07' },
  referencias: {
    jejum: { min: 65, max: 95, label: 'Jejum: 65–95 mg/dL' },
    pos1h: { max: 140, label: '1h após refeição: < 140 mg/dL' },
    pos2h: { max: 120, label: '2h após refeição: < 120 mg/dL' },
  },
  observacoes: [
    'Automonitorização capilar durante gestação — controle antes do rastreio formal de DMG (24–28 sem).',
    'Primeiros 3 dias com jejum acima do alvo (113 → 108 → 108); estabiliza na faixa a partir do 6º dia.',
    'Picos pós-refeição associados a refeições de carboidrato refinado / fast-food (ver lista abaixo do gráfico).',
    'Dias sem medição: 4º dia (19/05) sem registro; 5º dia (20/05) sem jejum; algumas pós-refeições não medidas (esqueceu a máquina / vômito).',
  ],
  // pos[].valor em mg/dL; refeicao = contexto anotado no caderno.
  dias: [
    { dia: 1, data: '2026-05-16', jejum: 113, pos: [], nota: 'Almoço: vomitou, não mediu. Jantar (acarajé): sem máquina.' },
    { dia: 2, data: '2026-05-17', jejum: 108, pos: [
      { valor: 174, refeicao: 'Almoço — arroz, feijão e farofa de ovos' },
      { valor: 127, refeicao: 'Noite — pastel de queijo + 2 pratos de lasanha, Heineken s/ álcool' },
    ] },
    { dia: 3, data: '2026-05-18', jejum: 108, pos: [
      { valor: 119, refeicao: 'Tarde — lasanha' },
    ] },
    { dia: 4, data: '2026-05-19', jejum: null, pos: [], nota: 'Sem registro neste dia.' },
    { dia: 5, data: '2026-05-20', jejum: null, pos: [
      { valor: 110, refeicao: 'Noite — feijão, carne, tomate e couve' },
    ], nota: '1º exame de imagem ♥' },
    { dia: 6, data: '2026-05-21', jejum: 90, pos: [
      { valor: 85, refeicao: 'Noite' },
    ], nota: 'Almoço: esqueceu a máquina, não mediu após 1h.' },
    { dia: 7, data: '2026-05-22', jejum: 89, pos: [
      { valor: 128, refeicao: 'Almoço — arroz, feijão preto, carne, couve-flor, tomate' },
      { valor: 99, refeicao: 'Jantar — sopa de legumes e frango desfiado' },
    ] },
    { dia: 8, data: '2026-05-23', jejum: 88, pos: [
      { valor: 87, refeicao: 'Almoço — arroz integral, feijão preto, alcatra, salada' },
      { valor: 127, refeicao: 'Jantar — purê de abóbora, alcatra, feijão preto' },
    ] },
    { dia: 9, data: '2026-05-24', jejum: 73, pos: [
      { valor: 113, refeicao: 'Almoço — arroz integral, frango desfiado, abobrinha, abóbora' },
      { valor: 97, refeicao: 'Jantar — sopa de legumes com frango desfiado' },
    ] },
    { dia: 10, data: '2026-05-25', jejum: 86, pos: [
      { valor: 104, refeicao: 'Jantar — sopa de legumes c/ frango + 2 biscoitos diet' },
    ] },
    { dia: 11, data: '2026-05-26', jejum: 90, pos: [
      { valor: 108, refeicao: 'Tarde — arroz, feijão, alcatra (vomitou antes de acabar) — 2h depois' },
      { valor: 96, refeicao: 'Jantar — arroz, feijão, alcatra + salada' },
    ] },
    { dia: 12, data: '2026-05-27', jejum: 97, pos: [
      { valor: 116, refeicao: 'Tarde — arroz, feijão, alcatra, salada e tomate' },
      { valor: 154, refeicao: 'Noite — CHEESEBURGER + batata' },
    ] },
    { dia: 13, data: '2026-05-28', jejum: 93, pos: [
      { valor: 95, refeicao: 'Almoço — arroz, feijão, tilápia grelhada (2h depois)' },
      { valor: 98, refeicao: 'Jantar — omelete de abobrinha, salada' },
    ] },
    { dia: 14, data: '2026-05-29', jejum: 71, pos: [
      { valor: 103, refeicao: 'Tarde — arroz, feijão, tilápia, salada' },
      { valor: 104, refeicao: 'Janta — pizza low carb (pesto, manjericão, tomate)' },
    ] },
    { dia: 15, data: '2026-05-30', jejum: 94, pos: [
      { valor: 104, refeicao: 'Jantar — 2 fatias de pizza low carb' },
    ] },
    { dia: 16, data: '2026-05-31', jejum: 88, pos: [
      { valor: 104, refeicao: 'Almoço — brie, tomate, pão, lasanha, cheesecake' },
      { valor: 139, refeicao: "Jantar — DOIS hambúrgueres Sandy's" },
    ] },
    { dia: 17, data: '2026-06-01', jejum: 100, pos: [
      { valor: 163, refeicao: 'Tarde — cuscuz c/ ovo + enroladinho de salsicha assado' },
      { valor: 121, refeicao: 'Janta — caldinho de feijão' },
    ] },
    { dia: 18, data: '2026-06-02', jejum: 94, pos: [
      { valor: 108, refeicao: 'Tarde — arroz integral, feijão, patinho' },
      { valor: 115, refeicao: 'Noite — muqueca de banana c/ leite de coco, arroz, torta low carb' },
    ] },
    { dia: 19, data: '2026-06-03', jejum: 88, pos: [
      { valor: 119, refeicao: 'Tarde — salada com grão de bico' },
    ] },
    { dia: 20, data: '2026-06-04', jejum: 88, pos: [
      { valor: 144, refeicao: 'Tarde — 10 pães de queijo, arroz, frango assado, abóbora, picolé' },
      { valor: 107, refeicao: 'Noite — pão de sal/muçarela/ovo, arroz, alcatra, feijão' },
    ] },
    { dia: 21, data: '2026-06-05', jejum: 83, pos: [
      { valor: 127, refeicao: 'Tarde — arroz cateto, feijão, falafel, tomate, molho de iogurte' },
      { valor: 93, refeicao: 'Jantar — tortinha de frango desfiado e requeijão caseiro' },
    ] },
    { dia: 22, data: '2026-06-06', jejum: 88, pos: [
      { valor: 103, refeicao: 'Tarde — lasanha à bolonhesa (Spoletto)' },
    ], nota: 'Jantar — macarrão de abobrinha c/ patinho grelhado (valor não anotado).' },
    { dia: 23, data: '2026-06-07', jejum: 81, pos: [
      { valor: 150, refeicao: 'Almoço — dois pratos de lasanha à bolonhesa' },
      { valor: 153, refeicao: 'Jantar — 5 guiozas de carne + trufa zero açúcar (Cacau Show)' },
    ] },
  ],
}
