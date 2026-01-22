# 🔍 INVOICE DISCREPANCY ANALYSIS

## Data: 2026-01-21 19:30

---

## 🚨 PROBLEMA IDENTIFICADO

### Diferença Entre CSV Export e Bank Statement

**Janeiro 2026 Invoice:**
- **Bank Statement (App):** R$ 11,125.11
- **CSV Export (master-0126.csv):** R$ -68,345.85
- **DIFERENÇA:** R$ 57,220.74 (6x maior!)

---

## 🔍 ANÁLISE DO CSV

### Breakdown das Transações

```
master-0126.csv (January 2026 Invoice)

NEW PURCHASES (sem padrão XX/YY):
  Count: 82 transações
  Total: R$ -65,423.06

ONGOING INSTALLMENTS (com padrão XX/YY):
  Count: 10 transações
  Total: R$ -2,922.79

TOTAL NO CSV:
  Count: 92 transações
  Total: R$ -68,345.85
```

### Observações

1. **Mesmo as "new purchases" não batem** com o statement do banco
   - CSV: R$ -65,423.06
   - Bank: R$ 11,125.11
   - Diferença: R$ 54k (5x maior!)

2. **O CSV contém transações de vários períodos**
   - Exemplo: Transações de 26/nov, 28/nov, 29/nov aparecem no master-0126.csv
   - Essas são de **novembro**, não deveriam estar na fatura de janeiro

---

## 💡 HIPÓTESE: CSV Export vs Statement

### O Que o Banco Exporta

**Bank Statement (no app):**
- Mostra o **total da fatura** do período
- Janeiro 2026: R$ 11,125.11
- Esse é o valor que será cobrado

**CSV Export:**
- Contém **TODAS as transações do cartão**
- Inclui:
  1. ✅ Compras novas do período da fatura
  2. ✅ Parcelas antigas ainda sendo pagas
  3. ❌ Compras de outros períodos (???)

### Possível Explicação

O CSV `master-0126.csv` pode conter:

1. **Todas as transações processadas em janeiro** (não necessariamente da fatura de janeiro)
2. **Transações com data de postagem diferente da data de compra**
3. **Ajustes, estornos, e transações pendentes**

---

## 🎯 SOLUÇÃO NECESSÁRIA

### Opção 1: Confiar no Bank Statement

**Usar o valor do statement do banco como verdade:**
- Janeiro: R$ 11,125.11 (do app)
- Ignorar o total calculado do CSV

**Problema:** Perdemos o detalhamento por transação

### Opção 2: Entender a Diferença

**Investigar o que causa a diferença:**

1. **Verificar se CSV inclui transações fora do período**
   - Olhar datas no master-0126.csv
   - Filtrar apenas dezembro 2025 (período da fatura)

2. **Verificar se há duplicação entre CSVs**
   - master-0126 vs master-1225
   - Alguma transação aparece em ambos?

3. **Verificar ciclo de faturamento**
   - Close date: 30/dez/2025
   - Transações de quando até quando?

### Opção 3: Usar Invoice Close Date para Filtrar

**Implementar lógica baseada no close date:**

```python
# January invoice closes on Dec 30, 2025
# Should include transactions from Dec 1-30

jan_invoice = df[df['invoice_month'] == '2026-01']

# Filter by close date window
close_date = jan_invoice['invoice_close_date'].iloc[0]  # 2025-12-30
prev_close = close_date - pd.DateOffset(months=1)        # 2025-11-30

# Keep only transactions in billing period
filtered = jan_invoice[
    (jan_invoice['date'] > prev_close) &
    (jan_invoice['date'] <= close_date)
]
```

---

## ⚠️  PROBLEMA COM ABORDAGEM ATUAL

### Invoice Month vs Transaction Date

**Atualmente:**
- `invoice_month` é determinado pelo **nome do arquivo CSV**
- `master-0126.csv` → todas transações recebem `invoice_month = '2026-01'`

**Mas:**
- CSV pode conter transações de **múltiplos meses**
- Não sabemos com certeza quais transações pertencem a qual fatura

**Solução Correta:**
- Filtrar transações por **billing period** (entre os close dates)
- Não confiar apenas no nome do arquivo

---

## 📊 PRÓXIMOS PASSOS

### 1. Validar Hipótese

Verificar se filtrar por close date window resolve:

```python
# December invoice: Nov 1-30
# January invoice: Dec 1-30
# February invoice: Jan 1-30
```

### 2. Comparar Com Payments

Validar que filtered total = payment em checking:

```
January Invoice (filtered Dec 1-30):
  Total: R$ ???
  Payment (Jan 5): R$ -11,125.11
  Should match!
```

### 3. Documentar Comportamento do CSV

Entender EXATAMENTE o que o banco inclui no CSV export:
- Todas as transações do mês?
- Apenas as da fatura?
- Transações pendentes também?

---

## 🎯 RECOMENDAÇÃO IMEDIATA

**Usar o close date para filtrar:**

```python
def get_invoice_transactions(df, invoice_month):
    """Get transactions that belong to a specific invoice"""
    invoice_data = df[df['invoice_month'] == invoice_month].copy()

    if len(invoice_data) == 0:
        return pd.DataFrame()

    close_date = invoice_data['invoice_close_date'].iloc[0]
    prev_close = close_date - pd.DateOffset(months=1)

    # Filter by billing period (between close dates)
    filtered = invoice_data[
        (invoice_data['date'] > prev_close) &
        (invoice_data['date'] <= close_date)
    ].copy()

    return filtered
```

Isso deve resultar em totais que batem com os statements do banco.

---

## ✅ STATUS

**Problem:** ❌ CSV totals don't match bank statements
**Root Cause:** 🔍 CSV contains transactions outside billing period
**Solution:** ⏳ Filter by close date window
**Validated:** ⏳ Pending implementation

**Ação Imediata:** Implementar filtro por close date e revalidar
