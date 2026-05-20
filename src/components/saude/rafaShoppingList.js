/**
 * RAFA_SHOPPING_LIST — Lista semanal de compras derivada do plano alimentar
 * prescrito pela Dra. Elorrane Cordeiro em 19/05/2026.
 *
 * Quantidades calculadas para 7 dias, 1 pessoa, considerando rotação de
 * substituições (carne vermelha 2×/sem, peixe 1×, fígado 1× a cada 15d).
 */
export const RAFA_SHOPPING_LIST = {
  base_prescricao: '2026-05-19',
  periodo_dias: 7,
  custo_estimado_min: 350,
  custo_estimado_max: 500,
  categorias: [
    {
      id: 'proteina',
      titulo: 'Proteína animal',
      icone: '🥩',
      alerta: { tipo: 'danger', texto: 'Toxoplasmose: TODAS as carnes muito bem passadas. Sem carne crua, embutidos crus, defumados artesanais. Congelar >24h a -12°C antes de cozinhar reduz risco residual.' },
      itens: [
        { item: 'Peito de frango (sem pele)', qty: '1,5 kg', uso: 'Almoço + jantar (4-5×/sem)' },
        { item: 'Ovos', qty: '30 u (2 cartelas)', uso: 'Café 2u + omelete/panqueca' },
        { item: 'Alcatra / contrafilé / coxão mole', qty: '400 g', uso: 'Substituição 2×/sem' },
        { item: 'Tilápia (filé)', qty: '300 g', uso: 'Substituição 1×/sem' },
        { item: 'Fígado bovino', qty: '200 g', uso: '1× a cada 15 dias (ferro + B12)' },
      ],
    },
    {
      id: 'laticinios',
      titulo: 'Laticínios',
      icone: '🥛',
      alerta: { tipo: 'danger', texto: 'Evitar versões "zero/light/diet" com ciclamato + aspartame. Ler rótulo: ingrediente único deve ser leite + fermento lácteo (eventual creme de leite).' },
      itens: [
        { item: 'Leite de vaca desnatado UHT', qty: '2 L', uso: '200ml/dia no café' },
        { item: 'Iogurte natural integral sem açúcar/adoçante (Itambé, Batavo natural, Nestlé, Vigor)', qty: '14 × 170g (ou 2 × pote 1kg)', uso: 'Colação + ceia' },
      ],
    },
    {
      id: 'cereais',
      titulo: 'Cereais e grãos',
      icone: '🌾',
      itens: [
        { item: 'Flocão de milho (cuscuz)', qty: '500 g', uso: 'Café 60g/dia' },
        { item: 'Arroz integral', qty: '500 g', uso: 'Almoço 80g/dia' },
        { item: 'Aveia em flocos finos', qty: '250 g', uso: 'Colação 10g + panqueca 22,5g' },
      ],
    },
    {
      id: 'leguminosas',
      titulo: 'Leguminosas',
      icone: '🫘',
      tip: 'Prep: cozinhar 500g de cada cru de uma vez → rende a semana. Congelar em porções de 70g.',
      itens: [
        { item: 'Feijão carioca seco', qty: '500 g (~1kg cozido)', uso: 'Almoço + jantar' },
        { item: 'Feijão preto', qty: '250 g', uso: 'Rotação' },
        { item: 'Lentilha seca', qty: '250 g', uso: 'Rotação' },
        { item: 'Grão de bico seco', qty: '250 g', uso: 'Rotação' },
      ],
    },
    {
      id: 'hortalicas',
      titulo: 'Hortaliças (folhas e legumes)',
      icone: '🥦',
      alerta: { tipo: 'danger', texto: 'Toxoplasmose: lavar TODAS folhas/verduras em água corrente + 15min de molho em hipoclorito 2,5% (1 colher sopa/L) → enxaguar. Mesmo orgânicos.' },
      itens: [
        { item: 'Couve manteiga', qty: '2 maços', uso: 'Almoço + jantar à vontade' },
        { item: 'Alface americana (ou crespa)', qty: '1 pé grande', uso: 'Lanche + saladas' },
        { item: 'Escarola / rúcula / agrião (rotativo)', qty: '1 maço', uso: 'Substituição couve' },
        { item: 'Abobrinha italiana', qty: '2-3 u (~800g)', uso: 'Almoço + jantar 60g cada' },
        { item: 'Cenoura', qty: '3 u', uso: 'Substituição abobrinha' },
        { item: 'Brócolis', qty: '1 cabeça', uso: 'Rotação' },
        { item: 'Quiabo', qty: '300 g', uso: 'Rotação' },
        { item: 'Espinafre', qty: '1 maço', uso: 'Rotação' },
        { item: 'Tomate (caqui / italiano)', qty: '6 u', uso: 'Almoço + jantar + saladas' },
        { item: 'Tomate cereja', qty: '1 bandeja (200g)', uso: 'Lanche omelete' },
        { item: 'Pepino', qty: '2 u', uso: 'Substituição tomate' },
      ],
    },
    {
      id: 'tuberculos',
      titulo: 'Tubérculos e raízes',
      icone: '🎃',
      itens: [
        { item: 'Abóbora (cabotiá ou japonesa)', qty: '1 pedaço (~1 kg)', uso: 'Purê 100g/dia jantar' },
        { item: 'Batata inglesa', qty: '500 g', uso: 'Substituição purê' },
      ],
    },
    {
      id: 'frutas',
      titulo: 'Frutas',
      icone: '🍓',
      itens: [
        { item: 'Mamão papaia (formosa pequeno)', qty: '1 médio (~700g)', uso: 'Café 100g/dia' },
        { item: 'Morango', qty: '2 bandejas 250g', uso: 'Colação 48g/dia' },
        { item: 'Banana prata', qty: '6 u', uso: 'Substituição / panqueca' },
        { item: 'Maçã', qty: '3 u', uso: 'Substituição' },
        { item: 'Mexerica (tangerina)', qty: '6 u', uso: 'Substituição lanche escape' },
        { item: 'Laranja', qty: '3 u', uso: 'Substituição lanche escape' },
      ],
    },
    {
      id: 'sementes',
      titulo: 'Sementes, oleaginosas e pastas',
      icone: '🥜',
      tip: 'Pasta de amendoim: preferir industrializada (controle aflatoxina). Marcas ok: Vitao, Mãe Terra, Madhu, Dr. Peanut natural. Ingrediente único "amendoim", sem óleo hidrogenado.',
      itens: [
        { item: 'Castanha de caju (sem sal)', qty: '100 g', uso: 'Lanche escape 10g/dia' },
        { item: 'Castanha-do-pará (sugestão extra — selênio)', qty: '30 g', uso: '1-2u/dia (discutir Elorrane)' },
        { item: 'Pasta de amendoim integral (sem açúcar)', qty: '1 pote 350g', uso: 'Panqueca alternativa' },
        { item: 'Semente de chia', qty: '150 g', uso: 'Ceia 15g/dia' },
        { item: 'Semente de linhaça', qty: '100 g', uso: 'Substituição chia' },
        { item: 'Granola zero açúcar', qty: '1 pacote 250g', uso: 'Substituição chia' },
      ],
    },
    {
      id: 'chas',
      titulo: 'Chás (gestação-safe)',
      icone: '🍵',
      alerta: { tipo: 'danger', texto: 'Evitar na gestação: hibisco, sálvia, alecrim em chá, boldo, carqueja, sene, espinheira-santa, canela em quantidade, gengibre >1g/dia.' },
      itens: [
        { item: 'Camomila (saquinhos)', qty: '1 caixa', uso: 'Ceia 200ml' },
        { item: 'Hortelã (saquinhos)', qty: '1 caixa', uso: 'Substituição' },
        { item: 'Cidreira (saquinhos)', qty: '1 caixa', uso: 'Substituição' },
      ],
    },
    {
      id: 'despensa',
      titulo: 'Despensa (itens permanentes — repor quando acabar)',
      icone: '🧂',
      itens: [
        { item: 'Sal, alho, cebola, azeite extra virgem, vinagre de maçã', qty: '—', uso: 'Cozimento' },
        { item: 'Limão', qty: '3-4/sem', uso: 'Saladas' },
        { item: 'Hipoclorito de sódio 2,5%', qty: '1 frasco', uso: 'Sanitização hortaliças' },
        { item: 'Louro, orégano, manjericão fresco', qty: '—', uso: 'Tempero' },
        { item: 'Páprica doce, cúrcuma, pimenta-do-reino', qty: '—', uso: 'Tempero' },
      ],
    },
  ],
  custo_breakdown: [
    { categoria: 'Proteína animal', faixa: 'R$ 90 – 130' },
    { categoria: 'Laticínios', faixa: 'R$ 70 – 90' },
    { categoria: 'Cereais + leguminosas', faixa: 'R$ 30 – 40' },
    { categoria: 'Hortaliças', faixa: 'R$ 50 – 70' },
    { categoria: 'Frutas', faixa: 'R$ 50 – 70' },
    { categoria: 'Sementes / oleaginosas', faixa: 'R$ 40 – 60' },
    { categoria: 'Chás (compra inicial)', faixa: 'R$ 25 – 35' },
  ],
  reposicao_meio_semana: [
    'Folhas (alface, couve, rúcula)',
    'Tomate cereja, morango',
    'Mamão (se durar < 1 semana)',
  ],
  dica_economia: 'Hortifruti (Casa do Produtor, Verdurão, CEASA terça/sábado) ~30-40% mais barato em hortaliças/frutas.',
}
