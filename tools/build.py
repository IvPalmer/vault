# -*- coding: utf-8 -*-
"""Gera os PDFs do Mapa do Enxoval.

Saídas:
  pdfs/00_Como_usar.pdf … 10_Cha_de_bebe.pdf   — um por módulo, formato celular
  Mapa_do_Enxoval_da_Laura_COMPLETO_A4.pdf     — tudo junto, para imprimir
  Mapa_do_Enxoval_da_Laura_COMPLETO_CELULAR.pdf
"""
import json, subprocess, os, re, unicodedata

from engine import Renderer, PAL, esc
from bands2 import BANDS
from iconmap import icon_for
from modules import MODULES, COVER_META, SOURCES

HERE = os.path.dirname(os.path.abspath(__file__))
SPOTS = json.load(open(os.path.join(HERE, 'spots.json')))
ICONS = json.load(open(os.path.join(HERE, 'icons.json')))
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
OUT = os.path.join(HERE, 'pdfs')


def mk(profile):
    return Renderer(profile, BANDS, ICONS, icon_for)


def ascii_slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'[^A-Za-z0-9]+', '_', s).strip('_')


def cover_html(r):
    m = COVER_META
    chips = ''.join(
        f'<span style="background:{PAL[mod["pal"]]["tint"]};color:{PAL[mod["pal"]]["deep"]}">'
        f'{mod["num"]} · {esc(mod.get("short", mod["title"]))}</span>'
        for mod in MODULES if mod.get('in_index', True))
    return f'''<div class="cover">
  {m['art']}
  <div class="kicker">{esc(m['kicker'])}</div>
  <h1>{m['title_html']}</h1>
  <div class="dedic">{esc(m['dedic'])}</div>
  {m['chevron']}
  <div class="cchips">{chips}</div>
  <div class="note">{m['note_html']}</div>
  <div class="hand">{esc(m['sign'])}</div>
</div>'''


def sources_html():
    lis = ''.join(f'<li>{esc(s)}</li>' for s in SOURCES)
    return (f'<div style="page-break-inside:avoid; break-inside:avoid">'
            f'<div class="sources"><div class="t">fontes — por que confiar nesta lista</div>'
            f'<ul>{lis}</ul></div>'
            f'<div class="colophon"><div class="hand">'
            f'feito em casa, com carinho, café e torta de cereja.</div></div>'
            f'<div style="height:12mm"></div></div>')


def credit_html():
    return ('<div class="colophon" style="margin-top:8mm">'
            '<div class="hand">Mapa do Enxoval da Laura · feito em casa, com carinho.</div>'
            '</div><div style="height:10mm"></div>')


def to_pdf(html, path, tag):
    hp = os.path.join(HERE, f'_tmp_{tag}.html')
    open(hp, 'w').write(html)
    subprocess.run([CHROME, '--headless', '--disable-gpu', '--no-pdf-header-footer',
                    f'--print-to-pdf={path}', f'file://{hp}'], capture_output=True)
    os.remove(hp)
    return os.path.getsize(path)


def build_modules():
    """Um PDF por módulo, no formato de leitura no celular."""
    os.makedirs(OUT, exist_ok=True)
    r = mk('mobile')
    for m in MODULES:
        art = SPOTS.get(m.get('spot', ''), '')
        body = r.module(m, art).replace('</section>', credit_html() + '</section>')
        doc = r.document('', body, title=f"{m['num']} {m['title']}")
        name = f"{m['num']}_{ascii_slug(m['short'])}.pdf"
        size = to_pdf(doc, os.path.join(OUT, name), m['num'])
        print(f"  {name:34s} {size/1024:6.0f} KB")


def build_full(profile, filename):
    r = mk(profile)
    mods = [r.module(m, SPOTS.get(m.get('spot', ''), '')) for m in MODULES]
    mods[-1] = mods[-1].replace('</section>', sources_html() + '</section>')
    doc = r.document(cover_html(r), ''.join(mods))
    size = to_pdf(doc, os.path.join(HERE, filename), profile)
    print(f"  {filename:34s} {size/1024:6.0f} KB")


if __name__ == '__main__':
    # Dois arquivos apenas: um para ler no celular, um para imprimir.
    # build_modules() continua disponível se um dia quisermos os avulsos.
    build_full('mobile', 'Mapa_do_Enxoval_da_Laura_CELULAR.pdf')
    build_full('print', 'Mapa_do_Enxoval_da_Laura_IMPRIMIR_A4.pdf')
