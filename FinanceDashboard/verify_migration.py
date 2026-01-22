from DataLoader import DataLoader
import pandas as pd

def verify():
    print("🧪 Starting Verification...")
    dl = DataLoader()
    df = dl.load_all()
    
    # 1. Verify Jan 2026 Expenses
    # Filter: Date >= 2026-01-01 & < 2026-02-01
    mask_jan = (df['date'] >= '2026-01-01') & (df['date'] < '2026-02-01')
    jan_data = df[mask_jan]
    
    jan_expenses = jan_data[jan_data['amount'] < 0]['amount'].sum()
    print(f"\n📅 Jan 2026 Expenses: R$ {abs(jan_expenses):,.2f}")
    
    print("\n[Validação] Breakdown by Source (Jan 2026):")
    breakdown = jan_data[jan_data['amount'] < 0].groupby('source')['amount'].sum()
    print(breakdown)
    
    # Benchmark from Swift App: ~13k (or more precise if we check report)
    # Let's verify matches ballpark
    
    # 2. Verify Credit Card Balances (Jan or "Open Bill" logic?)
    # Swift App logic was summing specific CSV files for the month.
    # Here let's filter by Account and Date Range of the "Current Bill" (e.g. Closing Date)
    # Visa Closing: 17th?
    # Master Closing: 11th?
    
    # Let's just sum ALL data for Jan 2026 for each card to see if it matches "Current Invoice" + "Next Invoice" roughly
    
    mask_visa = (df['account'] == 'Visa Infinite') & mask_jan
    visa_jan = df.loc[mask_visa, 'amount'].sum()
    
    mask_master = (df['account'] == 'Mastercard Black') & mask_jan
    master_jan = df.loc[mask_master, 'amount'].sum()
    
    print(f"💳 Visa Jan Total: R$ {visa_jan:,.2f}")
    print(f"💳 Master Jan Total: R$ {master_jan:,.2f}")
    
    # 3. Check specific known transaction
    # "Pix Aut SEM PARAR" should be -94.17
    sem_parar = df[df['description'].str.contains("SEM PARAR", na=False)]
    if not sem_parar.empty:
        print(f"\n[OK] Found 'SEM PARAR': {sem_parar.iloc[0]['amount']}")
    else:
        print("\n[Erro] 'SEM PARAR' not found!")
        
    print("\n[Validação] Top 5 Positive Transactions (Visa/Master):")
    positives = df[(df['amount'] > 0) & (df['account'].isin(['Visa Infinite', 'Mastercard Black']))]
    print(positives.sort_values(by='amount', ascending=False).head(5)[['date', 'description', 'amount', 'account']])
    
    print("\n[Validação] Top 5 Duplicate Candidates (Description match):")
    # Check for "UBER" or similar common matches
    matches = df[df['description'].str.contains("UBER", na=False, case=False)]
    print(matches.head(10)[['date', 'description', 'amount', 'account']])

if __name__ == "__main__":
    verify()
