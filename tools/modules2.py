# -*- coding: utf-8 -*-
"""Módulos 02–06: sono, banho, fraldas, farmacinha, amamentação."""
from modules import i


# ══════════════════════════════════════════════════════════════
# 02 — QUARTO & SONO SEGURO
# ══════════════════════════════════════════════════════════════
M_SONO = dict(
    num='02', window=(24, 32), title='Quarto & sono seguro', short='Sono seguro', pal='blue',
    spot='sono', win='comprar entre as semanas 24–32',
    intro='A regra que organiza tudo aqui: berço vazio. Colchão firme, lençol bem '
          'esticado e nada mais dentro dele no primeiro ano. O resto do quarto é '
          'conforto de vocês dois — e, em Brasília, briga contra o ar seco.',
    blocks=[
        ('table', dict(
            title='Berço e colchão — o que a norma exige',
            head=['Item', 'Especificação', 'Por quê'],
            rows=[
                ['Espaço entre grades', 'máximo 6,5 cm', 'cabeça não passa'],
                ['Folga colchão–grade', 'máximo 2 dedos (~2 cm)', 'evita aprisionamento'],
                ['Altura da grade', 'mínimo 60 cm', 'impede queda quando ela ficar de pé'],
                ['Densidade do colchão', 'mínimo D18', 'firmeza reduz risco de sufocação'],
                ['Altura do colchão', '10–12 cm', 'padrão de berço certificado'],
            ],
            note='Berço padrão usa colchão de 130×60 cm; mini-berço, 86×38 cm; '
                 'berço acoplado (co-sleeper), ~75×67 cm e suporta até 9 kg. '
                 'Exija selo do Inmetro e tinta atóxica.')),

        ('items', [
            i('Berço certificado Inmetro', '1', True,
              'Considerem o modelo acoplado à cama: atende à recomendação de dividir o quarto '
              'sem dividir a superfície de sono.'),
            i('Colchão firme no tamanho exato', '1', True,
              'Sem frestas nas laterais. Firme de verdade — colchão macio é fator de risco.'),
            i('Lençol de elástico', '3', True, 'Um na cama, dois em revezamento.'),
            i('Protetor de colchão impermeável', '1–2', True),
            i('Saco de dormir', '2–3', True,
              'TOG 0,5 e 1,0 para o verão; TOG 2,5 só em maio, para a seca.'),
            i('Manta leve respirável', '3–4', False, 'Multiuso, nunca solta dentro do berço.'),
            i('Umidificador ultrassônico', '1', True,
              'Brasília é o motivo. Ver o quadro abaixo antes de usar.'),
            i('Cômoda com trocador', '1', False, 'Altura na cintura evita dor nas costas.'),
            i('Poltrona de amamentação', '1', False,
              'Vai ser usada 10 a 15 vezes por dia nos primeiros meses — não economize no conforto.'),
            i('Babá eletrônica', '1', False, 'Com câmera e visão noturna, se couber no orçamento.'),
            i('Luz noturna âmbar ou vermelha', '1', True,
              'Cor importa: luz azul e branca suprimem melatonina. 0,5–2 W bastam.'),
            i('Cortina blackout', '1', False, 'Ajuda no sono diurno e na volta ao sono de madrugada.'),
        ]),

        ('tip', dict(
            title='umidificador — o item mais brasiliense da lista',
            body='Na seca a umidade daqui cai bem abaixo dos <b>50–60%</b> que a OMS considera '
                 'saudável, e ar seco resseca a via aérea da Laura. Use o ultrassônico por '
                 '<b>2 a 3 horas à noite</b>, não a noite toda — excesso de umidade gera mofo, '
                 'que é pior que o ar seco. <b>Troque a água a cada 12 h</b> e limpe o filtro '
                 'uma vez por semana, sem falta: umidificador sujo vira nebulizador de fungo.')),

        ('tip', dict(
            title='sono seguro — o essencial da SBP e da AAP',
            body='<b>Sempre de barriga para cima</b>, nunca de lado ou de bruços. Quarto entre '
                 '<b>20 e 24 °C</b> (ideal 22–23). Ela deve dormir <b>no quarto de vocês, em '
                 'berço próprio, dos 6 aos 12 meses</b> — isso reduz o risco de morte súbita. '
                 'E o berço fica vazio: sem travesseiro, sem protetor, sem bicho de pelúcia, '
                 'sem coberta solta.')),

        ('avoid', dict(
            title='melhor evitar — sério mesmo · risco de sufocação',
            items=[
                'Travesseiro de qualquer tipo, inclusive "anatômico", antes de 12 meses.',
                'Protetor de berço / kit berço acolchoado.',
                'Cobertas soltas, almofadas e bichos de pelúcia dentro do berço.',
                'Ninho ou redutor de berço para dormir sem supervisão.',
                'Dormir no bebê conforto, no carrinho ou no sofá como rotina.',
                'Móbile com som alto ou peças pequenas ao alcance.',
                'Aquecedor de mamadeira e termômetro de banheira — dinheiro jogado fora.',
            ])),
        ('band', 'sono'),
    ])


# ══════════════════════════════════════════════════════════════
# 03 — BANHO & HIGIENE
# ══════════════════════════════════════════════════════════════
M_BANHO = dict(
    num='03', window=(28, 34), title='Banho & higiene', short='Banho', pal='sage',
    spot='banho', win='comprar entre as semanas 28–34',
    intro='Nas primeiras semanas, menos é mais: água morna resolve quase tudo. '
          'A pele dela ainda está montando a própria barreira — produto demais atrapalha.',
    blocks=[
        ('items', [
            i('Banheira com suporte', '1', True, 'Apoio firme é o que importa; a pia também serve.'),
            i('Toalha com capuz', '2–3', True, '100% algodão, bem macia.'),
            i('Sabonete líquido neutro', '1 · 200–250 ml', False,
              'Sem fragrância. Nas primeiras semanas, água já dá conta da maior parte do corpo.'),
            i('Algodão', '1–2 pacotes de 500 g por mês', True,
              'É o item que todo mundo subestima: usa-se a cada troca de fralda.'),
            i('Gaze estéril', '2–3 pacotes'),
            i('Pente ou escova macia', '1'),
            i('Tesourinha de ponta redonda ou cortador', '1', False,
              'Cortar com ela dormindo é infinitamente mais fácil.'),
            i('Termômetro de banho', '1', False,
              'Opcional — o punho ou o cotovelo testam igual.'),
        ]),

        ('tip', dict(
            title='coto umbilical — a recomendação mudou',
            body='O padrão atual da OMS para parto hospitalar é manter o coto '
                 '<b>limpo e seco</b>, sem antisséptico. Álcool 70% de rotina '
                 '<b>não é mais recomendado</b> nesse cenário: não reduz infecção onde o risco '
                 'já é baixo e ainda atrasa a queda em cerca de um dia. Na prática: lave com '
                 'água e sabão no banho, <b>seque bem</b>, e dobre a fralda para baixo do coto '
                 'para deixá-lo arejado. Cai sozinho entre <b>7 e 14 dias</b> — nunca puxe. '
                 'Procure o pediatra se houver odor forte, secreção com pus, vermelhidão ao '
                 'redor ou febre acima de 38 °C.')),

        ('table', dict(
            title='Banho, na prática',
            head=['Pergunta', 'Resposta'],
            rows=[
                ['Com que frequência?', 'diário é seguro; 2–3× por semana também basta'],
                ['Temperatura da água', '36–37 °C'],
                ['Duração', '5 a 10 minutos'],
                ['Antes do coto cair', 'possível, secando muito bem o coto depois'],
                ['O que limpar sempre', 'pregas de pele, região da fralda e o coto'],
            ],
            note='O que não pode faltar é a limpeza das dobrinhas e da área da fralda — '
                 'o banho inteiro é menos crítico do que isso.')),

        ('avoid', dict(items=[
            'Cotonete dentro do ouvido ou do nariz.',
            'Talco — risco de aspiração.',
            'Perfume, colônia e sabonete adulto nos primeiros meses.',
            'Amarrar o coto com fio, moeda ou faixa umbilical.',
            'Esfregar a pele; secar sempre por leves toques.',
        ])),
        ('band', 'banho'),
    ])


# ══════════════════════════════════════════════════════════════
# 04 — FRALDAS & TROCA
# ══════════════════════════════════════════════════════════════
M_FRALDAS = dict(
    num='04', window=(28, 36), title='Fraldas & troca', short='Fraldas', pal='terra',
    spot='fraldas', win='comprar entre as semanas 28–36',
    intro='O erro clássico é estocar RN. A fase dura duas ou três semanas e a marca '
          'pode simplesmente não servir na pele dela — melhor errar para menos.',
    blocks=[
        ('table', dict(
            title='Consumo real por tamanho',
            head=['Tam.', 'Peso', 'Por dia', 'Quanto dura'],
            rows=[
                ['RN', 'até 4,5 kg', '8 a 10', '2 a 3 semanas'],
                ['P', '4–8 kg', '7 a 10', 'até 2 meses'],
                ['M', '6–11 kg', '5 a 7', '3 a 7 meses'],
                ['G', '9–13 kg', '4 a 5', '9 a 13 meses'],
            ],
            note='A fase RN consome entre 110 e 210 fraldas no total. Um pacote traz de '
                 '20 a 40 unidades, dependendo da marca — compre pensando em unidades, '
                 'não em pacotes.')),

        ('items', [
            i('Fralda descartável RN', '120–180 unidades', True,
              'Cobre a fase inteira sem sobrar caixa fechada em casa.'),
            i('Fralda descartável P', '3–4 pacotes', False,
              'O grosso do estoque vai ser P e M — é o melhor pedido de chá de bebê.'),
            i('Trocador fixo + portátil', '1 + 1', True),
            i('Pomada de prevenção de assadura', '2–3', True,
              'Camada fina a cada troca. Prevenção e tratamento são produtos diferentes.'),
            i('Algodão para a troca', 'ver módulo 03', True,
              'Água morna + algodão é o padrão em casa para recém-nascido.'),
            i('Lenços umedecidos sem álcool e sem perfume', '1–2 pacotes por mês', False,
              'Para a rua. Uso diário em casa pode irritar a pele nova.'),
            i('Lixeira com tampa', '1'),
        ]),

        ('tip', dict(
            title='água e algodão × lenço umedecido',
            body='Para recém-nascido em casa, a recomendação é <b>algodão com água morna</b> — '
                 'o lenço umedecido é conveniência de rua, não rotina. Para xixi, algodão '
                 'basta; para cocô, água corrente limpa melhor e machuca menos. '
                 'Nunca esfregue: limpe com toques.')),

        ('avoid', dict(items=[
            'Comprar caixas da mesma marca antes de testar na pele dela.',
            'Lenço umedecido com álcool, parabeno, corante ou fragrância.',
            'Estocar tamanho RN — é o tamanho que menos dura.',
        ])),
        ('band', 'fraldas'),
    ])


# ══════════════════════════════════════════════════════════════
# 05 — FARMACINHA & SAÚDE
# ══════════════════════════════════════════════════════════════
M_FARMACIA = dict(
    num='05', window=(30, 36), title='Farmacinha & saúde', short='Farmacinha', pal='rose',
    spot='farmacinha', win='comprar entre as semanas 30–36',
    intro='Farmacinha de bebê é de suporte, não de tratamento. Nada de medicamento '
          'sem prescrição — dose de criança é por peso e muda de mês para mês.',
    blocks=[
        ('items', [
            i('Termômetro digital', '1–2', True,
              'Axilar ou infravermelho. Mercúrio é proibido no Brasil.'),
            i('Soro fisiológico 0,9%', '2–3 caixas por mês', True,
              'Higiene nasal e ocular — em Brasília, uso quase diário na seca.'),
            i('Aspirador nasal', '1', False, 'Ponta macia.'),
            i('Gaze estéril', '2–3 pacotes'),
            i('Álcool 70%', '1 frasco', False,
              'Para superfície e para as mãos de quem pega no colo — não para a pele dela.'),
            i('Antitérmico prescrito pelo pediatra', None, True,
              'Peça a receita com a dose por peso ANTES de precisar, na consulta pré-natal '
              'pediátrica. Às 3 da manhã não dá para improvisar.'),
            i('Lista de contatos na geladeira', None, True,
              'Pediatra, maternidade, SAMU 192.'),
        ]),

        ('tip', dict(
            title='febre — quando ligar para o pediatra',
            body='Considera-se febre a partir de <b>37,8–38 °C axilar</b>. Em bebê com '
                 '<b>menos de 3 meses, qualquer febre é motivo de avaliação médica no mesmo '
                 'dia</b> — não espere passar e não medique por conta. Antitérmico só com '
                 'prescrição, na dose calculada pelo peso atual.')),

        ('tip', dict(
            title='G6PD — o que muda por causa do papai',
            body='A deficiência de G6PD é ligada ao cromossomo X. Como o Palmer tem a '
                 'condição, ele passa o único X dele para todas as filhas: a Laura será '
                 '<b>portadora obrigatória</b> — não é probabilidade, é certeza. Portadoras '
                 'costumam ser assintomáticas, mas a inativação aleatória do X faz a atividade '
                 'da enzima variar bastante, e algumas têm deficiência clinicamente relevante. '
                 'Duas providências: <b>peça o teste do pezinho ampliado</b> (a versão básica '
                 'não dosa G6PD) e <b>registre a condição no prontuário dela</b>, para que '
                 'qualquer médico ou dentista saiba antes de prescrever.')),

        ('avoid', dict(
            title='substâncias a evitar — G6PD',
            items=[
                'Sulfas (sulfametoxazol) e nitrofurantoína.',
                'Antimaláricos, especialmente primaquina.',
                'Ácido acetilsalicílico (aspirina) em dose alta.',
                'Naftalina e cânfora — tirar de casa antes dela chegar.',
                'Fava e derivados.',
                'Antitérmico ou antigripal por conta própria — sempre confirmar com o pediatra.',
                'Mel antes de 1 ano — risco de botulismo infantil (vale para qualquer bebê).',
            ])),
        ('band', 'farmacinha'),
    ])


# ══════════════════════════════════════════════════════════════
# 06 — AMAMENTAÇÃO
# ══════════════════════════════════════════════════════════════
M_AMAMENTA = dict(
    num='06', window=(28, 36), title='Amamentação', short='Amamentação', pal='terra',
    spot='amamentacao', win='comprar entre as semanas 28–36',
    intro='Aleitamento exclusivo até os 6 meses é a recomendação da OMS e do Ministério '
          'da Saúde. Compre o mínimo antes: o que vocês vão precisar de verdade só '
          'aparece na segunda semana.',
    blocks=[
        ('items', [
            i('Sutiã de amamentação', '3–4', True,
              'Comprar a partir da semana 36 — o peito muda muito até lá. Algodão, sem aro.'),
            i('Absorvente de seio', '1–2 caixas por mês', False,
              'Ou 4–6 pares laváveis, se preferirem reutilizável.'),
            i('Lanolina pura', '1 bisnaga de 30 g', True,
              'Para fissura. Reaplicar depois das mamadas.'),
            i('Camisola com abertura frontal', '2–3'),
            i('Almofada de amamentação', '1', False, 'Opcional, mas salva as costas.'),
            i('Contato de consultora de amamentação', None, True,
              'Resolver ANTES do parto. As primeiras 48 h definem muita coisa.'),
            i('Potes ou sacos para armazenar leite', '1 kit', False,
              'Só se houver plano de extrair — não compre por precaução.'),
        ]),

        ('table', dict(
            title='Armazenamento do leite materno',
            head=['Onde', 'Por quanto tempo'],
            rows=[
                ['Temperatura ambiente', '2 horas (1 h em dia quente)'],
                ['Geladeira (4 °C)', '12 horas — prateleira alta, nunca na porta'],
                ['Freezer (−18 °C)', '15 dias'],
                ['Depois de descongelado', '12 horas na geladeira'],
            ],
            note='Descongele em banho-maria, nunca no micro-ondas — o calor irregular '
                 'destrói as imunoglobulinas. Leite descongelado não volta ao freezer.')),

        ('table', dict(
            title='Ela está mamando o suficiente?',
            head=['Sinal', 'Esperado'],
            rows=[
                ['Fraldas molhadas', '6 a 8 por dia, a partir do 5º dia'],
                ['Cor da urina', 'clara ou levemente amarelada'],
                ['Ganho de peso (0–4 meses)', '150 a 200 g por semana'],
                ['Peso na 1ª semana', 'perda de até 10% é normal; recupera até o 14º dia'],
                ['Fezes', 'mecônio escuro → amareladas pastosas a partir do 3º dia'],
            ],
            note='Ela soltar o peito sozinha, relaxar as mãozinhas e dormir depois da mamada '
                 'também são bons sinais.')),

        ('tip', dict(
            title='bancos de leite no DF — apoio gratuito',
            body='O DF tem rede de bancos de leite que também <b>orientam sobre pega e '
                 'ordenha, de graça</b>: Hospital Materno Infantil (Asa Sul), Maternidade '
                 'Brasília (Sudoeste), Hospital Regional de Santa Maria e Hospital '
                 'Universitário de Brasília. Informações pelo <b>Disque Saúde 160</b>. '
                 'Vale anotar isso na geladeira junto com os telefones de emergência.')),

        ('avoid', dict(items=[
            'Comprar bomba extratora antes do parto — alugue ou teste a manual primeiro.',
            'Chupeta e mamadeira antes da 4ª semana: risco de confusão de bicos e desmame precoce.',
            'Micro-ondas para aquecer leite materno.',
            'Estocar fórmula "por precaução" antes de qualquer avaliação.',
        ])),
        ('band', 'amamentacao'),
    ])
