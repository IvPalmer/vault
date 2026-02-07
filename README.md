# THE VAULT — Personal Finance Dashboard

Django + React application for tracking income, expenses, investments, and cash flow across multiple accounts.

## Stack

- **Backend:** Django 5.2 + Django REST Framework
- **Frontend:** React 18 + TanStack Table + TanStack Query + Recharts
- **Database:** PostgreSQL 15
- **Dev Server:** Vite

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8001

# Frontend
npm install
npx vite --port 5175
```

Backend API at `http://localhost:8001/api/`
Frontend at `http://localhost:5175/`

## Project Structure

```
Vault/
├── backend/                  # Django API
│   ├── vault_project/        # Django project settings
│   ├── api/                  # DRF app (models, views, services)
│   │   ├── models.py         # Account, Category, Transaction, RecurringMapping, etc.
│   │   ├── views.py          # ViewSets + analytics endpoints
│   │   ├── services.py       # Business logic (metricas, recurring, projection)
│   │   └── management/       # Import commands
│   └── requirements.txt
├── src/                      # React frontend
│   ├── api/                  # API client
│   ├── context/              # MonthContext (shared month state)
│   ├── hooks/                # useInvalidateAnalytics
│   ├── components/           # UI components
│   │   ├── Layout.jsx        # Tab navigation + MonthPicker
│   │   ├── MetricasSection   # Unified metrics dashboard (15 cards + balance input)
│   │   ├── RecurringSection  # Recurring items with inline editing
│   │   ├── OrcamentoSection  # Variable budget tracking
│   │   ├── CardsSection      # Credit card transactions
│   │   ├── CheckingSection   # Checking account transactions
│   │   ├── ProjectionSection # 6-month projection chart + table
│   │   └── VaultTable.jsx    # Shared table component (TanStack)
│   ├── App.jsx
│   └── main.jsx
├── FinanceDashboard/         # Legacy Streamlit app (data loader/ETL still used)
├── docker-compose.yml
├── package.json
└── vite.config.js
```

## Features

### Monthly Overview
- **METRICAS** — 15 unified metric cards in a 5-column grid:
  - Income: ENTRADAS ATUAIS, ENTRADAS PROJETADAS
  - Expenses: GASTOS ATUAIS, GASTOS PROJETADOS, GASTOS FIXOS, GASTOS VARIAVEIS
  - Credit Cards: FATURA MASTER (Black + Rafa combined), FATURA VISA
  - Installments: PARCELAS
  - Pending: A ENTRAR, A PAGAR (from RecurringMapping unlinked items)
  - Projections: SALDO PROJETADO, DIAS ATE FECHAMENTO, GASTO DIARIO MAX
  - Health: SAUDE DO MES (SAUDAVEL / ATENCAO / CRITICO)
- **SALDO EM CONTA** — Manual bank balance input that drives projected metrics
- **RECORRENTES** — Recurring budget items with inline transaction matching
- **ORCAMENTO VARIAVEL** — Category-level variable spending with progress bars
- **CONTROLE CARTOES** — CC transactions per card (Mastercard/Visa/Rafa tabs)
- **CONTA CORRENTE** — Checking account transactions
- **PROJECAO** — 6-month stacked bar chart + table

### Settings
- Recurring item template editor (global defaults applied to new months)
- CSV/OFX statement import

### Accounts
- Checking (Itau)
- Mastercard Black (credit card)
- Visa Infinite (credit card)
- Mastercard - Rafa (credit card)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analytics/metricas/` | GET | Unified dashboard metrics (15 cards) |
| `/api/analytics/recurring/` | GET | Recurring items with status/suggestions |
| `/api/analytics/cards/` | GET | Credit card transactions by invoice |
| `/api/analytics/installments/` | GET | Installment breakdown |
| `/api/analytics/checking/` | GET | Checking account transactions |
| `/api/analytics/projection/` | GET | 6-month cash flow projection |
| `/api/analytics/orcamento/` | GET | Variable budget by category |
| `/api/analytics/balance/` | POST | Save manual bank balance |
| `/api/analytics/recurring/map/` | POST/DELETE | Link/unlink transactions |
| `/api/analytics/recurring/reapply/` | POST | Reset month from template |
| `/api/analytics/smart-categorize/` | POST | Auto-categorize transactions |
| `/api/import/` | GET/POST | Statement import management |
