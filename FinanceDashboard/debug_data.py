from DataLoader import DataLoader
import pandas as pd
import os

print("--- Starting Debug ---")
dl = DataLoader()
# Force reload logic inspection
# We will manually invoke parsing on the specific file to isolate issues
path = os.path.join(dl.data_dir, "Finanças - CONTROLE CC RAFA.csv")
if os.path.exists(path):
    print(f"File exists: {path}")
    print(f"Size: {os.path.getsize(path)} bytes")
    
    # Test Raw Read
    try:
        raw = pd.read_csv(path)
        print("Raw Columns:", raw.columns.tolist())
        print("Raw Shape:", raw.shape)
        print("First row:", raw.iloc[0].to_dict())
    except Exception as e:
        print(f"Raw Read Error: {e}")

    # Test Loader Parsing
    parsed = dl._parse_historical_csv(path, "Checking")
    if parsed is not None and not parsed.empty:
        print("Parsed Shape:", parsed.shape)
        print("Parsed Columns:", parsed.columns.tolist())
        print("Date Range:", parsed['date'].min(), "-", parsed['date'].max())
        print("Sample Amounts:", parsed['amount'].head().tolist())
        print("Null Dates:", parsed['date'].isnull().sum())
    else:
        print("Parsed Result is EMPTY or None")
        
else:
    print(f"File NOT found: {path}")

# Load All check
all_df = dl.load_all()
print(f"Total Loaded Rows: {len(all_df)}")
checking_df = all_df[all_df['account'] == 'Checking']
print(f"Total Checking Rows: {len(checking_df)}")
if not checking_df.empty:
    print("Checking Months:", checking_df['date'].dt.to_period('M').unique())
