# 💰 Vault - Personal Finance Analytics

A comprehensive financial dashboard for tracking income, expenses, investments, and cash flow across multiple accounts.

**Version:** 2.0.0
**Status:** 🟢 Production Ready
**Validation Accuracy:** 99-100%

---

## 🎯 Key Features

- ✅ Multi-account tracking with automated categorization
- ✅ Invoice period mapping with bank statement validation
- ✅ Budget tracking with control metrics
- ✅ Internal transfer detection (avoid double-counting)
- ✅ Balance reconciliation across all accounts
- ✅ Data validation with 99%+ accuracy

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run FinanceDashboard/main.py
```

Dashboard opens at `http://localhost:8501`

---

## 📊 Recent Updates (v2.0.0 - Jan 22, 2026)

### Critical Invoice Validation Fix

**Problem:** Invoice totals inflated by 6x (R$ 68k vs R$ 11k actual)

**Solution:**
- ✅ Fixed payment entry duplication (R$ 30k per invoice)
- ✅ Fixed installment filtering logic (R$ 3k per invoice)
- ✅ Added invoice period metadata for cash flow tracking

**Results:**
```
January 2026: 99.8% match (R$ 18.37 diff)
December 2025: 100% match (R$ 0.48 diff)
```

See `FINAL_SOLUTION_SUMMARY.md` for details.

---

## 📁 Project Structure

```
Vault/
├── FinanceDashboard/              # Main dashboard application
│   ├── main.py                    # Streamlit app
│   ├── DataLoader.py              # ETL pipeline ✨ UPDATED
│   ├── DataNormalizer.py          # Data standardization ✨ NEW
│   ├── CategoryEngine.py          # Categorization logic
│   ├── ValidationEngine.py        # Data validation
│   └── SampleData/                # Transaction data
│
├── CHANGELOG.md                   # Version history ✨ NEW
├── PROJECT_STATUS.md              # Current state & roadmap ✨ NEW
├── FINAL_SOLUTION_SUMMARY.md     # Technical details ✨ NEW
└── README.md                      # This file
```

---

## 📚 Documentation

### Getting Started
- `README.md` (this file) - Quick overview
- `FinanceDashboard/README.md` - Detailed setup

### Implementation
- `FINAL_SOLUTION_SUMMARY.md` - Complete v2.0.0 solution
- `CHANGELOG.md` - Version history
- `PROJECT_STATUS.md` - Current state and roadmap

### Technical
- `INVOICE_SYSTEM_FINAL.md` - Invoice mapping system
- `MODELO_DADOS_PADRONIZADO.md` - Data model specification
- `VALIDACAO_FATURAS_IMPLEMENTADA.md` - Validation methodology

---

## 🎓 Key Concepts

### Invoice Period Mapping
- CSV filename indicates **invoice month**, not transaction month
- `master-0126.csv` = January 2026 invoice (contains December purchases)
- Payment due: 5th of invoice month

### Installment Handling
- `"01/12"` = 1st installment of 12, NOT invoice month
- Bank CSVs already contain correct transactions
- No filtering needed

### Payment Filtering
- Card CSVs include previous payment as 3 entries
- Automatically filtered to prevent duplication

---

## 📊 Statistics

- **Transactions:** 7,835
- **Date Range:** Sep 2022 - Jan 2026 (40 months)
- **Accounts:** 4 (Checking, 2x Credit Cards, 1x Additional)
- **Validation:** 99-100% accuracy
- **Load Time:** ~2 seconds

---

## 🔒 Security

- All data stored locally
- No external API calls
- No data transmission
- Data files git-ignored

---

**Last Updated:** 2026-01-22
**Next Review:** As needed

For detailed information, see `PROJECT_STATUS.md`
