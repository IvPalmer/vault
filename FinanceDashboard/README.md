# Finance Dashboard

A Streamlit-based personal finance dashboard for tracking expenses, managing budgets, and analyzing financial data.

## Features

- Transaction categorization with customizable rules
- Budget tracking and monitoring
- Interactive data visualization
- CSV and OFX file import support
- Category-based expense analysis

## Setup

1. Create a virtual environment:
```bash
cd FinanceDashboard
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the dashboard:
```bash
streamlit run dashboard.py
```

Or use the provided script:
```bash
./run.sh
```

## Project Structure

- `dashboard.py` - Main Streamlit application
- `components.py` - UI components
- `DataLoader.py` - Data loading and processing
- `CategoryEngine.py` - Transaction categorization logic
- `utils.py` - Utility functions
- `styles.py` - CSS styling
- `budget.json` - Budget configuration
- `rules.json` - Categorization rules
- `renames.json` - Account name mappings

## Data Privacy

User data files (CSV, XLSX, OFX) are excluded from version control to protect privacy. Sample data structure is documented but actual financial data remains local.
