# -*- coding: utf-8 -*-
"""
Motor de renderização do Mapa do Enxoval.

Uma fonte de dados (modules.py) → dois perfis de saída:
  - 'mobile' : página 110×195mm, coluna única, tipografia grande (leitura no celular)
  - 'print'  : A4, duas colunas, tipografia compacta (impressão / desktop)

Blocos suportados por módulo:
  intro    — parágrafo de abertura em itálico
  items    — checklist em cards {label, qty, ess, note}
  groups   — [(nome, [items])] subgrupos nomeados
  table    — {head: [...], rows: [[...]], note}
  timeline — [{when, what, hot}] prazos/etapas
  tip      — {title, body} caixa de destaque
  avoid    — {title, items} caixa "melhor evitar"
  band     — ilustração de rodapé (chave em bands)
"""
import html

INK = '#453c33'; SOFT = '#8f8478'; FAINT = '#b5aa9c'; CREAM = '#fbf7f1'

PAL = {
    'terra': dict(tint='#f2e3d2', deep='#a05f2c', mid='#c0763b'),
    'sage':  dict(tint='#e9efe7', deep='#5d7a5b', mid='#7a9678'),
    'rose':  dict(tint='#f6e9e5', deep='#a8544a', mid='#c2857b'),
    'blue':  dict(tint='#e8eef5', deep='#4d6f96', mid='#6b8fb5'),
    'sand':  dict(tint='#f0ead9', deep='#8a7430', mid='#b09a4e'),
}

# ── perfis ────────────────────────────────────────────────────
PROFILES = {
    'mobile': dict(
        page='110mm 195mm', pad='9mm 8mm 8mm',
        base=13, cols=1, h1=34, h2=19, banner_art='30mm', band_h='11mm', art_w='13mm',
        cover_h='177mm', chip_cols=2,
    ),
    'print': dict(
        page='A4', pad='15mm 15mm 12mm',
        base=11, cols=2, h1=50, h2=21.5, banner_art='40mm', band_h='16mm', art_w='12mm',
        cover_h='297mm', chip_cols=0,
    ),
}


def esc(s):
    return html.escape(str(s), quote=False) if s is not None else ''


class Renderer:
    def __init__(self, profile, bands, icons=None, icon_for=None):
        self.p = PROFILES[profile]
        self.profile = profile
        self.bands = bands
        self.icons = icons or {}
        self.icon_for = icon_for

    # ── blocos ────────────────────────────────────────────────
    def intro(self, text):
        return f'<p class="intro">{esc(text)}</p>'

    def card(self, it, pal):
        q = (f'<span class="qty" style="background:{pal["tint"]};color:{pal["deep"]}">'
             f'{esc(it["qty"])}</span>') if it.get('qty') else ''
        e = (f'<span class="ess" style="color:{pal["deep"]}">essencial</span>'
             ) if it.get('ess') else ''
        n = f'<div class="cnote">{esc(it["note"])}</div>' if it.get('note') else ''
        art = ''
        if self.icon_for:
            key = self.icon_for(it['label'])
            svg = self.icons.get(key)
            if svg:
                art = f'<span class="cart">{svg}</span>'
        return (f'<div class="card">{art}'
                f'<div class="cbody"><div class="clabel">{esc(it["label"])}{q}{e}</div>{n}</div>'
                f'<span class="cb" style="border-color:{pal["mid"]}"></span></div>')

    def items(self, its, pal):
        return '<div class="grid">' + ''.join(self.card(i, pal) for i in its) + '</div>'

    def groups(self, gs, pal):
        out = []
        for name, its in gs:
            out.append(f'<div class="gchip" style="background:{pal["tint"]};'
                       f'color:{pal["deep"]}">{esc(name)}</div>')
            out.append(self.items(its, pal))
        return ''.join(out)

    def table(self, t, pal):
        head = ''.join(f'<th>{esc(h)}</th>' for h in t['head'])
        rows = ''
        for r in t['rows']:
            cells = ''.join(f'<td>{esc(c)}</td>' for c in r)
            rows += f'<tr>{cells}</tr>'
        note = f'<div class="tnote">{esc(t["note"])}</div>' if t.get('note') else ''
        title = (f'<div class="ttitle" style="color:{pal["deep"]}">{esc(t["title"])}</div>'
                 ) if t.get('title') else ''
        return (f'<div class="tablewrap">{title}<table style="--tint:{pal["tint"]}">'
                f'<thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>{note}</div>')

    def timeline(self, rows, pal):
        out = []
        for r in rows:
            hp = PAL['terra'] if r.get('hot') else PAL['blue']
            out.append(f'<div class="dl"><span class="dwhen" style="background:{hp["tint"]};'
                       f'color:{hp["deep"]}">{esc(r["when"])}</span>'
                       f'<div class="dwhat">{r["what"]}</div></div>')
        return f'<div class="dlist">{"".join(out)}</div>'

    def tip(self, t, pal):
        return (f'<div class="tip" style="background:{pal["tint"]};border-color:{pal["mid"]}">'
                f'<div class="tiptitle" style="color:{pal["deep"]}">{esc(t["title"])}</div>'
                f'<div class="tipbody">{t["body"]}</div></div>')

    def avoid(self, a, pal):
        lis = ''.join(f'<li>{esc(x)}</li>' for x in a['items'])
        title = a.get('title', 'melhor evitar')
        return (f'<div class="avoid"><div class="t">✕ &nbsp;{esc(title)}</div>'
                f'<ul>{lis}</ul></div>')

    def band(self, key):
        # Só no perfil de impressão. No celular a faixa é alta demais para caber
        # na sobra da página e o Chrome ignora break-before:avoid — resultado:
        # uma página inteira só com a decoração. A ilustração do módulo já vive
        # no banner, então o celular não fica sem imagem.
        if self.profile == 'mobile':
            return ''
        svg = self.bands.get(key)
        return f'<div class="band">{svg}</div>' if svg else ''

    # ── banner do módulo ──────────────────────────────────────
    def banner(self, m, pal, art):
        intro = f'<p class="bintro">{esc(m["intro"])}</p>' if m.get('intro') else ''
        win = (f'<span class="bwin" style="color:{pal["deep"]}">{esc(m["win"])}</span>'
               ) if m.get('win') else ''
        return (f'<div class="banner" style="background:{pal["tint"]}">'
                f'<div class="btext"><div class="btop">'
                f'<span class="bnum" style="color:{pal["deep"]}">{esc(m["num"])}</span>{win}</div>'
                f'<h2>{esc(m["title"])}</h2>{intro}</div>'
                f'<div class="bart">{art}</div></div>')

    # ── módulo completo ───────────────────────────────────────
    def module(self, m, art):
        pal = PAL[m['pal']]
        out = [self.banner(m, pal, art)]
        for kind, payload in m['blocks']:
            if kind == 'intro':
                out.append(self.intro(payload))
            elif kind == 'items':
                out.append(self.items(payload, pal))
            elif kind == 'groups':
                out.append(self.groups(payload, pal))
            elif kind == 'table':
                out.append(self.table(payload, pal))
            elif kind == 'timeline':
                out.append(self.timeline(payload, pal))
            elif kind == 'tip':
                out.append(self.tip(payload, pal))
            elif kind == 'avoid':
                out.append(self.avoid(payload, pal))
            elif kind == 'band':
                out.append(self.band(payload))
            elif kind == 'html':
                out.append(payload)
        cls = 'mod' if self.profile == 'mobile' else 'mod brk'
        return f'<section class="{cls}">{"".join(out)}</section>'

    # ── CSS ───────────────────────────────────────────────────
    def css(self):
        p = self.p
        b = p['base']
        grid = ('grid-template-columns: 1fr;' if p['cols'] == 1
                else 'grid-template-columns: 1fr 1fr;')
        return f'''
  @font-face {{ font-family:'Young Serif'; src:url('fonts/YoungSerif-Regular.ttf'); }}
  @font-face {{ font-family:'Outfit'; src:url('fonts/Outfit-Regular.ttf'); font-weight:400; }}
  @font-face {{ font-family:'Outfit'; src:url('fonts/Outfit-Bold.ttf'); font-weight:700; }}
  @font-face {{ font-family:'Instrument Serif'; src:url('fonts/InstrumentSerif-Italic.ttf'); font-style:italic; }}
  @font-face {{ font-family:'Nothing You Could Do'; src:url('fonts/NothingYouCouldDo-Regular.ttf'); }}

  @page {{ size: {p['page']}; margin: 0; }}
  * {{ margin:0; padding:0; box-sizing:border-box; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
  html, body {{ background:{CREAM}; }}

  body {{ font-family:'Outfit',sans-serif; color:{INK}; font-size:{b}px;
         orphans:3; widows:3; }}
  .brk {{ page-break-before:always; }}
  .pg, .mod {{ padding:{p['pad']};
                -webkit-box-decoration-break:clone; box-decoration-break:clone; }}
  .hand {{ font-family:'Nothing You Could Do',cursive; color:#a05f2c; }}

  /* capa */
  .cover {{ height:{p['cover_h']}; padding:{p['pad']}; display:flex; flex-direction:column;
            justify-content:center; align-items:center; text-align:center; page-break-after:always; }}
  .kicker {{ font-size:{b*0.72:.1f}px; font-weight:700; letter-spacing:2.4px;
             text-transform:uppercase; color:#c0763b; margin-bottom:5mm; }}
  .cover h1 {{ font-family:'Young Serif',serif; font-size:{p['h1']}px; line-height:1.05; margin-bottom:4mm; }}
  .dedic {{ font-family:'Instrument Serif',serif; font-style:italic; font-size:{b*1.45:.1f}px;
            color:#a05f2c; margin-bottom:6mm; }}
  .cchips {{ display:flex; flex-wrap:wrap; gap:2mm; justify-content:center;
             margin-bottom:7mm; max-width:{'92mm' if p['cols']==1 else '150mm'}; }}
  .cchips span {{ font-size:{b*0.78:.1f}px; font-weight:700; border-radius:999px; padding:1.8mm 3.6mm; }}
  .cover .note {{ font-size:{b*0.85:.1f}px; color:{SOFT}; line-height:1.7;
                  max-width:{'92mm' if p['cols']==1 else '128mm'}; }}
  .cover .hand {{ font-size:{b*1.2:.1f}px; margin-top:6mm; }}

  /* banner do módulo */
  .banner {{ display:flex; align-items:center; gap:5mm; border-radius:4.5mm;
             padding:5mm 6mm; margin-bottom:4mm; page-break-inside:avoid; break-inside:avoid;
             page-break-after:avoid; break-after:avoid; }}
  .btext {{ flex:1; }}
  .btop {{ display:flex; align-items:baseline; justify-content:space-between; gap:3mm; margin-bottom:0.5mm; }}
  .bnum {{ font-family:'Young Serif',serif; font-size:{b*1.6:.1f}px; opacity:.85; }}
  .bwin {{ font-size:{b*0.7:.1f}px; font-weight:700; letter-spacing:1.4px; text-transform:uppercase;
           background:rgba(255,255,255,.75); border-radius:999px; padding:1.4mm 3mm; text-align:right; }}
  .banner h2 {{ font-family:'Young Serif',serif; font-size:{p['h2']}px; font-weight:400; }}
  .bintro {{ font-family:'Instrument Serif',serif; font-style:italic; font-size:{b*1.02:.1f}px;
             color:#7d6f60; line-height:1.5; margin-top:1mm; }}
  .bart {{ width:{p['banner_art']}; flex-shrink:0; }}
  .bart svg {{ width:100%; height:auto; display:block; }}

  /* texto */
  .intro {{ font-family:'Instrument Serif',serif; font-style:italic; font-size:{b*1.02:.1f}px;
            color:{SOFT}; line-height:1.6; margin:0 0 3.5mm; }}

  /* checklist */
  .grid {{ display:grid; {grid} gap:2.4mm; margin-bottom:3.5mm; }}
  .card {{ background:#fff; border:1px solid #ece2d2; border-radius:3.2mm; padding:3mm 3.6mm;
           display:flex; gap:3.4mm; align-items:center; page-break-inside:avoid; break-inside:avoid; }}
  .cart {{ flex:0 0 {p['art_w']}; width:{p['art_w']}; }}
  .cart svg {{ width:100%; height:auto; display:block; }}
  .cb {{ width:4.2mm; height:4.2mm; border:1.5px solid; border-radius:50%;
         flex:0 0 4.2mm; align-self:flex-start; margin-top:0.6mm; }}
  .cbody {{ min-width:0; flex:1; }}
  .clabel {{ font-size:{b*0.98:.1f}px; line-height:1.4; font-weight:700; }}
  .qty {{ display:inline-block; font-size:{b*0.74:.1f}px; font-weight:700; border-radius:999px;
          padding:0.6mm 2.2mm; margin-left:4px; white-space:nowrap; }}
  .ess {{ display:inline-block; font-size:{b*0.62:.1f}px; font-weight:700; text-transform:uppercase;
          letter-spacing:1.2px; margin-left:4px; }}
  .cnote {{ font-size:{b*0.8:.1f}px; font-weight:400; color:{SOFT}; line-height:1.45; margin-top:0.8mm; }}

  .gchip {{ page-break-after:avoid; display:inline-block; font-size:{b*0.72:.1f}px; font-weight:700; letter-spacing:1.8px;
            text-transform:uppercase; border-radius:999px; padding:1.6mm 4mm; margin:2mm 0 2.4mm; }}

  /* tabela */
  .tablewrap {{ margin-bottom:4mm; page-break-inside:avoid; break-inside:avoid; }}
  thead {{ display:table-header-group; }}
  tr {{ page-break-inside:avoid; }}
  .ttitle {{ font-size:{b*0.74:.1f}px; font-weight:700; letter-spacing:1.6px;
             text-transform:uppercase; margin-bottom:1.6mm; page-break-after:avoid; }}
  table {{ width:100%; border-collapse:separate; border-spacing:0; background:#fff;
           border:1px solid #ece2d2; border-radius:3.2mm; overflow:hidden; }}
  th {{ background:var(--tint); font-size:{b*0.74:.1f}px; font-weight:700; text-transform:uppercase;
        letter-spacing:0.8px; text-align:left; padding:2.2mm 3mm; }}
  td {{ font-size:{b*0.86:.1f}px; padding:2mm 3mm; border-top:1px solid #f0e8da; line-height:1.35; }}
  tbody tr:nth-child(even) td {{ background:#fdfaf5; }}
  .tnote {{ font-size:{b*0.76:.1f}px; color:{SOFT}; line-height:1.5; margin-top:1.6mm; }}

  /* timeline */
  .dlist {{ display:flex; flex-direction:column; gap:2.2mm; margin-bottom:4mm; }}
  .dl {{ display:flex; gap:3.5mm; align-items:flex-start; background:#fff; border:1px solid #ece2d2;
         border-radius:3.2mm; padding:3mm 4mm; page-break-inside:avoid; }}
  .dwhen {{ min-width:{'24mm' if p['cols']==1 else '28mm'}; text-align:center; font-size:{b*0.68:.1f}px;
            font-weight:700; text-transform:uppercase; letter-spacing:0.8px; border-radius:999px;
            padding:1.6mm 1.5mm; line-height:1.3; }}
  .dwhat {{ flex:1; font-size:{b*0.92:.1f}px; line-height:1.5; padding-top:0.4mm; }}

  /* tip */
  .tip {{ border:1px solid; border-radius:3.2mm; padding:3.4mm 4.5mm; margin-bottom:4mm;
          page-break-inside:avoid; break-inside:avoid; }}
  .tiptitle {{ page-break-after:avoid; font-size:{b*0.72:.1f}px; font-weight:700; text-transform:uppercase;
               letter-spacing:1.8px; margin-bottom:1.4mm; }}
  .tipbody {{ font-size:{b*0.88:.1f}px; line-height:1.55; color:#6b6055; }}

  /* avoid */
  .avoid {{ background:#f6e9e5; border-radius:3.2mm; padding:3.4mm 4.5mm; margin-bottom:3mm;
            page-break-inside:avoid; break-inside:avoid; }}
  .avoid .t {{ page-break-after:avoid; font-size:{b*0.72:.1f}px; font-weight:700; text-transform:uppercase;
               letter-spacing:1.8px; color:#a8544a; margin-bottom:1.4mm; }}
  .avoid ul {{ list-style:none; {'column-count:2; column-gap:7mm;' if p['cols']==2 else ''} }}
  .avoid li {{ font-size:{b*0.82:.1f}px; color:#6e564e; line-height:1.5; padding-left:3.5mm;
               position:relative; page-break-inside:avoid; margin-bottom:0.8mm; }}
  .avoid li::before {{ content:"×"; position:absolute; left:0; color:#a8544a; font-weight:700; }}

  /* banda ilustrada */
  .band {{ margin:4mm 0 0; page-break-before:avoid; break-before:avoid;
           page-break-inside:avoid; break-inside:avoid; }}
  .band svg {{ width:100%; height:{p['band_h']}; display:block; }}

  /* fontes */
  .sources {{ border-top:1.4px solid {INK}; padding-top:3.5mm; margin-top:6mm; }}
  .sources .t {{ font-size:{b*0.72:.1f}px; font-weight:700; text-transform:uppercase;
                 letter-spacing:2px; color:{SOFT}; margin-bottom:2mm; }}
  .sources ul {{ list-style:none; {'columns:2; column-gap:8mm;' if p['cols']==2 else ''} }}
  .sources li {{ font-size:{b*0.7:.1f}px; color:{SOFT}; line-height:1.7; break-inside:avoid; }}
  .colophon {{ margin-top:6mm; text-align:center; }}
  .colophon .hand {{ font-size:{b*1.1:.1f}px; }}
'''

    def document(self, cover, modules_html, title='Mapa do Enxoval'):
        return (f'<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">'
                f'<title>{esc(title)}</title><style>{self.css()}</style></head><body>'
                f'{cover}{modules_html}</body></html>')
