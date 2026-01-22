# Technology Stack

**Analysis Date:** 2026-01-22

## Languages

**Primary:**
- Python 3.13.1 - Core application logic, data processing, and dashboard backend

## Runtime

**Environment:**
- Python 3.13.1
- Virtual environment via `venv`

**Package Manager:**
- pip - Python package manager
- Lockfile: `requirements.txt` (simple requirements, no lock file)

## Frameworks

**Core:**
- Streamlit 1.x - Web dashboard framework for interactive financial UI (`FinanceDashboard/dashboard.py`)

**Data Processing:**
- pandas - DataFrames for transaction data manipulation and analysis (`FinanceDashboard/DataLoader.py`, `FinanceDashboard/components.py`)
- plotly - Interactive data visualization and charting (`FinanceDashboard/components.py`)

**UI Components:**
- st-aggrid - Advanced data grid component for Streamlit (`FinanceDashboard/components.py`, `FinanceDashboard/dashboard.py`)

**Excel Support:**
- openpyxl - Excel file reading/writing for sample data (`FinanceDashboard/SampleData/`)

**Utilities:**
- watchdog - File system event monitoring (likely for data reloading)

## Key Dependencies

**Critical:**
- streamlit - Web application framework
- pandas - Data manipulation library
- plotly - Interactive visualization engine
- st-aggrid - Streamlit table/grid component

**Infrastructure:**
- openpyxl - Excel file format support for legacy data imports

## Configuration

**Environment:**
- Manual configuration via JSON files:
  - `budget.json` - Budget limits and category metadata
  - `rules.json` - Merchant name to category mapping rules
  - `subcategory_rules.json` - Subcategory classification rules
  - `renames.json` - Transaction description normalization mappings
- No environment variables detected (.env file not present)
- Balance overrides stored in `balance_overrides.json`

**Build:**
- No build config detected - pure Python/Streamlit
- Development launcher: `run.sh` shell script
  - Creates/activates venv if needed
  - Installs dependencies
  - Launches Streamlit dashboard

## Platform Requirements

**Development:**
- Python 3.13.1
- Unix-like shell (bash, zsh)
- File system access to data directory

**Production:**
- Web browser for Streamlit UI (localhost:8501 default)
- File system for CSV/OFX/TXT data files and JSON configs
- No external server or cloud deployment required

---

*Stack analysis: 2026-01-22*
