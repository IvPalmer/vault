# -*- coding: utf-8 -*-
"""Exporta modules.py → enxovalData.js do Vault.

Fonte única: o mesmo arquivo que gera o PDF gera os dados do app.
Rodar sempre que os módulos mudarem, para os dois nunca divergirem.
"""
import json, os, re, sys, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modules import MODULES, SOURCES
from iconmap import icon_for

HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = json.load(open(os.path.join(HERE, 'icons.json')))
SPOTS = json.load(open(os.path.join(HERE, 'spots.json')))
DEST = '/Users/palmer/Work/Dev/vault/src/components/saude/enxovalData.js'


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:44]


def conv_item(mod_num, it):
    """Item com id estável e chave de ilustração já resolvida."""
    out = {'id': f"{mod_num}-{slug(it['label'])}", 'label': it['label'],
           'icon': icon_for(it['label'])}
    if it.get('qty'):
        out['qty'] = it['qty']
    if it.get('ess'):
        out['ess'] = True
    if it.get('note'):
        out['note'] = it['note']
    return out


def conv_block(mod_num, kind, payload):
    if kind == 'items':
        return {'kind': 'items', 'items': [conv_item(mod_num, i) for i in payload]}
    if kind == 'groups':
        return {'kind': 'groups', 'groups': [
            {'name': n, 'items': [conv_item(mod_num, i) for i in its]} for n, its in payload]}
    if kind in ('table', 'tip', 'avoid'):
        return dict(kind=kind, **payload)
    if kind == 'timeline':
        return {'kind': 'timeline', 'rows': payload}
    if kind == 'intro':
        return {'kind': 'intro', 'text': payload}
    return None  # 'band' é decoração só do PDF


def main():
    mods = []
    used_icons = set()
    for m in MODULES:
        blocks = [b for b in (conv_block(m['num'], k, p) for k, p in m['blocks']) if b]
        for b in blocks:
            if b['kind'] == 'items':
                for it in b['items']:
                    used_icons.add(it['icon'])
            elif b['kind'] == 'groups':
                for g in b['groups']:
                    for it in g['items']:
                        used_icons.add(it['icon'])
        mods.append({
            'num': m['num'], 'id': slug(m['short']), 'title': m['title'],
            'short': m['short'], 'pal': m['pal'], 'win': m.get('win', ''),
            'intro': m.get('intro', ''), 'inIndex': m.get('in_index', True),
            'buyWindow': list(m['window']) if m.get('window') else None,
            'spot': m.get('spot', ''), 'blocks': blocks,
        })

    icons = {k: v for k, v in ICONS.items() if k in used_icons}
    spots = {m['spot']: SPOTS[m['spot']] for m in mods if m.get('spot') in SPOTS}

    total = 0
    for m in mods:
        for b in m['blocks']:
            if b['kind'] == 'items':
                total += len(b['items'])
            elif b['kind'] == 'groups':
                total += sum(len(g['items']) for g in b['groups'])

    js = f'''/**
 * Mapa do Enxoval da Laura — dados dos módulos.
 *
 * ARQUIVO GERADO. Não editar à mão.
 * Fonte: scratchpad/enxoval/modules.py + icons.json, via export_vault.py.
 * O mesmo arquivo gera o PDF entregue à família, então app e PDF não divergem.
 *
 * Conteúdo apoiado em SBP, Ministério da Saúde, NHS, ANS, CONTRAN e guias
 * brasileiros de enxoval; onde as fontes divergiam, adotamos o limite inferior.
 *
 * {len(mods)} módulos · {total} itens · {len(icons)} ilustrações
 */

export const MODULES = {json.dumps(mods, ensure_ascii=False, indent=2)}

export const ICONS = {json.dumps(icons, ensure_ascii=False, indent=2)}

export const SPOTS = {json.dumps(spots, ensure_ascii=False, indent=2)}

export const SOURCES = {json.dumps(SOURCES, ensure_ascii=False, indent=2)}

export const PAL = {{
  terra: {{ tint: '#f2e3d2', deep: '#a05f2c', mid: '#c0763b' }},
  sage:  {{ tint: '#e9efe7', deep: '#5d7a5b', mid: '#7a9678' }},
  rose:  {{ tint: '#f6e9e5', deep: '#a8544a', mid: '#c2857b' }},
  blue:  {{ tint: '#e8eef5', deep: '#4d6f96', mid: '#6b8fb5' }},
  sand:  {{ tint: '#f0ead9', deep: '#8a7430', mid: '#b09a4e' }},
}}
'''
    open(DEST, 'w').write(js)
    print(f'{DEST}\n  {len(mods)} módulos · {total} itens · {len(icons)} ilustrações · '
          f'{os.path.getsize(DEST)/1024:.0f} KB')


if __name__ == '__main__':
    main()
