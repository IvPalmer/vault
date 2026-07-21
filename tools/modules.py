# -*- coding: utf-8 -*-
"""
Mapa do Enxoval da Laura — dados dos módulos.

Cada módulo: num, title, short (índice), pal, spot, win (janela), intro, blocks.
Blocos: intro | items | groups | table | timeline | tip | avoid | band | html
Ver engine.py para o contrato de cada bloco.

PROVENIÊNCIA: números vindos de pesquisa cruzada em guias BR + fontes oficiais
(SBP, MS, NHS, ANS, CONTRAN). Onde as fontes divergiam, adotamos o limite
inferior — a maioria das listas quantitativas vem de lojas de enxoval e tem
viés inflacionário. Divergências relevantes viram nota no próprio item.
"""

def i(label, qty=None, ess=False, note=None):
    """Atalho para item de checklist."""
    return dict(label=label, qty=qty, ess=ess, note=note)


# ══════════════════════════════════════════════════════════════
# 01 — ROUPINHAS
# ══════════════════════════════════════════════════════════════
M_ROUPAS = dict(
    num='01', window=(24, 32), title='Roupinhas', short='Roupinhas', pal='terra',
    spot='roupas', win='comprar entre as semanas 24–32',
    intro='Laura nasce no verão de Brasília, mas o clima real dela é o do '
          'ar-condicionado. Por isso a lista tem manga curta em peso e manga '
          'longa fininha — não é contradição, é as duas temperaturas do dia.',
    blocks=[
        ('table', dict(
            title='Tamanho é peso, não idade',
            head=['Tam.', 'Peso', 'Altura', 'Idade aprox.', 'Quanto dura'],
            rows=[
                ['RN', '2,5–4 kg', '46–52 cm', '0–1 mês', '2 a 4 semanas'],
                ['P', '4–6 kg', '53–60 cm', '1–3 meses', '6 a 10 semanas'],
                ['M', '6–8 kg', '61–66 cm', '3–6 meses', '~3 meses'],
                ['G', '8–9 kg', '67–72 cm', '6–9 meses', '~3 meses'],
                ['GG', '9–10 kg', '73–78 cm', '9–12 meses', '~3 meses'],
            ],
            note='Peso primeiro, altura como desempate, idade por último — dois bebês '
                 'da mesma idade podem ter 2 kg de diferença. Carter\'s e marcas '
                 'americanas usam NB/3M/6M/9M, equivalentes a RN/P/M/G. Na dúvida '
                 'entre dois tamanhos, pegue o maior.')),

        ('tip', dict(
            title='a conta que define a quantidade',
            body='Recém-nascido troca de roupa <b>3 a 4 vezes por dia</b>. '
                 'A fórmula é <b>(trocas por dia) × (dias entre lavagens) + 2 de folga</b>. '
                 'Lavando dia sim dia não: 4 × 2 + 2 = 10 bodies no P. '
                 'Jan/fev é estação chuvosa em Brasília e roupa demora a secar — '
                 'sem secadora, some 2 a 3 peças por item em RN e P.')),

        ('groups', [
            ('Tamanho RN · deliberadamente enxuto', [
                i('Body manga curta', '5', True,
                  'Peça mais usada de todas. Dura só 2–4 semanas neste tamanho.'),
                i('Body manga longa de algodão fino', '2', False,
                  'Não é para frio — é para o ar-condicionado.'),
                i('Mijão / culote', '4', False, 'Cós largo, sem elástico apertado.'),
                i('Macacão manga longa com pé', '3', True,
                  'Peça de dormir. Abertura frontal facilita a troca da madrugada.'),
                i('Macaquinho / macacão manga curta', '2'),
                i('Pagão', '1'),
                i('Meias', '3 pares'),
                i('Casaquinho de algodão', '2'),
                i('Touca de maternidade', '1', False,
                  'Para a saída e o ar-condicionado. Nunca para dormir.'),
                i('Saída de maternidade', '1', False,
                  'De algodão, não tricô nem plush — bebê de janeiro.'),
                i('Manta leve de musselina', '2', True),
                i('Manta média (soft fino)', '1'),
            ]),
            ('Tamanho P · o investimento principal', [
                i('Body manga curta', '8', True, 'É a base de tudo no verão.'),
                i('Body manga longa fino', '4'),
                i('Body regata', '3'),
                i('Mijão / culote', '6'),
                i('Macacão manga longa com pé', '5', True),
                i('Macaquinho manga curta', '5', True, 'Peça-chave do verão.'),
                i('Shorts', '3'),
                i('Casaquinho / cardigã leve', '2'),
                i('Meias', '5 pares'),
                i('Chapéu de sol de algodão', '2', False, 'UV de Brasília é alto o ano todo.'),
                i('Manta leve', '2'),
                i('Vestidinho / conjunto', '2', False, 'Uso ocasional — comprar pouco.'),
            ]),
            ('Sem tamanho · compra única', [
                i('Fralda de pano / pano de boca', '20', True,
                  'Item mais versátil do enxoval: golfada, ombro, sombra, forrar trocador.'),
                i('Babador', '4', False, 'Sobe para 6–8 na introdução alimentar (~6 meses).'),
                i('Toalha com capuz', '2–3'),
                i('Cueiro', '2', False, 'Uso decrescente — muitas famílias abandonam em semanas.'),
                i('Saco de dormir TOG 0,5', '1', True, 'Para quarto acima de 24 °C.'),
                i('Saco de dormir TOG 1,0', '1', True,
                  'O mais versátil para quarto com ar-condicionado no verão.'),
                i('Lavar tudo antes do primeiro uso', None, True,
                  'Sabão de coco ou neutro, enxágue duplo, SEM amaciante. '
                  'Fazer por volta da semana 30–34. Remover etiquetas ásperas da nuca.'),
            ]),
        ]),

        ('table', dict(
            title='Como vestir para dormir, por temperatura do quarto',
            head=['Temperatura', 'Saco de dormir', 'Por baixo'],
            rows=[
                ['acima de 24 °C', 'TOG 0,5', 'só body manga curta'],
                ['20–23 °C (ar-cond.)', 'TOG 1,0', 'body manga curta + macacão leve'],
                ['18–20 °C', 'TOG 2,5', 'body manga longa + macacão'],
            ],
            note='Com saco de dormir, não somar cobertor por cima — se estiver frio, '
                 'aumente o TOG ou a camada de roupa. Sinal de superaquecimento: '
                 'pele úmida na nuca e no peito. Superaquecer é mais perigoso que '
                 'estar levemente frio.')),

        ('tip', dict(
            title='o que comprar depois, e quando',
            body='<b>Março/abril</b> (tamanho M, para usar de abr a jul): 8 bodies manga curta, '
                 '8 manga longa, 6 calças, 6 macacões com pé, 2 de plush, 3 casaquinhos de '
                 'moletom, saco TOG 2,5. <b>Maio/junho</b> (tamanho G): o inverno seco de '
                 'Brasília chega a 12–15 °C ao amanhecer com a Laura em M/G — é aí, e só aí, '
                 'que peça de frio se justifica. Comprar M/G antes do parto é aposta: '
                 'o ritmo de crescimento é imprevisível.')),

        ('avoid', dict(items=[
            'Estocar tamanho RN — dura 2 a 4 semanas e muito bebê já nasce vestindo P.',
            'Luvinhas: cobrir as mãos limita o desenvolvimento sensorial. 1 par, no máximo.',
            'Sapatinhos antes de 1 ano — decorativos, e o bebê se irrita com eles.',
            'Macacão de plush em RN e P: ela nunca vai usar em janeiro.',
            'Faixa umbilical — sem respaldo pediátrico atual.',
            'Amaciante: deixa película perfumada que não sai no enxágue e irrita a pele.',
            'Cordões e laços soltos perto do pescoço (proibidos por norma até 7 anos).',
            'Laço/faixa de cabelo para dormir — risco de garroteamento e asfixia.',
            'Comprar tudo antes do chá de bebê: bodies e mantas são justamente o que mais ganham.',
        ])),
        ('band', 'roupas'),
    ])



M_COMO = dict(
    num='00', window=None, title='Como usar este mapa', short='Como usar', pal='sand',
    spot='tamanhos', win='o segredo é o timing', in_index=False,
    intro='Enxoval não se compra de uma vez — se compra em janelas. Cedo demais é '
          'palpite sobre tamanho e estação; tarde demais é correria. Cada módulo traz '
          'a sua janela em semanas de gestação.',
    blocks=[
        ('timeline', [
            dict(when='até a 20ª', what='<b>Pesquisa.</b> Listas, preços, o que pedir emprestado '
                 'e o que aceitar de doação. Comprar quase nada.'),
            dict(when='20 a 24', what='<b>Definição.</b> Depois da morfológica, decidir o que entra. '
                 'Móveis grandes: encomendar agora, por causa do prazo de entrega.'),
            dict(when='24 a 32', hot=True, what='<b>Janela principal.</b> Roupas, quarto e banho, '
                 'com tempo de pesquisar preço.'),
            dict(when='28 a 34', hot=True, what='<b>Reta final.</b> Fraldas, farmacinha, '
                 'amamentação, e a mala pronta na porta.'),
            dict(when='até a 36', hot=True, what='<b>Bebê conforto instalado e testado no carro</b>, '
                 'e todas as roupinhas lavadas e guardadas.'),
            dict(when='pós-parto', what='<b>Só prazos.</b> Documentos e triagens — módulo 09. '
                 'Nada de compra.'),
        ]),
        ('tip', dict(title='três regras que valem para o mapa inteiro',
            body='<b>1.</b> Tamanho é peso, não idade — dois bebês da mesma idade podem ter '
                 '2 kg de diferença. <b>2.</b> A quantidade depende do seu ciclo de lavagem, '
                 'não da lista. <b>3.</b> Na dúvida, compre menos: falta se resolve em uma tarde, '
                 'sobra vira armário cheio de coisa que ela nunca usou.')),
        ('band', 'howto'),
    ])

from modules2 import M_SONO, M_BANHO, M_FRALDAS, M_FARMACIA, M_AMAMENTA
from modules3 import M_PASSEIO, M_MALA, M_PRAZOS, M_CHA

MODULES = [M_COMO, M_ROUPAS, M_SONO, M_BANHO, M_FRALDAS, M_FARMACIA,
           M_AMAMENTA, M_PASSEIO, M_MALA, M_PRAZOS, M_CHA]

ARC = '''<svg width="330" height="140" viewBox="0 0 360 150" fill="none">
    <defs><g id="lL"><path d="M0 0 Q-7 -7 -14 -4 Q-8 3 0 0 Z" fill="none" stroke="#7a9678" stroke-width="1.3" stroke-linejoin="round"/></g>
    <g id="lR"><path d="M0 0 Q7 -7 14 -4 Q8 3 0 0 Z" fill="none" stroke="#7a9678" stroke-width="1.3" stroke-linejoin="round"/></g></defs>
    <circle cx="180" cy="118" r="24" fill="none" stroke="#c0763b" stroke-width="1.5"/><circle cx="180" cy="118" r="16.5" fill="#f2e3d2"/>
    <g stroke="#c0763b" stroke-width="1.3" stroke-linecap="round"><line x1="180" y1="84" x2="180" y2="76"/><line x1="204" y1="94" x2="210" y2="88"/><line x1="156" y1="94" x2="150" y2="88"/><line x1="214" y1="118" x2="222" y2="118"/><line x1="146" y1="118" x2="138" y2="118"/></g>
    <path d="M150 128 Q60 118 30 60" fill="none" stroke="#5d7a5b" stroke-width="1.4" stroke-linecap="round"/>
    <path d="M210 128 Q300 118 330 60" fill="none" stroke="#5d7a5b" stroke-width="1.4" stroke-linecap="round"/>
    <use href="#lL" transform="translate(126 124) rotate(8)"/><use href="#lL" transform="translate(103 118) rotate(14)"/><use href="#lL" transform="translate(81 110) rotate(22)"/><use href="#lL" transform="translate(62 99) rotate(32)"/><use href="#lL" transform="translate(47 86) rotate(44)"/><use href="#lL" transform="translate(36 71) rotate(56)"/>
    <use href="#lR" transform="translate(234 124) rotate(-8)"/><use href="#lR" transform="translate(257 118) rotate(-14)"/><use href="#lR" transform="translate(279 110) rotate(-22)"/><use href="#lR" transform="translate(298 99) rotate(-32)"/><use href="#lR" transform="translate(313 86) rotate(-44)"/><use href="#lR" transform="translate(324 71) rotate(-56)"/>
    <g fill="#c0763b"><circle cx="96" cy="102" r="1.5"/><circle cx="72" cy="88" r="1.2"/><circle cx="53" cy="72" r="1.5"/><circle cx="264" cy="102" r="1.5"/><circle cx="288" cy="88" r="1.2"/><circle cx="307" cy="72" r="1.5"/></g>
    <g stroke="#b5aa9c" stroke-width="1" stroke-linecap="round"><path d="M120 40 v6 M117 43 h6"/><path d="M240 40 v6 M237 43 h6"/><path d="M180 22 v7 M176.5 25.5 h7"/></g>
    <g transform="translate(16 108) scale(0.8)" stroke="#5d7a5b" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" fill="#e9efe7"><path d="M0 -34 L8 -20 L4 -20 L12 -8 L7 -8 L15 4 L-15 4 L-7 -8 L-12 -8 L-4 -20 L-8 -20 Z"/><path d="M0 4 L0 12" stroke="#a05f2c"/></g>
    <g transform="translate(344 108) scale(0.8)" stroke="#5d7a5b" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" fill="#e9efe7"><path d="M0 -34 L8 -20 L4 -20 L12 -8 L7 -8 L15 4 L-15 4 L-7 -8 L-12 -8 L-4 -20 L-8 -20 Z"/><path d="M0 4 L0 12" stroke="#a05f2c"/></g>
    <g transform="translate(96 78)"><circle r="4.6" fill="#6b8fb5" opacity="0.85"/><circle r="2.2" fill="#e8eef5"/><circle cx="-4.5" cy="3.5" r="1.8" fill="#6b8fb5" opacity="0.6"/><path d="M0 5 Q-1 11 -4 14" stroke="#5d7a5b" stroke-width="1.2" fill="none" stroke-linecap="round"/></g>
  </svg>'''

CHEV = '''<div style="margin:1mm 0 6mm"><svg width="168" height="22" viewBox="0 0 168 22" fill="none"><path d="M0 15 L8 5 L16 15 L24 5 L32 15 L40 5 L48 15 L56 5 L64 15 L72 5 L80 15 L88 5 L96 15 L104 5 L112 15 L120 5 L128 15 L136 5 L144 15 L152 5 L160 15 L168 5" stroke="#453c33" stroke-width="4.5" stroke-linejoin="miter"/><path d="M0 15 L8 5 L16 15 L24 5 L32 15 L40 5 L48 15 L56 5 L64 15 L72 5 L80 15 L88 5 L96 15 L104 5 L112 15 L120 5 L128 15 L136 5 L144 15 L152 5 L160 15 L168 5" transform="translate(0 7)" stroke="#c0763b" stroke-width="2" opacity="0.55"/></svg></div>'''

COVER_META = dict(
    kicker='um guia de chegada · verão 2027',
    title_html='Mapa do<br>Enxoval',
    dedic='da nossa Laura Palmer',
    sign='com carinho — P.',
    art=ARC,
    chevron=CHEV,
    note_html='Feito com base em recomendações da Sociedade Brasileira de Pediatria, do '
              'Ministério da Saúde e do NHS — cruzadas com guias brasileiros de enxoval. '
              'Cada categoria traz a época certa de comprar, as quantidades que fazem '
              'sentido e o que é melhor <em>não</em> comprar.',
)

SOURCES = [
    'SBP — Nota de Alerta: sono seguro (recomendações AAP) · sbp.com.br',
    'Ministério da Saúde — Caderneta da Gestante · bvsms.saude.gov.br',
    'NHS — What to buy for your newborn baby · nhs.uk',
    'Lei 9.656/98 art. 12 — cobertura e inclusão do recém-nascido · planalto.gov.br',
    'Resolução CONTRAN 819/2021 — dispositivo de retenção infantil · gov.br/transportes',
    'ANOREG — registro civil de nascimento · anoreg.org.br',
    'ABNT NBR 16365 — segurança de vestuário infantil (cordões e laços)',
    'Instituto PENSI · Macetes de Mãe · Integralmente Mãe — o que NÃO comprar',
    'Sou Mãe · Vestindo Crianças · Timirim · Novo Bebê — quantidades por tamanho',
    'Huggies · Cabide Infantil — consumo real de fraldas por dia',
]
