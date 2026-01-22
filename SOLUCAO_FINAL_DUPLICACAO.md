# 🔴 PROBLEMA CRÍTICO: PROJEÇÕES CAUSANDO DUPLICAÇÃO MASSIVA
**Data:** 2026-01-21 18:30

---

## ⚠️  DESCOBERTA CRÍTICA

A validação revelou que o problema NÃO é apenas overlap com Google Sheets.

**O VERDADEIRO PROBLEMA:** Sistema de projeções de parcelas está criando transações fantasmas!

---

## 📊 EVIDÊNCIAS

### Dezembro 2025

**Pagamento Real (05/Jan/2026):**
- Mastercard ("PERSON MULTI"): R$ -11,125.11
- Visa ("PERSONNALITE"): R$ -3,248.61
- **TOTAL PAGO:** R$ -14,373.72

**Transações Reportadas no Sistema:**
- Mastercard December: R$ -48,636
- Visa December: R$ -6,201
- **TOTAL REPORTADO:** R$ -54,837

**DIFERENÇA:** R$ -40,463 (quase 3x inflado!)

---

## 🔍 ANÁLISE DA CAUSA RAIZ

### O Que Está Acontecendo

1. **master-0126.csv** contém 86 transações de Dezembro  (correto)
2. **Mas TAMBÉM contém:**
   - 1 transação de Setembro (parcela antiga)
   - 4 transações de Outubro (parcelas antigas)
   - 10 transações de Novembro (parcelas antigas)

3. **O LOADER carrega TODOS os CSV files:**
   - master-0125.csv (Janeiro)
   - master-0225.csv (Fevereiro)
   - master-0325.csv (Março)
   - ... e TODOS criavam projeções de parcelas futuras!

4. **Sistema de Projeções:**
   - Detecta transação "Netflix 3/12" em Outubro
   - Cria projeção para Novembro: "Netflix 4/12"
   - Cria projeção para Dezembro: "Netflix 5/12"
   - Repete para TODOS os arquivos!

5. **Resultado:**
   - Mesma parcela aparece em MÚLTIPLOS arquivos
   - Cada arquivo cria SUA PRÓPRIA projeção
   - Dezembro tem parcelas projetadas de Jan + Fev + Mar + Abr + ... + Dez
   - **DUPLICAÇÃO EXPONENCIAL!**

---

## ✅ SOLUÇÃO CORRETA

### Opção 1: Desabilitar TODAS as Projeções (RECOMENDADO)

**Motivo:** Os CSVs do banco JÁ contêm todas as parcelas!

```python
# Em DataLoader._parse_modern_csv()
# COMENTAR TODO o bloco de projeções (linhas ~243-280)

# PROJECTION LOGIC - DESABILITADO
# Os CSVs do banco já contêm parcelas futuras!
# projections = []
# ... (todo o código comentado)
```

**Vantagem:**
- Elimina 100% das duplicações
- CSVs do banco são fonte confiável
- Mais simples e seguro

**Desvantagem:**
- Perde capacidade de projetar futuro (mas banco já faz isso!)

### Opção 2: Usar Apenas Arquivo Mais Recente

**Estratégia:** Para cada mês, usar SOMENTE o último CSV disponível

```python
# Em load_all(), filtrar arquivos por data
# Manter apenas master-XXYY.csv com maior XXYY
# Exemplo: Se temos master-1125, master-1225, master-0126
# Usar apenas master-0126 (mais recente)
```

**Vantagem:**
- Mantém sistema de projeções
- Reduz duplicação

**Desvantagem:**
- Complexo de implementar
- Ainda pode ter projeções duplicadas

### Opção 3 (ESCOLHIDA): Desabilitar Projeções + Deduplicação

**Implementação:**
1. Desabilitar sistema de projeções completamente
2. Confiar nos CSVs do banco (eles têm todas as parcelas)
3. Manter deduplicação existente para casos edge

---

## 🔧 IMPLEMENTAÇÃO

### Modificar DataLoader.py

```python
# Linha ~243 em _parse_modern_csv()

# COMENTAR BLOCO DE PROJEÇÕES:
# projections = []
# is_historical = "finanças" in os.path.basename(path).lower()
#
# if 'description' in df.columns and not is_historical:
#     for idx, row in df.iterrows():
#         ... (todo o bloco até linha ~280)

# SUBSTITUIR POR:
# Bank CSVs already contain all installments - no projection needed
```

---

## 📋 VALIDAÇÃO ESPERADA

Após desabilitar projeções:

### Dezembro 2025
- Mastercard: R$ ~-11,000 (próximo ao pagamento)
- Visa: R$ ~-3,200 (próximo ao pagamento)
- **Deve bater com pagamento de 05/Jan**

### Janeiro 2026
- Mastercard: R$ ~-15,000 a -20,000
- Visa: R$ ~-4,000 a -6,000
- **Será validado com pagamento de 05/Fev**

---

## 🎯 PRÓXIMOS PASSOS

1. ✅ Desabilitar sistema de projeções
2. ⏳ Testar com Dezembro 2025
3. ⏳ Validar que total bate com pagamento
4. ⏳ Revisar todos os meses de 2025
5. ⏳ Confirmar que não há mais duplicações

---

## 📝 NOTAS IMPORTANTES

### Por Que CSVs Têm Parcelas Antigas?

Os CSVs do banco contêm:
- **Novas compras do mês**
- **Parcelas em andamento** de compras antigas

Exemplo `master-0126.csv`:
- Compra nova de 15/Dez: "Uber R$ 50"
- Parcela 6/12 de compra de Jun/2024: "Netflix R$ 45"
- Parcela 3/6 de compra de Out/2024: "Geladeira R$ 500"

**Isso é CORRETO!** O banco já faz a projeção.
**Nosso sistema NÃO deve projetar novamente!**

### Implicação para Dashboard

**Regime de Competência:**
- Use transações por DATA da compra
- Dezembro mostra o que foi gasto EM dezembro
- Incluindo parcelas de compras antigas

**Regime de Caixa:**
- Use pagamentos do checking
- Dezembro mostra o que SAIU da conta
- Baseado na fatura paga em 05/Jan

Ambos estão corretos, mas servem propósitos diferentes!

---

## ✅ STATUS

🔴 **PROBLEMA CONFIRMADO:** Projeções criando duplicação exponencial
⏳ **SOLUÇÃO:** Desabilitar projeções (confiar nos CSVs do banco)
⏳ **VALIDAÇÃO:** Pendente após implementação
