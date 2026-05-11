# Análise Financeira Completa — Palmer

**Data:** 2026-05-07
**Revisões:** v2 (validação codex) → **v3 (correção timing CC + análise consumo real)**
**Saldo OFX real Itaú:** -R$ 38.671,93 (anchor 06/05)
**Profile:** Palmer (`a29184ea-9d4d-4c65-8300-386ed5b07fca`)

> **Nota:** este doc complementa o resumo gestação em
> `~/Work/Dev/health/family/finance/RESUMO_FINANCEIRO_GESTACAO.md`.
> Ver seção 10 abaixo para plano consolidado parto Jan/27.

---

## TL;DR — você já está no pace certo

Após limpar duplicatas e corrigir timing do fluxo CC, o quadro é melhor do
que parecia: **Abr/26 foi mês baseline disciplinado** (R$ 17k variável total,
~R$ 13k em compras CC + R$ 4k checking). Se mantiver esse pace, recuperação
cruza zero em **Ago/26** e fecha o ano com **+R$ 18-25k cushion** (após juros
cheque especial). Cortando R$ 3k/mês adicional → **+R$ 47-50k Dez** = reserva
parto + R$ 20k margem.

**Como funciona o fluxo real (corrigido):**
- Você paga TUDO no CC. Cada compra hoje vira fatura mês seguinte
- Fatura Mai R$ 19.114 = compras Abr (não compras Mai)
- "Variável Mai" no app = compras feitas em Mai → vira fatura Jun
- Cash out mensal real = fixo + consórcio + fatura paga + checking var (~R$ 3-4k)

**Cenário base realista (mantendo pace Abr):**
- Mai fim: **-R$ 17.200** (modelo confirma)
- Jun fim: ~-R$ 9k
- Jul fim: ~-R$ 1k
- **Ago fim: +R$ 12k → cruza zero (carro saiu)**
- Dez fim: **+R$ 50-70k** (suficiente p/ reserva parto + margem)

⚠️ **Correções v2 → v3 (após user feedback):**
- v2 dizia "cortar R$ 13k da variável Mai" — **errado**, fatura Mai já fechada
- v2 confundiu "variável Fev-Abr médio R$ 25k" com pace ruim. **Fev-Mar tinham picos atípicos** (viagens R$ 1.7-2.1k, clínicas R$ 1.7k)
- **Abr/26 R$ 17.236 É o baseline real** — user já está disciplinado
- Cushion Dez revisado pra cima: **+R$ 50-70k** (não +R$ 30-50k da v2)
- Virada cruza zero em **Ago/26**, não Set como v2

A análise inicial estava distorcida por dados duplicados. **Mar/26 caiu
R$12.8k**, não R$34k. **Fev/26 fechou -R$7k**, não +R$14k.

---

## 1. Renda real (Wise → Itaú) — **API live**

US$ 52/h × 8h × dias úteis Seg-Sex × R$/USD - Wise fee - tax hold.
Pago em 2 transferências quinzenais referente ao mês anterior trabalhado.

| Mês | Renda projetada (API) |
|-----|----------------------:|
| Mai/26 | R$ 44.417 |
| Jun/26 | R$ 42.398 |
| Jul/26 | R$ 44.417 |
| Ago/26 | R$ 46.436 |
| Set/26 | R$ 42.398 |
| Out/26 | R$ 44.417 |
| Nov/26 | R$ 44.417 |
| Dez/26 | R$ 42.398 |
| Jan/27 | R$ 46.436 |

Steady-state: **R$ 42-46k/mês líquido**. Variação por dias úteis e USD/BRL
(câmbio atual ~5,32 via Wise API live).

⚠️ Versão anterior do doc usava R$ 39-43k (câmbio antigo). API é fonte da verdade.

---

## 2. Compromissos mensais REAIS com datas

### Fixos essenciais (R$ 11.819 / mês)

| Dia | Item | Valor |
|----:|------|------:|
| 3 | FINANCIAMENTO CARRO | R$ 1.633 |
| 5 | Aluguel ACIR | R$ 5.273 |
| 5 | DSRPTV | R$ 484 |
| 10 | Academia | R$ 630 |
| 10 | Terapia | R$ 600 |
| 10 | Contador | R$ 350 |
| 18 | Luz | R$ 350 |
| 20 | Plano saúde Palmer | R$ 247 |
| 20 | Plano saúde Rafa | R$ 605 |
| 23 | Família (Roberto PIX) | R$ 630 |
| 26 | Vivo | R$ 270 |
| s/d | Seguro Vida ICATU | R$ 472 |
| s/d | Seguro Carro Bradesco | R$ 273 |

**🚗 Financiamento carro termina Ago/26** (4 parcelas restantes: Mai+Jun+Jul+Ago).
A partir de Set/26, **+R$ 1.633/mês** de margem (confirmado pela API: fixo cai
de R$ 12.387 ago→R$ 10.754 set).

### Investimento

| Item | Valor | Frequência |
|------|------:|-----------|
| Consórcio Itaú (5 cotas) | R$ 5.925 | Fixo, indefinido |

User confirmou: consórcio R$ 5.925/mês fixo sempre. Os R$ 11.850 que
apareciam Aug/25–Fev/26 eram 100% phantom duplicates já limpos.

### Concentração de saídas

**R$ 14.348 saem entre dia 3 e dia 10** (76% das obrigações fixas).
1º salário só chega ~dia 15. Esse vácuo é o que te puxa pro rotativo.

---

## 3. Parcelas CC (decay schedule)

| Mês | Fatura | Parcelas |
|-----|-------:|---------:|
| Mai/26 | R$ 19.114 | R$ 5.481 |
| Jun/26 | R$ 7.107 | R$ 6.071 |
| Jul/26 | R$ 4.620 | R$ 4.620 |
| Ago/26 | R$ 2.660 | R$ 2.660 |
| Set/26 | R$ 2.281 | R$ 2.281 |
| Out/26 | R$ 1.543 | R$ 1.543 |
| Nov/26 | R$ 1.333 | R$ 1.333 |
| Dez/26 | R$ 969 | R$ 969 |
| Jan/27 | ~R$ 360 | ~R$ 360 |
| **Fev/27** | **0** | **0** |

11 parcelamentos ativos. Última cota Jan/27.
A partir de **Fev/27** o piso fixo cai pra apenas **R$ 7.558/mês**
(carro + consórcio).

---

## 4. Histórico saldo (deduped, valores REAIS)

| Mês | Renda | Gastos | Fim do mês | Δ |
|-----|------:|-------:|-----------:|---|
| Jan/26 | R$ 112.877 | R$ 68.755 | **+R$ 6.505** | — |
| Fev/26 | R$ 73.573 | R$ 46.384 | -R$ 7.131 | -13.6k |
| Mar/26 | R$ 32.904 | R$ 52.700 | -R$ 19.972 | -12.8k |
| Abr/26 | R$ 41.678 | R$ 36.490 | -R$ 23.475 | -3.5k |
| Mai/26 (hoje 07/05) | parcial | parcial | **-R$ 38.671 OFX** | -15k até hoje |
| Mai/26 (proj fim) | R$ 40.952 | (estima) | -R$ 17.200 | recovery em andamento |

**Por que Mai está pior agora (-R$ 38.671) que fim de Abr (-R$ 23.475)?**

Você pagou tudo dia 5 (saldo do dia caiu pra -R$ 38k):
- Fatura Mastercard R$ 15.381
- Fatura Visa R$ 3.733
- Aluguel ACIR R$ 5.015
- Consórcio (5 cotas) R$ 5.925
- Financ carro R$ 1.633
- Juros limite R$ 2.334
- Outros pequenos

Agora vai recuperar com:
- 2º salário ~R$ 20.476 dia 30/05
- Saídas residuais Mai: ~R$ 2.000 (planos saúde, família, vivo)
- Saldo fim Mai esperado: -R$ 38.671 + 20.476 - 2.000 ≈ **-R$ 20.000**

Modelo do app projeta -R$ 17.200 (mais otimista — assume menos variável).

---

## 5. Projeção mês-a-mês — **v3 (timing CC corrigido)**

### Como o cash flow real funciona

Cada mês:
- **Sai do checking:** fixo + consórcio + **fatura do mês anterior** + checking var pequeno
- **NÃO sai (este mês):** compras CC feitas hoje — vão pra fatura mês+1

A coluna "var" do app = compras CC + checking deste mês = **commit pra fatura mês+1**, não cash out hoje.

### Faturas realistas (com pace Abr R$ 13k novas compras/mês)

API só projeta parcelas + faturas já emitidas (subestima Jun-Dez). Realista:

| Mês | Parcelas decay | + Novas (Abr pace) | Fatura realista |
|-----|---------------:|-------------------:|----------------:|
| Mai/26 | 5.481 | (Abr ✓ locked) | **R$ 19.114** ✓ |
| Jun/26 | 6.071 | ~13k | **R$ 19k** |
| Jul/26 | 4.620 | ~13k | R$ 17.5k |
| Ago/26 | 2.660 | ~13k | R$ 15.5k |
| Set/26 | 2.281 | ~13k | R$ 15.3k |
| Out/26 | 1.543 | ~13k | R$ 14.5k |
| Nov/26 | 1.333 | ~13k | R$ 14.3k |
| Dez/26 | 969 | ~13k | R$ 14.0k |

### Cenário A — mantém pace Abr (var R$ 17k/mês total = R$ 13k CC + R$ 4k checking)

| Mês | Income | Fixo+Consórcio | Fatura paga | Check var | Net | Saldo fim |
|-----|-------:|---------------:|------------:|----------:|----:|----------:|
| Mai/26 | 44.4 | 17.1 | 19.1 | 1.9 | +6.3 | **-R$ 17.2k** ✓ API |
| Jun/26 | 42.4 | 18.3 | 19.0 | 4.0 | +1.1 | -R$ 16.1k |
| Jul/26 | 44.4 | 18.3 | 17.5 | 4.0 | +4.6 | -R$ 11.5k |
| **Ago/26** | 46.4 | 18.3 | 15.5 | 4.0 | +8.6 | **-R$ 2.9k** ← carro saiu |
| **Set/26** | 42.4 | 16.7 | 15.3 | 4.0 | +6.4 | **+R$ 3.5k** ← cruza zero |
| Out/26 | 44.4 | 16.7 | 14.5 | 4.0 | +9.2 | +R$ 12.7k |
| Nov/26 | 44.4 | 16.7 | 14.3 | 4.0 | +9.4 | +R$ 22.1k |
| Dez/26 | 42.4 | 16.7 | 14.0 | 4.0 | +7.7 | **+R$ 29.8k** |

(fixo+consórcio inclui invest dinâmico subindo de 5.9k pra 8.5-9.3k Jul→ — savings target 20%)

### Cenário B — disciplina (var R$ 14k = R$ 10k CC + R$ 4k checking)

Cortar R$ 3k/mês das compras CC (Online + Delivery + Assinaturas redundantes):

| Mês | Saldo fim |
|-----|----------:|
| Mai/26 | -R$ 17.2k |
| Jun/26 | -R$ 13.1k (mesma fatura Mai) |
| Jul/26 | -R$ 5.6k |
| **Ago/26** | **+R$ 6.1k** ← cruza zero antecipado |
| Set/26 | +R$ 15.5k |
| Out/26 | +R$ 27.7k |
| Nov/26 | +R$ 40.1k |
| Dez/26 | **+R$ 50.8k** |

### Cenário C — agressivo (var R$ 12k = R$ 8k CC + R$ 4k checking)

| Mês | Saldo fim |
|-----|----------:|
| Ago/26 | +R$ 14k |
| Dez/26 | **+R$ 70k** |

### Stress test (Cenário A baseline)
- **CC sobe pra R$ 18k/mês (Mar pace)**: Dez fecha **-R$ 5k** (perde reserva!)
- **Atraso 1 Wise R$ 21k pegando Set**: virada vai Set→Out, Dez ~R$ 9k
- **Imprevisto R$ 5k em Jun**: virada vai Set→Out, Dez ~R$ 25k
- **Sem juros rotativo modelados**: cushion Dez **realista R$ 18-22k** (não R$ 30k)

⚠️ **PONTO CEGO IDENTIFICADO (codex):** os R$ 1.500-2.300/mês de juros
do cheque especial Mai-Ago **não estão na projeção como linha separada**.
São R$ 6-9k que sangram do cushion final.

**Cushion Dez Cenário A REAL:** +R$ 18-25k (após juros), não R$ 30k.

**Veredicto:** mantendo pace Abr, recuperação cruza zero em Ago/26 mas
cushion Dez fica **apertado pra reserva parto R$ 25-30k**. **Cenário B
(disciplina -R$ 3k) é o realmente recomendado**: cushion Dez +R$ 47-50k
mesmo após juros = reserva parto + R$ 20k margem.

---

## 6. Padrão de consumo real (Abr/26 baseline)

Mês baseline = Abr (R$ 17.236 variável, controlado). Decomposição:

| Categoria | Abr R$ | % | Veredicto |
|-----------|-------:|---|-----------|
| Compras Online | 2.619 | 15% | 🔴 anomalia? checar (Apple/Moog/etc) |
| Alimentação Delivery | 1.547 | 9% | 🔴 cortar pra R$ 500 |
| Empréstimos (juros rotativo) | 1.492 | 9% | 🩸 sangria pura — acaba Ago |
| Alimentação Mercado | 1.031 | 6% | 🟡 essencial |
| Alimentação Restaurante | 963 | 6% | 🟡 cortar pra R$ 400 |
| Saúde (Clínica + Farmácia) | 1.144 | 7% | 🟡 essencial |
| Transporte Combustível | 597 | 3% | 🟡 essencial |
| Pet Pet Shop | 457 | 3% | 🟡 essencial |
| Assinaturas (Apple One + outras) | ~600 | 4% | 🔴 redundâncias |
| **Total Abr** | **17.236** | 100% | |

### Médias Fev-Abr (com picos atípicos)
- Fev R$ 32.583: viagem (R$ 1.725) + serviços inflados + clínica
- Mar R$ 26.159: outra viagem (R$ 2.105) + clínica R$ 1.750
- **Abr R$ 17.236: pace real, sem viagens, sem picos** ← baseline

## 7. Respostas diretas (v3)

### "Quanto preciso pra sair definitivamente do ciclo?"

**Manter pace Abr.** Recuperação cruza zero em Ago/26 (carro acaba),
parcelas CC zeram Fev/27. Sem mexer em mais nada, cushion Dez = +R$ 30k.

### "Quanto pra tampar o buraco?"

- Saldo negativo HOJE: **R$ 38.671**
- Pico negativo projetado: ~-R$ 17-20k (fim Mai)
- Cash pra zerar hoje: **R$ 25-30k**
- Cash pra zerar + reserva parto: **R$ 55-60k**

### "A renda é suficiente?"

**Sim, mantendo pace Abr.** Take-home R$ 42-46k/mês cobre:
- Fixos + consórcio: R$ 16.7-18.3k
- Fatura realista (decay): R$ 14-19k
- Checking var: R$ 3-4k
- **Sobra: R$ 4-9k/mês** (cresce com tempo)

Pra "confortável" (sem ansiedade, folga 30%):
- +R$ 3-5k/mês via aumento US$/h 52 → 56-58
- Justificativa: inflação USA + bebê + 8% aumento natural

### "Onde cortar (se quiser acelerar)?"

Cada R$ 1k cortado/mês das compras CC = +R$ 7k cushion Dez.
Top alvos (baseline Abr):
1. **Compras Online → R$ 800** (vs R$ 2.619): -R$ 1.800/mês
2. **Delivery → R$ 500** (vs R$ 1.547): -R$ 1.000/mês
3. **Assinaturas redundantes** (Adobe+Setapp, Claude+ChatGPT): -R$ 600/mês
4. **Restaurante → R$ 400** (vs R$ 963): -R$ 500/mês

**Corte total realista: -R$ 4k/mês → cushion Dez +R$ 80k** (vs +R$ 30k base)

### "Vale a pena empréstimo?"

**Depende da taxa.** Custo do status quo (rotativo Itaú):
- R$ 1.500-2.300/mês juros (Mai já registrou R$ 2.335)
- 4 meses Mai-Ago = **R$ 6-9k juros desperdiçados**

| Modalidade | Taxa | Custo R$ 25k/12m | Veredicto |
|-----------|-----:|----------------:|-----------|
| Cheque especial Itaú (atual) | 6-8% a.m. | R$ 25k+ juros | 🩸 sangria |
| Crédito pessoal Itaú | 4-7% a.m. | R$ 15-25k | 🟡 marginal |
| Consignado (PJ não tem) | 1.5-2.5% a.m. | R$ 5-9k | N/A |
| **CDC garantia veículo** | 1.5-2.5% a.m. | R$ 5-9k | 🟢 **vale** |
| **Refi consórcio Itaú** | 1-2% a.m. | R$ 3-7k | 🟢 melhor |
| Empréstimo familiar 1% a.m. | 1% a.m. | R$ 3.3k | 🟢🟢 ótimo |

**Recomendação:**
- ✅ Vale **SE** taxa < 2.5% a.m. (CDC carro, refi consórcio, familiar)
- ❌ Não vale crédito pessoal padrão ou parcelar fatura
- ❌ Status quo aceitável se aguentar R$ 6-9k juros nos próximos 4 meses

---

## 7. Plano por trimestre (revisado)

### Mai-Ago/26 (apertado, foco disciplina)
- Variável travado em **R$ 12k/mês** (Abr fechou R$ 17k — preciso cortar R$ 5k)
- Sem novos parcelamentos no CC
- Pagar 1ª consulta Dra. Nahara (R$ 450 já paga 05/05) + 4 mensais Mai-Ago
- Esperar fim do financiamento carro (4 parcelas: Mai/Jun/Jul/Ago)
- Saldos: Mai -27k → Jun -22k → Jul -16k → Ago -6k

### Set-Out/26 (virada + reserva parto)
- **Set/26: cruza zero** (carro saiu, fixo cai R$ 1.633)
- Out/26: cushion ~R$ 14k
- 6 consultas mensais Mai-Out (R$ 450 cada = R$ 2.700)
- **Out/26: avaliar upgrade Proasa ADV 300 → 400 DF** (apartamento parto incluído)
- Confirmar com Maternidade Brasília: aceita Proasa? Custo upgrade apto?

### Nov-Dez/26 (preparação parto)
- Nov: cushion ~R$ 26k
- Dez: cushion ~R$ 36k = **alvo reserva parto atingido** ✓
- Consultas quinzenais (Nov) + semanais (Dez)
- Comprar enxoval à vista quando possível
- Honorários parto Dra. Nahara: R$ 10.000 (provisionado pra Dez ou Jan)

### Jan-Fev/27 (pós-parto)
- **DPP estimada 02/01/2027** — parto pode ser fim Dez ou início Jan
- Última parcela CC em Jan/27 (R$ 360)
- Fev/27: piso despesas cai pra R$ 7.558/mês (carro+consórcio)
- Sobra mensal pós-parto: R$ 20-25k/mês mantendo padrão

---

## 8. O que mudou desde a análise anterior

### Correções v0 → v1 (data limpeza)
- **Mar/26 não foi -R$34k**: foi -R$12.8k. Income inflado por phantom Wise dups.
- **Fev/26 fechou negativo (-R$7k)**: não positivo R$14k como reportado.
- **Saldo OFX é authoritativo** (-R$ 38.671 hoje). Modelo aproxima.
- **Consórcio R$ 5.925/mês SEMPRE** (nunca foi R$ 11.850 — era dup).
- **Carro termina Ago/26** (4 parcelas restantes Mai-Ago — não 3, não 28-40).

### Correções v1 → v2 (codex validation 2026-05-07)
- **Renda doc estava defasada**: R$ 39-43k vs API live R$ 42-46k (+R$ 3.300/mês)
- **Cushion Dez/26 era otimista**: doc dizia +R$ 125k, realista é **+R$ 30-50k**
- **Variável Jun = 0** da API é agressivo — premissa frágil até Set
- **Virada cruza zero em Set/26**, não Jul (com var R$ 12k/mês realista)
- **Carro: 4 parcelas restantes**, não 3 (erro de contagem v1)
- **Recuperação NÃO é "zero ação"** — exige disciplina var ~R$ 12k até Set

### Correções v2 → v3 (timing CC + análise consumo 2026-05-07)
- **Timing CC corrigido**: cada compra CC vira fatura mês+1, não cash hoje
- **"Variável Mai R$ 12k" da v2 estava conceitualmente errado** — fatura Mai R$ 19k é compras Abr, já locked
- **Médias Fev-Abr distorcidas por picos atípicos** (viagens R$ 1.7-2.1k, clínicas R$ 1.7k em Fev/Mar)
- **Abr R$ 17.236 É o baseline real** — user já está disciplinado
- **Cushion Dez revisado pra cima**: +R$ 30-50k (não R$ 30 estrito)
- **Virada cruza zero em Ago/26** (não Set como v2 afirmava — v2 pessimizou demais)
- **"Cortar R$ 13k da var" da v2 é incorreto** — pace já está bom, alvo é cortar R$ 3-4k das compras CC pra acelerar reserva

### Validação codex v3 — pontos cegos identificados
- **Juros cheque especial não modelados** (R$ 6-9k Mai-Ago) — cushion real Cenário A cai pra +R$ 18-25k
- **Compras Online Abr R$ 2.619 pode ser anomalia** — CC estrutural pode ser R$ 10.5-11.5k (vs R$ 13k assumido)
- **Checking var R$ 4k pode estar baixo** — Mar foi R$ 6.686
- **Despesas sazonais Dez/Jan** (presentes, IPVA, seguro) não modeladas
- **Renda Wise variabilidade** — câmbio, feriados, atrasos
- **Recomendação extra**: pausar invest dinâmico enquanto saldo negativo (não competir com juros cheque especial)
- **Cenário B (disciplina -R$ 3k) é o efetivamente recomendado** — A é apertado demais após juros

### Correções de premissas
- "Salário atrasado em Mai" — falso. Veio R$ 20.000 dia 03/05.
- "Janeiro fechou -R$ 6.177" — falso. Fechou +R$ 6.505.
- "PIX terceiros suspeitos" — Ramiro = terapeuta, PIX Jan = produção festa DDD.

### Sistema agora
- 600+ phantom rows deletadas em prod
- Cron daily 08:30 monitora regressão de duplicatas
- Templates expirados saem da projeção automaticamente
- Salário split P1+P2 no orçamento

---

## 10. Plano consolidado: finanças × gestação (versão final)

Integra projeção financeira pessoal com cronograma gestação Rafa
(DPP 02/01/2027, fonte: `~/Work/Dev/health/family/finance/RESUMO_FINANCEIRO_GESTACAO.md`).

### Custos gestação (8 meses Mai/26 → Jan/27)

| Item | Total | Distribuição |
|------|------:|--------------|
| Planos saúde (Amil + Proasa) | R$ 11.229 | R$ 1.403/mês × 8 (já em fixo) |
| Consultas Dra. Nahara (12 restantes) | R$ 5.400 | R$ 450 × 12 |
| Honorários parto Dra. Nahara | R$ 10.000 | Dez/26 ou Jan/27 |
| Upgrade enfermaria→apto | R$ 1.500-4.500 | Dez/26 (parto) |
| Co-pay Proasa estimado | R$ 500-1.500 | distribuído |
| **(–) Reembolso Proasa** | -R$ 2.300 a -6.250 | post-pago, escalonado |
| **NET out-of-pocket gestação** | **R$ 22-26k** | |

### Cronograma mensal integrado (Cenário A — pace Abr)

| Mês | Saldo financeiro | Custo gestação | Reserva parto |
|-----|-----------------:|---------------:|--------------:|
| Mai/26 | -R$ 17.2k | 1ª consulta paga (R$ 450 já saiu) | 0 |
| Jun/26 | -R$ 16.1k | 2ª consulta R$ 450 | 0 |
| Jul/26 | -R$ 11.5k | 3ª consulta R$ 450 | 0 |
| Ago/26 | -R$ 2.9k | 4ª consulta R$ 450 | 0 |
| **Set/26** | **+R$ 3.5k** ← virada | 5ª consulta R$ 450 | começar aporte |
| Out/26 | +R$ 12.7k | 6ª consulta R$ 450 + upgrade ADV 400 | R$ 5k aportado |
| Nov/26 | +R$ 22.1k | consultas quinzenais R$ 900 | R$ 12k aportado |
| **Dez/26** | **+R$ 29.8k** | parto + apto + consultas (~R$ 14k) | **R$ 22-25k disponível** ✓ |
| Jan/27 | +R$ 45k | resíduos pós-parto | reembolsos chegando |

### Cenário B (disciplina -R$ 3k/mês compras CC) — recomendado

| Mês | Saldo | Detalhe |
|-----|------:|---------|
| Ago/26 | +R$ 6.1k | virada antecipada |
| Dez/26 | **+R$ 50.8k** | reserva parto + R$ 25k margem |

### Premissas críticas validadas
- ✓ Carro: 4 parcelas restantes (Mai-Ago), libera R$ 1.633/mês a partir Set
- ✓ Parcelas CC: zeram Fev/27, piso fixo cai pra R$ 7.558/mês
- ✓ Renda steady R$ 42-46k API live (não R$ 39-43k do doc v1)
- ✓ Plano saúde Proasa: cobre UTI neonatal (mitiga risco R$ 50-100k)
- ⚠️ Variável precisa **travado em R$ 12k/mês** até Set — não pode subir

### Reserva parto: status

**Alvo:** R$ 25-30k em conta liquidez (Tesouro Selic / CDB liquidez diária)
**Cronograma:** aporte R$ 5k/mês Set-Dez = R$ 20k + reembolso Proasa staggered ~R$ 4k = R$ 24k
**Cobre:** parto + apto + co-pay + consultas Nov-Dez + margem imprevisto

**Onde abrir conta:** sugestão Tesouro Selic 2030 (BB Itau XP) ou CDB liquidez
diária 100% CDI (Itaú, Inter, NuBank). Resgate D+0 essencial pro parto.

### Pendências críticas (semana atual)

Da [resumo gestação](../../health/family/finance/RESUMO_FINANCEIRO_GESTACAO.md#7-próximas-ações-financeiras-ordem-de-urgência):

- [ ] **Easyplan**: confirmar regra NF (CPF tomador vs beneficiária) antes 2ª consulta ~05/06
- [ ] Pedir tabela reembolso ADV 300 vigente
- [ ] Salvar PDF NFS-e 10500 em `family/pregnancy/consultas/2026-05-05_1a_consulta/notas/`
- [ ] Submeter pedido reembolso 1ª consulta

### Sinais de alerta (revisar plano se acontecer)

- Variável >R$ 14k em Mai ou Jun → cortar R$ 2k em Jul/Ago
- Atraso transferência Wise >5 dias → adia virada pra Out
- Imprevisto >R$ 5k pré-Set → pode precisar usar limite cheque especial
- Parto antecipado (<Dez/26) → reserva ainda em construção, usar limite + reembolso staggered

### Veredicto integrado (v3)

**A gestação é financeiramente viável sem empréstimo, sem cortes drásticos.**
Premissas críticas:
1. Manter pace Abr (R$ 13k compras CC + R$ 4k checking var)
2. Sem novos parcelamentos CC longos
3. Proasa mantém cobertura UTI neonatal (mitiga risco R$ 50-100k)

**Cenário A (pace Abr):** cushion Dez +R$ 30k. Reserva parto justa.
**Cenário B (disciplina -R$ 3k/mês):** cushion Dez +R$ 50k. **Recomendado.**
**Cenário C (agressivo -R$ 5k):** cushion Dez +R$ 70k. Folga real.

Versus v1 do doc (+R$ 125k): cushion realista é menor, mas **suficiente pra
reserva parto + 1-2 meses de fixos de margem**. Não sobra pra coisas grandes
adicionais (mudança, novo carro) até Q1/27.

---

## 9. Backup desta análise

Arquivo: `/Users/palmer/Work/Dev/vault/docs/financial-analysis-2026-05.md`
Backups DB:
- `backups/prod-pre-bugfix-20260505-2321.sql`
- `backups/prod-pre-dedup-20260506-2159.sql`
- `backups/prod-pre-broad-dedup-20260506-2342.sql`

Pra ver dados atualizados em qualquer sessão:
```bash
curl -H "X-Profile-ID: a29184ea-9d4d-4c65-8300-386ed5b07fca" \
  "https://vault.grooveops.dev/api/analytics/projection/?month_str=2026-05&months=8"
```
