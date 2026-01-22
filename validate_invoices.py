"""
Invoice Payment Validation Report
Validates that credit card invoice totals match checking account payments
"""
from DataLoader import DataLoader
import pandas as pd

def main():
    loader = DataLoader()
    df = loader.load_all()

    # Get all card transactions with invoice metadata
    cards = df[df['invoice_month'].notna()].copy()
    checking = df[df['account'] == 'Checking'].copy()

    # Get unique invoice periods
    invoice_periods = cards['invoice_month'].unique()
    invoice_periods = sorted([p for p in invoice_periods if pd.notna(p)])

    print("=" * 80)
    print("CREDIT CARD INVOICE VALIDATION REPORT")
    print("=" * 80)
    print()

    for invoice_period in invoice_periods:
        invoice_data = cards[cards['invoice_month'] == invoice_period].copy()

        if len(invoice_data) == 0:
            continue

        # Get invoice metadata
        close_date = invoice_data['invoice_close_date'].iloc[0]
        payment_date = invoice_data['invoice_payment_date'].iloc[0]

        print(f"{'=' * 80}")
        print(f"INVOICE: {invoice_period}")
        print(f"Close Date: {close_date.date()}")
        print(f"Payment Date: {payment_date.date()}")
        print(f"{'=' * 80}")
        print()

        # Calculate invoice totals by account
        print("INVOICE TOTALS (expenses only):")
        for account in ['Mastercard Black', 'Visa Infinite']:
            acc_data = invoice_data[invoice_data['account'] == account]
            if len(acc_data) > 0:
                expenses = acc_data[acc_data['amount'] < 0]['amount'].sum()
                credits = acc_data[acc_data['amount'] > 0]['amount'].sum()
                total = acc_data['amount'].sum()

                print(f"  {account}:")
                print(f"    Expenses: R$ {expenses:>12,.2f}")
                print(f"    Credits:  R$ {credits:>12,.2f}")
                print(f"    Net:      R$ {total:>12,.2f}")
        print()

        # Find payments on the payment date
        payments_on_date = checking[checking['date'] == payment_date].copy()

        if len(payments_on_date) > 0:
            print(f"PAYMENTS ON {payment_date.date()}:")
            for idx, row in payments_on_date.iterrows():
                desc = row['description']
                amt = row['amount']

                # Filter for card payments
                if amt < 0 and any(keyword in desc.upper() for keyword in [
                    'FATURA', 'PERSON', 'ITAU', 'ITAUCARD', 'CARTAO', 'CARD'
                ]):
                    print(f"  {desc[:50]:50} R$ {amt:>12,.2f}")
        else:
            print(f"WARNING: No transactions found on payment date {payment_date.date()}")

            # Search nearby dates
            print(f"\n  Searching {payment_date.date()} ± 5 days...")
            nearby = checking[
                (checking['date'] >= payment_date - pd.Timedelta(days=5)) &
                (checking['date'] <= payment_date + pd.Timedelta(days=5))
            ].copy()

            for idx, row in nearby.iterrows():
                desc = row['description']
                amt = row['amount']
                date = row['date'].strftime('%Y-%m-%d')

                if amt < 0 and any(keyword in desc.upper() for keyword in [
                    'FATURA', 'PERSON', 'ITAU', 'ITAUCARD'
                ]):
                    print(f"  {date} | {desc[:40]:40} R$ {amt:>12,.2f}")

        print()
        print()

if __name__ == "__main__":
    main()
