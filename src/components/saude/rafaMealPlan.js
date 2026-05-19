/**
 * RAFA_MEAL_PLAN — Plano alimentar prescrito pela nutri durante gestação.
 *
 * Source: Prescrição alimentar PDF assinada 19/05/2026.
 * Original PDF: family/pregnancy/consultas/2026-05-19_nutri_elorrane/plano_alimentar.pdf
 */
export const RAFA_MEAL_PLAN = {
  data_prescricao: '2026-05-19',
  ig_na_prescricao: '~12+1 sem',
  profissional: {
    nome: 'Dra. Elorrane Cordeiro de Oliveira',
    conselho: 'CRN-26246',
    instituto: 'Instituto Seroto Saúde Integrada',
    endereco: 'Torre Pátio Brasil, SCS Q. 7 BL A, sala 605/607 — Asa Sul, Brasília-DF',
    telefone: '(61) 99567-0621',
    convenio: 'Proasa',
  },
  observacoes: [
    'Substituições por refeição estão listadas no perfil de cada alimento; equivalentes nutricionais.',
    'Hipovitaminose D (19 ng/mL em 13/05/2026): suplementação D3 deve ser prescrita pela Dra. Nahara — plano alimentar suporta com leite desnatado, ovos e laticínios fortificados.',
    'Toxoplasmose suscetível: carnes SEMPRE muito bem passadas, lavar verduras com hipoclorito, evitar embutidos crus.',
    'HbA1c 5,4 (tendência ↑): plano controla carboidratos refinados — manter aderência durante rastreio DMG (24-28 sem).',
  ],
  refeicoes: [
    {
      id: 'lanche_escape',
      horario: '00:00',
      titulo: 'Lanche / escape',
      itens: [
        { alimento: 'Castanha de caju', quantidade: '4 unidades (10g)', substituicoes: [
          'Gelatina maracujá/morango zero açúcar (Royal) — 30g',
          'Laranja — 1 unidade média (180g)',
          'Mexerica (tangerina) — 1 unidade pequena (75g)',
          'Torrada integral — 2 unidades (20g)',
        ]},
      ],
    },
    {
      id: 'cafe_manha',
      horario: '07:30',
      titulo: 'Café-da-manhã',
      itens: [
        { alimento: 'Ovo de galinha mexido', quantidade: '2 unidades médias (90g)', substituicoes: ['Frango desfiado — 40g'] },
        { alimento: 'Cuscuz de milho cozido com sal', quantidade: '60g' },
        { alimento: 'Mamão papaia', quantidade: '1 fatia pequena (100g)' },
        { alimento: 'Leite de vaca desnatado', quantidade: '1 xícara de chá (200ml)' },
      ],
    },
    {
      id: 'colacao',
      horario: '09:30',
      titulo: 'Colação',
      itens: [
        { alimento: 'Iogurte natural', quantidade: '170g' },
        { alimento: 'Aveia em flocos', quantidade: '10g' },
        { alimento: 'Morango', quantidade: '4 unidades médias (48g)', substituicoes: [
          'Banana prata — 1 unidade média (65g)',
          'Maçã — 1 unidade média (130g)',
          'Mexerica — 1 unidade pequena (75g)',
        ]},
      ],
    },
    {
      id: 'almoco',
      horario: '12:00',
      titulo: 'Almoço',
      itens: [
        { alimento: 'Peito de frango sem pele grelhado', quantidade: '1 filé médio (100g)', substituicoes: [
          'Carne (alcatra, contrafilé, coxão mole, filé mignon, lagarto, patinho) refogada — 100g',
          'Tilápia cozida/grelhada — 120g',
          'Fígado bovino cozido/grelhado — 100g',
        ]},
        { alimento: 'Arroz integral cozido', quantidade: '80g' },
        { alimento: 'Feijão carioca cozido', quantidade: '2 colheres de servir cheias (70g)', substituicoes: [
          'Feijão preto cozido — 70g',
          'Lentilha cozida — 50g',
          'Grão de bico cozido — 40g',
        ]},
        { alimento: 'Abobrinha italiana', quantidade: '60g', substituicoes: [
          'Cenoura cozida — 50g', 'Brócolis — 50g', 'Quiabo cozido — 50g', 'Espinafre — 50g',
        ]},
        { alimento: 'Tomate', quantidade: '2 colheres de sopa cheias picado (30g)', substituicoes: ['Pepino — 20g'] },
        { alimento: 'Couve (manteiga / folhas) cozida', quantidade: 'À vontade', substituicoes: [
          'Alface americana — à vontade', 'Escarola — à vontade', 'Rúcula — à vontade', 'Agrião — à vontade',
        ]},
      ],
    },
    {
      id: 'lanche_tarde',
      horario: '15:00',
      titulo: 'Lanche (omelete)',
      itens: [
        { alimento: 'Omelete simples', quantidade: '2 unidades (130g)' },
        { alimento: 'Frango desfiado', quantidade: '2 colheres de sopa cheias (40g)' },
        { alimento: 'Tomate cereja', quantidade: '2 unidades (20g)' },
        { alimento: 'Alface', quantidade: 'À vontade' },
      ],
    },
    {
      id: 'lanche_panqueca',
      horario: '15:00',
      titulo: 'Lanche (panqueca — alternativa)',
      itens: [
        { alimento: 'Banana prata', quantidade: '1 unidade grande (100g)' },
        { alimento: 'Aveia em flocos', quantidade: '1,5 colheres de sopa cheias (22,5g)' },
        { alimento: 'Ovo de galinha', quantidade: '1 unidade (50g)' },
        { alimento: 'Pasta de amendoim', quantidade: '1 colher de sopa (16g)' },
      ],
    },
    {
      id: 'jantar',
      horario: '19:00',
      titulo: 'Jantar',
      itens: [
        { alimento: 'Peito de frango sem pele grelhado', quantidade: '1 filé médio (100g)', substituicoes: [
          'Carne (alcatra, contrafilé, coxão mole, filé mignon, lagarto, patinho) refogada — 100g',
          'Tilápia cozida/grelhada — 120g',
          'Fígado bovino cozido/grelhado — 100g',
        ]},
        { alimento: 'Purê de abóbora', quantidade: '100g', substituicoes: [
          'Purê de batata inglesa — 100g', 'Batata inglesa — 100g',
        ]},
        { alimento: 'Feijão carioca cozido', quantidade: '2 colheres de servir cheias (70g)', substituicoes: [
          'Feijão preto cozido — 70g', 'Lentilha cozida — 50g', 'Grão de bico cozido — 40g',
        ]},
        { alimento: 'Abobrinha italiana', quantidade: '60g', substituicoes: [
          'Cenoura cozida — 50g', 'Brócolis — 50g', 'Quiabo cozido — 50g', 'Espinafre — 50g',
        ]},
        { alimento: 'Tomate', quantidade: '2 colheres de sopa cheias picado (30g)', substituicoes: ['Pepino — 20g'] },
        { alimento: 'Couve cozida', quantidade: 'À vontade', substituicoes: [
          'Alface americana — à vontade', 'Escarola — à vontade', 'Rúcula — à vontade', 'Agrião — à vontade',
        ]},
      ],
    },
    {
      id: 'jantar_sopa',
      horario: '19:00',
      titulo: 'Jantar (sopa — alternativa)',
      itens: [
        { alimento: 'Peito de frango sem pele grelhado', quantidade: '1 filé médio (100g)', substituicoes: [
          'Carne refogada — 100g', 'Tilápia — 120g', 'Fígado bovino — 100g',
        ]},
        { alimento: 'Sopa de legumes', quantidade: '200g' },
      ],
    },
    {
      id: 'ceia',
      horario: '22:00',
      titulo: 'Ceia',
      itens: [
        { alimento: 'Semente de chia', quantidade: '15g', substituicoes: [
          'Semente de linhaça — 2 colheres de sobremesa cheias (20g)',
          'Granola zero açúcar — 20g',
        ]},
        { alimento: 'Iogurte natural', quantidade: '170g' },
      ],
    },
    {
      id: 'cha',
      horario: '22:00',
      titulo: 'Chá',
      itens: [
        { alimento: 'Chá de camomila', quantidade: '1 xícara de chá (200ml)', substituicoes: [
          'Chá de hortelã — 200ml', 'Chá de cidreira — 200ml',
        ]},
      ],
    },
  ],
}
