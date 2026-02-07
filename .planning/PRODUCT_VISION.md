# THE VAULT — Product Vision & Workflow

## Core Purpose
Break the negative-balance snowball cycle. Palmer is always one month behind on bills because:
- Credit cards close on day 30, due on day 5 of next month
- Salary arrives either end of current month or beginning of next
- When salary hits, negative balance eats a chunk of it
- What's left isn't enough for the incoming month's bills
- Forced to use negative balance again → interest charges → cycle repeats

THE VAULT exists to give strict control over spending so this cycle ends permanently.

## Monthly Workflow (from spreadsheet)

1. **Import credit card transactions** — categorize them
2. **Reconcile recurring items** — verify fixed expense values for the month (they're mostly stable but can vary), map each to an actual transaction
3. **Update checking balance** — enter current bank balance
4. **Review dashboard** — with everything populated:
   - How much do I have right now?
   - How much is still coming in (salary)?
   - How much do I still need to pay this month?
   - What's my daily spending budget to cover everything?
   - How are future months looking? (project forward with recurring + installments + salary)

## Key Problem: Salary Timing

December 2025 example: received November salary at beginning of month AND January salary at end of month → R$ 100k+ in "entries" for December. Meanwhile January shows almost nothing because both salaries landed in December.

**This needs a programmatic solution** — salary entries need to be normalized/attributed to the month they're "for", not just when the bank shows them. Ideas:
- Allow marking income entries with "effective month" vs "bank month"
- Auto-detect salary patterns and suggest attribution
- Show both views: cash flow (when money moved) vs accrual (what month it belongs to)

## Spreadsheet Structure (source of truth)

### Monthly Tab Layout
**Header (rows 2-7):**
- Budget allocation: GASTOS FIXOS %, GASTOS VARIÁVEIS %, INVESTIMENTOS %
- Actual vs target percentages
- SALDO EM CONTA (checking balance)
- PARCELAS CC (credit card installment totals)
- VARIAVEL CC (variable credit card totals)
- CONTROLE GASTOS: A PAGAR, A ENTRAR, GASTO MAX ATUAL, PROXIMO FECHAMENTO, DIAS ATE FECHAMENTO, GASTO DIARIO RECOMENDADO
- INVESTIMENTOS MACRO: CRYPTO, RESERVA, RV
- ORÇAMENTO: Variable spending categories with LIMITE, GASTO ATUAL, GASTO MÊS ANTERIOR, GASTO MÉDIO 6 MESES

**Line items (rows 8+):**
- Columns: MES BASE, DATA, TIPO, DESCRIÇÃO, STATUS, % TOTAL, VALOR (expected), VALOR (actual), OBSERVAÇÕES
- Types: ENTRADA, INVESTIMENTOS, FIXO, VARIAVEL
- STATUS: "OK" = reconciled/mapped, empty = pending
- Two VALOR columns: expected amount vs actual matched amount

### Credit Card Tabs
- CONTROLE VISA BLACK: ANO/MES, DATA, DIA DA SEMANA, CATEGORIA, SUB-CATEGORIA, DESCRIÇÃO, VALOR, PARCELADO + CONTROLE DE CATEGORIAS sidebar
- CONTROLE CC RAFA: Same structure
- Página69 (Mastercard Black): Same data, no headers

### What the spreadsheet has that we're missing:
1. **Editable expected values** — recurring items should have editable ESPERADO per month
2. **Add/remove recurring items per month** — some months have extra items, some items pause
3. **Default recurring list in Settings** — template for future months
4. **ORÇAMENTO section** — variable spending categories with limits and historical comparison
5. **INVESTIMENTOS MACRO** — investment portfolio tracking (CRYPTO, RESERVA, RV)
6. **Budget allocation percentages** — 40/40/20 split tracking
7. **Future month projection** — critical for planning, using recurring + installments + expected salary
8. **PARCELAS CC / VARIAVEL CC** — separate installment and variable CC totals as summary rows

## Current App Status

### Working:
- RESUMO (5 metric cards)
- CONTROLE GASTOS (6 metric cards)
- RECORRENTES with 5 sub-tabs (TODOS, ENTRADAS, FIXOS, VARIÁVEIS, INVESTIMENTOS)
- TransactionPicker inline dropdown for mapping (map, unmap, re-map, search)
- CONTROLE CARTÕES with per-card filtering
- Data import (CSV/OFX upload)
- Month picker and navigation

### Missing (prioritized by workflow impact):

**P0 — Core workflow blockers:**
- Editable recurring item values (ESPERADO should be editable per month)
- Add/remove recurring items per month
- Checking balance input (SALDO EM CONTA)
- GASTOS FIXOS metric showing R$ 0 (needs to use mapped recurring totals, not transaction categories)

**P1 — Essential for financial control:**
- Future month projection (the main planning tool)
- Salary normalization (effective month vs bank month)
- ORÇAMENTO section (variable spending budgets with limits)
- Default recurring item template in Settings
- Category/subcategory management in Settings

**P2 — Nice to have:**
- INVESTIMENTOS MACRO tracking
- Budget allocation % tracking
- Analytics/charts page
- PARCELAS CC / VARIAVEL CC summary rows
- Historical budget comparison (GASTO MÊS ANTERIOR, MÉDIO 6 MESES)
