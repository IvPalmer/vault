/**
 * Mapa do Enxoval da Laura — dados dos módulos.
 *
 * ARQUIVO GERADO. Não editar à mão.
 * Fonte: scratchpad/enxoval/modules.py + icons.json, via export_vault.py.
 * O mesmo arquivo gera o PDF entregue à família, então app e PDF não divergem.
 *
 * Conteúdo apoiado em SBP, Ministério da Saúde, NHS, ANS, CONTRAN e guias
 * brasileiros de enxoval; onde as fontes divergiam, adotamos o limite inferior.
 *
 * 11 módulos · 104 itens · 77 ilustrações
 */

export const MODULES = [
  {
    "num": "00",
    "id": "como-usar",
    "title": "Como usar este mapa",
    "short": "Como usar",
    "pal": "sand",
    "win": "o segredo é o timing",
    "intro": "Enxoval não se compra de uma vez — se compra em janelas. Cedo demais é palpite sobre tamanho e estação; tarde demais é correria. Cada módulo traz a sua janela em semanas de gestação.",
    "inIndex": false,
    "buyWindow": null,
    "spot": "tamanhos",
    "blocks": [
      {
        "kind": "timeline",
        "rows": [
          {
            "when": "até a 20ª",
            "what": "<b>Pesquisa.</b> Listas, preços, o que pedir emprestado e o que aceitar de doação. Comprar quase nada."
          },
          {
            "when": "20 a 24",
            "what": "<b>Definição.</b> Depois da morfológica, decidir o que entra. Móveis grandes: encomendar agora, por causa do prazo de entrega."
          },
          {
            "when": "24 a 32",
            "hot": true,
            "what": "<b>Janela principal.</b> Roupas e quarto, com tempo de pesquisar preço."
          },
          {
            "when": "28 a 36",
            "hot": true,
            "what": "<b>Reta final.</b> Banho, fraldas e amamentação a partir da 28; farmacinha a partir da 30; mala pronta na porta até a 34."
          },
          {
            "when": "até a 36",
            "hot": true,
            "what": "<b>Bebê conforto instalado e testado no carro</b>, e todas as roupinhas lavadas e guardadas."
          },
          {
            "when": "pós-parto",
            "what": "<b>Só prazos.</b> Documentos e triagens — módulo 09. Nada de compra."
          }
        ]
      },
      {
        "kind": "tip",
        "title": "três regras que valem para o mapa inteiro",
        "body": "<b>1.</b> Tamanho é peso, não idade — dois bebês da mesma idade podem ter 2 kg de diferença. <b>2.</b> A quantidade depende do seu ciclo de lavagem, não da lista. <b>3.</b> Na dúvida, comprem menos: falta se resolve em uma tarde, sobra vira armário cheio de coisa que ela nunca usou."
      }
    ]
  },
  {
    "num": "01",
    "id": "roupinhas",
    "title": "Roupinhas",
    "short": "Roupinhas",
    "pal": "terra",
    "win": "comprar entre as semanas 24–32",
    "intro": "Laura nasce no verão de Brasília, mas o clima real dela é o do ar-condicionado. Por isso a lista tem manga curta em peso e manga longa fininha — não é contradição, é as duas temperaturas do dia.",
    "inIndex": true,
    "buyWindow": [
      24,
      32
    ],
    "spot": "roupas",
    "blocks": [
      {
        "kind": "table",
        "title": "Tamanho é peso, não idade",
        "head": [
          "Tam.",
          "Peso",
          "Altura",
          "Idade aprox.",
          "Quanto dura"
        ],
        "rows": [
          [
            "RN",
            "2,5–4 kg",
            "46–52 cm",
            "0–1 mês",
            "2 a 4 semanas"
          ],
          [
            "P",
            "4–6 kg",
            "53–60 cm",
            "1–3 meses",
            "6 a 10 semanas"
          ],
          [
            "M",
            "6–8 kg",
            "61–66 cm",
            "3–6 meses",
            "~3 meses"
          ],
          [
            "G",
            "8–9 kg",
            "67–72 cm",
            "6–9 meses",
            "~3 meses"
          ],
          [
            "GG",
            "9–10 kg",
            "73–78 cm",
            "9–12 meses",
            "~3 meses"
          ]
        ],
        "note": "Peso primeiro, altura como desempate, idade por último — dois bebês da mesma idade podem ter 2 kg de diferença. Carter's e marcas americanas usam NB/3M/6M/9M, equivalentes a RN/P/M/G. Na dúvida entre dois tamanhos, pegue o maior."
      },
      {
        "kind": "tip",
        "title": "a conta que define a quantidade",
        "body": "Recém-nascido troca de roupa <b>3 a 4 vezes por dia</b>. A fórmula é <b>(trocas por dia) × (dias entre lavagens) + 2 de folga</b>. Lavando dia sim dia não: 4 × 2 + 2 = 10 bodies no P. Jan/fev é estação chuvosa em Brasília e roupa demora a secar — sem secadora, somem 2 a 3 peças por item em RN e P."
      },
      {
        "kind": "groups",
        "groups": [
          {
            "name": "Tamanho RN · deliberadamente enxuto",
            "items": [
              {
                "id": "01-tamanho-rn-deliberadamente-enxuto-body-manga-curta",
                "label": "Body manga curta",
                "icon": "body-mc",
                "qty": "5",
                "ess": true,
                "note": "Peça mais usada de todas. Dura só 2–4 semanas neste tamanho."
              },
              {
                "id": "01-tamanho-rn-deliberadamente-enxuto-body-manga-longa-de-algodao-fino",
                "label": "Body manga longa de algodão fino",
                "icon": "body-ml",
                "qty": "3",
                "note": "Não é para frio — é para o ar-condicionado."
              },
              {
                "id": "01-tamanho-rn-deliberadamente-enxuto-mijao-culote",
                "label": "Mijão / culote",
                "icon": "mijao",
                "qty": "4",
                "note": "Cós largo, sem elástico apertado."
              },
              {
                "id": "01-tamanho-rn-deliberadamente-enxuto-macacao-manga-longa-com-pe",
                "label": "Macacão manga longa com pé",
                "icon": "macacao",
                "qty": "3",
                "ess": true,
                "note": "Peça de dormir. Abertura frontal facilita a troca da madrugada."
              },
              {
                "id": "01-tamanho-rn-deliberadamente-enxuto-macaquinho-macacao-manga-curta",
                "label": "Macaquinho / macacão manga curta",
                "icon": "macaquinho",
                "qty": "2"
              },
              {
                "id": "01-tamanho-rn-deliberadamente-enxuto-pagao",
                "label": "Pagão",
                "icon": "pagao",
                "qty": "1"
              },
              {
                "id": "01-tamanho-rn-deliberadamente-enxuto-meias",
                "label": "Meias",
                "icon": "meias",
                "qty": "3 pares"
              },
              {
                "id": "01-tamanho-rn-deliberadamente-enxuto-casaquinho-de-algodao",
                "label": "Casaquinho de algodão",
                "icon": "casaquinho",
                "qty": "2"
              },
              {
                "id": "01-tamanho-rn-deliberadamente-enxuto-touca-de-maternidade",
                "label": "Touca de maternidade",
                "icon": "touca",
                "qty": "1",
                "note": "Para a saída e o ar-condicionado. Nunca para dormir."
              },
              {
                "id": "01-tamanho-rn-deliberadamente-enxuto-saida-de-maternidade",
                "label": "Saída de maternidade",
                "icon": "saida",
                "qty": "1",
                "note": "De algodão, não tricô nem plush — bebê de janeiro."
              },
              {
                "id": "01-tamanho-rn-deliberadamente-enxuto-manta-leve-de-musselina",
                "label": "Manta leve de musselina",
                "icon": "manta-leve",
                "qty": "2",
                "ess": true
              },
              {
                "id": "01-tamanho-rn-deliberadamente-enxuto-manta-media-soft-fino",
                "label": "Manta média (soft fino)",
                "icon": "manta-media",
                "qty": "1"
              }
            ]
          },
          {
            "name": "Tamanho P · o investimento principal",
            "items": [
              {
                "id": "01-tamanho-p-o-investimento-principal-body-manga-curta",
                "label": "Body manga curta",
                "icon": "body-mc",
                "qty": "8",
                "ess": true,
                "note": "É a base de tudo no verão."
              },
              {
                "id": "01-tamanho-p-o-investimento-principal-body-manga-longa-fino",
                "label": "Body manga longa fino",
                "icon": "body-ml",
                "qty": "4"
              },
              {
                "id": "01-tamanho-p-o-investimento-principal-body-regata",
                "label": "Body regata",
                "icon": "body-regata",
                "qty": "3"
              },
              {
                "id": "01-tamanho-p-o-investimento-principal-mijao-culote",
                "label": "Mijão / culote",
                "icon": "mijao",
                "qty": "6"
              },
              {
                "id": "01-tamanho-p-o-investimento-principal-macacao-manga-longa-com-pe",
                "label": "Macacão manga longa com pé",
                "icon": "macacao",
                "qty": "5",
                "ess": true
              },
              {
                "id": "01-tamanho-p-o-investimento-principal-macaquinho-manga-curta",
                "label": "Macaquinho manga curta",
                "icon": "macaquinho",
                "qty": "5",
                "ess": true,
                "note": "Peça-chave do verão."
              },
              {
                "id": "01-tamanho-p-o-investimento-principal-shorts",
                "label": "Shorts",
                "icon": "shorts",
                "qty": "3"
              },
              {
                "id": "01-tamanho-p-o-investimento-principal-casaquinho-cardiga-leve",
                "label": "Casaquinho / cardigã leve",
                "icon": "casaquinho",
                "qty": "2"
              },
              {
                "id": "01-tamanho-p-o-investimento-principal-meias",
                "label": "Meias",
                "icon": "meias",
                "qty": "5 pares"
              },
              {
                "id": "01-tamanho-p-o-investimento-principal-chapeu-de-sol-de-algodao",
                "label": "Chapéu de sol de algodão",
                "icon": "chapeu",
                "qty": "2",
                "note": "UV de Brasília é alto o ano todo."
              },
              {
                "id": "01-tamanho-p-o-investimento-principal-manta-leve",
                "label": "Manta leve",
                "icon": "manta-leve",
                "qty": "2"
              },
              {
                "id": "01-tamanho-p-o-investimento-principal-vestidinho-conjunto",
                "label": "Vestidinho / conjunto",
                "icon": "vestido",
                "qty": "2",
                "note": "Uso ocasional — comprar pouco."
              }
            ]
          },
          {
            "name": "Sem tamanho · compra única",
            "items": [
              {
                "id": "01-sem-tamanho-compra-unica-fralda-de-pano-pano-de-boca",
                "label": "Fralda de pano / pano de boca",
                "icon": "pano",
                "qty": "15",
                "ess": true,
                "note": "Item mais versátil do enxoval: golfada, ombro, sombra, forrar trocador."
              },
              {
                "id": "01-sem-tamanho-compra-unica-babador",
                "label": "Babador",
                "icon": "babador",
                "qty": "4",
                "note": "Sobe para 6–8 na introdução alimentar (~6 meses)."
              },
              {
                "id": "01-sem-tamanho-compra-unica-cueiro",
                "label": "Cueiro",
                "icon": "cueiro",
                "qty": "2",
                "note": "Uso decrescente — muitas famílias abandonam em semanas."
              },
              {
                "id": "01-sem-tamanho-compra-unica-lavar-tudo-antes-do-primeiro-uso",
                "label": "Lavar tudo antes do primeiro uso",
                "icon": "lavar",
                "ess": true,
                "note": "Sabão de coco ou neutro, enxágue duplo, SEM amaciante. Fazer por volta da semana 30–34. Remover etiquetas ásperas da nuca."
              }
            ]
          }
        ]
      },
      {
        "kind": "table",
        "title": "Como vestir para dormir, por temperatura do quarto",
        "head": [
          "Temperatura",
          "Saco de dormir",
          "Por baixo"
        ],
        "rows": [
          [
            "acima de 24 °C",
            "TOG 0,5",
            "só body manga curta"
          ],
          [
            "20–23 °C (ar-cond.)",
            "TOG 1,0",
            "body manga curta + macacão leve"
          ],
          [
            "18–20 °C",
            "TOG 2,5",
            "body manga longa + macacão"
          ]
        ],
        "note": "Com saco de dormir, não somar cobertor por cima — se estiver frio, aumente o TOG ou a camada de roupa. Sinal de superaquecimento: pele úmida na nuca e no peito. Superaquecer é mais perigoso que estar levemente frio."
      },
      {
        "kind": "tip",
        "title": "o que comprar depois, e quando",
        "body": "<b>Março/abril</b> (tamanho M, para usar de abr a jul): 8 bodies manga curta, 8 manga longa, 6 calças, 6 macacões com pé, 2 de plush, 3 casaquinhos de moletom, saco TOG 2,5. <b>Maio/junho</b> (tamanho G): o inverno seco de Brasília chega a 12–15 °C ao amanhecer com a Laura em M/G — é aí, e só aí, que peça de frio se justifica. Comprar M/G antes do parto é aposta: o ritmo de crescimento é imprevisível."
      },
      {
        "kind": "avoid",
        "items": [
          "Estocar tamanho RN — dura 2 a 4 semanas e muito bebê já nasce vestindo P.",
          "Luvinhas: cobrir as mãos limita o desenvolvimento sensorial. 1 par, no máximo.",
          "Sapatinhos antes de 1 ano — decorativos, e o bebê se irrita com eles.",
          "Macacão de plush em RN e P: ela nunca vai usar em janeiro.",
          "Faixa umbilical — sem respaldo pediátrico atual.",
          "Amaciante: deixa película perfumada que não sai no enxágue e irrita a pele.",
          "Cordões e laços soltos perto do pescoço (proibidos por norma até 7 anos).",
          "Laço/faixa de cabelo para dormir — risco de garroteamento e asfixia.",
          "Comprar tudo antes do chá de bebê: bodies e mantas são justamente o que mais ganham."
        ]
      }
    ]
  },
  {
    "num": "02",
    "id": "sono-seguro",
    "title": "Quarto & sono seguro",
    "short": "Sono seguro",
    "pal": "blue",
    "win": "comprar entre as semanas 24–32",
    "intro": "A regra que organiza tudo aqui: berço vazio. Colchão firme, lençol bem esticado e nada mais dentro dele no primeiro ano. O resto do quarto é conforto de vocês dois — e, em Brasília, briga contra o ar seco.",
    "inIndex": true,
    "buyWindow": [
      24,
      32
    ],
    "spot": "sono",
    "blocks": [
      {
        "kind": "table",
        "title": "Berço e colchão — o que a norma exige",
        "head": [
          "Item",
          "Especificação",
          "Por quê"
        ],
        "rows": [
          [
            "Espaço entre grades",
            "máximo 6 cm",
            "cabeça e mãos não passam"
          ],
          [
            "Folga colchão–grade",
            "máximo 3 cm",
            "evita aprisionamento"
          ],
          [
            "Altura da grade",
            "mínimo 60 cm",
            "impede queda quando ela ficar de pé"
          ],
          [
            "Densidade do colchão",
            "mínimo D18",
            "firmeza reduz risco de sufocação"
          ],
          [
            "Altura do colchão",
            "10–12 cm",
            "padrão de berço certificado"
          ]
        ],
        "note": "Berço padrão usa colchão de 130×60 cm; mini-berço, 86×38 cm; berço acoplado (co-sleeper), ~75×67 cm e suporta até 9 kg. Exijam selo do Inmetro e tinta atóxica. A NBR 15860 foi revisada e o espaçamento máximo caiu de 6,5 para 6 cm — berço antigo ou de segunda mão pode estar na norma velha. Teste prático da folga: não deve caber mais que dois dedos entre o colchão e a grade."
      },
      {
        "kind": "items",
        "items": [
          {
            "id": "02-berco-certificado-inmetro",
            "label": "Berço certificado Inmetro",
            "icon": "berco",
            "qty": "1",
            "ess": true,
            "note": "Considerem o modelo acoplado à cama: atende à recomendação de dividir o quarto sem dividir a superfície de sono."
          },
          {
            "id": "02-colchao-firme-no-tamanho-exato",
            "label": "Colchão firme no tamanho exato",
            "icon": "colchao",
            "qty": "1",
            "ess": true,
            "note": "Sem frestas nas laterais. Firme de verdade — colchão macio é fator de risco."
          },
          {
            "id": "02-lencol-de-elastico",
            "label": "Lençol de elástico",
            "icon": "lencol",
            "qty": "3",
            "ess": true,
            "note": "Um na cama, dois em revezamento."
          },
          {
            "id": "02-protetor-de-colchao-impermeavel",
            "label": "Protetor de colchão impermeável",
            "icon": "protetor-colchao",
            "qty": "1–2",
            "ess": true
          },
          {
            "id": "02-saco-de-dormir",
            "label": "Saco de dormir",
            "icon": "saco-dormir",
            "qty": "1 de TOG 0,5 + 1 de TOG 1,0",
            "ess": true,
            "note": "Os dois cobrem o verão; o TOG 2,5 só faz sentido comprar em maio, para a seca. Ver a tabela de temperatura no módulo 01."
          },
          {
            "id": "02-manta-leve-respiravel",
            "label": "Manta leve respirável",
            "icon": "manta-leve",
            "qty": "3–4",
            "note": "Multiuso, nunca solta dentro do berço."
          },
          {
            "id": "02-umidificador-ultrassonico",
            "label": "Umidificador ultrassônico",
            "icon": "umidificador",
            "qty": "1",
            "ess": true,
            "note": "Brasília é o motivo. Ver o quadro abaixo antes de usar."
          },
          {
            "id": "02-comoda-com-trocador",
            "label": "Cômoda com trocador",
            "icon": "comoda",
            "qty": "1",
            "note": "Altura na cintura evita dor nas costas."
          },
          {
            "id": "02-poltrona-de-amamentacao",
            "label": "Poltrona de amamentação",
            "icon": "poltrona",
            "qty": "1",
            "note": "Vai ser usada 10 a 15 vezes por dia nos primeiros meses — vale investir no conforto."
          },
          {
            "id": "02-baba-eletronica",
            "label": "Babá eletrônica",
            "icon": "baba-eletronica",
            "qty": "1",
            "note": "Com câmera e visão noturna, se couber no orçamento."
          },
          {
            "id": "02-luz-noturna-ambar-ou-vermelha",
            "label": "Luz noturna âmbar ou vermelha",
            "icon": "luz-noturna",
            "qty": "1",
            "ess": true,
            "note": "Cor importa: luz azul e branca suprimem melatonina. 0,5–2 W bastam."
          },
          {
            "id": "02-cortina-blackout",
            "label": "Cortina blackout",
            "icon": "cortina",
            "qty": "1",
            "note": "Ajuda no sono diurno e na volta ao sono de madrugada."
          }
        ]
      },
      {
        "kind": "tip",
        "title": "umidificador — o item mais brasiliense da lista",
        "body": "Na seca a umidade daqui cai bem abaixo dos <b>50–60%</b> que a OMS considera saudável, e ar seco resseca a via aérea da Laura. Use o ultrassônico por <b>2 a 3 horas à noite</b>, não a noite toda — excesso de umidade gera mofo, que é pior que o ar seco. <b>Troque a água a cada 12 h</b> e limpe o filtro uma vez por semana, sem falta: umidificador sujo vira nebulizador de fungo."
      },
      {
        "kind": "tip",
        "title": "sono seguro — o essencial da SBP e da AAP",
        "body": "<b>Sempre de barriga para cima</b>, nunca de lado ou de bruços. Quarto entre <b>20 e 24 °C</b> (ideal 22–23). Ela deve dormir <b>no quarto de vocês, em berço próprio, dos 6 aos 12 meses</b> — isso reduz o risco de morte súbita. E o berço fica vazio: sem travesseiro, sem protetor, sem bicho de pelúcia, sem coberta solta."
      },
      {
        "kind": "avoid",
        "title": "melhor evitar — sério mesmo · risco de sufocação",
        "items": [
          "Travesseiro de qualquer tipo, inclusive \"anatômico\", antes de 12 meses.",
          "Protetor de berço / kit berço acolchoado.",
          "Cobertas soltas, almofadas e bichos de pelúcia dentro do berço.",
          "Ninho ou redutor de berço para dormir sem supervisão.",
          "Dormir no bebê conforto, no carrinho ou no sofá como rotina.",
          "Móbile com som alto ou peças pequenas ao alcance.",
          "Aquecedor de mamadeira e termômetro de banheira — dinheiro jogado fora."
        ]
      }
    ]
  },
  {
    "num": "03",
    "id": "banho",
    "title": "Banho & higiene",
    "short": "Banho",
    "pal": "sage",
    "win": "comprar entre as semanas 28–34",
    "intro": "Nas primeiras semanas, menos é mais: água morna resolve quase tudo. A pele dela ainda está montando a própria barreira — produto demais atrapalha.",
    "inIndex": true,
    "buyWindow": [
      28,
      34
    ],
    "spot": "banho",
    "blocks": [
      {
        "kind": "items",
        "items": [
          {
            "id": "03-banheira-com-suporte",
            "label": "Banheira com suporte",
            "icon": "banheira",
            "qty": "1",
            "ess": true,
            "note": "Apoio firme é o que importa; a pia também serve."
          },
          {
            "id": "03-toalha-com-capuz",
            "label": "Toalha com capuz",
            "icon": "toalha",
            "qty": "2–3",
            "ess": true,
            "note": "100% algodão, bem macia."
          },
          {
            "id": "03-sabonete-liquido-neutro",
            "label": "Sabonete líquido neutro",
            "icon": "sabonete",
            "qty": "1 · 200–250 ml",
            "note": "Sem fragrância. Nas primeiras semanas, água já dá conta da maior parte do corpo."
          },
          {
            "id": "03-algodao",
            "label": "Algodão",
            "icon": "algodao",
            "qty": "500 g a 1 kg por mês",
            "ess": true,
            "note": "Item que todo mundo subestima: usa-se a cada troca de fralda. Compre por peso — as embalagens variam de 25 g a 500 g e comparar \"pacotes\" engana."
          },
          {
            "id": "03-pente-ou-escova-macia",
            "label": "Pente ou escova macia",
            "icon": "pente",
            "qty": "1"
          },
          {
            "id": "03-tesourinha-de-ponta-redonda-ou-cortador",
            "label": "Tesourinha de ponta redonda ou cortador",
            "icon": "tesourinha",
            "qty": "1",
            "note": "Cortar com ela dormindo é infinitamente mais fácil."
          },
          {
            "id": "03-termometro-de-banho",
            "label": "Termômetro de banho",
            "icon": "termometro-banho",
            "qty": "1",
            "note": "Opcional — o punho ou o cotovelo testam igual."
          }
        ]
      },
      {
        "kind": "tip",
        "title": "coto umbilical — a recomendação mudou",
        "body": "O padrão atual da OMS para parto hospitalar é manter o coto <b>limpo e seco</b>, sem antisséptico. Álcool 70% de rotina <b>não é mais recomendado</b> nesse cenário: não reduz infecção onde o risco já é baixo e ainda atrasa a queda em cerca de um dia. Na prática: lave com água e sabão no banho, <b>sequem bem</b>, e dobrem a fralda para baixo do coto para deixá-lo arejado. Cai sozinho entre <b>7 e 14 dias</b> — nunca puxe. Procurem o pediatra se houver odor forte, secreção com pus, vermelhidão ao redor ou febre acima de 38 °C."
      },
      {
        "kind": "table",
        "title": "Banho, na prática",
        "head": [
          "Pergunta",
          "Resposta"
        ],
        "rows": [
          [
            "Com que frequência?",
            "diário é seguro; 2–3× por semana também basta"
          ],
          [
            "Temperatura da água",
            "36–37 °C"
          ],
          [
            "Duração",
            "5 a 10 minutos"
          ],
          [
            "Antes do coto cair",
            "a AAP prefere banho de esponja; confirme com o pediatra"
          ],
          [
            "O que limpar sempre",
            "pregas de pele, região da fralda e o coto"
          ]
        ],
        "note": "O que não pode faltar é a limpeza das dobrinhas e da área da fralda — o banho inteiro é menos crítico do que isso."
      },
      {
        "kind": "avoid",
        "items": [
          "Cotonete dentro do ouvido ou do nariz.",
          "Talco — risco de aspiração.",
          "Perfume, colônia e sabonete adulto nos primeiros meses.",
          "Amarrar o coto com fio, moeda ou faixa umbilical.",
          "Esfregar a pele; secar sempre por leves toques."
        ]
      }
    ]
  },
  {
    "num": "04",
    "id": "fraldas",
    "title": "Fraldas & troca",
    "short": "Fraldas",
    "pal": "terra",
    "win": "comprar entre as semanas 28–36",
    "intro": "O erro clássico é estocar RN. A fase dura duas ou três semanas e a marca pode simplesmente não servir na pele dela — melhor errar para menos.",
    "inIndex": true,
    "buyWindow": [
      28,
      36
    ],
    "spot": "fraldas",
    "blocks": [
      {
        "kind": "table",
        "title": "Consumo real por tamanho",
        "head": [
          "Tam.",
          "Peso",
          "Por dia",
          "Quanto dura"
        ],
        "rows": [
          [
            "RN",
            "até 4,5 kg",
            "8 a 10",
            "2 a 3 semanas"
          ],
          [
            "P",
            "4–8 kg",
            "7 a 10",
            "até 2 meses"
          ],
          [
            "M",
            "6–11 kg",
            "5 a 7",
            "3 a 7 meses"
          ],
          [
            "G",
            "9–13 kg",
            "4 a 5",
            "9 a 13 meses"
          ]
        ],
        "note": "A fase RN consome de 110 a 210 fraldas, conforme ela nasça grande ou pequena; 120–180 cobre a maioria dos casos sem sobrar caixa fechada. Um pacote traz de 20 a 40 unidades, dependendo da marca — compre pensando em unidades, não em pacotes."
      },
      {
        "kind": "items",
        "items": [
          {
            "id": "04-fralda-descartavel-rn",
            "label": "Fralda descartável RN",
            "icon": "fralda",
            "qty": "120–180 unidades",
            "ess": true,
            "note": "Cobre a fase inteira sem sobrar caixa fechada em casa."
          },
          {
            "id": "04-fralda-descartavel-p",
            "label": "Fralda descartável P",
            "icon": "fralda-pacote",
            "qty": "3–4 pacotes",
            "note": "O grosso do estoque vai ser P e M — é o melhor pedido de chá de bebê."
          },
          {
            "id": "04-trocador-fixo-portatil",
            "label": "Trocador fixo + portátil",
            "icon": "trocador",
            "qty": "1 + 1",
            "ess": true
          },
          {
            "id": "04-pomada-de-prevencao-de-assadura",
            "label": "Pomada de prevenção de assadura",
            "icon": "pomada",
            "qty": "2–3",
            "ess": true,
            "note": "Camada fina a cada troca. Prevenção e tratamento são produtos diferentes."
          },
          {
            "id": "04-algodao-para-a-troca",
            "label": "Algodão para a troca",
            "icon": "algodao",
            "qty": "ver módulo 03",
            "ess": true,
            "note": "Água morna + algodão é o padrão em casa para recém-nascido."
          },
          {
            "id": "04-lencos-umedecidos-sem-alcool-e-sem-perfume",
            "label": "Lenços umedecidos sem álcool e sem perfume",
            "icon": "lencos",
            "qty": "1–2 pacotes por mês",
            "note": "Para a rua. Uso diário em casa pode irritar a pele nova."
          },
          {
            "id": "04-lixeira-com-tampa",
            "label": "Lixeira com tampa",
            "icon": "lixeira",
            "qty": "1"
          }
        ]
      },
      {
        "kind": "tip",
        "title": "água e algodão × lenço umedecido",
        "body": "Para recém-nascido em casa, a recomendação é <b>algodão com água morna</b> — o lenço umedecido é conveniência de rua, não rotina. Para xixi, algodão basta; para cocô, água corrente limpa melhor e machuca menos. Nunca esfreguem: limpem com toques."
      },
      {
        "kind": "avoid",
        "items": [
          "Comprar caixas da mesma marca antes de testar na pele dela.",
          "Lenço umedecido com álcool, parabeno, corante ou fragrância.",
          "Estocar tamanho RN — é o tamanho que menos dura."
        ]
      }
    ]
  },
  {
    "num": "05",
    "id": "farmacinha",
    "title": "Farmacinha & saúde",
    "short": "Farmacinha",
    "pal": "rose",
    "win": "comprar entre as semanas 30–36",
    "intro": "Farmacinha de bebê é de suporte, não de tratamento. Nada de medicamento sem prescrição — dose de criança é por peso e muda de mês para mês.",
    "inIndex": true,
    "buyWindow": [
      30,
      36
    ],
    "spot": "farmacinha",
    "blocks": [
      {
        "kind": "items",
        "items": [
          {
            "id": "05-termometro-digital",
            "label": "Termômetro digital",
            "icon": "termometro",
            "qty": "1–2",
            "ess": true,
            "note": "Axilar ou infravermelho. Mercúrio é proibido no Brasil."
          },
          {
            "id": "05-soro-fisiologico-0-9",
            "label": "Soro fisiológico 0,9%",
            "icon": "soro",
            "qty": "2–3 caixas por mês",
            "ess": true,
            "note": "Higiene nasal e ocular — em Brasília, uso quase diário na seca."
          },
          {
            "id": "05-aspirador-nasal",
            "label": "Aspirador nasal",
            "icon": "aspirador",
            "qty": "1",
            "note": "Ponta macia."
          },
          {
            "id": "05-gaze-esteril",
            "label": "Gaze estéril",
            "icon": "gaze",
            "qty": "2–3 pacotes"
          },
          {
            "id": "05-alcool-70",
            "label": "Álcool 70%",
            "icon": "alcool",
            "qty": "1 frasco",
            "note": "Para superfície e para as mãos de quem pega no colo — não para a pele dela."
          },
          {
            "id": "05-antitermico-prescrito-pelo-pediatra",
            "label": "Antitérmico prescrito pelo pediatra",
            "icon": "receita",
            "ess": true,
            "note": "Peçam a receita com a dose por peso ANTES de precisar, na consulta pré-natal pediátrica. Às 3 da manhã não dá para improvisar."
          },
          {
            "id": "05-lista-de-contatos-na-geladeira",
            "label": "Lista de contatos na geladeira",
            "icon": "contatos",
            "ess": true,
            "note": "Pediatra, maternidade, SAMU 192."
          }
        ]
      },
      {
        "kind": "tip",
        "title": "febre — quando ligar para o pediatra",
        "body": "Considera-se febre a partir de <b>37,8–38 °C axilar</b>. Em bebê com <b>menos de 3 meses, qualquer febre é motivo de avaliação médica no mesmo dia</b> — não espere passar e não medique por conta. Antitérmico só com prescrição, na dose calculada pelo peso atual."
      },
      {
        "kind": "tip",
        "title": "G6PD — o que muda por causa do papai",
        "body": "A deficiência de G6PD é ligada ao cromossomo X. Como o Palmer tem a condição, ele passa o único X dele para todas as filhas: a Laura será <b>portadora obrigatória</b> — não é probabilidade, é certeza. Portadoras costumam ser assintomáticas, mas a inativação aleatória do X faz a atividade da enzima variar bastante, e algumas têm deficiência clinicamente relevante. Duas providências: <b>peça o teste do pezinho ampliado</b> (a versão básica não dosa G6PD) e <b>registre a condição no prontuário dela</b>, para que qualquer médico ou dentista saiba antes de prescrever."
      },
      {
        "kind": "avoid",
        "title": "substâncias a evitar — G6PD",
        "items": [
          "Sulfas (sulfametoxazol) e nitrofurantoína.",
          "Antimaláricos, especialmente primaquina.",
          "Ácido acetilsalicílico (aspirina) em dose alta.",
          "Naftalina e cânfora — tirar de casa antes dela chegar.",
          "Fava e derivados.",
          "Antitérmico ou antigripal por conta própria — sempre confirmar com o pediatra.",
          "Mel antes de 1 ano — risco de botulismo infantil (vale para qualquer bebê)."
        ]
      }
    ]
  },
  {
    "num": "06",
    "id": "amamentacao",
    "title": "Amamentação",
    "short": "Amamentação",
    "pal": "terra",
    "win": "comprar entre as semanas 28–36",
    "intro": "Aleitamento exclusivo até os 6 meses é a recomendação da OMS e do Ministério da Saúde. Compre o mínimo antes: o que vocês vão precisar de verdade só aparece na segunda semana.",
    "inIndex": true,
    "buyWindow": [
      28,
      36
    ],
    "spot": "amamentacao",
    "blocks": [
      {
        "kind": "items",
        "items": [
          {
            "id": "06-sutia-de-amamentacao",
            "label": "Sutiã de amamentação",
            "icon": "sutia",
            "qty": "3–4",
            "ess": true,
            "note": "Comprar a partir da semana 36 — o peito muda muito até lá. Algodão, sem aro."
          },
          {
            "id": "06-absorvente-de-seio",
            "label": "Absorvente de seio",
            "icon": "absorvente-seio",
            "qty": "1–2 caixas por mês",
            "note": "Ou 4–6 pares laváveis, se preferirem reutilizável."
          },
          {
            "id": "06-lanolina-pura",
            "label": "Lanolina pura",
            "icon": "lanolina",
            "qty": "1 bisnaga de 30 g",
            "ess": true,
            "note": "Para fissura. Reaplicar depois das mamadas."
          },
          {
            "id": "06-camisola-com-abertura-frontal",
            "label": "Camisola com abertura frontal",
            "icon": "camisola",
            "qty": "3–4",
            "note": "A mala da maternidade sozinha já leva de 3 a 4 — ver módulo 08."
          },
          {
            "id": "06-almofada-de-amamentacao",
            "label": "Almofada de amamentação",
            "icon": "almofada",
            "qty": "1",
            "note": "Opcional, mas salva as costas."
          },
          {
            "id": "06-contato-de-consultora-de-amamentacao",
            "label": "Contato de consultora de amamentação",
            "icon": "apoio",
            "ess": true,
            "note": "Resolver ANTES do parto. As primeiras 48 h definem muita coisa."
          },
          {
            "id": "06-potes-ou-sacos-para-armazenar-leite",
            "label": "Potes ou sacos para armazenar leite",
            "icon": "potes-leite",
            "qty": "1 kit",
            "note": "Só se houver plano de extrair — não compre por precaução."
          }
        ]
      },
      {
        "kind": "table",
        "title": "Armazenamento do leite materno",
        "head": [
          "Onde",
          "Por quanto tempo"
        ],
        "rows": [
          [
            "Temperatura ambiente",
            "2 horas (1 h em dia quente)"
          ],
          [
            "Geladeira (4 °C)",
            "12 horas — prateleira alta, nunca na porta"
          ],
          [
            "Freezer (−18 °C)",
            "15 dias"
          ],
          [
            "Depois de descongelado",
            "12 horas na geladeira"
          ]
        ],
        "note": "Descongelem em banho-maria, nunca no micro-ondas — o calor irregular destrói as imunoglobulinas. Leite descongelado não volta ao freezer."
      },
      {
        "kind": "table",
        "title": "Ela está mamando o suficiente?",
        "head": [
          "Sinal",
          "Esperado"
        ],
        "rows": [
          [
            "Fraldas molhadas",
            "6 a 8 por dia, a partir do 5º dia"
          ],
          [
            "Cor da urina",
            "clara ou levemente amarelada"
          ],
          [
            "Ganho de peso (0–4 meses)",
            "150 a 200 g por semana"
          ],
          [
            "Peso na 1ª semana",
            "perda de até 10% é normal; recupera até o 14º dia"
          ],
          [
            "Fezes",
            "mecônio escuro → amareladas pastosas a partir do 3º dia"
          ]
        ],
        "note": "Ela soltar o peito sozinha, relaxar as mãozinhas e dormir depois da mamada também são bons sinais."
      },
      {
        "kind": "tip",
        "title": "bancos de leite no DF — apoio gratuito",
        "body": "O DF tem rede de bancos de leite que também <b>orientam sobre pega e ordenha, de graça</b>: Hospital Materno Infantil (Asa Sul), Maternidade Brasília (Sudoeste), Hospital Regional de Santa Maria e Hospital Universitário de Brasília. Informações pelo <b>Disque Saúde 160</b>. Vale anotar isso na geladeira junto com os telefones de emergência."
      },
      {
        "kind": "avoid",
        "items": [
          "Comprar bomba extratora antes do parto — alugue ou teste a manual primeiro.",
          "Chupeta e mamadeira antes de 3 a 4 semanas: risco de confusão de bicos e desmame precoce.",
          "Micro-ondas para aquecer leite materno.",
          "Estocar fórmula \"por precaução\" antes de qualquer avaliação."
        ]
      }
    ]
  },
  {
    "num": "07",
    "id": "passeio",
    "title": "Passeio & transporte",
    "short": "Passeio",
    "pal": "sage",
    "win": "comprar entre as semanas 28–36",
    "intro": "Brasília é cidade de carro, então o bebê conforto não é acessório: é o item que precisa estar instalado e testado antes de vocês saírem de casa para a maternidade.",
    "inIndex": true,
    "buyWindow": [
      28,
      36
    ],
    "spot": "passeio",
    "blocks": [
      {
        "kind": "table",
        "title": "O que a lei exige — CONTRAN 819/2021",
        "head": [
          "Dispositivo",
          "Idade / peso",
          "Como usar"
        ],
        "rows": [
          [
            "Bebê conforto",
            "até 1 ano ou 13 kg",
            "de costas, banco traseiro"
          ],
          [
            "Cadeirinha",
            "1 a 4 anos ou 9–18 kg",
            "banco traseiro"
          ],
          [
            "Assento de elevação",
            "4 a 7,5 anos ou 15–36 kg",
            "banco traseiro, com cinto"
          ]
        ],
        "note": "A obrigação vale até 10 anos ou 1,45 m de altura. Exijam o selo do Inmetro. A validade vem gravada no plástico — o polímero degrada e perde capacidade de absorver impacto."
      },
      {
        "kind": "items",
        "items": [
          {
            "id": "07-bebe-conforto-grupo-0",
            "label": "Bebê conforto grupo 0+",
            "icon": "bebe-conforto",
            "qty": "1",
            "ess": true,
            "note": "Instalar e testar até a semana 36. Se o carro tiver ISOFIX, use — reduz muito a chance de instalação errada."
          },
          {
            "id": "07-carrinho-com-reclinio-de-170180",
            "label": "Carrinho com reclínio de 170–180°",
            "icon": "carrinho",
            "qty": "1",
            "ess": true,
            "note": "Recém-nascido precisa ir deitado: sentado, o queixo cai no peito e comprime a via aérea."
          },
          {
            "id": "07-sling-ou-canguru-ergonomico",
            "label": "Sling ou canguru ergonômico",
            "icon": "sling",
            "qty": "1",
            "note": "Ergonômico de verdade, não o modelo que deixa a criança pendurada pela virilha."
          },
          {
            "id": "07-bolsa-de-passeio-com-trocador-portatil",
            "label": "Bolsa de passeio com trocador portátil",
            "icon": "bolsa",
            "qty": "1"
          },
          {
            "id": "07-sombrinha-ou-capota-com-protecao-uv",
            "label": "Sombrinha ou capota com proteção UV",
            "icon": "sombrinha",
            "qty": "1",
            "ess": true,
            "note": "Antes dos 6 meses, proteção solar é física — sombra e roupa."
          }
        ]
      },
      {
        "kind": "tip",
        "title": "regra TICKS — o sling seguro em 5 checagens",
        "body": "O acróstico é inglês, mas a checagem é simples. <b>T</b>ight: tenso, ela colada em quem carrega · <b>I</b>n view: rosto sempre à vista, descoberto · <b>C</b>lose enough to kiss: perto o bastante para beijar a cabeça dela · <b>K</b>eep chin off chest: queixo longe do peito, cabendo um dedo embaixo · <b>S</b>upported back: costas apoiadas, coluna em C. Sling mal posicionado compromete a respiração — é o único risco real dele."
      },
      {
        "kind": "tip",
        "title": "sol e mosquito em Brasília",
        "body": "<b>Protetor solar só a partir dos 6 meses</b> (SBP) — antes disso, sombra, chapéu e roupa, evitando o sol entre 10 h e 16 h. <b>Repelente:</b> icaridina é liberada a partir dos <b>2 meses</b>, IR3535 a partir dos 6 meses, e DEET só depois dos 2 anos. Em ano de dengue isso importa: mosquiteiro no berço e no carrinho resolve a fase em que nenhum repelente é permitido."
      },
      {
        "kind": "avoid",
        "items": [
          "Andador — a SBP contraindica: trauma craniano, queimadura e atraso motor.",
          "Bebê conforto usado sem histórico, ou com validade vencida.",
          "Deixá-la dormindo no bebê conforto ou na cadeirinha de descanso por longos períodos.",
          "Carrinho sem reclínio total nos primeiros meses.",
          "Bebê conforto no banco da frente com airbag."
        ]
      }
    ]
  },
  {
    "num": "08",
    "id": "mala",
    "title": "Mala da maternidade",
    "short": "Mala",
    "pal": "blue",
    "win": "pronta na porta até a semana 34",
    "intro": "Deixem pronta entre as semanas 32 e 34. Parto prematuro acontece, e a partir daí carregar peso e organizar armário fica cada vez mais desconfortável.",
    "inIndex": true,
    "buyWindow": [
      32,
      34
    ],
    "spot": "mala",
    "blocks": [
      {
        "kind": "groups",
        "groups": [
          {
            "name": "Documentos",
            "items": [
              {
                "id": "08-documentos-rg-e-cpf-dos-dois",
                "label": "RG e CPF dos dois",
                "icon": "documento",
                "ess": true,
                "note": "Originais e uma cópia de cada."
              },
              {
                "id": "08-documentos-carteirinha-do-plano-guia-de-internacao",
                "label": "Carteirinha do plano + guia de internação",
                "icon": "carteirinha",
                "ess": true
              },
              {
                "id": "08-documentos-caderneta-da-gestante-ultimos-exames-e-ultra",
                "label": "Caderneta da gestante + últimos exames e ultrassons",
                "icon": "caderneta",
                "ess": true,
                "note": "É o canal de comunicação com a equipe que vai receber vocês."
              },
              {
                "id": "08-documentos-plano-de-parto-impresso",
                "label": "Plano de parto impresso",
                "icon": "plano-parto",
                "qty": "2 cópias"
              },
              {
                "id": "08-documentos-comprovante-de-residencia",
                "label": "Comprovante de residência",
                "icon": "comprovante",
                "qty": "1 cópia",
                "note": "Útil se a maternidade tiver posto de cartório para o registro."
              }
            ]
          },
          {
            "name": "Para a Rafaella — internação",
            "items": [
              {
                "id": "08-para-a-rafaella-internacao-camisola-ou-pijama-com-abertura-frontal",
                "label": "Camisola ou pijama com abertura frontal",
                "icon": "camisola",
                "qty": "3–4",
                "ess": true
              },
              {
                "id": "08-para-a-rafaella-internacao-robe-chinelo-antiderrapante",
                "label": "Robe + chinelo antiderrapante",
                "icon": "robe",
                "qty": "1"
              },
              {
                "id": "08-para-a-rafaella-internacao-calcinha-de-algodao-ou-descartavel",
                "label": "Calcinha de algodão ou descartável",
                "icon": "calcinha",
                "qty": "6",
                "ess": true,
                "note": "Cós alto, elástico largo."
              },
              {
                "id": "08-para-a-rafaella-internacao-sutia-de-amamentacao",
                "label": "Sutiã de amamentação",
                "icon": "sutia",
                "qty": "2",
                "ess": true
              },
              {
                "id": "08-para-a-rafaella-internacao-absorvente-pos-parto",
                "label": "Absorvente pós-parto",
                "icon": "absorvente-pos",
                "qty": "1–2 pacotes",
                "ess": true,
                "note": "A maternidade costuma fornecer parte — leve reforço mesmo assim."
              },
              {
                "id": "08-para-a-rafaella-internacao-necessaire-de-higiene-pessoal",
                "label": "Nécessaire de higiene pessoal",
                "icon": "necessaire",
                "qty": "1"
              },
              {
                "id": "08-para-a-rafaella-internacao-roupa-confortavel-para-a-alta",
                "label": "Roupa confortável para a alta",
                "icon": "roupa-dobrada",
                "qty": "1"
              }
            ]
          },
          {
            "name": "Para a Laura",
            "items": [
              {
                "id": "08-para-a-laura-body",
                "label": "Body",
                "icon": "body-mc",
                "qty": "4–6",
                "ess": true,
                "note": "Levar tamanho RN e P — o peso ao nascer é imprevisível."
              },
              {
                "id": "08-para-a-laura-macacao",
                "label": "Macacão",
                "icon": "macacao",
                "qty": "4–6",
                "ess": true
              },
              {
                "id": "08-para-a-laura-meias",
                "label": "Meias",
                "icon": "meias",
                "qty": "3 pares"
              },
              {
                "id": "08-para-a-laura-manta-leve",
                "label": "Manta leve",
                "icon": "manta-leve",
                "qty": "2"
              },
              {
                "id": "08-para-a-laura-touca",
                "label": "Touca",
                "icon": "touca",
                "qty": "1–2"
              },
              {
                "id": "08-para-a-laura-fraldas-rn",
                "label": "Fraldas RN",
                "icon": "fralda",
                "qty": "1 pacote",
                "note": "A maternidade fornece a maior parte — confirmar na visita."
              },
              {
                "id": "08-para-a-laura-saida-de-maternidade",
                "label": "Saída de maternidade",
                "icon": "saida",
                "qty": "1"
              }
            ]
          },
          {
            "name": "Para o Palmer",
            "items": [
              {
                "id": "08-para-o-palmer-trocas-de-roupa",
                "label": "Trocas de roupa",
                "icon": "roupa-dobrada",
                "qty": "3",
                "ess": true,
                "note": "Internação costuma durar 2 a 3 dias."
              },
              {
                "id": "08-para-o-palmer-chinelo-e-necessaire",
                "label": "Chinelo e nécessaire",
                "icon": "necessaire",
                "qty": "1"
              },
              {
                "id": "08-para-o-palmer-carregadores-power-bank",
                "label": "Carregadores + power bank",
                "icon": "carregador",
                "qty": "1",
                "ess": true
              },
              {
                "id": "08-para-o-palmer-lanches-e-garrafa-de-agua",
                "label": "Lanches e garrafa de água",
                "icon": "lanche",
                "note": "Trabalho de parto é longo e a cantina fecha."
              },
              {
                "id": "08-para-o-palmer-bebe-conforto-instalado-no-carro",
                "label": "Bebê conforto instalado no carro",
                "icon": "bebe-conforto",
                "ess": true,
                "note": "Não dá para sair da maternidade sem ele."
              }
            ]
          }
        ]
      },
      {
        "kind": "tip",
        "title": "perguntas para levar na visita à maternidade",
        "body": "Façam a visita entre as semanas 28 e 32 e perguntem: quantas fraldas por dia eles fornecem? Fornecem camisola, kit de higiene e absorvente? A Rafaella pode usar roupa própria durante o trabalho de parto? Tem banheira ou chuveiro disponível? Tem posto de cartório para registro dentro do hospital? A resposta muda o tamanho da mala."
      },
      {
        "kind": "tip",
        "title": "quando ir para a maternidade",
        "body": "<b>Regra 5-1-1:</b> contrações a cada 5 minutos, durando 1 minuto, por 1 hora seguida. Também é hora de ir se a bolsa romper (mesmo sem contração) ou se houver sangramento parecido com menstruação. <b>Ir imediatamente, sem esperar:</b> sangramento intenso, febre alta, dor abdominal forte e persistente, tontura ou desmaio, e — o mais importante — <b>redução perceptível dos movimentos da Laura</b>."
      },
      {
        "kind": "tip",
        "title": "o direito de ter o Palmer junto",
        "body": "A <b>Lei 11.108/2005</b> garante à Rafaella um acompanhante de livre escolha durante todo o trabalho de parto, o parto e o pós-parto imediato — em qualquer maternidade, pública ou privada. Não é cortesia do hospital, é direito. Se alguém disser o contrário, cite a lei pelo número."
      }
    ]
  },
  {
    "num": "09",
    "id": "prazos",
    "title": "Depois que nascer: prazos",
    "short": "Prazos",
    "pal": "rose",
    "win": "nada se compra — são prazos",
    "intro": "Esta é a única página sem compra nenhuma. São prazos legais, e dois deles valem dinheiro e carência se passarem em branco.",
    "inIndex": true,
    "buyWindow": null,
    "spot": "docs",
    "blocks": [
      {
        "kind": "timeline",
        "rows": [
          {
            "when": "primeiras 12 h",
            "hot": true,
            "what": "<b>Vacina Hepatite B</b> — primeira dose ainda na maternidade."
          },
          {
            "when": "dia 0–1",
            "hot": false,
            "what": "<b>BCG</b> (peso mínimo 2 kg) e <b>guardar a DNV</b>, a Declaração de Nascido Vivo que o hospital emite — é ela que destrava todo o resto."
          },
          {
            "when": "dia 1–2",
            "hot": false,
            "what": "<b>Teste do coraçãozinho</b> (oximetria, detecta cardiopatia congênita) e <b>teste da linguinha</b>."
          },
          {
            "when": "dia 2–3",
            "hot": false,
            "what": "<b>Teste da orelhinha</b> — triagem auditiva."
          },
          {
            "when": "dia 3–5",
            "hot": true,
            "what": "<b>Teste do pezinho</b> — não antes de 48 h de vida. Peça a <b>versão ampliada</b>: a básica não dosa G6PD, que é o que importa no caso da Laura."
          },
          {
            "when": "dia 1–7",
            "hot": false,
            "what": "<b>Teste do olhinho</b> e <b>primeira consulta pediátrica</b> — o Ministério da Saúde recomenda até o 7º dia, idealmente entre o 3º e o 5º."
          },
          {
            "when": "até 15 dias",
            "hot": true,
            "what": "<b>Registro civil em cartório</b> — certidão gratuita por lei. Basta a DNV e o documento de um dos pais. O CPF costuma sair junto, mas isso varia por cartório e por estado — confirmem no ato."
          },
          {
            "when": "até 30 dias",
            "hot": true,
            "what": "<b>Incluir a Laura no plano de saúde.</b> Pela Lei 9.656/98 e pela Súmula 25 da ANS, a inscrição feita nesse prazo entra <b>sem carência nenhuma</b>. Depois dele, a operadora pode alegar doença preexistente e impor cobertura parcial temporária. Não deixem para o dia 29."
          },
          {
            "when": "até 30 dias",
            "hot": false,
            "what": "<b>Licença-paternidade e maternidade</b> — dar entrada. Ver quadro abaixo."
          }
        ]
      },
      {
        "kind": "tip",
        "title": "licença-paternidade: a lei mudou a favor de vocês",
        "body": "A <b>Lei 15.371/2026</b> ampliou a licença-paternidade de forma escalonada: <b>10 dias para nascimentos a partir de 1º de janeiro de 2027</b> — ou seja, a Laura já nasce sob a regra nova (eram 5 dias até dez/2026). Sobe para 15 dias em 2028 e 20 em 2029. Mais importante: a lei criou o <b>salário-paternidade pago pelo INSS</b>, que passou a contemplar <b>autônomos, MEI e domésticos</b> — categorias que antes simplesmente não tinham direito ao benefício. Vale conferir a situação contributiva antes do parto."
      },
      {
        "kind": "tip",
        "title": "e a licença-maternidade",
        "body": "São <b>120 dias</b>, pagos pelo INSS via salário-maternidade. A entrada pode ser feita a partir de 28 dias antes do parto e até o primeiro dia depois. <b>Não há mais carência</b>: o STF derrubou a exigência de 10 contribuições que valia para autônoma e contribuinte individual, por violar isonomia. O que ainda é preciso é ter <b>qualidade de segurada</b> na data do parto — vale conferir o extrato do CNIS com antecedência, não depois."
      }
    ]
  },
  {
    "num": "10",
    "id": "cha-de-bebe",
    "title": "Chá de bebê — o que pedir",
    "short": "Chá de bebê",
    "pal": "sand",
    "win": "organizar entre as semanas 28–34",
    "intro": "Chá de bebê bem pedido cobre justamente a parte cara e recorrente do enxoval. Mal pedido, vira armário cheio de roupa tamanho RN que ela nunca vai usar.",
    "inIndex": true,
    "buyWindow": [
      28,
      34
    ],
    "spot": "cha",
    "blocks": [
      {
        "kind": "items",
        "items": [
          {
            "id": "10-fraldas-tamanho-p-m-e-g",
            "label": "Fraldas tamanho P, M e G",
            "icon": "fralda-pacote",
            "ess": true,
            "note": "O melhor pedido possível. Peça pouca coisa em RN: essa fase dura semanas e vocês já compraram."
          },
          {
            "id": "10-lencos-umedecidos-sem-perfume",
            "label": "Lenços umedecidos sem perfume",
            "icon": "lencos",
            "ess": true
          },
          {
            "id": "10-pomada-de-assadura",
            "label": "Pomada de assadura",
            "icon": "pomada",
            "ess": true,
            "note": "Nunca sobra."
          },
          {
            "id": "10-algodao-e-produtos-de-banho",
            "label": "Algodão e produtos de banho",
            "icon": "algodao",
            "note": "Consumo alto e contínuo."
          },
          {
            "id": "10-absorventes-de-seio-e-lanolina",
            "label": "Absorventes de seio e lanolina",
            "icon": "absorvente-seio",
            "note": "Ninguém lembra de pedir — e acaba."
          },
          {
            "id": "10-vale-presente-de-loja-de-bebe",
            "label": "Vale-presente de loja de bebê",
            "icon": "vale",
            "note": "Resolve o que faltar depois, quando vocês souberem o que realmente usam."
          },
          {
            "id": "10-cotizacao-para-item-grande",
            "label": "Cotização para item grande",
            "icon": "presente",
            "note": "Carrinho, poltrona de amamentação ou babá eletrônica: combine em particular com quem se ofereceu, para não duplicar."
          }
        ]
      },
      {
        "kind": "tip",
        "title": "use uma lista online",
        "body": "Uma lista compartilhada evita o clássico: quatro pessoas dando a mesma manta e ninguém dando fralda tamanho M. Também facilita para quem mora longe e vai mandar pelos correios."
      },
      {
        "kind": "avoid",
        "title": "o que costuma sobrar",
        "items": [
          "Roupa tamanho RN — é o que mais ganha e o que menos dura.",
          "Sapatinhos e luvinhas.",
          "Kit berço e protetor de grade — contraindicados pela SBP.",
          "Bichos de pelúcia grandes: não podem ir para o berço no primeiro ano.",
          "Aquecedor de mamadeira e termômetro de banheira."
        ]
      }
    ]
  }
]

export const ICONS = {
  "macacao": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e9efe7\" d=\"M18 15h10l4 4 4-4h10l5 10-7 5v25H34l-2-6-2 6H20V30l-7-5z\"/><path fill=\"#f0ead9\" d=\"M34 20h6v29h-6z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M18 15h10l4 4 4-4h10l5 10-7 5v25H34l-2-6-2 6H20V30l-7-5zM32 20v29\"/><circle cx=\"32\" cy=\"27\" r=\"1\"/><circle cx=\"32\" cy=\"35\" r=\"1\"/><circle cx=\"32\" cy=\"43\" r=\"1\"/><path stroke=\"#b5aa9c\" d=\"M23 49h5m13 0h-5\"/></g></svg>",
  "macaquinho": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M18 17h11l3 4 3-4h11l5 9-7 5v17h-8v7h-8v-7h-8V31l-7-5z\"/><path fill=\"#f2e3d2\" d=\"M35 31h7v8h-7z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M18 17h11l3 4 3-4h11l5 9-7 5v17h-8v7h-8v-7h-8V31l-7-5zM35 31h7v8h-7z\"/><path d=\"M39 39v-3\"/><circle cx=\"25\" cy=\"29\" r=\"1\"/><circle cx=\"29\" cy=\"29\" r=\"1\"/></g></svg>",
  "mijao": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f2e3d2\" d=\"M17 17h30v12l-4 25H32v-15l-4 15H17l4-25z\"/><path fill=\"#f0ead9\" d=\"M17 17h30v8H17z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M17 17h30v12l-4 25H32v-15l-4 15H17l4-25zM17 25h30M31 25v14M20 43l10 2M34 43l9-2\"/><path stroke=\"#b5aa9c\" d=\"M21 21h22\"/></g></svg>",
  "shorts": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e9efe7\" d=\"M16 19h32l-3 28H33l-1-9-2 9H19z\"/><path fill=\"#f0ead9\" d=\"M16 19h32v8H16z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M16 19h32l-3 28H33l-1-9-2 9H19zM16 27h32M32 27v20\"/><path d=\"M32 28c-3 4-7 3-7 0m7 0c3 4 7 3 7 0\"/><circle cx=\"25\" cy=\"35\" r=\"1\"/><circle cx=\"40\" cy=\"35\" r=\"1\"/></g></svg>",
  "casaquinho": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M18 18l10-4 4 6 4-6 10 4 5 12-7 4v20H20V34l-7-4z\"/><path fill=\"#f2e3d2\" d=\"M29 20h6v34h-6z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M18 18l10-4 4 6 4-6 10 4 5 12-7 4v20H20V34l-7-4zM32 20v34\"/><circle cx=\"32\" cy=\"31\" r=\"1.4\"/><circle cx=\"32\" cy=\"41\" r=\"1.4\"/><path stroke=\"#b5aa9c\" d=\"M23 28l3 3 3-3m6 0l3 3 3-3m-18 10l3 3 3-3m6 0l3 3 3-3\"/></g></svg>",
  "meias": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M15 14h13v23l9 5c4 3 1 9-4 9H15z\"/><path fill=\"#f6e9e5\" d=\"M37 23h12v17l6 4c4 4 0 8-5 8H37z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M15 14h13v23l9 5c4 3 1 9-4 9H15zM37 23h12v17l6 4c4 4 0 8-5 8H37z\"/><path d=\"M15 19h13m-13 4h13m22 5h-13m13 4h-13\"/><path stroke=\"#b5aa9c\" d=\"M19 36h5m18 6h5\"/></g></svg>",
  "chapeu": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f0ead9\" d=\"M11 42c2-10 13-12 21-12s19 2 21 12c-8 8-34 8-42 0z\"/><path fill=\"#f2e3d2\" d=\"M20 31c1-13 23-13 24 0v7H20z\"/><path fill=\"#c2857b\" d=\"M20 35h24v4H20z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M11 42c2-10 13-12 21-12s19 2 21 12c-8 8-34 8-42 0zM20 35v-4c1-13 23-13 24 0v4M20 35h24v4H20\"/><path d=\"M32 39c2 3 5 3 7 0\"/><circle cx=\"39\" cy=\"39\" r=\"1\"/></g></svg>",
  "touca": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e9efe7\" d=\"M16 38c0-22 32-22 32 0v8H16z\"/><path fill=\"#f0ead9\" d=\"M16 39h32v9H16z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M16 39c0-23 32-23 32 0v9H16zM16 39h32\"/><path stroke=\"#b5aa9c\" d=\"M23 25l3 14m6-17v17m9-14l-3 14\"/><circle cx=\"32\" cy=\"18\" r=\"2\"/></g></svg>",
  "babador": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M24 15h16v10c9 9 7 26-1 29-3 2-6-1-8 1-2-2-5 1-8-1-8-3-10-20 1-29z\"/><path fill=\"#e9efe7\" d=\"M29 24h6l2 6-5 3-5-3z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M24 15h16v10c9 9 7 26-1 29-3 2-6-1-8 1-2-2-5 1-8-1-8-3-10-20 1-29z\"/><circle cx=\"37\" cy=\"20\" r=\"1.3\"/><path d=\"M20 46q3 3 6 0q3 3 6 0q3 3 6 0q3 3 6 0\"/><circle cx=\"32\" cy=\"31\" r=\"1\"/></g></svg>",
  "pano": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M14 27l33-5 5 22-33 5z\"/><path fill=\"#f2e3d2\" d=\"M12 19l33-5 4 18-33 5z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M14 27l33-5 5 22-33 5zM12 19l33-5 4 18-33 5z\"/><path stroke=\"#b5aa9c\" d=\"M18 23l24-4m-21 10l24-4m-19 14l21-3\"/><circle cx=\"40\" cy=\"39\" r=\"1\"/></g></svg>",
  "saco-dormir": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M23 15h7l2 5 2-5h7v12l7 6-3 19H19l-3-19 7-6z\"/><path fill=\"#f6e9e5\" d=\"M31 22h3v28h-3z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M23 15h7l2 5 2-5h7v12l7 6-3 19H19l-3-19 7-6zM31 22v28\"/><path d=\"M23 22h-6v10m24-10h6v10\"/><circle cx=\"32\" cy=\"26\" r=\"1\"/><path stroke=\"#b5aa9c\" d=\"M24 42h5m6 0h5\"/></g></svg>",
  "cueiro": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M15 20c13-10 35-4 35 13 0 15-18 22-31 13-12-9-4-22 8-22 13 0 17 15 7 20\"/><path fill=\"#f2e3d2\" d=\"M25 27c8-5 18 4 13 13-4 7-15 4-15-4\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M15 20c13-10 35-4 35 13 0 15-18 22-31 13-12-9-4-22 8-22 13 0 17 15 7 20\"/><path d=\"M25 27c8-5 18 4 13 13-4 7-15 4-15-4\"/><circle cx=\"28\" cy=\"32\" r=\"1\"/><path stroke=\"#b5aa9c\" d=\"M19 23l4 2m20 15l3 2\"/></g></svg>",
  "vestido": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#c0763b\" d=\"M23 12h18l-9 8z\"/><path fill=\"#f6e9e5\" d=\"M25 20h14v12l11 18H14l11-18z\"/><path fill=\"#f2e3d2\" d=\"M19 42h26l5 8H14z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M23 12h18l-9 8zM25 20h14v12l11 18H14l11-18zM25 30h14M19 42h26\"/><path d=\"M23 35v5m6-5v5m6-5v5m6-5v5\"/><circle cx=\"32\" cy=\"25\" r=\"1\"/></g></svg>",
  "saida": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M14 32h36v17H14z\"/><path fill=\"#f6e9e5\" d=\"M18 25h28v13H18z\"/><path fill=\"#e9efe7\" d=\"M22 15c0-9 20-9 20 0v10H22z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M14 32h36v17H14zM18 25h28v13H18zM22 25v-10c0-9 20-9 20 0v10\"/><path d=\"M32 38c-5 5-8 0-5-2 2-2 5 2 5 2 5-5 8 0 5 2-2 2-5-2-5-2z\"/><path stroke=\"#b5aa9c\" d=\"M18 43h28\"/></g></svg>",
  "lavar": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M14 13h36v40H14z\"/><path fill=\"#f2e3d2\" d=\"M18 17h28v9H18z\"/><circle fill=\"#f0ead9\" cx=\"32\" cy=\"39\" r=\"11\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M14 13h36v40H14zM18 17h28v9H18z\"/><circle cx=\"32\" cy=\"39\" r=\"11\"/><path d=\"M25 39c4-6 10 6 15 0\"/><circle cx=\"22\" cy=\"21\" r=\"1\"/><circle cx=\"27\" cy=\"21\" r=\"1\"/></g></svg>",
  "roupa-dobrada": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M15 18h32v8H15z\"/><path fill=\"#e9efe7\" d=\"M12 27h36v8H12z\"/><path fill=\"#e8eef5\" d=\"M16 36h33v8H16z\"/><path fill=\"#f0ead9\" d=\"M13 45h38v8H13z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M15 18h32v8H15zM12 27h36v8H12zM16 36h33v8H16zM13 45h38v8H13z\"/><path stroke=\"#b5aa9c\" d=\"M21 22h11m-13 9h12m-8 9h12m-15 9h12\"/></g></svg>",
  "berco": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f2e3d2\" d=\"M14 22h36v27H14z\"/><path fill=\"#e8eef5\" d=\"M18 30h28v10H18z\"/><path fill=\"#f6e9e5\" d=\"M30 34h16v6H30z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M14 22v31m36-31v31M14 25h36v24H14zM18 30h28v10H18z\"/><path d=\"M21 25v24m7-24v24m8-24v24m7-24v24\"/><path d=\"M18 53h-4m36 0h-4\"/></g></svg>",
  "colchao": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M13 26l28-12 11 7-28 12z\"/><path fill=\"#f2e3d2\" d=\"M13 26l11 7v16l-11-7z\"/><path fill=\"#f0ead9\" d=\"M24 33l28-12v16L24 49z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M13 26l28-12 11 7-28 12zM13 26v16l11 7 28-12V21M24 33v16\"/><circle cx=\"32\" cy=\"25\" r=\"1\"/><circle cx=\"40\" cy=\"22\" r=\"1\"/><path stroke=\"#b5aa9c\" d=\"M27 30l17-7\"/></g></svg>",
  "protetor-colchao": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e9efe7\" d=\"M14 21h36v26H14z\"/><path fill=\"#e8eef5\" d=\"M18 17h28l4 4H14z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M14 21h36v26H14zM18 17h28l4 4H14z\"/><path d=\"M14 47l5 5m31-5l-5 5\"/><path stroke=\"#b5aa9c\" d=\"M20 27q3 3 6 0q3 3 6 0q3 3 6 0q3 3 6 0\"/></g></svg>",
  "lencol": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M16 17h31v31H16z\"/><path fill=\"#f2e3d2\" d=\"M37 17h10v10z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M16 17h31v31H16zM37 17h10v10L37 17\"/><path d=\"M16 42q6 0 6 6m19 0q0-6 6-6\"/><path stroke=\"#b5aa9c\" d=\"M22 24h10m-10 6h10\"/></g></svg>",
  "comoda": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f2e3d2\" d=\"M15 19h34v34H15z\"/><path fill=\"#e9efe7\" d=\"M18 14h28v7H18z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M15 19h34v34H15zM18 14h28v7H18zM15 30h34M15 41h34\"/><circle cx=\"32\" cy=\"25\" r=\"1\"/><circle cx=\"32\" cy=\"36\" r=\"1\"/><circle cx=\"32\" cy=\"47\" r=\"1\"/><path d=\"M19 53v3m26-3v3\"/></g></svg>",
  "poltrona": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e9efe7\" d=\"M18 31V19c0-8 17-8 17 0v12h9c6 0 6 17 0 17H20c-8 0-8-17-2-17z\"/><path fill=\"#f2e3d2\" d=\"M24 29h14v15H24z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M18 31V19c0-8 17-8 17 0v12h9c6 0 6 17 0 17H20c-8 0-8-17-2-17zM24 29h14v15H24z\"/><path d=\"M23 48l-3 7m22-7l3 7\"/><path stroke=\"#b5aa9c\" d=\"M20 35h4\"/></g></svg>",
  "baba-eletronica": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M19 19h25v32H19z\"/><path fill=\"#f0ead9\" d=\"M23 24h17v13H23z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M19 19h25v32H19zM23 24h17v13H23zM32 19l4-7\"/><circle cx=\"32\" cy=\"44\" r=\"1\"/><path d=\"M48 27q7 5 0 10m4-14q12 9 0 18\"/></g></svg>",
  "luz-noturna": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f0ead9\" d=\"M19 30c0-16 26-16 26 0v16H19z\"/><path fill=\"#f2e3d2\" d=\"M23 26c3-8 15-8 18 0v20H23z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M19 46V30c0-16 26-16 26 0v16zM23 46V26c3-8 15-8 18 0v20\"/><path d=\"M17 52h30\"/><circle cx=\"32\" cy=\"33\" r=\"2\"/></g></svg>",
  "cortina": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M16 16h28v27H16z\"/><path fill=\"#f6e9e5\" d=\"M17 15h15v35l-7-6-8 6z\"/><path fill=\"#f2e3d2\" d=\"M32 25h12v18H32z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M14 14h34M16 16h28v27H16zM17 15h15v35l-7-6-8 6zM32 25h12\"/><path d=\"M17 31l15 3\"/><circle cx=\"38\" cy=\"33\" r=\"2\"/></g></svg>",
  "umidificador": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M18 34c0-12 28-12 28 0v14H18z\"/><path fill=\"#f0ead9\" d=\"M22 30h20v8H22z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M18 48V34c0-12 28-12 28 0v14zM22 30h20v8\"/><path d=\"M27 26c-4-4 4-6 0-10m10 10c4-4-4-6 0-10\"/><circle cx=\"32\" cy=\"41\" r=\"1\"/></g></svg>",
  "banheira": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M13 30h38l-5 15H18z\"/><path fill=\"#f0ead9\" d=\"M16 27h32v7H16z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M13 30h38l-5 15H18zM16 27h32v7H16zM20 45l-3 9m27-9l3 9\"/><circle cx=\"27\" cy=\"25\" r=\"2\"/><circle cx=\"36\" cy=\"22\" r=\"1\"/></g></svg>",
  "toalha": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f2e3d2\" d=\"M17 22l15-10 15 10v29H17z\"/><path fill=\"#f6e9e5\" d=\"M25 22l7-5 7 5v9H25z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M17 22l15-10 15 10v29H17zM25 22l7-5 7 5v9H25z\"/><path stroke=\"#b5aa9c\" d=\"M23 40l5 4m8-4l5 4m-18 4h18\"/></g></svg>",
  "sabonete": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e9efe7\" d=\"M21 24h22v29H21z\"/><path fill=\"#f0ead9\" d=\"M25 17h14v8H25z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M21 24h22v29H21zM25 24v-7h14v7M32 17v-4h12\"/><path d=\"M26 35c4-5 8 5 12 0\"/><circle cx=\"32\" cy=\"43\" r=\"1\"/></g></svg>",
  "algodao": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><circle fill=\"#f6e9e5\" cx=\"25\" cy=\"35\" r=\"10\"/><circle fill=\"#f2e3d2\" cx=\"36\" cy=\"31\" r=\"10\"/><circle fill=\"#e9efe7\" cx=\"39\" cy=\"42\" r=\"9\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><circle cx=\"25\" cy=\"35\" r=\"10\"/><circle cx=\"36\" cy=\"31\" r=\"10\"/><circle cx=\"39\" cy=\"42\" r=\"9\"/><path stroke=\"#b5aa9c\" d=\"M21 35l4 2m8-6l4 2m-2 9l4 2\"/></g></svg>",
  "gaze": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f0ead9\" d=\"M16 17h32v32H16z\"/><path fill=\"#f6e9e5\" d=\"M20 21h24v24H20z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M16 17h32v32H16zM20 21h24v24H20z\"/><path stroke=\"#b5aa9c\" d=\"M20 27h24m-24 6h24m-24 6h24M27 21v24m6-24v24m6-24v24\"/></g></svg>",
  "pente": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e9efe7\" d=\"M18 18c12-8 23 3 15 15L24 42l-8-8z\"/><path fill=\"#f2e3d2\" d=\"M23 37l8 8-12 10-7-7z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M18 18c12-8 23 3 15 15L24 42l-8-8zM23 37l8 8-12 10-7-7z\"/><path d=\"M19 23l10 10m-14-6l10 10m-7-14l10 10\"/></g></svg>",
  "tesourinha": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><circle fill=\"#f6e9e5\" cx=\"22\" cy=\"43\" r=\"7\"/><circle fill=\"#e8eef5\" cx=\"39\" cy=\"43\" r=\"7\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><circle cx=\"22\" cy=\"43\" r=\"7\"/><circle cx=\"39\" cy=\"43\" r=\"7\"/><path d=\"M27 38l17-22m-10 22L20 16\"/><circle cx=\"45\" cy=\"15\" r=\"2\"/><circle cx=\"19\" cy=\"15\" r=\"2\"/></g></svg>",
  "termometro-banho": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><circle fill=\"#f0ead9\" cx=\"32\" cy=\"31\" r=\"15\"/><path fill=\"#e8eef5\" d=\"M17 35h30v11H17z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><circle cx=\"32\" cy=\"31\" r=\"15\"/><path d=\"M17 35h30v11H17zM32 31l7-5M22 35q3 3 6 0q3 3 6 0q3 3 6 0\"/><circle cx=\"32\" cy=\"31\" r=\"1\"/></g></svg>",
  "termometro": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M26 15h12v28a9 9 0 1 1-12 0z\"/><path fill=\"#f0ead9\" d=\"M29 20h6v10h-6z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M26 15h12v28a9 9 0 1 1-12 0zM29 20h6v10h-6zM32 34v13\"/><circle cx=\"32\" cy=\"49\" r=\"2\"/></g></svg>",
  "fralda": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M13 21h38v26l-10 6H23l-10-6z\"/><path fill=\"#e8eef5\" d=\"M13 25h12v13H13zm26 0h12v13H39z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M13 21h38v26l-10 6H23l-10-6zM13 25h12v13H13m26-13h12v13H39\"/><path d=\"M25 43q7 5 14 0\"/><circle cx=\"29\" cy=\"31\" r=\"1\"/></g></svg>",
  "trocador": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e9efe7\" d=\"M13 26c0-8 7-10 12-5h14c5-5 12-3 12 5v22H13z\"/><path fill=\"#f0ead9\" d=\"M18 30h28v14H18z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M13 48V26c0-8 7-10 12-5h14c5-5 12-3 12 5v22zM18 30h28v14H18z\"/><path stroke=\"#b5aa9c\" d=\"M22 35h20\"/></g></svg>",
  "pomada": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f2e3d2\" d=\"M16 28l29-7 5 20-29 7z\"/><path fill=\"#c2857b\" d=\"M13 31l5-1 5 16-5 1z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M16 28l29-7 5 20-29 7zM13 31l5-1 5 16-5 1z\"/><path d=\"M28 31l9-2m-7 8l9-2\"/><circle cx=\"40\" cy=\"40\" r=\"1\"/></g></svg>",
  "lencos": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M15 28h34v21H15z\"/><path fill=\"#f0ead9\" d=\"M20 22h24v11H20z\"/><path fill=\"#f6e9e5\" d=\"M26 14h12v14H26z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M15 28h34v21H15zM20 22h24v11H20zM26 14h12v14H26z\"/><path d=\"M23 40c6-4 12 4 18 0\"/><circle cx=\"32\" cy=\"27\" r=\"1\"/></g></svg>",
  "lixeira": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e9efe7\" d=\"M20 22h24l-3 31H23z\"/><path fill=\"#f2e3d2\" d=\"M18 18h28v6H18z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M20 22h24l-3 31H23zM18 18h28v6H18zM27 18v-3h10v3\"/><path stroke=\"#b5aa9c\" d=\"M28 29v17m8-17v17\"/><path d=\"M17 53h30\"/></g></svg>",
  "soro": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M24 20h16v29H24z\"/><path fill=\"#f0ead9\" d=\"M27 15h10v7H27z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M24 20h16v29H24zM27 15h10v7H27z\"/><path d=\"M28 35c3-4 5 4 8 0\"/><circle cx=\"32\" cy=\"42\" r=\"1\"/></g></svg>",
  "aspirador": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f2e3d2\" d=\"M18 35c0-13 18-13 18 0 0 9-6 14-9 14s-9-5-9-14z\"/><path fill=\"#e8eef5\" d=\"M36 31h13v8H36z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M18 35c0-13 18-13 18 0 0 9-6 14-9 14s-9-5-9-14zM36 31h13v8H36z\"/><path d=\"M49 33h5v4h-5\"/><circle cx=\"27\" cy=\"36\" r=\"1\"/></g></svg>",
  "alcool": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M21 25h21v28H21z\"/><path fill=\"#f0ead9\" d=\"M25 18h12v8H25z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M21 25h21v28H21zM25 25v-7h12v7M37 18h9v5h-5\"/><path d=\"M27 39l9-4m-7 9l7-3\"/><circle cx=\"32\" cy=\"31\" r=\"1\"/></g></svg>",
  "receita": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M17 14h27v36H17z\"/><path fill=\"#e8eef5\" d=\"M39 39l11 11-4 4-11-11z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M17 14h27v36H17zM39 39l11 11-4 4-11-11z\"/><path d=\"M25 22h10m-5-5v10m-7 8h14m-14 6h10\"/></g></svg>",
  "contatos": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f0ead9\" d=\"M32 25h18v23H32z\"/><path fill=\"#e9efe7\" d=\"M15 19c10-6 20 4 14 10l-4 4 7 7-5 5c-12-7-18-16-12-26z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M32 25h18v23H32zM15 19c10-6 20 4 14 10l-4 4 7 7-5 5c-12-7-18-16-12-26z\"/><path d=\"M37 32h8m-8 5h8\"/><circle cx=\"40\" cy=\"42\" r=\"1\"/></g></svg>",
  "sutia": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M15 28c7-8 14-8 17 2 3-10 10-10 17-2v17H15z\"/><path fill=\"#f2e3d2\" d=\"M15 28v-8m34 8v-8\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M15 28c7-8 14-8 17 2 3-10 10-10 17-2v17H15zM15 28v-8m34 8v-8\"/><circle cx=\"25\" cy=\"29\" r=\"1\"/><circle cx=\"39\" cy=\"29\" r=\"1\"/></g></svg>",
  "absorvente-seio": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><circle fill=\"#f0ead9\" cx=\"26\" cy=\"35\" r=\"13\"/><circle fill=\"#f6e9e5\" cx=\"39\" cy=\"29\" r=\"13\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><circle cx=\"26\" cy=\"35\" r=\"13\"/><circle cx=\"39\" cy=\"29\" r=\"13\"/><circle cx=\"26\" cy=\"35\" r=\"4\"/><circle cx=\"39\" cy=\"29\" r=\"4\"/></g></svg>",
  "absorvente-pos": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M23 17h18c7 9 7 21 0 30H23c-7-9-7-21 0-30z\"/><path fill=\"#e8eef5\" d=\"M16 28h9v8h-9zm23 0h9v8h-9z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M23 17h18c7 9 7 21 0 30H23c-7-9-7-21 0-30zM16 28h9v8h-9m23-8h9v8h-9\"/><path stroke=\"#b5aa9c\" d=\"M32 22v20\"/></g></svg>",
  "lanolina": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f2e3d2\" d=\"M20 20h24v29H20z\"/><path fill=\"#c0763b\" d=\"M20 20h24v9H20z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M20 20h24v29H20zM20 20h24v9H20z\"/><path d=\"M32 34c-5-5-8 2 0 8 8-6 5-13 0-8z\"/><circle cx=\"32\" cy=\"25\" r=\"1\"/></g></svg>",
  "almofada": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e9efe7\" d=\"M17 42c0-23 30-29 34-8l-9 5c-3-10-15-4-14 7z\"/><path fill=\"#f0ead9\" d=\"M23 44c0-13 13-16 19-5l-5 5z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M17 42c0-23 30-29 34-8l-9 5c-3-10-15-4-14 7zM23 44c0-13 13-16 19-5\"/><path stroke=\"#b5aa9c\" d=\"M25 37l5 3m9-7l3 4\"/></g></svg>",
  "apoio": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M32 42c-16-12-8-25 0-17 8-8 16 5 0 17z\"/><path fill=\"#f2e3d2\" d=\"M12 41c6-7 13-4 20 5l-5 6c-8-8-13-6-15-11zm40 0c-6-7-13-4-20 5l5 6c8-8 13-6 15-11z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M32 42c-16-12-8-25 0-17 8-8 16 5 0 17zM12 41c6-7 13-4 20 5l-5 6c-8-8-13-6-15-11zm40 0c-6-7-13-4-20 5l5 6c8-8 13-6 15-11z\"/><path d=\"M18 43l6 4m22-4l-6 4\"/></g></svg>",
  "potes-leite": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M22 20h20v30H22z\"/><path fill=\"#f0ead9\" d=\"M25 15h14v6H25z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M22 20h20v30H22zM25 15h14v6H25z\"/><path d=\"M26 29h5m-5 7h5m-5 7h5\"/><path stroke=\"#b5aa9c\" d=\"M33 27v18\"/></g></svg>",
  "bebe-conforto": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M20 47c-7-22 6-32 23-24l6 25z\"/><path fill=\"#f2e3d2\" d=\"M25 39c3-12 13-10 18 1v8H25z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M20 47c-7-22 6-32 23-24l6 25zM25 39c3-12 13-10 18 1v8H25zM24 25c3-16 24-15 26 2\"/><path d=\"M30 38l8 8m0-8l-8 8\"/><circle cx=\"30\" cy=\"31\" r=\"1\"/></g></svg>",
  "carrinho": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M16 29h25l7 17H22z\"/><path fill=\"#e9efe7\" d=\"M16 29c4-18 25-15 25 0z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M16 29h25l7 17H22zM16 29c4-18 25-15 25 0zM41 22l7-9\"/><circle cx=\"25\" cy=\"50\" r=\"4\"/><circle cx=\"44\" cy=\"50\" r=\"4\"/><path stroke=\"#b5aa9c\" d=\"M22 35h18\"/></g></svg>",
  "sling": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f2e3d2\" d=\"M20 15c16 1 18 19 20 33l-12 3C23 35 20 25 20 15z\"/><path fill=\"#e9efe7\" d=\"M27 36c11-13 24-3 16 11l-16 4z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M20 15c16 1 18 19 20 33l-12 3C23 35 20 25 20 15zM27 36c11-13 24-3 16 11l-16 4z\"/><circle cx=\"35\" cy=\"39\" r=\"2\"/><path d=\"M25 23l9 17\"/></g></svg>",
  "bolsa": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M15 26h34v25H15z\"/><path fill=\"#f0ead9\" d=\"M23 26c0-12 18-12 18 0z\"/><path fill=\"#f6e9e5\" d=\"M25 35h14v10H25z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M15 26h34v25H15zM23 26c0-12 18-12 18 0M25 35h14v10H25z\"/><circle cx=\"32\" cy=\"40\" r=\"1\"/></g></svg>",
  "sombrinha": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M14 30c6-19 30-19 36 0z\"/><path fill=\"#e8eef5\" d=\"M14 30c6-8 12-8 18 0 6-8 12-8 18 0z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M14 30c6-19 30-19 36 0zM14 30c6-8 12-8 18 0 6-8 12-8 18 0M32 18v28c0 7 8 7 8 2\"/><circle cx=\"32\" cy=\"17\" r=\"1\"/></g></svg>",
  "documento": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M13 18h38v28H13z\"/><path fill=\"#f2e3d2\" d=\"M18 24h11v15H18z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M13 18h38v28H13zM18 24h11v15H18z\"/><circle cx=\"23\" cy=\"29\" r=\"2\"/><path d=\"M34 26h11m-11 6h11m-11 6h7\"/></g></svg>",
  "carteirinha": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e9efe7\" d=\"M13 21h38v23H13z\"/><path fill=\"#f0ead9\" d=\"M13 21h38v7H13z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M13 21h38v23H13zM13 21h38v7H13z\"/><path d=\"M23 32h10m-5-5v10m8-3h9\"/><circle cx=\"45\" cy=\"37\" r=\"1\"/></g></svg>",
  "caderneta": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M19 15h27v35H19z\"/><path fill=\"#c2857b\" d=\"M19 15h5v35h-5z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M19 15h27v35H19zM24 15v35\"/><path d=\"M34 29c-6-6-10 3 0 10 10-7 6-16 0-10z\"/><path stroke=\"#b5aa9c\" d=\"M28 20h12\"/></g></svg>",
  "plano-parto": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M15 14h29v37H15z\"/><path fill=\"#e8eef5\" d=\"M39 40l11 11-4 4-11-11z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M15 14h29v37H15zM39 40l11 11-4 4-11-11z\"/><path d=\"M21 23h16m-16 7h16m-16 7h11\"/></g></svg>",
  "calcinha": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M17 18h30v30H38c-1-10-11-10-12 0h-9z\"/><path fill=\"#f2e3d2\" d=\"M17 18h30v8H17z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M17 18h30v30H38c-1-10-11-10-12 0h-9zM17 26h30\"/><path stroke=\"#b5aa9c\" d=\"M23 33h5m13 0h-5\"/></g></svg>",
  "camisola": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M22 17h20v11l7 24H15l7-24z\"/><path fill=\"#f2e3d2\" d=\"M29 17h6v22h-6z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M22 17h20v11l7 24H15l7-24zM29 17v22\"/><circle cx=\"32\" cy=\"27\" r=\"1\"/><path d=\"M32 37c-4 4-6 0-4-2 2-2 4 2 4 2 4-4 6 0 4 2-2 2-4-2-4-2z\"/></g></svg>",
  "robe": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e9efe7\" d=\"M18 17h28l4 31H14z\"/><path fill=\"#f2e3d2\" d=\"M26 17l6 10 6-10\"/><path fill=\"#f0ead9\" d=\"M42 46h13v7H42z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M18 17h28l4 31H14zM26 17l6 10 6-10M16 37h32M42 46h13v7H42z\"/><path d=\"M32 37l-5 7m5-7l5 7\"/></g></svg>",
  "necessaire": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M15 27h34v22H15z\"/><path fill=\"#f0ead9\" d=\"M23 22h18v6H23z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M15 27h34v22H15zM23 22h18v6H23z\"/><path d=\"M15 31h34\"/><circle cx=\"32\" cy=\"31\" r=\"1\"/><path stroke=\"#b5aa9c\" d=\"M22 40h20\"/></g></svg>",
  "carregador": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M17 22h22v25H17z\"/><path fill=\"#f0ead9\" d=\"M39 31c11 0 11 15 2 15h-3\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M17 22h22v25H17zM39 31c11 0 11 15 2 15h-3\"/><path d=\"M24 34h8m-4-4v8\"/><circle cx=\"28\" cy=\"42\" r=\"1\"/></g></svg>",
  "lanche": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M16 19h14v32H16z\"/><path fill=\"#f0ead9\" d=\"M19 15h8v5h-8z\"/><path fill=\"#f2e3d2\" d=\"M35 30h15v17H35z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M16 19h14v32H16zM19 15h8v5h-8zM35 30h15v17H35z\"/><path d=\"M39 36h7m-7 5h7\"/><circle cx=\"23\" cy=\"38\" r=\"1\"/></g></svg>",
  "vale": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f0ead9\" d=\"M13 23h38v19H13z\"/><path fill=\"#c2857b\" d=\"M29 23h6v19h-6z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M13 23h38v19H13zM29 23v19\"/><path d=\"M32 23c-6-7-10 3-3 6m3-6c6-7 10 3 3 6\"/><circle cx=\"22\" cy=\"33\" r=\"1\"/></g></svg>",
  "presente": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M16 27h32v24H16z\"/><path fill=\"#c0763b\" d=\"M16 27h32v7H16zm13 0h6v24h-6z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M16 27h32v24H16zM16 27h32v7H16M29 27v24m6-24v24\"/><path d=\"M32 27c-8-9-13 2-3 3m3-3c8-9 13 2 3 3\"/></g></svg>",
  "body-ml": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M24 16h16l5 7 10 4-4 20-8-2v11H21V45l-8 2-4-20 10-4z\"/><path fill=\"#f0ead9\" d=\"M9 27l10-4 4 13-10 4zm46 0l-10-4-4 13 10 4z\"/><path fill=\"#f6e9e5\" d=\"M24 16h16v8c-5 5-11 5-16 0z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M24 16h16l5 7 10 4-4 20-8-2v11H21V45l-8 2-4-20 10-4zM9 27l10-4 4 13-10 4m46-13l-10-4-4 13 10 4M24 16v8c5 5 11 5 16 0v-8\"/><path d=\"M13 40l10-4m28 0l-10-4M21 50h22\"/><circle cx=\"27\" cy=\"53\" r=\"1.4\"/><circle cx=\"37\" cy=\"53\" r=\"1.4\"/><path stroke=\"#b5aa9c\" d=\"M27 31h10m-8 5h6\"/></g></svg>",
  "body-regata": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M22 14h8l2 6 2-6h8l4 10v25l-7 8H25l-7-8V24z\"/><path fill=\"#e9efe7\" d=\"M22 14h8l2 6 2-6h8l4 10-7 3-7-7-7 7-7-3z\"/><path fill=\"#f2e3d2\" d=\"M25 48h14v9H25z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M22 14h8l2 6 2-6h8l4 10v25l-7 8H25l-7-8V24zM22 14l-4 10 7 3 7-7 7 7 7-3-4-10\"/><path d=\"M25 48v9m14-9v9M25 48c2 3 4 4 7 4s5-1 7-4\"/><circle cx=\"28\" cy=\"54\" r=\"1.3\"/><circle cx=\"36\" cy=\"54\" r=\"1.3\"/><path stroke=\"#c2857b\" d=\"M28 34c-3 3 1 6 4 2 3 4 7 1 4-2-2-2-4 1-4 1s-2-3-4-1z\"/></g></svg>",
  "pagao": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f0ead9\" d=\"M22 15h20l5 8 8 5-5 15-5-2-2 15H21l-2-15-5 2-5-15 8-5z\"/><path fill=\"#e9efe7\" d=\"M21 40c7 4 15 4 22 0l2 16H19z\"/><path fill=\"#f2e3d2\" d=\"M25 15h14v8c-4 4-10 4-14 0z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M22 15h20l5 8 8 5-5 15-5-2-2 15H21l-2-15-5 2-5-15 8-5zM25 15v8c4 4 10 4 14 0v-8M19 41c7 4 19 4 26 0\"/><path d=\"M14 28l8-5 3 13-11 7m36-15l-8-5-3 13 11 7M24 51c5 3 11 3 16 0\"/><path stroke=\"#c0763b\" d=\"M24 52c5 3 11 3 16 0\"/><path d=\"M29 54l-2 4m8-4 2 4\"/><circle cx=\"32\" cy=\"31\" r=\"1\"/></g></svg>",
  "manta-media": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f2e3d2\" d=\"M12 22c0-5 4-8 9-8h26c5 0 8 3 8 8v22c0 5-3 8-8 8H21c-5 0-9-3-9-8z\"/><path fill=\"#e9efe7\" d=\"M12 22c4 4 8 5 12 5h31v17c0 5-3 8-8 8H21c-5 0-9-3-9-8z\"/><path fill=\"#f6e9e5\" d=\"M17 18h27c4 0 7 3 7 7v5H17z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M12 22c0-5 4-8 9-8h26c5 0 8 3 8 8v22c0 5-3 8-8 8H21c-5 0-9-3-9-8zM12 22c4 4 8 5 12 5h31M17 18h27c4 0 7 3 7 7v5H17z\"/><path d=\"M24 27v25m11-25v25m11-25v22\"/><path stroke=\"#b5aa9c\" d=\"M17 36h34M17 44h34\"/><circle cx=\"20\" cy=\"22\" r=\"1\"/><circle cx=\"30\" cy=\"22\" r=\"1\"/><circle cx=\"40\" cy=\"22\" r=\"1\"/></g></svg>",
  "fralda-pacote": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e8eef5\" d=\"M13 20c2-5 8-7 15-7h19c6 0 10 3 11 8l-2 28c-1 5-5 7-10 7H19c-5 0-8-3-9-8z\"/><path fill=\"#f0ead9\" d=\"M21 28h28v17H21z\"/><path fill=\"#f6e9e5\" d=\"M8 38c5-4 13-4 17 1l-2 14c-6 3-13 1-16-4z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M13 20c2-5 8-7 15-7h19c6 0 10 3 11 8l-2 28c-1 5-5 7-10 7H19c-5 0-8-3-9-8zM21 28h28v17H21z\"/><path d=\"M8 38c5-4 13-4 17 1l-2 14c-6 3-13 1-16-4zM10 42c4 2 8 2 13 0M10 49c4 2 8 2 13 0\"/><path d=\"M25 33c3-4 8-4 11 0 3-4 8-4 10 0\"/><circle cx=\"35\" cy=\"39\" r=\"3\"/><path stroke=\"#7a9678\" d=\"M27 49h18\"/></g></svg>",
  "comprovante": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f0ead9\" d=\"M19 10h26v43l-3 3-3-3-3 3-3-3-3 3-3-3-3 3-3-3-3 3-3-3z\"/><path fill=\"#e8eef5\" d=\"M22 17h20v9H22z\"/><path fill=\"#f6e9e5\" d=\"M33 42h8v7h-8z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M19 10h26v43l-3 3-3-3-3 3-3-3-3 3-3-3-3 3-3-3-3 3-3-3z\"/><path d=\"M19 10l3 3 3-3 3 3 3-3 3 3 3-3 3 3 3-3 3 3\"/><path d=\"M22 17h20v9H22zM24 31h16m-16 5h12m-12 5h8\"/><path d=\"M33 42h8v7h-8zM35 45l1 1 3-3\"/><circle cx=\"26\" cy=\"21\" r=\"1\"/><path stroke=\"#b5aa9c\" d=\"M24 52h16\"/></g></svg>",
  "body-mc": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#f6e9e5\" d=\"M19 16h9l4 4 4-4h9l6 9-7 5v22l-7 7-5-4-5 4-7-7V30l-7-5z\"/><path fill=\"#f2e3d2\" d=\"M32 20l4 5-4 3-4-3z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M19 16h9l4 4 4-4h9l6 9-7 5v22l-7 7-5-4-5 4-7-7V30l-7-5zM28 16l4 7 4-7M32 23v25\"/><circle cx=\"28\" cy=\"52\" r=\"1\"/><circle cx=\"36\" cy=\"52\" r=\"1\"/><path stroke=\"#b5aa9c\" d=\"M22 31h5M37 31h5\"/></g></svg>",
  "manta-leve": "<svg viewBox=\"0 0 64 64\" fill=\"none\"><path fill=\"#e9efe7\" d=\"M13 20h37v28H13z\"/><path fill=\"#f0ead9\" d=\"M13 20h22l15 12v16H28V32H13z\"/><g stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M13 20h37v28H13zM13 20h22l15 12v16M13 32h15v16\"/><path d=\"M13 48q3-3 6 0q3-3 6 0q3-3 6 0q3-3 6 0q3-3 6 0q3-3 6 0\"/><path stroke=\"#b5aa9c\" d=\"M33 26l10 8\"/></g></svg>"
}

export const SPOTS = {
  "tamanhos": "<svg viewBox=\"0 0 140 110\" fill=\"none\">\n  <ellipse cx=\"70\" cy=\"58\" rx=\"60\" ry=\"42\" fill=\"#ffffff\" opacity=\"0.85\"/>\n  <g stroke=\"#453c33\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n    <ellipse cx=\"67\" cy=\"79\" rx=\"45\" ry=\"11\" fill=\"#e9efe7\" opacity=\".48\" stroke=\"none\"/>\n    <path d=\"M26 42 C43 26 60 35 62 48 S49 66 64 72 S91 71 108 53\" stroke=\"#c0763b\" stroke-width=\"6\" opacity=\".63\"/>\n    <path d=\"M26 42 C43 26 60 35 62 48 S49 66 64 72 S91 71 108 53\"/>\n    <path d=\"M75 65 Q75 56 83 54 L107 54 Q113 58 111 65 Q93 70 75 65Z\" fill=\"#f6e9e5\" opacity=\".78\"/>\n    <path d=\"M78 55 Q92 59 109 55 M75 65 Q93 62 111 65\"/>\n    <path d=\"M79 54 Q78 47 85 45 L105 45 Q111 48 108 55 Q93 58 79 54Z\" fill=\"#e8eef5\" opacity=\".8\"/>\n    <path d=\"M83 46 Q94 50 105 45\"/>\n    <path d=\"M27 71 Q35 64 43 71 L43 84 L27 84Z\" fill=\"#e9efe7\" opacity=\".78\"/>\n    <path d=\"M31 71 L31 80 M35 71 L35 77 M39 71 L39 80\"/>\n    <path d=\"M112 33 L112 48 M108 35 L116 35 M109 40 L115 40 M108 45 L116 45\"/>\n    <circle cx=\"103\" cy=\"79\" r=\"1.5\" fill=\"#7a9678\" opacity=\".68\" stroke=\"none\"/>\n  </g></svg>",
  "roupas": "<svg viewBox=\"0 0 140 110\" fill=\"none\"><ellipse cx=\"70\" cy=\"58\" rx=\"60\" ry=\"42\" fill=\"#ffffff\" opacity=\"0.85\"/><path d=\"M10 30 Q70 42 130 26\" stroke=\"#453c33\" stroke-width=\"1.6\" stroke-linecap=\"round\"/>\n<g stroke=\"#453c33\" stroke-width=\"1.5\" stroke-linejoin=\"round\" stroke-linecap=\"round\">\n<rect x=\"30\" y=\"34\" width=\"3.6\" height=\"7\" rx=\"1.6\" fill=\"#c0763b\" stroke=\"none\" transform=\"rotate(8 32 37)\"/>\n<path d=\"M27 42 L23 47 L26 52 L29 50 L29 62 Q33 66 37 62 L37 50 L40 52 L43 47 L39 42 Q33 46 27 42 Z\" fill=\"#ffffff\"/>\n<path d=\"M29 62 Q33 60 37 62\"/></g>\n<g stroke=\"#453c33\" stroke-width=\"1.5\" stroke-linejoin=\"round\" stroke-linecap=\"round\">\n<rect x=\"66\" y=\"36\" width=\"3.6\" height=\"7\" rx=\"1.6\" fill=\"#c0763b\" stroke=\"none\" transform=\"rotate(-4 68 39)\"/>\n<path d=\"M62 44 L58 49 L61 53 L64 51 L64 60 L67 72 L71 72 L72 63 L73 72 L77 72 L80 60 L80 51 L83 53 L86 49 L82 44 Q72 49 62 44 Z\" fill=\"#e9efe7\"/></g>\n<g stroke=\"#453c33\" stroke-width=\"1.5\" stroke-linejoin=\"round\" stroke-linecap=\"round\">\n<rect x=\"103\" y=\"30\" width=\"3.6\" height=\"7\" rx=\"1.6\" fill=\"#c0763b\" stroke=\"none\" transform=\"rotate(6 105 33)\"/>\n<path d=\"M101 38 L101 52 Q101 58 95 58 Q90 58 90 53 Q90 49 95 49 L95 38 Z\" fill=\"#f6e9e5\"/>\n<path d=\"M95 41 L101 41\"/></g></svg>",
  "sono": "<svg viewBox=\"0 0 140 110\" fill=\"none\"><ellipse cx=\"70\" cy=\"58\" rx=\"60\" ry=\"42\" fill=\"#ffffff\" opacity=\"0.85\"/><g stroke=\"#453c33\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n<path d=\"M70 14 L70 22 M56 22 L84 22 M58 22 L58 30 M70 22 L70 32 M82 22 L82 28\"/>\n<path d=\"M58 33 l2.2 4.5 -4.4 0 Z\" fill=\"#c0763b\" stroke=\"none\"/><circle cx=\"70\" cy=\"35\" r=\"2.6\" fill=\"#7a9678\" stroke=\"none\"/>\n<path d=\"M82 31 A3.2 3.2 0 1 0 84.5 36 A2.4 2.4 0 0 1 82 31 Z\" fill=\"#c0763b\" stroke=\"none\"/>\n<path d=\"M38 52 L102 52\"/><path d=\"M40 52 L40 88 M100 52 L100 88\"/>\n<path d=\"M48 55 L48 78 M58 55 L58 78 M70 55 L70 78 M82 55 L82 78 M92 55 L92 78\" stroke-width=\"1.2\"/>\n<path d=\"M38 78 L102 78\"/><path d=\"M42 88 L38 94 M98 88 L102 94\"/>\n<rect x=\"44\" y=\"68\" width=\"52\" height=\"10\" rx=\"4\" fill=\"#e9efe7\"/></g></svg>",
  "banho": "<svg viewBox=\"0 0 140 110\" fill=\"none\"><ellipse cx=\"70\" cy=\"58\" rx=\"60\" ry=\"42\" fill=\"#ffffff\" opacity=\"0.85\"/><g stroke=\"#453c33\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n<path d=\"M30 52 L110 52 Q108 76 88 80 L52 80 Q32 76 30 52 Z\" fill=\"#ffffff\"/>\n<path d=\"M30 52 Q70 60 110 52\" stroke-width=\"1.2\"/><path d=\"M46 84 L44 92 M94 84 L96 92\"/>\n<circle cx=\"52\" cy=\"42\" r=\"4.5\"/><circle cx=\"63\" cy=\"36\" r=\"3\"/><circle cx=\"44\" cy=\"34\" r=\"2.2\"/>\n<path d=\"M84 44 Q84 38 89 38 Q93 38 93 42 L97 41 Q95 45 93 45 Q97 46 97 50 Q97 55 90 55 Q83 55 83 49 Z\" fill=\"#f2e3d2\"/>\n<circle cx=\"90\" cy=\"41.5\" r=\"0.9\" fill=\"#453c33\" stroke=\"none\"/></g></svg>",
  "fraldas": "<svg viewBox=\"0 0 140 110\" fill=\"none\"><ellipse cx=\"70\" cy=\"58\" rx=\"60\" ry=\"42\" fill=\"#ffffff\" opacity=\"0.85\"/><g stroke=\"#453c33\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n<path d=\"M42 34 Q70 30 98 34 L94 46 Q70 42 46 46 Z\" fill=\"#ffffff\"/>\n<path d=\"M44 48 Q70 44 96 48 L93 60 Q70 56 47 60 Z\" fill=\"#e9efe7\"/>\n<path d=\"M40 62 Q70 57 100 62 L97 76 Q70 71 43 76 Z\" fill=\"#ffffff\"/>\n<path d=\"M43 76 Q70 82 97 76\" stroke-width=\"1.2\"/>\n<path d=\"M56 88 Q70 82 84 88\" stroke=\"#c0763b\" stroke-width=\"1.8\"/>\n<circle cx=\"56\" cy=\"89\" r=\"2.6\" fill=\"#c0763b\" stroke=\"none\"/><circle cx=\"84\" cy=\"89\" r=\"2.6\" stroke=\"#c0763b\" stroke-width=\"1.6\"/></g></svg>",
  "farmacinha": "<svg viewBox=\"0 0 140 110\" fill=\"none\"><ellipse cx=\"70\" cy=\"58\" rx=\"60\" ry=\"42\" fill=\"#ffffff\" opacity=\"0.85\"/><g stroke=\"#453c33\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n<path d=\"M28 80 L112 80\"/>\n<path d=\"M46 44 L54 44 L54 50 Q60 52 60 60 L60 76 Q60 80 56 80 L44 80 Q40 80 40 76 L40 60 Q40 52 46 50 Z\" fill=\"#ffffff\"/>\n<path d=\"M44 62 L56 62 M44 68 L56 68\" stroke=\"#6b8fb5\" stroke-width=\"1.2\"/>\n<rect x=\"45.5\" y=\"38\" width=\"9\" height=\"6\" rx=\"1.5\" fill=\"#e8eef5\"/>\n<rect x=\"70\" y=\"40\" width=\"6\" height=\"30\" rx=\"3\" fill=\"#ffffff\"/><circle cx=\"73\" cy=\"74\" r=\"5\" fill=\"#f6e9e5\"/>\n<path d=\"M73 70 L73 52\" stroke=\"#c2857b\" stroke-width=\"1.6\"/>\n<path d=\"M88 58 L104 58 L102 80 L90 80 Z\" fill=\"#e9efe7\"/><rect x=\"92.5\" y=\"52\" width=\"7\" height=\"6\" rx=\"1.2\" fill=\"#ffffff\"/>\n<path d=\"M92 66 L100 66\" stroke=\"#7a9678\" stroke-width=\"1.4\"/></g></svg>",
  "amamentacao": "<svg viewBox=\"0 0 140 110\" fill=\"none\"><ellipse cx=\"70\" cy=\"58\" rx=\"60\" ry=\"42\" fill=\"#ffffff\" opacity=\"0.85\"/><g stroke=\"#453c33\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n<path d=\"M56 34 Q60 28 64 34 L64 40 L56 40 Z\" fill=\"#f2e3d2\"/><rect x=\"53\" y=\"40\" width=\"14\" height=\"7\" rx=\"2.5\" fill=\"#ffffff\"/>\n<path d=\"M50 50 Q50 47 53 47 L67 47 Q70 47 70 50 L70 78 Q70 84 64 84 L56 84 Q50 84 50 78 Z\" fill=\"#ffffff\"/>\n<path d=\"M53 58 L67 58 M53 66 L67 66\" stroke=\"#b5aa9c\" stroke-width=\"1.2\"/><path d=\"M50 72 L70 72\" stroke=\"#6b8fb5\" stroke-width=\"1.3\"/>\n<path d=\"M80 66 L108 66 Q112 66 112 70 L112 80 Q112 84 108 84 L80 84 Z\" fill=\"#e9efe7\"/>\n<path d=\"M80 72 L112 72 M80 78 L112 78\" stroke-width=\"1.1\"/>\n<path d=\"M92 42 Q92 37 96.5 37 Q100 37 100 41 Q100 37 103.5 37 Q108 37 108 42 Q108 47 100 53 Q92 47 92 42 Z\" fill=\"#f6e9e5\" stroke=\"#c2857b\"/></g></svg>",
  "passeio": "<svg viewBox=\"0 0 140 110\" fill=\"none\"><ellipse cx=\"70\" cy=\"58\" rx=\"60\" ry=\"42\" fill=\"#ffffff\" opacity=\"0.85\"/><g stroke=\"#453c33\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n<path d=\"M38 46 Q38 24 62 24 L62 46 Z\" fill=\"#f2e3d2\"/>\n<path d=\"M44 28 Q48 34 47 44 M53 25 Q55 33 55 46\" stroke-width=\"1.1\" stroke=\"#c0763b\"/>\n<path d=\"M30 46 L92 46 Q100 46 100 54 Q100 64 88 64 L44 64 Q34 64 32 52 Z\" fill=\"#ffffff\"/>\n<path d=\"M100 48 Q108 44 112 34\"/><circle cx=\"112\" cy=\"33\" r=\"2.2\" fill=\"#c0763b\" stroke=\"none\"/>\n<circle cx=\"50\" cy=\"76\" r=\"8.5\" fill=\"#ffffff\"/><circle cx=\"50\" cy=\"76\" r=\"2\" fill=\"#453c33\" stroke=\"none\"/>\n<circle cx=\"84\" cy=\"76\" r=\"8.5\" fill=\"#ffffff\"/><circle cx=\"84\" cy=\"76\" r=\"2\" fill=\"#453c33\" stroke=\"none\"/>\n<path d=\"M50 68 L50 84 M42 76 L58 76 M78 71 L90 81 M78 81 L90 71\" stroke-width=\"1\"/></g></svg>",
  "mala": "<svg viewBox=\"0 0 140 110\" fill=\"none\"><ellipse cx=\"70\" cy=\"58\" rx=\"60\" ry=\"42\" fill=\"#ffffff\" opacity=\"0.85\"/><g stroke=\"#453c33\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n<path d=\"M34 46 L106 46 L106 40 Q106 34 100 34 L40 34 Q34 34 34 40 Z\" fill=\"#f2e3d2\"/>\n<path d=\"M62 34 L62 30 Q62 27 65 27 L75 27 Q78 27 78 30 L78 34\"/>\n<rect x=\"30\" y=\"48\" width=\"80\" height=\"34\" rx=\"5\" fill=\"#ffffff\"/><path d=\"M30 58 L110 58\" stroke-width=\"1.1\"/>\n<path d=\"M38 48 Q42 40 50 42 Q58 44 56 48 M64 48 Q70 40 78 44 Q84 46 82 48 M88 48 Q94 42 100 45 Q104 47 102 48\" stroke=\"#7a9678\" stroke-width=\"1.3\"/>\n<rect x=\"46\" y=\"64\" width=\"12\" height=\"8\" rx=\"2\" fill=\"#f6e9e5\"/><rect x=\"82\" y=\"64\" width=\"12\" height=\"8\" rx=\"2\" fill=\"#e9efe7\"/></g></svg>",
  "docs": "<svg viewBox=\"0 0 140 110\" fill=\"none\"><ellipse cx=\"70\" cy=\"58\" rx=\"60\" ry=\"42\" fill=\"#ffffff\" opacity=\"0.85\"/><g stroke=\"#453c33\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n<rect x=\"44\" y=\"26\" width=\"52\" height=\"62\" rx=\"3\" fill=\"#ffffff\"/>\n<path d=\"M52 38 L88 38 M52 46 L88 46 M52 54 L76 54\" stroke=\"#b5aa9c\" stroke-width=\"1.2\"/>\n<circle cx=\"80\" cy=\"72\" r=\"8\" fill=\"#f2e3d2\" stroke=\"#c0763b\"/><path d=\"M77 72 L79.5 75 L84 69\" stroke=\"#c0763b\" stroke-width=\"1.5\"/>\n<path d=\"M52 66 Q58 62 62 66 Q66 70 60 71\" stroke=\"#7a9678\" stroke-width=\"1.3\"/>\n<path d=\"M100 50 L110 78 L107 84 L103 79 Z\" fill=\"#e9efe7\"/></g></svg>",
  "cha": "<svg viewBox=\"0 0 140 110\" fill=\"none\">\n  <ellipse cx=\"70\" cy=\"58\" rx=\"60\" ry=\"42\" fill=\"#ffffff\" opacity=\"0.85\"/>\n  <g stroke=\"#453c33\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n    <ellipse cx=\"65\" cy=\"86\" rx=\"43\" ry=\"9\" fill=\"#f6e9e5\" opacity=\".5\" stroke=\"none\"/>\n    <path d=\"M40 62 L76 62 L76 84 L40 84Z\" fill=\"#f2e3d2\" opacity=\".78\"/>\n    <path d=\"M40 62 L58 70 L76 62 M58 62 L58 84\"/>\n    <path d=\"M55 62 Q47 55 50 51 Q56 49 58 58 Q61 49 67 52 Q70 56 61 62Z\" fill=\"#c2857b\" opacity=\".72\"/>\n    <path d=\"M50 52 Q55 53 58 58 Q62 53 67 53\"/>\n    <path d=\"M52 43 L82 43 L82 63 L52 63Z\" fill=\"#e9efe7\" opacity=\".8\"/>\n    <path d=\"M52 43 L67 50 L82 43 M67 43 L67 63\"/>\n    <path d=\"M64 43 Q57 37 60 33 Q66 32 67 40 Q70 32 76 34 Q79 38 70 43Z\" fill=\"#c0763b\" opacity=\".7\"/>\n    <path d=\"M60 34 Q65 35 67 40 Q71 35 76 35\"/>\n    <ellipse cx=\"103\" cy=\"30\" rx=\"8\" ry=\"11\" fill=\"#f6e9e5\" opacity=\".78\"/>\n    <ellipse cx=\"116\" cy=\"37\" rx=\"7\" ry=\"10\" fill=\"#e8eef5\" opacity=\".8\"/>\n    <ellipse cx=\"97\" cy=\"43\" rx=\"7\" ry=\"10\" fill=\"#e9efe7\" opacity=\".82\"/>\n    <path d=\"M103 41 Q100 55 91 66 M116 47 Q112 58 92 69 M97 53 Q95 60 90 68\"/>\n    <path d=\"M88 69 Q93 71 96 67\"/>\n    <path d=\"M28 35 l2 5 5 2-5 2-2 5-2-5-5-2 5-2Z\" fill=\"#f2e3d2\" opacity=\".82\"/>\n    <path d=\"M35 54 l1.5 4 4 1.5-4 1.5-1.5 4-1.5-4-4-1.5 4-1.5Z\" fill=\"#e9efe7\" opacity=\".84\"/>\n    <circle cx=\"101\" cy=\"72\" r=\"1.7\" fill=\"#c2857b\" opacity=\".68\" stroke=\"none\"/>\n    <circle cx=\"27\" cy=\"77\" r=\"1.5\" fill=\"#c0763b\" opacity=\".68\" stroke=\"none\"/>\n  </g></svg>"
}

export const SOURCES = [
  "SBP — Nota de Alerta: sono seguro (recomendações AAP) · sbp.com.br",
  "Ministério da Saúde — Caderneta da Gestante · bvsms.saude.gov.br",
  "NHS — What to buy for your newborn baby · nhs.uk",
  "Lei 9.656/98 art. 12 — cobertura e inclusão do recém-nascido · planalto.gov.br",
  "Resolução CONTRAN 819/2021 — dispositivo de retenção infantil · gov.br/transportes",
  "ANOREG — registro civil de nascimento · anoreg.org.br",
  "ABNT NBR 16365 — segurança de vestuário infantil (cordões e laços)",
  "Instituto PENSI · Macetes de Mãe · Integralmente Mãe — o que NÃO comprar",
  "Sou Mãe · Vestindo Crianças · Timirim · Novo Bebê — quantidades por tamanho",
  "Huggies · Cabide Infantil — consumo real de fraldas por dia"
]

export const PAL = {
  terra: { tint: '#f2e3d2', deep: '#a05f2c', mid: '#c0763b' },
  sage:  { tint: '#e9efe7', deep: '#5d7a5b', mid: '#7a9678' },
  rose:  { tint: '#f6e9e5', deep: '#a8544a', mid: '#c2857b' },
  blue:  { tint: '#e8eef5', deep: '#4d6f96', mid: '#6b8fb5' },
  sand:  { tint: '#f0ead9', deep: '#8a7430', mid: '#b09a4e' },
}
