# Coding Conventions

**Analysis Date:** 2026-01-22

## Naming Patterns

**Files:**
- Snake_case for module files: `DataLoader.py`, `CategoryEngine.py`, `ValidationEngine.py`
- PascalCase for main classes within files
- Helper/utility files: lowercase with underscores: `utils.py`, `styles.py`

**Functions:**
- Snake_case for function names: `load_all()`, `validate_data_integrity()`, `apply_renames()`
- Private methods prefixed with single underscore: `_load_json()`, `_parse_file()`, `_validate_sources()`
- Methods that return boolean values often named with `is_` or `_detect_` prefix: `is_installment`, `_detect_installment()`, `_is_internal_transfer()`

**Variables:**
- Snake_case for local and instance variables: `month_str`, `transaction_pool`, `category_counts`, `source_files`
- Constants in UPPERCASE (occasionally): `HISTORICAL_CUTOFF` in `DataLoader.py` (line 18)
- Column names often use underscores: `description_original`, `cat_type`, `invoice_month`

**Types/Classes:**
- PascalCase for class names: `DataLoader`, `ValidationEngine`, `CategoryEngine`, `DataNormalizer`, `ControlMetrics`
- Descriptive class names that indicate purpose: `ValidationEngine`, `CategoryEngine`

## Code Style

**Formatting:**
- No explicit formatter configured (no .black, .flake8, or .pylintrc files detected)
- Indentation: 4 spaces (observed in all source files)
- Line length: No strict enforcement observed; lines range from 80-120 characters

**Linting:**
- No linter configuration files detected
- Code follows Python conventions by convention rather than enforcement

**Comments & Docstrings:**
- Module-level docstrings present: `"""Validation Engine for Finance Data..."""` at top of files
- Function docstrings use triple quotes with description: `"""Validate source files exist and are readable"""`
- Inline comments use `#` for complex logic sections, especially for multi-step processes
- Section headers for clarity: `# ========== CUTOFF DATE CONFIGURATION ==========` in `DataLoader.py`

## Import Organization

**Order:**
1. Standard library imports (`import sys`, `from datetime import datetime`)
2. Third-party imports (`import pandas as pd`, `import streamlit as st`)
3. Local imports (`from CategoryEngine import CategoryEngine`)

**Example from `DataLoader.py` (lines 1-7):**
```python
from CategoryEngine import CategoryEngine
from ValidationEngine import ValidationEngine
from DataNormalizer import DataNormalizer
import pandas as pd
import os
import io
```

**Path Aliases:**
- No explicit path aliases configured
- Relative imports used within same directory: `from CategoryEngine import CategoryEngine`
- Sys.path manipulation in test files for test discovery: `sys.path.insert(0, os.path.abspath(...))`

## Error Handling

**Patterns:**
- Bare `except:` blocks used but not recommended (seen in multiple places, e.g., `DataLoader._parse_file()` line 188)
- More specific error handling: `except Exception as e:` with logging to stdout via `print()`
- Error messages printed rather than logged: `print(f"   [Erro] Failed to load {filename}: {e}")`
- Fallback values returned on error: `return None` or `return pd.DataFrame()` for file parsing failures
- Try-except-finally not commonly used; relies on try-except with early return

**Example error handling pattern from `CategoryEngine._load_json()` (lines 18-26):**
```python
def _load_json(self, path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return {}
```

## Logging

**Framework:** Console printing via `print()` - no formal logging library used

**Patterns:**
- Status messages with prefixes: `[OK]`, `[Erro]`, `[Aviso]`, `[Arquivos]`
- Portuguese mixed with English in messages (e.g., "Faltando" means "Missing")
- Multi-line output with separators: `"=" * 60` for visual section breaks
- Progress tracking: `print(f"   [OK] Loaded {filename}: {len(df)} rows")`
- No structured logging or log levels (DEBUG, INFO, WARNING, ERROR)

**Example from `DataLoader.load_all()` (lines 58, 76-78):**
```python
print(f"[Arquivos] Found {len(files)} files to load")
if df is not None and not df.empty:
    all_data.append(df)
    print(f"   [OK] Loaded {filename}: {len(df)} rows")
```

## Function Design

**Size:** Functions average 30-50 lines; larger methods (100+ lines) used for complex multi-step operations like `DataLoader._parse_modern_csv()` (618 total lines)

**Parameters:**
- Mix of positional and keyword arguments
- Default parameters used: `def __init__(self, data_dir=None)` (line 20 in `DataLoader.py`)
- Parameters documented in method docstrings: `"""Loads all CSV/TXT files from the data directory."""`

**Return Values:**
- Functions return dictionaries for structured data: `validate_all()` returns report dict with 'status', 'results', etc.
- Return None for missing files or data
- Return empty DataFrames (`pd.DataFrame()`) for parsing failures rather than None
- Tuple returns for multiple values: `return category, subcategory` from `categorize_full()` (line 116 in `CategoryEngine.py`)

## Module Design

**Exports:**
- Classes exported implicitly; no `__all__` declarations observed
- Initialization patterns: `self.transactions = pd.DataFrame()` in constructors to establish available attributes

**Barrel Files:**
- Not used in this codebase
- Direct imports from specific modules: `from CategoryEngine import CategoryEngine`

## Data Handling Patterns

**DataFrames:**
- Heavy use of pandas DataFrames for tabular operations
- Column existence checks before operations: `if 'category' in df.columns`
- Null handling: `df[col].isna().sum()` for null counting, `.dropna()` for removal
- Type conversions: `pd.to_datetime()`, `pd.to_numeric()` with error handling

**Dictionary/JSON:**
- Configuration stored in JSON files: `rules.json`, `budget.json`, `renames.json`
- Dict comprehensions used: `{k: v for k, v in dl_instance.engine.budget.items() if v.get('type') in ['Fixo', 'Income']}`
- Safe dict access with `.get()` method and defaults: `row.get('description', '')`, `v.get('type', 'Variável')`

## String Processing

**Pattern Matching:**
- Substring matching with `.upper()` for case-insensitive rules: `if keyword in desc_upper:`
- Regex patterns for structured data: `re.search(r'\d{2}/\d{2}', description)` for installment detection
- String replacement: `str.replace()` for formatting: `df['amount'].str.replace('R$', '', regex=False)`

## Defensive Programming

**Patterns:**
- Column existence checks before operations: `if 'cat_type' in month_df.columns:`
- DataFrame emptiness checks: `if df.empty:` before processing
- Type checking: `if not description or not isinstance(description, str):`
- Null coalescing with fallbacks: `meta.get('limit', 0.0)` with sensible defaults
- Safe attribute access on rows: `primary.get('description', '')` instead of direct access

**Example from `components.py` (lines 18-28):**
```python
if not month_df.empty and 'amount' in month_df.columns:
    income = month_df[month_df['amount'] > 0]['amount'].sum()
    total_expense = month_df[month_df['amount'] < 0]['amount'].sum()

    if 'cat_type' in month_df.columns:
        fixed_expenses = month_df[(month_df['amount'] < 0) & (month_df['cat_type'] == 'Fixo')]['amount'].sum()
```

---

*Convention analysis: 2026-01-22*
