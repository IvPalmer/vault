"""
Validation Engine for Finance Data
Ensures data integrity across sources and transformations
"""
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import json
import os

class ValidationEngine:
    def __init__(self):
        self.validation_results = []
        self.warnings = []
        self.errors = []

    def validate_all(self, df: pd.DataFrame, source_files: List[str], dl_instance) -> Dict:
        """
        Runs all validation checks and returns comprehensive report
        """
        self.validation_results = []
        self.warnings = []
        self.errors = []

        # 1. Source-level validation
        self._validate_sources(source_files)

        # 2. Data integrity validation
        self._validate_data_integrity(df)

        # 3. Balance reconciliation
        self._validate_balances(df)

        # 4. Categorization validation
        self._validate_categorization(df, dl_instance)

        # 5. Completeness validation
        self._validate_completeness(df, dl_instance)

        # 6. Duplicate detection
        self._validate_duplicates(df)

        # 7. Date continuity validation
        self._validate_date_continuity(df)

        # 8. Amount reasonableness
        self._validate_amounts(df)

        return {
            'status': 'PASS' if len(self.errors) == 0 else 'FAIL',
            'total_checks': len(self.validation_results),
            'passed': len([r for r in self.validation_results if r['status'] == 'PASS']),
            'warnings': len(self.warnings),
            'errors': len(self.errors),
            'results': self.validation_results,
            'warning_details': self.warnings,
            'error_details': self.errors
        }

    def _validate_sources(self, source_files: List[str]):
        """Validate source files exist and are readable"""
        check = {
            'check': 'Source File Validation',
            'status': 'PASS',
            'details': []
        }

        for filepath in source_files:
            if not os.path.exists(filepath):
                self.errors.append(f"Source file not found: {filepath}")
                check['status'] = 'FAIL'
                check['details'].append(f"[Erro] Faltando: {filepath}")
            else:
                check['details'].append(f"[OK] Found: {os.path.basename(filepath)}")

        self.validation_results.append(check)

    def _validate_data_integrity(self, df: pd.DataFrame):
        """Validate required columns and data types"""
        check = {
            'check': 'Data Integrity',
            'status': 'PASS',
            'details': []
        }

        required_cols = ['date', 'description', 'amount', 'account', 'category']

        for col in required_cols:
            if col not in df.columns:
                self.errors.append(f"Faltando required column: {col}")
                check['status'] = 'FAIL'
                check['details'].append(f"[Erro] Faltando column: {col}")
            else:
                # Check for nulls
                null_count = df[col].isna().sum()
                if null_count > 0:
                    self.warnings.append(f"Column '{col}' has {null_count} null values")
                    check['details'].append(f"[Aviso] {col}: {null_count} nulls")
                else:
                    check['details'].append(f"[OK] {col}: No nulls")

        # Validate date format
        if 'date' in df.columns:
            try:
                pd.to_datetime(df['date'])
                check['details'].append(f"[OK] Date format valid")
            except:
                self.errors.append("Invalid date format detected")
                check['status'] = 'FAIL'
                check['details'].append(f"[Erro] Date format invalid")

        self.validation_results.append(check)

    def _validate_balances(self, df: pd.DataFrame):
        """Validate account balances and reconciliation"""
        check = {
            'check': 'Balance Reconciliation',
            'status': 'PASS',
            'details': []
        }

        if df.empty:
            check['status'] = 'SKIP'
            check['details'].append("No data to validate")
            self.validation_results.append(check)
            return

        # Group by account and month
        df['month_str'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m')

        for account in df['account'].unique():
            acc_df = df[df['account'] == account]
            monthly_totals = acc_df.groupby('month_str')['amount'].sum()

            for month, total in monthly_totals.items():
                # Check for unreasonable totals
                if abs(total) > 1000000:  # Over 1M seems suspicious
                    self.warnings.append(f"{account} {month}: Unusually high total R$ {total:,.2f}")
                    check['details'].append(f"[Aviso] {account} {month}: R$ {total:,.2f} (high)")
                else:
                    check['details'].append(f"[OK] {account} {month}: R$ {total:,.2f}")

        self.validation_results.append(check)

    def _validate_categorization(self, df: pd.DataFrame, dl_instance):
        """Validate all transactions are properly categorized"""
        check = {
            'check': 'Categorization',
            'status': 'PASS',
            'details': []
        }

        # Check for uncategorized
        uncategorized = df[df['category'].isna() | (df['category'] == '')]
        if len(uncategorized) > 0:
            self.warnings.append(f"{len(uncategorized)} transactions without category")
            check['details'].append(f"[Aviso] {len(uncategorized)} uncategorized transactions")
            check['status'] = 'WARN'
        else:
            check['details'].append(f"[OK] All {len(df)} transactions categorized")

        # Check for unknown categories (not in budget)
        budget_cats = set(dl_instance.engine.budget.keys())
        df_cats = set(df['category'].dropna().unique())
        unknown_cats = df_cats - budget_cats

        if unknown_cats:
            self.warnings.append(f"Categories not in budget: {unknown_cats}")
            check['details'].append(f"[Aviso] Unknown categories: {', '.join(unknown_cats)}")
            check['status'] = 'WARN'
        else:
            check['details'].append(f"[OK] All categories defined in budget")

        self.validation_results.append(check)

    def _validate_completeness(self, df: pd.DataFrame, dl_instance):
        """Validate expected recurring transactions are present"""
        check = {
            'check': 'Recurring Items Completeness',
            'status': 'PASS',
            'details': []
        }

        # Get all recurring items from budget
        recurring_items = {k: v for k, v in dl_instance.engine.budget.items()
                          if v.get('type') in ['Fixo', 'Income']}

        # Check each month
        df['month_str'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m')
        months = df['month_str'].unique()

        missing_count = 0
        for month in sorted(months):
            month_df = df[df['month_str'] == month]
            month_cats = set(month_df['category'].unique())

            expected_cats = set(recurring_items.keys())
            missing = expected_cats - month_cats

            if missing:
                missing_count += len(missing)
                self.warnings.append(f"{month}: Faltando recurring items: {missing}")
                check['details'].append(f"[Aviso] {month}: {len(missing)} items missing")

        if missing_count == 0:
            check['details'].append(f"[OK] All recurring items present in all months")
        else:
            check['status'] = 'WARN'

        self.validation_results.append(check)

    def _validate_duplicates(self, df: pd.DataFrame):
        """Detect potential duplicate transactions"""
        check = {
            'check': 'Duplicate Detection',
            'status': 'PASS',
            'details': []
        }

        # Check for exact duplicates
        duplicates = df[df.duplicated(subset=['date', 'description', 'amount', 'account'], keep=False)]

        if len(duplicates) > 0:
            dup_groups = duplicates.groupby(['date', 'description', 'amount', 'account']).size()
            self.warnings.append(f"Found {len(dup_groups)} potential duplicate transaction groups")
            check['details'].append(f"[Aviso] {len(duplicates)} potential duplicates detected")
            check['status'] = 'WARN'

            # Show examples
            for idx, count in list(dup_groups.items())[:5]:  # Show first 5
                check['details'].append(f"   • {idx[0]} - {idx[1]}: R$ {idx[2]} ({count}x)")
        else:
            check['details'].append(f"[OK] No duplicate transactions detected")

        self.validation_results.append(check)

    def _validate_date_continuity(self, df: pd.DataFrame):
        """Check for gaps in transaction dates by account"""
        check = {
            'check': 'Date Continuity',
            'status': 'PASS',
            'details': []
        }

        if df.empty:
            check['status'] = 'SKIP'
            self.validation_results.append(check)
            return

        df['date_obj'] = pd.to_datetime(df['date'])

        for account in df['account'].unique():
            acc_df = df[df['account'] == account].sort_values('date_obj')
            dates = acc_df['date_obj']

            if len(dates) < 2:
                continue

            # Check for gaps > 60 days (might indicate missing statements)
            date_diffs = dates.diff()
            large_gaps = date_diffs[date_diffs > pd.Timedelta(days=60)]

            if len(large_gaps) > 0:
                self.warnings.append(f"{account}: {len(large_gaps)} gaps > 60 days")
                check['details'].append(f"[Aviso] {account}: {len(large_gaps)} large gaps")
                check['status'] = 'WARN'
            else:
                check['details'].append(f"[OK] {account}: No large gaps")

        self.validation_results.append(check)

    def _validate_amounts(self, df: pd.DataFrame):
        """Validate transaction amounts are reasonable"""
        check = {
            'check': 'Amount Reasonableness',
            'status': 'PASS',
            'details': []
        }

        # Check for zero amounts
        zero_amounts = df[df['amount'] == 0]
        if len(zero_amounts) > 0:
            self.warnings.append(f"{len(zero_amounts)} transactions with R$ 0.00")
            check['details'].append(f"[Aviso] {len(zero_amounts)} zero-amount transactions")

        # Check for extremely large amounts (potential data errors)
        large_amounts = df[abs(df['amount']) > 100000]  # > R$ 100k
        if len(large_amounts) > 0:
            self.warnings.append(f"{len(large_amounts)} transactions > R$ 100,000")
            check['details'].append(f"[Aviso] {len(large_amounts)} very large transactions")
            for idx, row in large_amounts.head(3).iterrows():
                check['details'].append(f"   • {row['date']}: {row['description']} - R$ {row['amount']:,.2f}")

        if len(zero_amounts) == 0 and len(large_amounts) == 0:
            check['details'].append(f"[OK] All amounts within reasonable range")

        self.validation_results.append(check)

    def generate_validation_report(self, report_path: str = None):
        """Generate a detailed validation report"""
        if not report_path:
            report_path = os.path.join(os.path.dirname(__file__), "validation_report.json")

        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_checks': len(self.validation_results),
                'passed': len([r for r in self.validation_results if r['status'] == 'PASS']),
                'warnings': len(self.warnings),
                'errors': len(self.errors),
                'status': 'PASS' if len(self.errors) == 0 else 'FAIL'
            },
            'checks': self.validation_results,
            'warnings': self.warnings,
            'errors': self.errors
        }

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        return report_path

    def print_validation_summary(self):
        """Print a console-friendly validation summary"""
        print("\n" + "="*60)
        print("[Validação] VALIDATION REPORT")
        print("="*60)

        for result in self.validation_results:
            status_icon = "[OK]" if result['status'] == 'PASS' else "[Aviso]" if result['status'] == 'WARN' else "[Erro]"
            print(f"\n{status_icon} {result['check']}")
            for detail in result.get('details', []):
                print(f"  {detail}")

        print("\n" + "="*60)
        print(f"[Métricas] SUMMARY")
        print("="*60)
        print(f"Total Checks: {len(self.validation_results)}")
        print(f"[OK] Passed: {len([r for r in self.validation_results if r['status'] == 'PASS'])}")
        print(f"[Aviso] Warnings: {len(self.warnings)}")
        print(f"[Erro] Errors: {len(self.errors)}")
        print(f"\nOverall Status: {'🟢 PASS' if len(self.errors) == 0 else '🔴 FAIL'}")
        print("="*60 + "\n")
