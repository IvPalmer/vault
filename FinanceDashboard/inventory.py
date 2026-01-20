from DataLoader import DataLoader
import pandas as pd
import os

def check_coverage():
    dl = DataLoader()
    
    all_rows = []
    
    files = [f for f in os.listdir(dl.data_dir) if not f.startswith(".")]
    print(f"📂 Scanning {len(files)} files...")
    
    for filename in files:
        path = os.path.join(dl.data_dir, filename)
        # Use _parse_file directly to get RAW data (ignoring the Nov 1st cutoff in load_all)
        try:
            df = dl._parse_file(path, filename)
            if df is not None and not df.empty:
                # Add metadata
                df['filename'] = filename
                df['is_historical'] = "Finanças" in filename
                df['month_key'] = df['date'].dt.to_period('M')
                all_rows.append(df)
        except Exception as e:
            print(f"Error parsing {filename}: {e}")

    if not all_rows:
        print("No data found.")
        return

    full_df = pd.concat(all_rows, ignore_index=True)
    
    # Aggregation
    # Group by Account, Month, IsHistorical
    summary = full_df.groupby(['account', 'month_key', 'is_historical']).size().unstack(fill_value=0)
    
    # Sort by month
    summary = summary.sort_index()
    
    print("\n📊 Data Coverage (Row Counts per Month):")
    print("Columns: False = Raw Statements, True = Historical/Old App")
    pd.set_option('display.max_rows', None)
    print(summary)
    
    # Check specifically for gaps in 2025
    print("\n🔍 Missing Data Analysis (2025):")
    for acc in full_df['account'].unique():
        print(f"\n--- {acc} ---")
        acc_df = full_df[full_df['account'] == acc]
        # Get set of present months
        present_months = acc_df['month_key'].unique()
        
        # Generate expected range (Jan 2025 to Jan 2026)
        expected = pd.period_range(start='2025-01', end='2026-02', freq='M')
        
        missing = []
        for m in expected:
            if m not in present_months:
                missing.append(str(m))
        
        if missing:
            print(f"❌ Missing Months: {', '.join(missing)}")
        else:
            print("✅ Full coverage for 2025-2026!")

if __name__ == "__main__":
    check_coverage()
