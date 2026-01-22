"""
Systematic testing of the current FinanceDashboard application
Tests data loading, categorization, and core functionality
"""

import sys
import os
from pathlib import Path

# Add FinanceDashboard to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'FinanceDashboard'))

from DataLoader import DataLoader
import pandas as pd
import json


def test_data_loading():
    """Test loading all data sources"""
    print("\n" + "=" * 60)
    print("TEST: Data Loading")
    print("=" * 60)

    dl = DataLoader()
    df = dl.load_all()

    print(f"\n✓ Total transactions loaded: {len(df)}")
    print(f"✓ Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"✓ Unique accounts: {df['account'].unique()}")
    print(f"✓ Total amount: R$ {df['amount'].sum():,.2f}")

    # Check for required columns
    required_cols = ['date', 'description', 'amount', 'account', 'category']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        print(f"✗ Missing columns: {missing}")
        return False
    else:
        print(f"✓ All required columns present")

    # Check for nulls
    null_counts = df[required_cols].isnull().sum()
    if null_counts.any():
        print(f"\n⚠ Null values found:")
        for col, count in null_counts[null_counts > 0].items():
            print(f"  {col}: {count} nulls ({count/len(df)*100:.1f}%)")
    else:
        print(f"✓ No null values in required columns")

    return True, df, dl


def test_categorization(df, dl):
    """Test categorization functionality"""
    print("\n" + "=" * 60)
    print("TEST: Categorization")
    print("=" * 60)

    # Check category distribution
    cat_counts = df['category'].value_counts()
    print(f"\n✓ Categories found: {len(cat_counts)}")
    print(f"\nTop 10 categories:")
    for cat, count in cat_counts.head(10).items():
        pct = count / len(df) * 100
        print(f"  {cat}: {count} ({pct:.1f}%)")

    # Check uncategorized
    uncategorized = df[df['category'].isnull() | (df['category'] == 'OUTROS')]
    print(f"\n⚠ Uncategorized transactions: {len(uncategorized)} ({len(uncategorized)/len(df)*100:.1f}%)")

    if len(uncategorized) > 0:
        print(f"\nSample uncategorized transactions:")
        for _, row in uncategorized.head(5).iterrows():
            print(f"  {row['date']}: {row['description'][:50]} - R$ {row['amount']:.2f}")

    # Check category types
    if 'cat_type' in df.columns:
        type_counts = df['cat_type'].value_counts()
        print(f"\n✓ Category types:")
        for cat_type, count in type_counts.items():
            total = df[df['cat_type'] == cat_type]['amount'].sum()
            print(f"  {cat_type}: {count} transactions, R$ {total:,.2f}")

    # Check subcategories
    if 'subcategory' in df.columns:
        subcat_counts = df['subcategory'].value_counts()
        print(f"\n✓ Subcategories found: {len(subcat_counts)}")
        print(f"✓ Transactions with subcategories: {df['subcategory'].notna().sum()}")

    return True


def test_rules_and_budget():
    """Test loading of rules and budget configuration"""
    print("\n" + "=" * 60)
    print("TEST: Rules & Budget Configuration")
    print("=" * 60)

    base_dir = os.path.join(os.path.dirname(__file__), '..', 'FinanceDashboard')

    # Load rules.json
    rules_path = os.path.join(base_dir, 'rules.json')
    if os.path.exists(rules_path):
        with open(rules_path, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        print(f"✓ rules.json loaded: {len(rules)} rules")
        print(f"\nSample rules:")
        for keyword, category in list(rules.items())[:5]:
            print(f"  '{keyword}' → {category}")
    else:
        print(f"✗ rules.json not found")

    # Load budget.json
    budget_path = os.path.join(base_dir, 'budget.json')
    if os.path.exists(budget_path):
        with open(budget_path, 'r', encoding='utf-8') as f:
            budget = json.load(f)
        print(f"\n✓ budget.json loaded: {len(budget)} categories")

        # Count by type
        types = {}
        for cat, meta in budget.items():
            cat_type = meta.get('type', 'Unknown')
            types[cat_type] = types.get(cat_type, 0) + 1

        print(f"\nCategories by type:")
        for cat_type, count in types.items():
            print(f"  {cat_type}: {count}")
    else:
        print(f"✗ budget.json not found")

    # Load subcategory_rules.json
    subcat_path = os.path.join(base_dir, 'subcategory_rules.json')
    if os.path.exists(subcat_path):
        with open(subcat_path, 'r', encoding='utf-8') as f:
            subcat_rules = json.load(f)
        print(f"\n✓ subcategory_rules.json loaded")
        print(f"  Categories with subcategory rules: {len(subcat_rules)}")
    else:
        print(f"✗ subcategory_rules.json not found")

    return True


def test_installment_detection(df):
    """Test installment pattern detection"""
    print("\n" + "=" * 60)
    print("TEST: Installment Detection")
    print("=" * 60)

    # Look for installment patterns like "1/3", "2/12", etc.
    import re
    pattern = r'\d{1,2}/\d{1,2}'

    df['has_installment'] = df['description'].str.contains(pattern, regex=True, na=False)
    installments = df[df['has_installment']]

    print(f"\n✓ Transactions with installment pattern: {len(installments)}")

    if len(installments) > 0:
        total_installment_amount = installments['amount'].sum()
        print(f"✓ Total installment amount: R$ {abs(total_installment_amount):,.2f}")

        print(f"\nSample installment transactions:")
        for _, row in installments.head(10).iterrows():
            match = re.search(pattern, row['description'])
            if match:
                print(f"  {row['date']}: {row['description'][:60]} - R$ {row['amount']:.2f}")

    return True


def test_account_distribution(df):
    """Test account distribution"""
    print("\n" + "=" * 60)
    print("TEST: Account Distribution")
    print("=" * 60)

    account_summary = df.groupby('account').agg({
        'amount': ['count', 'sum'],
        'date': ['min', 'max']
    }).round(2)

    print(f"\nAccount summary:")
    for account in df['account'].unique():
        acc_data = df[df['account'] == account]
        count = len(acc_data)
        total = acc_data['amount'].sum()
        date_min = acc_data['date'].min()
        date_max = acc_data['date'].max()
        print(f"\n  {account}:")
        print(f"    Transactions: {count}")
        print(f"    Total: R$ {total:,.2f}")
        print(f"    Date range: {date_min} to {date_max}")

    return True


def test_monthly_analysis(df):
    """Test monthly aggregation"""
    print("\n" + "=" * 60)
    print("TEST: Monthly Analysis")
    print("=" * 60)

    df['month'] = pd.to_datetime(df['date']).dt.to_period('M')

    monthly = df.groupby('month')['amount'].agg(['count', 'sum']).round(2)

    print(f"\nMonthly transaction summary:")
    print(f"Total months: {len(monthly)}")
    print(f"\nLast 6 months:")
    for month, row in monthly.tail(6).iterrows():
        print(f"  {month}: {row['count']} transactions, R$ {row['sum']:,.2f}")

    # Income vs Expenses by month
    df_monthly_type = df.groupby(['month', 'cat_type'])['amount'].sum().unstack(fill_value=0).round(2)

    if not df_monthly_type.empty:
        print(f"\nLast 3 months by category type:")
        for month, row in df_monthly_type.tail(3).iterrows():
            print(f"\n  {month}:")
            for cat_type, amount in row.items():
                if amount != 0:
                    print(f"    {cat_type}: R$ {amount:,.2f}")

    return True


def test_data_quality(df):
    """Test data quality issues"""
    print("\n" + "=" * 60)
    print("TEST: Data Quality")
    print("=" * 60)

    issues = []

    # Check for duplicate transactions
    duplicates = df[df.duplicated(subset=['date', 'description', 'amount', 'account'], keep=False)]
    if len(duplicates) > 0:
        issues.append(f"Duplicates: {len(duplicates)} transactions")
        print(f"✗ Found {len(duplicates)} duplicate transactions")
    else:
        print(f"✓ No duplicate transactions")

    # Check for zero amounts
    zero_amounts = df[df['amount'] == 0]
    if len(zero_amounts) > 0:
        issues.append(f"Zero amounts: {len(zero_amounts)} transactions")
        print(f"⚠ Found {len(zero_amounts)} transactions with zero amount")
    else:
        print(f"✓ No zero amount transactions")

    # Check for future dates
    future_dates = df[pd.to_datetime(df['date']) > pd.Timestamp.now()]
    if len(future_dates) > 0:
        issues.append(f"Future dates: {len(future_dates)} transactions")
        print(f"⚠ Found {len(future_dates)} transactions with future dates")
    else:
        print(f"✓ No future date transactions")

    # Check for very old dates (potential data errors)
    very_old = df[pd.to_datetime(df['date']) < pd.Timestamp('2020-01-01')]
    if len(very_old) > 0:
        print(f"⚠ Found {len(very_old)} transactions before 2020")

    # Check for suspicious amounts (very large)
    large_amounts = df[abs(df['amount']) > 50000]
    if len(large_amounts) > 0:
        print(f"\n⚠ Found {len(large_amounts)} transactions over R$ 50,000:")
        for _, row in large_amounts.iterrows():
            print(f"  {row['date']}: {row['description'][:50]} - R$ {row['amount']:,.2f}")

    if not issues:
        print(f"\n✓ Data quality: GOOD")
    else:
        print(f"\n⚠ Data quality issues found: {len(issues)}")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("THE VAULT - Current Application Testing")
    print("=" * 60)

    try:
        # Run tests
        success, df, dl = test_data_loading()

        if success and not df.empty:
            test_categorization(df, dl)
            test_rules_and_budget()
            test_installment_detection(df)
            test_account_distribution(df)
            test_monthly_analysis(df)
            test_data_quality(df)

            print("\n" + "=" * 60)
            print("✓ ALL TESTS COMPLETED")
            print("=" * 60)
        else:
            print("\n✗ Data loading failed, cannot continue tests")

    except Exception as e:
        print(f"\n✗ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
