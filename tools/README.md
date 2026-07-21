# Mapa do Enxoval — fonte única

`enxovalData.js` é **gerado**. Não editar à mão.

```
modules.py  modules2.py  modules3.py   conteúdo dos 11 módulos
iconmap.py                             rótulo do item → chave da ilustração
icons.json  spots.json  bands.py       ilustrações (SVG)
engine.py   build.py                   gera os PDFs da família
export_vault.py                        gera src/components/saude/enxovalData.js
```

Fluxo ao mudar conteúdo:

```bash
cd tools
python3 export_vault.py     # atualiza o app
python3 build.py            # regera os dois PDFs
```

Assim o que a família lê no PDF e o que o casal marca no app nunca divergem.

Proveniência do conteúdo: SBP, Ministério da Saúde, NHS, ANS, CONTRAN 819/2021,
Lei 9.656/98, Lei 11.108/2005, Lei 15.371/2026 e guias brasileiros de enxoval.
Onde as fontes divergiam, adotou-se o limite inferior — listas de loja inflam
quantidade.
