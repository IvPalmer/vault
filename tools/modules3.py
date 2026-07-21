# -*- coding: utf-8 -*-
"""Módulos 07–10: passeio, mala, prazos, chá de bebê."""
from modules import i


# ══════════════════════════════════════════════════════════════
# 07 — PASSEIO & TRANSPORTE
# ══════════════════════════════════════════════════════════════
M_PASSEIO = dict(
    num='07', window=(28, 36), title='Passeio & transporte', short='Passeio', pal='sage',
    spot='passeio', win='comprar entre as semanas 28–36',
    intro='Brasília é cidade de carro, então o bebê conforto não é acessório: '
          'é o item que precisa estar instalado e testado antes de vocês saírem de casa '
          'para a maternidade.',
    blocks=[
        ('table', dict(
            title='O que a lei exige — CONTRAN 819/2021',
            head=['Dispositivo', 'Idade / peso', 'Como usar'],
            rows=[
                ['Bebê conforto', 'até 1 ano ou 13 kg', 'de costas, banco traseiro'],
                ['Cadeirinha', '1 a 4 anos ou 9–18 kg', 'banco traseiro'],
                ['Assento de elevação', '4 a 7,5 anos ou 15–36 kg', 'banco traseiro, com cinto'],
            ],
            note='A obrigação vale até 10 anos ou 1,45 m de altura. Exija selo do Inmetro. '
                 'A validade vem gravada no plástico — o polímero degrada e perde capacidade '
                 'de absorver impacto.')),

        ('items', [
            i('Bebê conforto grupo 0+', '1', True,
              'Instalar e testar até a semana 36. Se o carro tiver ISOFIX, use — reduz muito '
              'a chance de instalação errada.'),
            i('Carrinho com reclínio de 170–180°', '1', True,
              'Recém-nascido precisa ir deitado: sentado, o queixo cai no peito e comprime '
              'a via aérea.'),
            i('Sling ou canguru ergonômico', '1', False,
              'Ergonômico de verdade, não o modelo que deixa a criança pendurada pela virilha.'),
            i('Bolsa de passeio com trocador portátil', '1'),
            i('Sombrinha ou capota com proteção UV', '1', True,
              'Antes dos 6 meses, proteção solar é física — sombra e roupa.'),
        ]),

        ('tip', dict(
            title='regra TICKS — o sling seguro em 5 checagens',
            body='<b>T</b>enso o suficiente para ela ficar colada em você · '
                 '<b>I</b> sempre à vista, rosto descoberto · '
                 '<b>C</b>lose: perto o bastante para você beijar a cabeça dela · '
                 '<b>K</b>eep o queixo longe do peito, cabendo um dedo sob o queixo · '
                 '<b>S</b>uporte nas costas, coluna acompanhada em C. '
                 'Sling mal posicionado compromete a respiração — é o único risco real dele.')),

        ('tip', dict(
            title='sol e mosquito em Brasília',
            body='<b>Protetor solar só a partir dos 6 meses</b> (SBP) — antes disso, sombra, '
                 'chapéu e roupa, evitando o sol entre 10 h e 16 h. '
                 '<b>Repelente:</b> icaridina é liberada a partir dos <b>2 meses</b>, IR3535 a '
                 'partir dos 6 meses, e DEET só depois dos 2 anos. Em ano de dengue isso '
                 'importa: mosquiteiro no berço e no carrinho resolve a fase em que nenhum '
                 'repelente é permitido.')),

        ('avoid', dict(items=[
            'Andador — a SBP contraindica: trauma craniano, queimadura e atraso motor.',
            'Bebê conforto usado sem histórico, ou com validade vencida.',
            'Deixá-la dormindo no bebê conforto ou na cadeirinha de descanso por longos períodos.',
            'Carrinho sem reclínio total nos primeiros meses.',
            'Bebê conforto no banco da frente com airbag.',
        ])),
        ('band', 'passeio'),
    ])


# ══════════════════════════════════════════════════════════════
# 08 — MALA DA MATERNIDADE
# ══════════════════════════════════════════════════════════════
M_MALA = dict(
    num='08', window=(32, 34), title='Mala da maternidade', short='Mala', pal='blue',
    spot='mala', win='pronta na porta até a semana 34',
    intro='Deixem pronta entre as semanas 32 e 34. Parto prematuro acontece, e a partir '
          'daí carregar peso e organizar armário fica cada vez mais desconfortável.',
    blocks=[
        ('groups', [
            ('Documentos', [
                i('RG e CPF dos dois', None, True, 'Originais e uma cópia de cada.'),
                i('Carteirinha do plano + guia de internação', None, True),
                i('Caderneta da gestante + últimos exames e ultrassons', None, True,
                  'É o canal de comunicação com a equipe que vai receber vocês.'),
                i('Plano de parto impresso', '2 cópias'),
                i('Comprovante de residência', '1 cópia', False,
                  'Útil se a maternidade tiver posto de cartório para o registro.'),
            ]),
            ('Para a Rafaella — internação', [
                i('Camisola ou pijama com abertura frontal', '3–4', True),
                i('Robe + chinelo antiderrapante', '1'),
                i('Calcinha de algodão ou descartável', '6', True, 'Cós alto, elástico largo.'),
                i('Sutiã de amamentação', '2', True),
                i('Absorvente pós-parto', '1–2 pacotes', True,
                  'A maternidade costuma fornecer parte — leve reforço mesmo assim.'),
                i('Nécessaire de higiene pessoal', '1'),
                i('Roupa confortável para a alta', '1'),
            ]),
            ('Para a Laura', [
                i('Body', '4–6', True, 'Levar tamanho RN e P — o peso ao nascer é imprevisível.'),
                i('Macacão', '4–6', True),
                i('Meias', '3 pares'),
                i('Manta leve', '2'),
                i('Touca', '1–2'),
                i('Fraldas RN', '1 pacote', False,
                  'A maternidade fornece a maior parte — confirmar na visita.'),
                i('Saída de maternidade', '1'),
            ]),
            ('Para o Palmer', [
                i('Trocas de roupa', '3', True, 'Internação costuma durar 2 a 3 dias.'),
                i('Chinelo e nécessaire', '1'),
                i('Carregadores + power bank', '1', True),
                i('Lanches e garrafa de água', None, False,
                  'Trabalho de parto é longo e a cantina fecha.'),
                i('Bebê conforto instalado no carro', None, True,
                  'Não dá para sair da maternidade sem ele.'),
            ]),
        ]),

        ('tip', dict(
            title='perguntas para levar na visita à maternidade',
            body='Faça a visita entre as semanas 28 e 32 e pergunte: quantas fraldas por dia '
                 'eles fornecem? Fornecem camisola, kit de higiene e absorvente? A Rafaella pode '
                 'usar roupa própria durante o trabalho de parto? Tem banheira ou chuveiro '
                 'disponível? Tem posto de cartório para registro dentro do hospital? '
                 'A resposta muda o tamanho da mala.')),

        ('tip', dict(
            title='quando ir para a maternidade',
            body='<b>Regra 5-1-1:</b> contrações a cada 5 minutos, durando 1 minuto, por 1 hora '
                 'seguida. Também é hora de ir se a bolsa romper (mesmo sem contração) ou se '
                 'houver sangramento parecido com menstruação. '
                 '<b>Ir imediatamente, sem esperar:</b> sangramento intenso, febre alta, dor '
                 'abdominal forte e persistente, tontura ou desmaio, e — o mais importante — '
                 '<b>redução perceptível dos movimentos da Laura</b>.')),

        ('tip', dict(
            title='o direito de ter o Palmer junto',
            body='A <b>Lei 11.108/2005</b> garante à Rafaella um acompanhante de livre escolha '
                 'durante todo o trabalho de parto, o parto e o pós-parto imediato — em '
                 'qualquer maternidade, pública ou privada. Não é cortesia do hospital, '
                 'é direito. Se alguém disser o contrário, cite a lei pelo número.')),
        ('band', 'mala'),
    ])


# ══════════════════════════════════════════════════════════════
# 09 — PRAZOS & DOCUMENTOS
# ══════════════════════════════════════════════════════════════
M_PRAZOS = dict(
    num='09', window=None, title='Depois que nascer: prazos', short='Prazos', pal='rose',
    spot='docs', win='nada se compra — são prazos',
    intro='Esta é a única página sem compra nenhuma. São prazos legais, e dois deles '
          'valem dinheiro e carência se passarem em branco.',
    blocks=[
        ('timeline', [
            dict(when='primeiras 12 h', hot=True,
                 what='<b>Vacina Hepatite B</b> — primeira dose ainda na maternidade.'),
            dict(when='dia 0–1', hot=False,
                 what='<b>BCG</b> (peso mínimo 2 kg) e <b>guardar a DNV</b>, a Declaração de '
                      'Nascido Vivo que o hospital emite — é ela que destrava todo o resto.'),
            dict(when='dia 1–2', hot=False,
                 what='<b>Teste do coraçãozinho</b> (oximetria, detecta cardiopatia congênita) '
                      'e <b>teste da linguinha</b>.'),
            dict(when='dia 2–3', hot=False,
                 what='<b>Teste da orelhinha</b> — triagem auditiva.'),
            dict(when='dia 3–5', hot=True,
                 what='<b>Teste do pezinho</b> — não antes de 48 h de vida. '
                      'Peça a <b>versão ampliada</b>: a básica não dosa G6PD, que é o que '
                      'importa no caso da Laura.'),
            dict(when='dia 1–7', hot=False,
                 what='<b>Teste do olhinho</b> e <b>primeira consulta pediátrica</b> — '
                      'o Ministério da Saúde recomenda até o 7º dia, idealmente entre o 3º e o 5º.'),
            dict(when='até 15 dias', hot=True,
                 what='<b>Registro civil em cartório</b> — certidão gratuita por lei, e o CPF '
                      'sai junto na hora. Basta a DNV e o documento de um dos pais.'),
            dict(when='até 30 dias', hot=True,
                 what='<b>Incluir a Laura no plano de saúde.</b> Pela Lei 9.656/98 e pela '
                      'Súmula 25 da ANS, a inscrição feita nesse prazo entra <b>sem carência '
                      'nenhuma</b>. Depois dele, a operadora pode alegar doença preexistente e '
                      'impor cobertura parcial temporária. Não deixem para o dia 29.'),
            dict(when='até 30 dias', hot=False,
                 what='<b>Licença-paternidade e maternidade</b> — dar entrada. Ver quadro abaixo.'),
        ]),

        ('tip', dict(
            title='licença-paternidade: a lei mudou a favor de vocês',
            body='A <b>Lei 15.371/2026</b> ampliou a licença-paternidade de forma escalonada: '
                 '<b>10 dias para nascimentos a partir de 1º de janeiro de 2027</b> — ou seja, '
                 'a Laura já nasce sob a regra nova (eram 5 dias até dez/2026). Sobe para 15 '
                 'dias em 2028 e 20 em 2029. Mais importante: a lei criou o '
                 '<b>salário-paternidade pago pelo INSS</b>, que passou a contemplar '
                 '<b>autônomos, MEI e domésticos</b> — categorias que antes simplesmente não '
                 'tinham direito ao benefício. Vale conferir a situação contributiva antes '
                 'do parto.')),

        ('tip', dict(
            title='e a licença-maternidade',
            body='São <b>120 dias</b>, pagos pelo INSS via salário-maternidade. A entrada pode '
                 'ser feita a partir de 28 dias antes do parto e até o primeiro dia depois. '
                 'Para autônoma e contribuinte individual há <b>carência de 10 contribuições</b> '
                 '— vale confirmar o extrato do CNIS com antecedência, não depois.')),
        ('band', 'docs'),
    ])


# ══════════════════════════════════════════════════════════════
# 10 — CHÁ DE BEBÊ
# ══════════════════════════════════════════════════════════════
M_CHA = dict(
    num='10', window=(28, 34), title='Chá de bebê — o que pedir', short='Chá de bebê', pal='sand',
    spot='cha', win='organizar entre as semanas 28–34',
    intro='Chá de bebê bem pedido cobre justamente a parte cara e recorrente do enxoval. '
          'Mal pedido, vira armário cheio de roupa tamanho RN que ela nunca vai usar.',
    blocks=[
        ('items', [
            i('Fraldas tamanho P, M e G', None, True,
              'O melhor pedido possível. Peça pouca coisa em RN: essa fase dura semanas '
              'e vocês já compraram.'),
            i('Lenços umedecidos sem perfume', None, True),
            i('Pomada de assadura', None, True, 'Nunca sobra.'),
            i('Algodão e produtos de banho', None, False, 'Consumo alto e contínuo.'),
            i('Absorventes de seio e lanolina', None, False, 'Ninguém lembra de pedir — e acaba.'),
            i('Vale-presente de loja de bebê', None, False,
              'Resolve o que faltar depois, quando vocês souberem o que realmente usam.'),
            i('Cotização para item grande', None, False,
              'Carrinho, poltrona de amamentação ou babá eletrônica: combine em particular '
              'com quem se ofereceu, para não duplicar.'),
        ]),

        ('tip', dict(
            title='use uma lista online',
            body='Uma lista compartilhada evita o clássico: quatro pessoas dando a mesma manta '
                 'e ninguém dando fralda tamanho M. Também facilita para quem mora longe e vai '
                 'mandar pelos correios.')),

        ('avoid', dict(
            title='o que costuma sobrar',
            items=[
                'Roupa tamanho RN — é o que mais ganha e o que menos dura.',
                'Sapatinhos e luvinhas.',
                'Kit berço e protetor de grade — contraindicados pela SBP.',
                'Bichos de pelúcia grandes: não podem ir para o berço no primeiro ano.',
                'Aquecedor de mamadeira e termômetro de banheira.',
            ])),
        ('band', 'mala'),
    ])
