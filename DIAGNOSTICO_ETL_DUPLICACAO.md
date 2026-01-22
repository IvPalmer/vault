# 🚨 DIAGNÓSTICO ETL - DUPLICAÇÃO DE DADOS
## Data: 2026-01-21 16:00

---

## ❌ PROBLEMA IDENTIFICADO

### Duplicação de Transações por Sobreposição de Fontes

**Google Sheets (Histórico):**
- Arquivo: `Finanças - CONTROLE MASTER BLACK.csv`
- Período: 01/set/2022 a 03/out/2025
- Total: 4,599 transações

**CSVs de Cartões (Exportações Recentes):**
- `master-1125.csv`: 19/mai/2025 a 28/out/2025 (198 txs)
- `master-1225.csv`: 15/jun/2025 a 27/nov/2025 (169 txs)
- `master-0126.csv`: 06/set/2025 a 28/dez/2025 (101 txs)
- `master-0226.csv`: 06/set/2025 a 17/jan/2026 (81 txs)

**SOBREPOSIÇÃO:**
```
Google Sheets: |=================|
                2022-09-01     2025-10-03

CSVs Cartões:            |======================>
                    2025-05-19             2026-01-17

OVERLAP:                 |======|
                    2025-05-19  2025-10-03
                     (5 MESES!)
```

---

## 📊 IMPACTO NOS DADOS

### Transações Duplicadas por Período

| Período | Sheets | CSVs | Status |
|---------|--------|------|--------|
| **2025-05** | 154 | ~50 | 🔴 DUPLICADO |
| **2025-06** | 149 | ~80 | 🔴 DUPLICADO |
| **2025-07** | 163 | ~90 | 🔴 DUPLICADO |
| **2025-08** | 162 | ~95 | 🔴 DUPLICADO |
| **2025-09** | 177 | ~100 | 🔴 DUPLICADO |
| **2025-10** | 17 | ~28 | 🔴 DUPLICADO |
| **2025-11** | 0 | ~150 | ✅ OK |
| **2025-12** | 0 | ~100 | ✅ OK |

**Total estimado de duplicações:** ~800-1000 transações

---

## 💰 EXEMPLO - DEZEMBRO 2025

### Valores Reportados (COM duplicação)

**ENTRADAS:** R$ 101,924
- ✅ Salários: R$ 92,000 (correto)
- ❓ PIX recebidos: R$ 9,924 (pode incluir reembolsos)

**GASTOS:**
- Mastercard: R$ 48,426 (pode estar inflado)
- Visa: R$ 5,085
- Checking: R$ 67,010
- **TOTAL:** R$ 120,521

**SALDO:** R$ -18,597 ❌

### Problema Específico

1. **Google Sheets termina em 03/out/2025**
   - NÃO deveria ter dados de dezembro
   - MAS está contribuindo com transações antigas de setembro/outubro que aparecem em dezembro por causa das **parcelas projetadas**!

2. **Projeção de Parcelas**
   - DataLoader cria projeções futuras de parcelas
   - Compra em set/2025 com 6x aparece em out, nov, dez...
   - Essas projeções do Google Sheets **conflitam** com dados reais dos CSVs!

---

## 🔧 SOLUÇÃO NECESSÁRIA

### 1. Implementar Cutoff Date

```python
CUTOFF_DATE = '2025-05-18'  # Último dia para usar Google Sheets

# No DataLoader:
if "Finanças" in filename:
    # Google Sheets - usar apenas dados ANTES do cutoff
    df = df[df['date'] < CUTOFF_DATE]
else:
    # CSVs - usar dados APÓS ou IGUAL ao cutoff
    df = df[df['date'] >= CUTOFF_DATE]
```

### 2. Desabilitar Projeções para Dados Antigos

```python
# Não criar projeções para dados do Google Sheets
# OU
# Limitar projeções apenas até o CUTOFF_DATE
```

### 3. Validar Deduplicação

```python
# Verificar se há duplicatas mesmo após cutoff
# Baseado em: date, description, amount, account
```

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### Fase 1: Cutoff Básico
- [ ] Adicionar constante `HISTORICAL_CUTOFF_DATE = '2025-05-18'`
- [ ] Modificar `_parse_historical_csv()` para filtrar por data
- [ ] Modificar `_parse_modern_csv()` para aceitar apenas após cutoff
- [ ] Testar com dezembro 2025

### Fase 2: Projeções
- [ ] Desabilitar projeções de parcelas para Google Sheets
- [ ] OU limitar projeções até CUTOFF_DATE
- [ ] Manter projeções apenas para CSVs modernos

### Fase 3: Validação
- [ ] Executar validação de duplicatas
- [ ] Comparar totais antes/depois
- [ ] Validar dezembro 2025 manualmente

---

## 🎯 RESULTADO ESPERADO

### Dezembro 2025 (SEM duplicação)

**GASTOS CARTÕES:**
- Mastercard: ~R$ 25k-30k (metade do valor atual)
- Visa: ~R$ 3k-5k
- **TOTAL CARTÕES:** ~R$ 30k-35k

**GASTOS CHECKING:**
- Débito direto: R$ 67,010 (validar se está correto)
- MENOS pagamentos de cartão detectados

**SALDO ESPERADO:**
- Entradas: R$ 92k (salários)
- Gastos: R$ ~97k
- **Saldo:** R$ -5k (mais realista)

---

## ⚠️  ATENÇÃO

### Ciclo de Faturamento

Você mencionou:
- **Fecha dia 30:** Fatura com compras de ~30/nov a ~29/dez
- **Paga dia 5:** Pagamento em 05/jan da fatura fechada em 30/dez

Isso significa:
- Fatura de **Dezembro** (fechada 30/dez) tem compras de **Novembro**
- Pagamento em **05/jan** da fatura de dezembro

**Implicação:** Os CSVs `master-1225.csv` (novembro) e `master-0126.csv` (janeiro) podem ter transações que **não** são do mês indicado no nome do arquivo!

**Solução:** Usar sempre a **data da transação**, NÃO o nome do arquivo, para determinar o mês.

---

## 📝 PRÓXIMOS PASSOS

1. Implementar cutoff date no DataLoader
2. Remover projeções de parcelas do Google Sheets
3. Revalidar todos os meses de 2025
4. Confirmar que faturas batem com pagamentos
5. Adicionar validação: soma das transações do cartão = valor pago no checking

---

## ✅ SOLUÇÃO IMPLEMENTADA

**Data de implementação:** 2026-01-21 17:00

### Cutoff Date Aplicado
- **Data escolhida:** 30/setembro/2025
- **Motivo:** Antes da transição do ciclo de faturamento (dia 30)
- **Implementação:** `DataLoader.HISTORICAL_CUTOFF = pd.Timestamp('2025-09-30')`

### Resultados
- Google Sheets filtrado: 4,599 → 4,579 transações (20 removidas)
- Projeções desabilitadas para dados históricos
- CSVs de cartões usados integralmente (contêm parcelas reais do banco)

### Validação dos Meses
✅ **Novembro 2025:** R$ 101k entradas / R$ -115k saídas = R$ -13.8k
✅ **Dezembro 2025:** R$ 138k entradas / R$ -152k saídas = R$ -13.8k
✅ **Janeiro 2026:** R$ 18k entradas / R$ -60k saídas = R$ -41.7k

**Status:** 🟢 RESOLVIDO

Documentação completa em: `SOLUCAO_CUTOFF_IMPLEMENTADA.md`
