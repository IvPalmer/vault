# 🔍 VALIDAÇÃO: CARTÕES vs PAGAMENTOS
**Data:** 2026-01-21 18:00

---

## ⚠️ PROBLEMA CRÍTICO IDENTIFICADO

A validação revelou uma **incompatibilidade fundamental** entre:
1. Transações de cartão agrupadas por MÊS da compra
2. Pagamentos de fatura que representam compras do MÊS ANTERIOR

---

## 📊 DADOS REAIS - DEZEMBRO 2025

### Cenário Atual (INCORRETO)

**Transações de Cartão em Dezembro:**
- Mastercard: R$ -78,836.28 (127 transações)
- Visa: R$ -6,201.18 (41 transações)
- **Total:** R$ -85,037.46

**Pagamentos em Dezembro:**
- Mastercard (05/Dez): R$ -30,200.31
- Visa (10/Dez): R$ -6,151.52
- **Total:** R$ -36,351.83

**❌ MISMATCH:** R$ 48,636 de diferença!

---

## 🔍 ANÁLISE DO CICLO DE FATURAMENTO

### Regra do Ciclo
- **Fecha:** Dia 30 do mês
- **Pagamento:** Dia 5 do mês seguinte

### Mapeamento Correto

| Mês da Compra | Fecha Fatura | Paga em | Valor Pago |
|---------------|--------------|---------|------------|
| **Outubro** | 30/Out | 05/Nov | R$ -33,685 |
| **Novembro** | 30/Nov | 05/Dez | R$ -30,200 |
| **Dezembro** | 30/Dez | 05/Jan | R$ -11,125 |

### Validação Real

**DEZEMBRO 2025:**
- Compras feitas: R$ -78,836 (gastos do mês)
- Fatura paga: R$ -30,200 (compras de NOVEMBRO)
- Próxima fatura: R$ -11,125 (será paga em JANEIRO)

**O que sai da conta em Dezembro:**
- Pagamento de R$ -30,200 (fatura de Nov)
- NÃO os R$ -78,836 de compras (serão pagas em Jan)

---

## 🎯 METODOLOGIAS DE CÁLCULO

### Método 1: REGIME DE CAIXA (Atual - Checking)
**O que importa:** Quando o dinheiro sai da conta

```
Dezembro 2025:
├─ Entradas: R$ 92,000 (salários)
├─ Saídas Checking: R$ -67,010
│  ├─ Pagamento cartão Master: R$ -30,200 (fatura Nov)
│  ├─ Pagamento cartão Visa: R$ -6,152 (fatura Nov)
│  └─ Outros gastos: R$ -30,658
└─ Saldo Real: R$ +24,990
```

**Vantagem:** Reflete o fluxo de caixa real
**Desvantagem:** Não mostra gastos do mês atual

### Método 2: REGIME DE COMPETÊNCIA (Desejado)
**O que importa:** Quando a despesa foi incorrida

```
Dezembro 2025:
├─ Entradas: R$ 92,000
├─ Saídas por Competência:
│  ├─ Compras cartão Master: R$ -78,836 (gastos dez)
│  ├─ Compras cartão Visa: R$ -6,201 (gastos dez)
│  └─ Gastos Checking diretos: R$ -30,658
└─ Saldo Competência: R$ -23,695
```

**Vantagem:** Mostra gastos reais do período
**Desvantagem:** Não reflete o caixa disponível

---

## 💡 SOLUÇÃO PROPOSTA

### Dashboard Deve Ter Dois Modos

#### Modo 1: FLUXO DE CAIXA (Cash Flow)
- Usa pagamentos de cartão do checking
- Mostra dinheiro que realmente saiu
- **Dezembro:** R$ 92k - R$ 67k = R$ +25k

#### Modo 2: COMPETÊNCIA (Accrual)
- Usa transações de cartão por data da compra
- Mostra gastos incorridos no período
- **Dezembro:** R$ 92k - R$ 115k = R$ -23k

### Validação Necessária

**Para cada mês, verificar:**

```python
# Pagamento em Dezembro = Compras de Novembro
payment_dec = checking_payments('2025-12')  # R$ -30,200
purchases_nov = card_transactions('2025-11')  # Should match!

# Se não bater: ERRO de duplicação ou falta de dados
```

---

## 📋 VALIDAÇÃO MÊS A MÊS

### Novembro 2025

**Pagamento (05/Nov):**
- Mastercard: R$ -33,685.05

**Compras de Outubro:**
- Mastercard Oct: Precisa validar se bate!

### Dezembro 2025

**Pagamento (05/Dez):**
- Mastercard: R$ -30,200.31
- Visa: R$ -6,151.52

**Compras de Novembro:**
- Mastercard Nov: R$ -36,660.69
- Visa Nov: R$ -7,204.02

**❌ MISMATCH:**
- Master: R$ -6,460 diferença
- Visa: R$ -1,052 diferença

**Possíveis causas:**
1. Pagamento mínimo (não pagou total da fatura)
2. Estornos/devoluções
3. Juros/encargos adicionados
4. Duplicação de dados

### Janeiro 2026

**Pagamento (05/Jan):**
- Mastercard: R$ -11,125.11
- Visa: R$ -3,248.61

**Compras de Dezembro:**
- Mastercard Dec: R$ -78,836.28
- Visa Dec: R$ -6,201.18

**❌ ENORME MISMATCH!**
- Master: R$ -67,711 diferença!!!
- Visa: R$ -2,952 diferença

**ISSO ESTÁ MUITO ERRADO!**

---

## 🚨 CONCLUSÃO

### Problemas Confirmados

1. **Duplicação ainda existe**
   - Dezembro tem R$ 78k de gastos Mastercard
   - Janeiro só paga R$ 11k
   - Diferença de R$ 67k indica DUPLICAÇÃO MASSIVA

2. **CSVs contêm parcelas antigas**
   - Arquivos têm transações de meses anteriores
   - Parcelas 3/12, 4/12 de compras antigas
   - Somando tudo = duplicação

3. **Cutoff não resolveu completamente**
   - Cutoff em Set/2025 evitou overlap com Google Sheets
   - MAS CSVs de cartões AINDA têm overlap entre si!

---

## ✅ AÇÃO NECESSÁRIA

### Urgente: Validar Faturas Reais

Precisamos dos **PDFs das faturas** ou **extratos oficiais do banco** para:

1. **Confirmar valor real** da fatura de Dezembro
   - Será pago em 05/Jan/2026
   - Deve ser muito menor que R$ 78k

2. **Identificar qual CSV está correto**
   - master-1225.csv: Fatura de dezembro (paga em jan)
   - master-0126.csv: Fatura de janeiro (paga em fev)

3. **Mapear corretamente** CSV → Fatura → Pagamento

### Pergunta Critical

**Você pode confirmar:**
- Qual foi o valor REAL da fatura de Dezembro paga em Janeiro?
- O arquivo `master-0126.csv` contém a fatura de qual mês?
- Há overlap entre master-1225.csv e master-0126.csv?

---

## 📊 PRÓXIMOS PASSOS

1. ✅ Obter valores reais das faturas (PDFs ou confirmação manual)
2. ⏳ Mapear corretamente: CSV filename → Período de compras
3. ⏳ Implementar validação: Soma das compras = Valor da fatura
4. ⏳ Criar filtro para remover overlap entre CSVs
5. ⏳ Adicionar modo "Caixa" vs "Competência" no dashboard

**Status:** 🔴 VALIDAÇÃO FALHOU - Dados ainda com duplicação
