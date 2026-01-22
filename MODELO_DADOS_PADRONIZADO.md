# MODELO DE DADOS PADRONIZADO
## Data: 2026-01-21 15:30

---

## 🎯 OBJETIVO

Normalizar TODAS as transações de TODAS as fontes (OFX, CSV, TXT, Sheets histórico) para um formato único e consistente.

---

## 📋 ESTRUTURA FINAL DO DATAFRAME

### Colunas Obrigatórias

| # | Coluna | Tipo | Descrição | Exemplo |
|---|--------|------|-----------|---------|
| 1 | **date** | datetime | Data da transação | 2025-11-03 |
| 2 | **description** | string | Descrição renomeada/limpa | "Salário Novembro" |
| 3 | **description_original** | string | Descrição original importada | "SISPAG PIX RAPHAEL AZEV" |
| 4 | **category** | string | Categoria principal | "FS" |
| 5 | **subcategory** | string | Subcategoria (opcional) | "Salário Base" |
| 6 | **source** | string | Fonte da transação | "Checking", "Mastercard Black", "Visa Infinite" |
| 7 | **amount** | float | Valor (positivo=entrada, negativo=saída) | 51000.00 |
| 8 | **is_installment** | boolean | Parcelado? (só para cartões) | True/False |
| 9 | **is_recurring** | boolean | Recorrente? (débito ou crédito) | True/False |
| 10 | **installment_info** | string | Info parcela (se aplicável) | "3/12" |
| 11 | **is_internal_transfer** | boolean | Transferência interna? | True/False |
| 12 | **cat_type** | string | Tipo de categoria | "Income", "Fixo", "Variável", "Investimento" |

### Colunas Adicionais (Metadados)

| # | Coluna | Tipo | Descrição | Exemplo |
|---|--------|------|-----------|---------|
| 13 | **account** | string | Conta/cartão (legacy, = source) | "Checking" |
| 14 | **budget_limit** | float | Limite orçado (da categoria) | 1000.00 |
| 15 | **month_str** | string | Mês (YYYY-MM) | "2025-11" |

---

## 🔄 MAPEAMENTO DE FONTES

### 1. OFX (Extrato Banco)
```python
Origem: Extrato Conta Corrente-*.ofx
Mapeamento:
  date → <DTPOSTED>
  description_original → <NAME> ou <MEMO>
  amount → <TRNAMT>
  source → "Checking"
  is_installment → False
  is_internal_transfer → detectar por padrão
```

### 2. CSV Cartões (Modern)
```python
Origem: master-0126.csv, visa-0126.csv
Mapeamento:
  date → coluna "data"
  description_original → coluna "lançamento"
  amount → coluna "valor" (sempre negativo)
  source → detectar por nome do arquivo
  is_installment → detectar "1/12" no description
  is_internal_transfer → False (cartões não transferem)
```

### 3. Google Sheets (Historical)
```python
Origem: Finanças - CONTROLE MASTER BLACK.csv
Mapeamento:
  date → coluna "Date"
  description_original → coluna "Title"
  amount → coluna "Amount"
  source → detectar por nome da sheet
  is_installment → detectar regex
  is_internal_transfer → False
```

---

## 🧠 LÓGICA DE DETECÇÃO

### 1. is_internal_transfer
```python
Padrões que indicam transferência interna:
- "PAGAMENTO EFETUADO" → pagamento de cartão
- "TRANSF" e source="Checking" e amount < 0 → pagamento
- "TED" e source="Checking" → pode ser interno
- "PIX TRANSF" e keywords específicos → reembolsos

NOTA: Transferências internas são EXCLUÍDAS do cálculo de ENTRADAS/SAÍDAS
```

### 2. is_installment
```python
Padrões que indicam parcelamento:
- Regex: r'(\d{1,2})/(\d{1,2})' no description_original
- Extração: installment_info = "3/12"
- Apenas se source != "Checking" (débito não parcela)
```

### 3. is_recurring
```python
Baseado no budget.json:
- Se category existe em budget com day != None → True
- Se é salário mensal (FS) → True
- Senão → False
```

### 4. description (renomeada)
```python
Regras de limpeza:
1. Remover prefixos técnicos: "SISPAG PIX ", "COMPRA ", "ASA*"
2. Capitalizar primeira letra
3. Remover espaços extras
4. Substituir por apelido se configurado

Exemplos:
  "SISPAG PIX  RAPHAEL AZEV" → "Salário Raphael"
  "COMPRA CARTAO MASTER 123" → "Compra Master 123"
  "ASA*OINC PAGAMENTOS E" → "OINC Pagamentos"
```

### 5. source vs account
```python
# Padronizar nomes
Mapeamento:
  "master" → "Mastercard Black"
  "visa" → "Visa Infinite"
  "rafa" → "Mastercard - Rafa"
  "extrato" / "ofx" → "Checking"

# Unificar
source = account (mesma coluna, só mudar nome)
```

---

## 📊 EXEMPLO DE DADOS FINAIS

```csv
date,description,description_original,category,subcategory,source,amount,is_installment,is_recurring,installment_info,is_internal_transfer,cat_type
2025-11-03,Salário Novembro,SISPAG PIX  RAPHAEL AZEV,FS,,Checking,51000.00,False,True,,False,Income
2025-11-05,Pagamento Master Black,PAGAMENTO EFETUADO,Transferência Interna,,Checking,-33685.05,False,False,,True,Transferência
2025-11-15,Netflix,NETFLIX.COM 3/12,Entretenimento,Streaming,Mastercard Black,-45.90,True,True,3/12,False,Fixo
2025-11-20,Uber,UBER *TRIP,Transporte,Mobilidade,Mastercard Black,-28.50,False,False,,False,Variável
```

---

## 🔧 IMPLEMENTAÇÃO

### Etapa 1: Adicionar Colunas Novas
```python
# Em DataLoader._parse_file()
df['description_original'] = df['description'].copy()
df['is_installment'] = False
df['is_recurring'] = False
df['installment_info'] = None
df['is_internal_transfer'] = False
df['source'] = account  # Rename account → source
```

### Etapa 2: Detectar Parcelamento
```python
import re

def detect_installment(desc):
    match = re.search(r'(\d{1,2})/(\d{1,2})', str(desc))
    if match:
        return True, match.group(0)  # True, "3/12"
    return False, None

df[['is_installment', 'installment_info']] = df['description_original'].apply(
    lambda x: pd.Series(detect_installment(x))
)
```

### Etapa 3: Detectar Transferências Internas
```python
def is_internal(row):
    desc = str(row['description_original']).upper()
    source = row['source']
    amount = row['amount']

    # Pagamento de cartão
    if 'PAGAMENTO EFETUADO' in desc:
        return True

    # PIX/TED saindo do Checking (pode ser pagamento)
    if source == 'Checking' and amount < 0 and ('PIX TRANSF' in desc or 'TED' in desc):
        # Lista de exceções (não são transferências)
        non_internal = ['SALARIO', 'BONUS', 'DIVIDENDO']
        if not any(kw in desc for kw in non_internal):
            return True

    return False

df['is_internal_transfer'] = df.apply(is_internal, axis=1)
```

### Etapa 4: Detectar Recorrentes
```python
def is_recurring_item(row, budget):
    cat = row['category']
    if cat in budget and budget[cat].get('day') is not None:
        return True
    if cat in ['FS', 'Investimento']:  # Always recurring
        return True
    return False

df['is_recurring'] = df.apply(lambda r: is_recurring_item(r, engine.budget), axis=1)
```

### Etapa 5: Limpar Descrições
```python
def clean_description(original):
    desc = str(original)

    # Remove prefixos técnicos
    prefixes = ['SISPAG PIX', 'COMPRA CARTAO', 'ASA*', 'PAGAMENTO']
    for prefix in prefixes:
        desc = desc.replace(prefix, '').strip()

    # Remove espaços extras
    desc = ' '.join(desc.split())

    # Capitaliza
    desc = desc.title()

    return desc

df['description'] = df['description_original'].apply(clean_description)
```

---

## 📈 CÁLCULOS AJUSTADOS

### Entradas Reais (Excluindo Transferências)
```python
# ANTES (errado)
income = df[df['amount'] > 0]['amount'].sum()  # R$ 101,237

# DEPOIS (correto)
real_income = df[(df['amount'] > 0) & (~df['is_internal_transfer'])]['amount'].sum()  # R$ 63,410
```

### Gastos Reais (Excluindo Transferências)
```python
# ANTES (errado)
expenses = df[df['amount'] < 0]['amount'].sum()

# DEPOIS (correto)
real_expenses = df[(df['amount'] < 0) & (~df['is_internal_transfer'])]['amount'].sum()
```

---

## ✅ BENEFÍCIOS

1. **Clareza:** Cada campo tem propósito bem definido
2. **Consistência:** Todas as fontes normalizadas no mesmo formato
3. **Rastreabilidade:** `description_original` preserva dados brutos
4. **Inteligência:** Flags booleanos facilitam filtros e análises
5. **Escalabilidade:** Fácil adicionar novas fontes
6. **Precisão:** Transferências internas não inflam métricas

---

## 🎯 PRÓXIMOS PASSOS

1. ✅ Implementar detecção de `is_internal_transfer`
2. ✅ Implementar detecção de `is_installment`
3. ✅ Implementar limpeza de `description`
4. ✅ Ajustar cálculos de ENTRADAS/SAÍDAS
5. ✅ Atualizar dashboard para usar novos campos
6. ✅ Adicionar filtros visuais (toggle "Mostrar Transferências")
7. ✅ Documentar regras de categorização
